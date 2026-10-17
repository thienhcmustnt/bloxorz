from __future__ import annotations
import pytest
from core.constants import Action, Status
from core.state import State
from core.rules import step
from tests.conftest import make_level

def split_level(dest=None):
    return make_level(['S##Y####','########','#######G'],switches=[
      {'cell':[0,3],'type':'split','mode':'toggle','targets':[], 'cubes':dest or [[2,1],[2,6]]}])

def test_split_swap_and_motion():
    level=split_level([[2,6],[2,1]])
    result=step(level,State(((0,1),(0,2))),Action.RIGHT)
    assert result.state==State(((2,1),(2,6)),True,1)
    swapped=step(level,result.state,Action.SWAP).state
    assert swapped.active==0
    moved=step(level,swapped,Action.RIGHT).state
    assert moved==State(((2,2),(2,6)),True,0)
    assert [e.type for e in result.events]==['roll','switch_pressed','split']

@pytest.mark.parametrize('state,action,expected', [
 (State(((1,1),(1,3)),True),Action.RIGHT,((1,2),(1,3))),
 (State(((0,1),(2,1)),True),Action.DOWN,((1,1),(2,1)))])
def test_merge(state,action,expected):
    result=step(split_level(),state,action)
    assert result.state==State(expected)
    assert result.events[-1].type=='merge'

def test_sort_preserves_moving_cube():
    state=State(((1,5),(2,1)),True,1)
    result=step(make_level(),state,Action.UP)
    assert result.state.cells==((1,1),(1,5))
    assert result.state.active==0
    assert step(make_level(),result.state,Action.UP).state.cells==((0,1),(1,5))

def test_swap_no_merge_or_switch():
    state=State(((1,1),(1,2)),True)
    result=step(make_level(),state,Action.SWAP)
    assert result.state.split and result.state.active==1
    assert [e.type for e in result.events]==['swap']

def test_overlap_and_invalid_swap():
    assert step(make_level(),State(((1,1),(1,2)),True),Action.RIGHT).status==Status.LOST
    assert step(make_level(),State(((1,1),)),Action.SWAP).status==Status.LOST
    assert step(make_level(),State(((0,1),(5,5)),True),Action.UP).status==Status.LOST

@pytest.mark.parametrize('state,action',[(State(((1,3),(1,4))),Action.UP),
                                       (State(((0,2),(2,7)),True),Action.RIGHT)])
def test_split_only_standing(state,action):
    result=step(split_level(),state,action)
    assert not any(e.type=='split' for e in result.events)

def test_destination_closed_by_split_switch():
    level=make_level(['S##Y###G','B#######'],[{'id':0,'cells':[[1,0]],'open':True}],
      [{'cell':[0,3],'type':'split','mode':'toggle','targets':[0],'cubes':[[1,0],[1,6]]}])
    result=step(level,State(((0,1),(0,2)),bridges=1),Action.RIGHT)
    assert result.status==Status.LOST
    assert result.events[-1].data['reason']=='unsupported_split_destination'
