from __future__ import annotations
import json
from pathlib import Path
import pytest
from core.constants import CODES

ROOT=Path(__file__).resolve().parents[2]
pytestmark=pytest.mark.e2e

@pytest.mark.parametrize('level_id',range(1,16))
def test_level_solution(page,level_id):
    page,errors=page
    level=json.loads((ROOT/'levels'/f'level_{level_id:02d}.json').read_text())
    page.evaluate('(id)=>window.__bloxorz.load(id)',level_id)
    for action in level['meta']['solution']:
        page.evaluate('(a)=>window.__bloxorz.move(a)',CODES[action].value)
    assert page.evaluate('window.__bloxorz.status')=='WON'
    assert page.evaluate('window.__bloxorz.moves')==len(level['meta']['solution'])
    assert not errors
