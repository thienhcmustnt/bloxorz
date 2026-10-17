from __future__ import annotations
import pytest
from fastapi.testclient import TestClient
from api.server import app, SESSIONS
from solvers.runner import ALGORITHMS
from core.constants import CODES

@pytest.fixture
def client():
    SESSIONS.clear()
    with TestClient(app) as client:yield client

def new(client,level=1):
    return client.post('/api/game/new',json={'level_id':level}).json()

def test_catalog_private(client):
    assert len(client.get('/api/levels').json())==15
    data=client.get('/api/levels/1').json()
    assert 'solution' not in data['meta']
    assert client.get('/api/levels/999').status_code==404

def test_errors_seq_undo_restart(client):
    session=new(client);key=session['session_id']
    assert client.post('/api/game/move',json={'session_id':key,'action':'BOGUS','seq':1}).status_code==422
    body={'session_id':key,'action':'DOWN','seq':1}
    assert client.post('/api/game/move',json=body).status_code==200
    assert client.post('/api/game/move',json=body).status_code==409
    undo=client.post('/api/game/undo',json={'session_id':key}).json()
    assert undo['state']==session['state'] and undo['moves']==0 and undo['seq']==2
    reset=client.post('/api/game/restart',json={'session_id':key}).json()
    assert reset['seq']==3
    assert client.post('/api/game/new',json={'level_id':999}).status_code==404
    assert client.post('/api/game/undo',json={'session_id':'expired'}).status_code==404

@pytest.mark.parametrize('algo',list(ALGORITHMS))
def test_solver_stub(client,algo):
    session=new(client)
    result=client.post('/api/solve',json={'session_id':session['session_id'],'algo':algo})
    assert result.status_code==200
    assert result.json()['reason']=='not_implemented'

def test_solve_fake(client,monkeypatch):
    monkeypatch.setitem(ALGORITHMS,'bfs','tests.fake_solver:solve')
    session=new(client)
    result=client.post('/api/solve',json={'session_id':session['session_id'],'algo':'bfs'}).json()
    assert result['found'] and result['solution_length']==6 and result['peak_memory_kb']>0

def test_terminal_and_undo(client):
    from api.server import LEVELS
    session=new(client);key=session['session_id']
    for i,code in enumerate(LEVELS[1].meta['solution'],1):
        result=client.post('/api/game/move',json={'session_id':key,'action':CODES[code].value,'seq':i}).json()
    assert result['status']=='WON'
    assert client.post('/api/game/move',json={'session_id':key,'action':'RIGHT','seq':i+1}).status_code==409
    assert client.post('/api/game/undo',json={'session_id':key}).json()['status']=='PLAYING'

def test_expiry(client,monkeypatch):
    from api import server
    session=new(client);SESSIONS[session['session_id']].touched-=7200
    server.cleanup()
    assert session['session_id'] not in SESSIONS
