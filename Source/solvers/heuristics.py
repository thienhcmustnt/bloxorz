"""Student heuristic contracts, intentionally unimplemented."""
from __future__ import annotations
from core.state import State
from solvers.base import Problem

def h_center(problem: Problem, state: State) -> float:
    """TODO(team): return a nonnegative estimate with h(goal)=0."""
    raise NotImplementedError("center chưa được cài đặt")

def h_relaxed(problem: Problem, state: State) -> float:
    """TODO(team): return a nonnegative estimate with h(goal)=0."""
    raise NotImplementedError("relaxed chưa được cài đặt")

HEURISTICS = {"center": h_center, "relaxed": h_relaxed}
