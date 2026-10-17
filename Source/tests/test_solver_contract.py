from __future__ import annotations
import pytest
from core.level import Level
from core.constants import Status
from core.rules import step
from solvers.base import Problem
from solvers.runner import ALGORITHMS, run_solver
from tests.test_level_loading import FILES

@pytest.mark.parametrize('algo',list(ALGORITHMS))
@pytest.mark.parametrize('path',FILES,ids=lambda p:p.stem)
def test_student_contract(algo,path):
    level=Level.load(path);snapshot=level.to_dict()
    result=run_solver(algo,level,heuristic='center' if algo=='astar' else None)
    if result.reason=='not_implemented':pytest.skip('Student implementation slot')
    assert result.found, result.reason
    assert result.solution_length==len(result.path)
    assert result.expanded_nodes>0
    state=level.initial_state();cost=0
    for index,action in enumerate(result.path):
        transition=step(level,state,action)
        assert transition.state is not None
        assert transition.status==(Status.WON if index==len(result.path)-1 else Status.PLAYING)
        state=transition.state;cost+=transition.cost
    assert result.cost==cost
    assert level.to_dict()==snapshot
    if algo=='bfs':assert result.solution_length==level.meta['optimal_moves']
    if algo in ('bfs','dfs','ids','astar'):
        reference=run_solver('ucs',level)
        if reference.reason!='not_implemented':assert reference.found and reference.cost<=result.cost
    if algo=='ucs':
        unit=run_solver('ucs',level,cost_model='unit')
        assert unit.found and unit.solution_length==level.meta['optimal_moves']
    if algo=='astar':
        reference=run_solver('ucs',level)
        if reference.reason!='not_implemented':assert reference.cost==result.cost
        for heuristic in ('center','relaxed'):
            answer=run_solver('astar',level,heuristic=heuristic)
            if answer.reason!='not_implemented' and reference.reason!='not_implemented':
                assert answer.found and answer.cost==reference.cost

@pytest.mark.parametrize('measure',['time','memory'])
def test_fake_measurement(monkeypatch,measure):
    monkeypatch.setitem(ALGORITHMS,'fixture','tests.fake_solver:solve')
    result=run_solver('fixture',Level.load(FILES[0]),measure=measure)
    assert result.found and result.solution_length==6
    assert (result.search_time>0) if measure=='time' else (result.peak_memory_kb>0)

@pytest.mark.parametrize('entry,reason',[('slow','timeout'),('broken','error:')])
def test_worker_failure(monkeypatch,entry,reason):
    monkeypatch.setitem(ALGORITHMS,'fixture',f'tests.fake_solver:{entry}')
    result=run_solver('fixture',Level.load(FILES[0]),timeout=.5 if entry=='slow' else 5)
    assert result.reason.startswith(reason)

def test_large_ipc(monkeypatch):
    monkeypatch.setitem(ALGORITHMS,'fixture','tests.fake_solver:huge')
    assert run_solver('fixture',Level.load(FILES[0]),timeout=5).solution_length==100000

def test_problem_adapter_immutable():
    from tests.fake_solver import solve
    level=Level.load(FILES[0]);problem=Problem(level);before=vars(problem).copy()
    solve(problem)
    assert vars(problem)==before
    for action,next_state,cost in problem.successors(problem.initial_state):
        assert cost==problem.step_cost(problem.initial_state,action,next_state)
