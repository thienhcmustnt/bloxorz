"""Spawn-isolated execution, bounded wall time and independent measurement passes."""

from __future__ import annotations
import importlib
import multiprocessing as mp
from multiprocessing.connection import Connection
import time
import traceback
import tracemalloc
from typing import Any, Literal
from core.level import Level
from core.state import State
from solvers.base import Problem, SearchResult

ALGORITHMS = {name: f"solvers.{name}:solve" for name in ("bfs", "dfs", "ids", "ucs", "astar")}


def _worker(
    connection: Connection,
    entry: str,
    data: dict[str, Any],
    start: State | None,
    heuristic: str | None,
    cost_model: str,
    measure: str,
) -> None:
    try:
        module, symbol = entry.split(":")
        solve = getattr(importlib.import_module(module), symbol)
        from solvers.heuristics import HEURISTICS

        problem = Problem(
            Level.from_dict(data), start, cost_model, HEURISTICS[heuristic] if heuristic else None
        )
        snapshot = vars(problem).copy()
        level_snapshot = problem.level.to_dict()
        if measure == "memory":
            tracemalloc.start()
        began = time.perf_counter()
        result = solve(problem)
        elapsed = time.perf_counter() - began
        peak = tracemalloc.get_traced_memory()[1] / 1024 if measure == "memory" else 0.0
        if tracemalloc.is_tracing():
            tracemalloc.stop()
        if vars(problem) != snapshot or problem.level.to_dict() != level_snapshot:
            raise ValueError("Solver mutated Problem or Level")
        if not isinstance(result, SearchResult):
            raise TypeError("solve must return SearchResult")
        result.solution_length = len(result.path)
        result.search_time = elapsed if measure == "time" else 0.0
        result.peak_memory_kb = peak
        connection.send(result)
    except NotImplementedError:
        connection.send(SearchResult(reason="not_implemented"))
    except BaseException as exc:
        detail = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__, limit=3))
        connection.send(SearchResult(reason=f"error: {detail[-1800:]}"))
    finally:
        if tracemalloc.is_tracing():
            tracemalloc.stop()
        connection.close()


def run_solver(
    algo: str,
    level: Level,
    *,
    heuristic: str | None = None,
    timeout: float = 30,
    measure: Literal["time", "memory"] = "time",
    start_state: State | None = None,
    cost_model: str = "risk",
) -> SearchResult:
    """Execute one measurement pass. Timeout includes spawn/import overhead.

    The child is always joined/terminated; the pipe is drained before joining so
    long paths cannot deadlock on a full IPC buffer. Unknown registry entries
    cannot break other solvers. A missing measurement is reported by its reason.
    """
    if algo not in ALGORITHMS:
        return SearchResult(reason=f"error: unknown algorithm {algo}")
    if measure not in ("time", "memory") or timeout <= 0 or cost_model not in ("risk", "unit"):
        return SearchResult(reason="error: invalid execution options")
    if heuristic not in (None, "center", "relaxed"):
        return SearchResult(reason="error: unknown heuristic")
    ctx = mp.get_context("spawn")
    receive, send = ctx.Pipe(duplex=False)
    process = ctx.Process(
        target=_worker,
        args=(send, ALGORITHMS[algo], level.to_dict(), start_state, heuristic, cost_model, measure),
    )
    try:
        process.start()
        send.close()
        if receive.poll(timeout):
            try:
                result = receive.recv()
            except EOFError:
                return SearchResult(reason="error: child exited without result")
            return result
        return SearchResult(reason="timeout")
    except Exception as exc:
        return SearchResult(reason=f"error: {exc}")
    finally:
        if process.pid:
            process.join(0.1)
            if process.is_alive():
                process.terminate()
                process.join(1)
                if process.is_alive():
                    process.kill()
                    process.join()
        receive.close()
        send.close()
