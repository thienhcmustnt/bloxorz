"""Pluggable costs. Minimum action cost is 1; a valid step lower bound stays admissible."""

from __future__ import annotations
from typing import Callable
from core.constants import Action
from core.level import Level
from core.state import State
from core.tiles import TileType

CostFunction = Callable[[Level, State, Action, State], float]
CostModel = str | CostFunction


def action_cost(
    level: Level, before: State, action: Action, after: State, model: CostModel = "risk"
) -> float:
    """Unit=1. Risk=2 for an unsplit lying block on fragile; SWAP and switch activation=1."""
    if callable(model):
        return model(level, before, action, after)
    if model not in ("unit", "risk"):
        raise ValueError(f"Unknown cost model: {model}")
    return (
        2.0
        if (
            model == "risk"
            and action != Action.SWAP
            and not after.split
            and len(after.cells) == 2
            and not any(level.tile_at(*c) == TileType.SOFT for c in after.cells)
            and any(level.tile_at(*c) == TileType.FRAGILE for c in after.cells)
        )
        else 1.0
    )
