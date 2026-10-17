"""Session orchestration only: all game rules are delegated to core.rules."""

from __future__ import annotations
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from typing import Any
from dataclasses import asdict, dataclass, field
from pathlib import Path
from threading import RLock
import asyncio
import os
import time
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from core.constants import Status
from core.level import Level
from core.rules import step
from core.state import State
from solvers.runner import run_solver
from api.schemas import Move, NewGame, SessionRequest, Solve

ROOT = Path(__file__).resolve().parents[1]
LEVELS = {
    level.id: level
    for level in (Level.load(p) for p in sorted((ROOT / "levels").glob("level_*.json")))
}
TTL = float(os.environ.get("BLOXORZ_SESSION_TTL", "3600"))
LOCK = RLock()


@dataclass
class Session:
    level: Level
    state: State
    status: Status = Status.PLAYING
    moves: int = 0
    seq: int = 0
    touched: float = field(default_factory=time.monotonic)
    history: list[tuple[State, Status, int]] = field(default_factory=list)


SESSIONS: dict[str, Session] = {}


def cleanup() -> None:
    """Expire idle sessions, including those that never send another request."""
    now = time.monotonic()
    with LOCK:
        for key in [key for key, value in SESSIONS.items() if now - value.touched > TTL]:
            del SESSIONS[key]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    async def sweep() -> None:
        while True:
            await asyncio.sleep(min(TTL, 60))
            cleanup()

    task = asyncio.create_task(sweep())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="Bloxorz Solver", version="1.0", lifespan=lifespan)


def state_json(state: State | None) -> dict[str, Any] | None:
    """Wire state includes derived display properties without changing identity."""
    if state is None:
        return None
    return {
        **asdict(state),
        "orientation": state.orientation.value,
        "bridges_open": [i for i in range(state.bridges.bit_length()) if state.bridges & (1 << i)],
    }


def get_session(key: str) -> Session:
    """Caller holds LOCK. Expired sessions return an actionable 404."""
    cleanup()
    if key not in SESSIONS:
        raise HTTPException(404, "Session expired or server restarted; start a new game")
    session = SESSIONS[key]
    session.touched = time.monotonic()
    return session


def snapshot(key: str, session: Session) -> dict[str, Any]:
    """Full control snapshot for new/restart/undo."""
    return dict(
        session_id=key,
        state=state_json(session.state),
        status=session.status.value,
        moves=session.moves,
        seq=session.seq,
        level_id=session.level.id,
    )


@app.get("/api/levels")
def levels() -> list[dict[str, Any]]:
    """Public catalog without solutions."""
    return [
        dict(
            id=level.id,
            name=level.name,
            difficulty=level.meta.get("difficulty", 1),
            group=level.meta.get("group", 1),
        )
        for level in LEVELS.values()
    ]


@app.get("/api/levels/{level_id}")
def level_data(level_id: int) -> dict[str, Any]:
    """Scene data, stripping private solution/verification fields."""
    if level_id not in LEVELS:
        raise HTTPException(404, "Unknown level id")
    data = LEVELS[level_id].to_dict()
    data["meta"] = {
        k: v
        for k, v in data.get("meta", {}).items()
        if k not in ("solution", "verification", "optimal_moves")
    }
    return data


@app.post("/api/game/new")
def new_game(body: NewGame) -> dict[str, Any]:
    """Start a fresh session; cap idle accumulation."""
    if body.level_id not in LEVELS:
        raise HTTPException(404, "Unknown level id")
    with LOCK:
        cleanup()
        if len(SESSIONS) >= 2000:
            raise HTTPException(503, "Session capacity reached; retry later")
        key = uuid.uuid4().hex
        level = LEVELS[body.level_id]
        session = Session(level, level.initial_state())
        SESSIONS[key] = session
        return snapshot(key, session)


@app.post("/api/game/move")
def move(body: Move) -> dict[str, Any]:
    """Atomic move with strictly consecutive sequence number."""
    with LOCK:
        session = get_session(body.session_id)
        if body.seq != session.seq + 1:
            raise HTTPException(409, f"Expected seq {session.seq + 1}; duplicate or stale move")
        if session.status != Status.PLAYING:
            raise HTTPException(409, "Game has ended; restart or undo")
        result = step(session.level, session.state, body.action)
        session.history.append((session.state, session.status, session.moves))
        session.seq = body.seq
        session.moves += 1
        session.status = result.status
        if result.state is not None:
            session.state = result.state
        return dict(
            state=state_json(result.state),
            status=result.status.value,
            cost=result.cost,
            events=[e.to_dict() for e in result.events],
            moves=session.moves,
            seq=session.seq,
        )


@app.post("/api/game/restart")
def restart(body: SessionRequest) -> dict[str, Any]:
    """Reset board while retaining monotonically increasing request sequence."""
    with LOCK:
        session = get_session(body.session_id)
        session.state = session.level.initial_state()
        session.status = Status.PLAYING
        session.moves = 0
        session.seq += 1
        session.history.clear()
        return snapshot(body.session_id, session)


@app.post("/api/game/undo")
def undo(body: SessionRequest) -> dict[str, Any]:
    """Restore state, bridge mask and preterminal status from history."""
    with LOCK:
        session = get_session(body.session_id)
        if not session.history:
            raise HTTPException(409, "No moves to undo")
        session.state, session.status, session.moves = session.history.pop()
        session.seq += 1
        return snapshot(body.session_id, session)


@app.post("/api/solve")
async def solve(body: Solve) -> dict[str, Any]:
    """Compute against an immutable snapshot without blocking the event loop."""
    with LOCK:
        session = get_session(body.session_id)
        level = session.level
        start = level.initial_state() if body.from_initial else session.state
        if session.status == Status.LOST and not body.from_initial:
            raise HTTPException(409, "Cannot solve a lost position; restart or solve from initial")
    kwargs = dict(
        heuristic=body.heuristic,
        timeout=body.timeout,
        start_state=start,
        cost_model=body.cost_model,
    )
    result = await asyncio.to_thread(run_solver, body.algo, level, measure="time", **kwargs)
    measurement_reason = None
    if result.found:
        memory = await asyncio.to_thread(run_solver, body.algo, level, measure="memory", **kwargs)
        result.peak_memory_kb = memory.peak_memory_kb
        measurement_reason = memory.reason
    return {
        **asdict(result),
        "start_state": state_json(start),
        "measurement_reason": measurement_reason,
    }


app.mount("/", StaticFiles(directory=ROOT / "web", html=True), name="web")
