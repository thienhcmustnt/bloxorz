"""Immutable tile metadata."""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from core.constants import Cell


class TileType(str, Enum):
    VOID = "void"
    FLOOR = "floor"
    FRAGILE = "fragile"
    GOAL = "goal"
    START = "start"
    BRIDGE = "bridge"
    SOFT = "soft_switch"
    HEAVY = "heavy_switch"
    SPLIT = "split_switch"


class SwitchType(str, Enum):
    SOFT = "soft"
    HEAVY = "heavy"
    SPLIT = "split"


class SwitchMode(str, Enum):
    TOGGLE = "toggle"
    PERMANENT = "permanent"


@dataclass(frozen=True)
class Bridge:
    id: int
    cells: tuple[Cell, ...]
    open: bool = False


@dataclass(frozen=True)
class Switch:
    cell: Cell
    type: SwitchType
    mode: SwitchMode
    targets: tuple[int, ...]
    set_open: bool = True
    cubes: tuple[Cell, ...] = ()
