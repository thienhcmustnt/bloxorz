"""Public solver contract; no search implementation lives in the framework."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable
from core.constants import Action
from core.level import Level
from core.state import State
from core import rules
from core.costs import action_cost

@dataclass
class SearchResult:
    """expanded_nodes counts nodes removed from the frontier for expansion.

    Solver owns found/path/cost/expanded_nodes. Runner owns length/time/memory.
    """
    found: bool = False
    path: list[Action] = field(default_factory=list)
    solution_length: int = 0
    cost: float = 0.0
    expanded_nodes: int = 0
    search_time: float = 0.0
    peak_memory_kb: float = 0.0
    reason: str | None = None

class Problem:
    """Read-only game adapter. Solvers obtain transitions only through successors."""
    def __init__(self, level: Level, start_state: State | None = None,
                 cost_model: str = "risk", heuristic: Callable[[Problem, State], float] | None = None):
        if cost_model not in ("unit", "risk"):
            raise ValueError("cost_model must be unit or risk")
        self.level = level
        self.initial_state = start_state if start_state is not None else level.initial_state()
        self.cost_model = cost_model
        self.heuristic = heuristic

    def successors(self, state: State) -> list[tuple[Action, State, float]]:
        """Valid transitions (including winning destinations) with nonnegative costs."""
        return rules.successors(self.level,state,self.cost_model)

    def is_goal(self, state: State) -> bool:
        """Whether the complete block stands in the goal."""
        return rules.is_goal(self.level,state)

    def step_cost(self, state: State, action: Action, next_state: State) -> float:
        """Cost of a transition already obtained from successors."""
        return action_cost(self.level,state,action,next_state,self.cost_model)
