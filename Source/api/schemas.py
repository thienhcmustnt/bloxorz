"""Validated request contracts; unknown fields are rejected."""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from core.constants import Action

class Request(BaseModel):
    model_config = ConfigDict(extra="forbid")

class NewGame(Request):
    level_id: int = Field(ge=1)

class SessionRequest(Request):
    session_id: str = Field(min_length=1,max_length=100)

class Move(SessionRequest):
    action: Action
    seq: int = Field(ge=1)

class Solve(SessionRequest):
    algo: Literal["bfs","dfs","ids","ucs","astar"]
    heuristic: Literal["center","relaxed"] | None = None
    from_initial: bool = False
    timeout: float = Field(default=30,gt=0,le=120)
    cost_model: Literal["risk","unit"] = "risk"
