"""Harness fixtures only: playback of a fixed certified string, never a search."""
from __future__ import annotations
import time
from core.constants import CODES
from core.rules import step
from solvers.base import SearchResult

def solve(problem):
    path=[CODES[c] for c in problem.level.meta['solution']]
    state=problem.initial_state;cost=0
    for action in path:
        transition=step(problem.level,state,action,problem.cost_model)
        assert transition.state is not None
        state=transition.state;cost+=transition.cost
    return SearchResult(found=True,path=path,cost=cost,expanded_nodes=1)

def slow(problem):
    time.sleep(10)
    return SearchResult()

def broken(problem):
    raise RuntimeError('fixture exception')

def huge(problem):
    return SearchResult(found=True,path=[CODES['R']]*100000,expanded_nodes=1)
