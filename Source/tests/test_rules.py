from __future__ import annotations
import json
from dataclasses import asdict
import pytest
from hypothesis import given, strategies as st
from core.constants import Action, Status
from core.state import State
from core.rules import step, successors
from tests.conftest import make_level

@pytest.mark.parametrize('row', ['S..G','S##G'])
def test_void_boundary(row):
    level=make_level([row])
    assert step(level,level.initial_state(),Action.LEFT).status==Status.LOST
    if '.' in row: assert step(level,level.initial_state(),Action.RIGHT).status==Status.LOST

def test_closed_bridge():
    level=make_level(['SBBG'],[{'id':0,'cells':[[0,1],[0,2]]}])
    assert step(level,level.initial_state(),Action.RIGHT).state is None

def test_hash_and_serialization():
    a=State(((2,3),(1,3)),True,0,5)
    b=State(**json.loads(json.dumps(asdict(a))))
    assert a==b and hash(a)==hash(b)
    assert State(((1,1),),active=1)==State(((1,1),),active=0)
    assert State(((1,1),),bridges=0)!=State(((1,1),),bridges=1)
    assert hash(State(((1,1),),bridges=0))!=hash(State(((1,1),),bridges=1))

def test_costs():
    level=make_level(['SFFG'])
    a=step(level,level.initial_state(),Action.RIGHT)
    b=step(level,level.initial_state(),Action.RIGHT,'unit')
    assert a.cost==2 and b.cost==1
    assert step(level,a.state,Action.RIGHT).cost==1

@given(st.lists(st.sampled_from(list(Action)),min_size=1,max_size=100))
def test_immutable_and_successor_invariants(actions):
    level=make_level(); state=level.initial_state()
    for action in actions:
        before=asdict(state)
        options=successors(level,state)
        assert len({a for a,_,_ in options})==len(options)
        for _,after,cost in options:
            assert after.cells==tuple(sorted(after.cells))
            assert all(level.is_supported(c,after.bridges) for c in after.cells)
            assert cost>=1
        result=step(level,state,action)
        assert asdict(state)==before
        if result.state: state=result.state

def test_switch_cost_overrides_fragile_risk():
    level=make_level(['SoFG'],switches=[{'cell':[0,1],'type':'soft','mode':'toggle','targets':[]}])
    assert step(level,level.initial_state(),Action.RIGHT).cost==1
