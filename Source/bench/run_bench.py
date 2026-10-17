"""Reproducible measurement harness. This module contains no search algorithm."""

from __future__ import annotations

import argparse
import csv
import json
import platform
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Permit the documented `python bench/run_bench.py` command from Source/.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.level import Level  # noqa: E402
from solvers.runner import ALGORITHMS, run_solver  # noqa: E402

COLUMNS = [
    "algo",
    "heuristic",
    "level_id",
    "group",
    "found",
    "solution_length",
    "cost",
    "expanded_nodes",
    "search_time_s",
    "peak_memory_kb",
    "reason",
]


def numbers(values: list[str]) -> set[int]:
    """Parse ids, inclusive ranges and comma-separated selections."""
    result: set[int] = set()
    for value in values:
        for part in value.split(","):
            if "-" in part:
                first, last = map(int, part.split("-", 1))
                if last < first:
                    raise ValueError(f"Invalid range: {part}")
                result.update(range(first, last + 1))
            else:
                result.add(int(part))
    return result


def benchmark(
    algos: list[str],
    levels: list[Level],
    *,
    timeout: float = 30,
    repeat: int = 3,
    cost_model: str = "risk",
    out: Path = Path("bench/results"),
) -> list[dict[str, Any]]:
    """Run separate time/memory processes; only aggregate fully successful repeats.

    Stub algorithms are warned once and skipped. A timeout/error remains a CSV
    row with found=false. Partial repetitions are never reported as success.
    """
    if repeat < 1 or timeout <= 0:
        raise ValueError("repeat and timeout must be positive")
    out.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for algo_spec in algos:
        algo, _, selected = algo_spec.partition(":")
        if algo not in ALGORITHMS:
            raise ValueError(f"Unknown algorithm: {algo}")
        heuristics: list[str | None] = (
            [selected] if selected else ["center", "relaxed"] if algo == "astar" else [None]
        )
        for heuristic in heuristics:
            for level in levels:
                samples = []
                failure = None
                for _ in range(repeat):
                    timed = run_solver(
                        algo,
                        level,
                        heuristic=heuristic,
                        timeout=timeout,
                        measure="time",
                        cost_model=cost_model,
                    )
                    if timed.reason == "not_implemented":
                        failure = "not_implemented"
                        break
                    if not timed.found:
                        failure = timed.reason or "no_solution"
                        break
                    memory = run_solver(
                        algo,
                        level,
                        heuristic=heuristic,
                        timeout=timeout,
                        measure="memory",
                        cost_model=cost_model,
                    )
                    if not memory.found:
                        failure = "memory_pass: " + (memory.reason or "no_solution")
                        break
                    samples.append((timed, memory))
                if failure == "not_implemented":
                    print(
                        f"WARNING: {algo}/{heuristic or '-'} chưa được cài đặt; skipping.",
                        file=sys.stderr,
                    )
                    break
                row: dict[str, Any] = dict.fromkeys(COLUMNS, "")
                row.update(
                    algo=algo,
                    heuristic=heuristic or "",
                    level_id=level.id,
                    group=level.meta["group"],
                    found=not failure,
                    reason=failure or "",
                )
                if not failure:
                    for field, attribute in [
                        ("solution_length", "solution_length"),
                        ("cost", "cost"),
                        ("expanded_nodes", "expanded_nodes"),
                        ("search_time_s", "search_time"),
                    ]:
                        row[field] = statistics.median(
                            getattr(sample[0], attribute) for sample in samples
                        )
                    row["peak_memory_kb"] = statistics.median(
                        sample[1].peak_memory_kb for sample in samples
                    )
                rows.append(row)
                print(
                    f"{algo:6s} {heuristic or '-':7s} level={level.id:02d} {failure or 'measured'}"
                )
    with (out / "results.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    (out / "environment.json").write_text(
        json.dumps(
            dict(
                python=sys.version,
                platform=platform.platform(),
                utc=datetime.now(timezone.utc).isoformat(),
                repeat=repeat,
                cost_model=cost_model,
                timeout=timeout,
                measurement="spawn; time and tracemalloc measured in separate processes; medians",
            ),
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return rows


def main() -> None:
    """CLI entry point; results and figures are stored together."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--algos", nargs="+", default=list(ALGORITHMS))
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--levels", nargs="+", default=None, help="Example: 1-4 7 10-15")
    selection.add_argument("--groups", nargs="+", type=int, choices=[1, 2, 3, 4])
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument("--cost-model", choices=["unit", "risk"], default="risk")
    parser.add_argument("--out", type=Path, default=ROOT / "bench" / "results")
    args = parser.parse_args()
    levels = [Level.load(p) for p in sorted((ROOT / "levels").glob("level_*.json"))]
    if args.levels:
        selected = numbers(args.levels)
        if not selected.issubset({level.id for level in levels}):
            parser.error("Unknown level id")
        levels = [level for level in levels if level.id in selected]
    if args.groups:
        levels = [level for level in levels if level.meta["group"] in args.groups]
    try:
        benchmark(
            args.algos,
            levels,
            timeout=args.timeout,
            repeat=args.repeat,
            cost_model=args.cost_model,
            out=args.out,
        )
    except ValueError as exc:
        parser.error(str(exc))
    from bench.plots import plot_results

    plot_results(args.out / "results.csv", args.out)


if __name__ == "__main__":
    main()
