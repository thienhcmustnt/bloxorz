from __future__ import annotations
import pytest
from core.constants import Action, Status
from core.state import State
from core.rules import step
from tests.conftest import make_level

@pytest.mark.parametrize('tile,status', [('F',Status.LOST),('G',Status.WON)])
def test_standing_fragile_goal(tile,status):
    row='S##'+tile+'##'+('G' if tile=='F' else '#')
    result=step(make_level([row]),State(((0,1),(0,2))),Action.RIGHT)
    assert result.status==status

@pytest.mark.parametrize('tile', ['F','G'])
def test_lying_and_cube_safe(tile):
    row='S'+tile+'####'+('G' if tile=='F' else '#')
    level=make_level([row])
    assert step(level,State(((0,0),)),Action.RIGHT).status==Status.PLAYING
    assert step(level,State(((0,0),(0,6)),True),Action.RIGHT).status==Status.PLAYING

@pytest.mark.parametrize('kind,symbol', [('soft','o'),('heavy','x')])
@pytest.mark.parametrize('pose,activated', [('standing',True),('lying',False),('split',False)])
def test_switch_pressure(kind,symbol,pose,activated):
    level=make_level(['S##'+symbol+'##BG','########'],
        [{'id':0,'cells':[[0,6]],'open':False}],
        [{'cell':[0,3],'type':kind,'mode':'toggle','targets':[0]}])
    state={'standing':State(((0,1),(0,2))), 'lying':State(((1,2),(1,3))),
           'split':State(((0,2),(1,7)),True)}[pose]
    action=Action.UP if pose=='lying' else Action.RIGHT
    after=step(level,state,action).state
    assert bool(after.bridges)==(kind=='soft' or activated)

@pytest.mark.parametrize('mode', ['toggle','permanent'])
def test_toggle_permanent_reentry(mode):
    switch={'cell':[0,3],'type':'heavy','mode':mode,'targets':[0,1]}
    if mode=='permanent': switch['set']='open'
    level=make_level(['S##x##BBG'],[{'id':0,'cells':[[0,6]]},{'id':1,'cells':[[0,7]]}],[switch])
    state=State(((0,1),(0,2)))
    after=step(level,state,Action.RIGHT).state
    assert after.bridges==3
    back=step(level,after,Action.LEFT).state
    again=step(level,back,Action.RIGHT).state
    assert again.bridges==(0 if mode=='toggle' else 3)
    if mode=='permanent':
        assert not any(e.type=='bridge_changed' for e in step(level,back,Action.RIGHT).events)

def test_two_switches_same_bridge():
    level=make_level(['Soo#BG','######'],[{'id':0,'cells':[[0,4]]}],
      [{'cell':[0,c],'type':'soft','mode':'toggle','targets':[0]} for c in (1,2)])
    result=step(level,State(((1,1),(1,2))),Action.UP)
    assert result.state.bridges==0
    assert [e.data['open'] for e in result.events if e.type=='bridge_changed']==[True,False]

def test_close_under_block():
    level=make_level(['SoBG','####'],[{'id':0,'cells':[[0,2]],'open':True}],
      [{'cell':[0,1],'type':'soft','mode':'toggle','targets':[0]}])
    result=step(level,State(((1,1),(1,2)),bridges=1),Action.UP)
    assert result.status==Status.LOST
    assert result.events[-1].data['reason']=='bridge_closed_under_block'

@pytest.mark.parametrize('set_value,mask', [('open',1),('closed',0)])
def test_permanent_direction(set_value,mask):
    level=make_level(['S##xBG'],[{'id':0,'cells':[[0,4]],'open':True}],
      [{'cell':[0,3],'type':'heavy','mode':'permanent','set':set_value,'targets':[0]}])
    assert step(level,State(((0,1),(0,2)),bridges=1),Action.RIGHT).state.bridges==mask
