"""Shared wire values: rules, API and documentation use these enums."""

from __future__ import annotations
from enum import Enum


class Action(str, Enum):
    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    SWAP = "SWAP"


class Orientation(str, Enum):
    STANDING = "standing"
    LYING_H = "lying_h"
    LYING_V = "lying_v"
    SPLIT = "split"


class Status(str, Enum):
    PLAYING = "PLAYING"
    WON = "WON"
    LOST = "LOST"


class EventType(str, Enum):
    ROLL = "roll"
    SWITCH = "switch_pressed"
    BRIDGE = "bridge_changed"
    FRAGILE = "fragile_break"
    SPLIT = "split"
    MERGE = "merge"
    SWAP = "swap"
    FALL = "fall"
    WIN = "win"


DELTAS = {Action.UP: (-1, 0), Action.DOWN: (1, 0), Action.LEFT: (0, -1), Action.RIGHT: (0, 1)}
DIRECTIONS = tuple(DELTAS)
CODES = {"U": Action.UP, "D": Action.DOWN, "L": Action.LEFT, "R": Action.RIGHT, "W": Action.SWAP}
Cell = tuple[int, int]
