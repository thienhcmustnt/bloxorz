from __future__ import annotations
import pytest
from hypothesis import given, strategies as st
from core.constants import Action
from core.state import State
from core.rules import step
from tests.conftest import make_level

@pytest.mark.parametrize("cells,expected", [
    (((8,8),), [((6,8),(7,8)),((9,8),(10,8)),((8,6),(8,7)),((8,9),(8,10))]),
    (((8,8),(8,9)), [((7,8),(7,9)),((9,8),(9,9)),((8,7),),((8,10),)]),
    (((8,8),(9,8)), [((7,8),),((10,8),),((8,7),(9,7)),((8,9),(9,9))])])
def test_table(floor,cells,expected):
    for action, target in zip(list(Action)[:4],expected):
        assert step(floor,State(cells),action).state.cells == target

@given(st.integers(3,15),st.integers(3,15),st.integers(0,2),st.sampled_from(list(Action)[:4]))
def test_inverse(r,c,orientation,action):
    cells = ((r,c),) if orientation==0 else ((r,c),(r,c+1)) if orientation==1 else ((r,c),(r+1,c))
    before = State(cells)
    opposite={Action.UP:Action.DOWN,Action.DOWN:Action.UP,Action.LEFT:Action.RIGHT,Action.RIGHT:Action.LEFT}
    middle=step(make_level(),before,action).state
    assert middle is not None
    assert step(make_level(),middle,opposite[action]).state == before
