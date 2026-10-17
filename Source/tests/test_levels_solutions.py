from __future__ import annotations
import pytest
from core.level import Level
from core.constants import CODES, Status
from core.rules import step
from tests.test_level_loading import FILES

@pytest.mark.parametrize('path',FILES,ids=lambda p:p.stem)
def test_verified_solution(path):
    level=Level.load(path);state=level.initial_state();solution=level.meta['solution']
    assert len(solution)==level.meta['optimal_moves']
    for i,code in enumerate(solution):
        result=step(level,state,CODES[code])
        assert result.state is not None
        assert result.status==(Status.WON if i==len(solution)-1 else Status.PLAYING)
        state=result.state
    if level.id<=12:
        assert 6<=len(solution)<=40
    for check in level.meta['verification']['mechanism_ablation'].values():
        assert check['disabled_unsolvable']

@pytest.mark.parametrize('path',FILES,ids=lambda p:p.stem)
def test_student_bfs_optimum(path):
    from solvers.runner import run_solver
    level=Level.load(path);result=run_solver('bfs',level)
    if result.reason=='not_implemented':pytest.skip('Student BFS intentionally absent')
    assert result.found and result.solution_length==level.meta['optimal_moves']
