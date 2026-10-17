from __future__ import annotations
import json
from pathlib import Path
import pytest
from core.constants import CODES

ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.e2e


@pytest.mark.parametrize("level_id", range(1, 16))
def test_level_solution(page, level_id):
    page, errors = page
    level = json.loads((ROOT / "levels" / f"level_{level_id:02d}.json").read_text())
    page.evaluate("(id)=>window.__bloxorz.load(id)", level_id)
    for action in level["meta"]["solution"]:
        page.evaluate("(a)=>window.__bloxorz.move(a)", CODES[action].value)
    assert page.evaluate("window.__bloxorz.status") == "WON"
    assert page.evaluate("window.__bloxorz.moves") == len(level["meta"]["solution"])
    assert not errors


def test_frenetic_input_and_thirty_level_changes(page):
    page, errors = page
    page.evaluate(
        """async()=>{const g=window.__bloxorz;g.holdTerminal=false;let seed=42;for(let i=0;i<200;i++){seed=(seed*1664525+1013904223)>>>0;window.dispatchEvent(new KeyboardEvent('keydown',{key:['ArrowUp','ArrowDown','ArrowLeft','ArrowRight',' '][seed%5]}));await new Promise(r=>setTimeout(r,2));}await g.load(1);}"""
    )
    page.wait_for_function('window.__bloxorz.mode === "IDLE"')
    start = page.evaluate("window.__bloxorz.scene.memory()")
    page.evaluate(
        """async()=>{for(let i=0;i<30;i++)await window.__bloxorz.load(i%15+1);await window.__bloxorz.load(1);}"""
    )
    end = page.evaluate("window.__bloxorz.scene.memory()")
    assert end["geometries"] <= start["geometries"] + 2
    assert end["textures"] <= start["textures"] + 2
    assert page.evaluate("window.__bloxorz.block.check(window.__bloxorz.state)")
    assert not errors


def test_interrupt_restart_undo_and_split_history(page):
    page, errors = page
    page.emulate_media(reduced_motion="no-preference")
    page.evaluate("window.__bloxorz.queue.reduced=false")
    page.evaluate('window.__bloxorz.input("DOWN")')
    page.evaluate("window.__bloxorz.restart()")
    page.wait_for_function('window.__bloxorz.mode === "IDLE"')
    assert page.evaluate("window.__bloxorz.moves") == 0
    page.evaluate("window.__bloxorz.queue.reduced=true")
    page.evaluate("window.__bloxorz.load(10)")
    for _ in range(8):
        page.evaluate('window.__bloxorz.move("RIGHT")')
    assert page.evaluate("window.__bloxorz.state.split")
    before = page.evaluate("window.__bloxorz.state")
    page.evaluate("window.__bloxorz.undo()")
    assert not page.evaluate("window.__bloxorz.state.split")
    page.evaluate('window.__bloxorz.move("RIGHT")')
    assert page.evaluate("window.__bloxorz.state") == before
    level = json.loads((ROOT / "levels" / "level_10.json").read_text())
    for action in level["meta"]["solution"][8:]:
        was_split = page.evaluate("window.__bloxorz.state.split")
        page.evaluate("(a)=>window.__bloxorz.move(a)", CODES[action].value)
        if was_split and not page.evaluate("window.__bloxorz.state.split"):
            page.evaluate("window.__bloxorz.undo()")
            assert page.evaluate("window.__bloxorz.state.split")
            break
    page.evaluate("window.__bloxorz.restart()")
    assert page.evaluate("window.__bloxorz.block.check(window.__bloxorz.state)")
    assert not errors


def test_solver_feedback_and_replay_controls(page):
    page, errors = page
    page.locator('[data-solve="bfs"]').click()
    page.wait_for_function('window.__bloxorz.mode === "IDLE"')
    assert "chưa được cài đặt" in page.locator("#metrics").inner_text()
    level = json.loads((ROOT / "levels" / "level_01.json").read_text())
    page.evaluate('window.__bloxorz.move("DOWN")')
    answer = {
        "found": True,
        "path": [CODES[c].value for c in level["meta"]["solution"][1:]],
        "solution_length": 5,
        "cost": 5,
        "expanded_nodes": 1,
        "search_time": 0.01,
        "peak_memory_kb": 1,
        "reason": None,
    }
    page.route("**/api/solve", lambda route: route.fulfill(json=answer))
    page.evaluate("""()=>{const g=window.__bloxorz;g.queue.reduced=false;g.holdTerminal=false;}""")
    page.locator('[data-solve="bfs"]').click()
    page.wait_for_function('window.__bloxorz.mode === "REPLAY"')
    page.locator("#play-pause").click()
    page.wait_for_function("!window.__bloxorz.replayBusy")
    old = page.evaluate("window.__bloxorz.moves")
    page.keyboard.press("ArrowUp")
    assert page.evaluate("window.__bloxorz.moves") == old
    page.locator("#replay-step").click()
    page.wait_for_function("!window.__bloxorz.replayBusy")
    assert page.evaluate("window.__bloxorz.moves") == old + 1
    page.locator("#speed").select_option("4")
    page.locator("#play-pause").click()
    page.wait_for_function(
        'window.__bloxorz.status === "WON" && !window.__bloxorz.replayBusy', timeout=15000
    )
    assert page.locator("#progress").get_attribute("value") == "5"
    page.locator("#stop").click()
    assert page.evaluate("window.__bloxorz.mode") == "IDLE"
    assert not errors


def test_session_recovery(page):
    page, errors = page
    page.evaluate('window.__bloxorz.session="expired-session"')
    page.evaluate('window.__bloxorz.move("DOWN")')
    page.wait_for_function('window.__bloxorz.mode === "IDLE"')
    assert page.evaluate("window.__bloxorz.session") != "expired-session"
    assert page.evaluate("window.__bloxorz.moves") == 0
    # Chromium logs the intentionally elicited 404; no JS or pose errors allowed.
    assert all("404" in e for e in errors)


def test_mobile_and_real_keyboard(page):
    page, errors = page
    page.set_viewport_size({"width": 390, "height": 844})
    page.keyboard.press("ArrowDown")
    page.wait_for_function('window.__bloxorz.mode === "IDLE" && window.__bloxorz.moves === 1')
    assert page.evaluate("window.__bloxorz.block.check(window.__bloxorz.state)")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.locator("#levels").click()
    assert page.locator(".level-card").count() == 15
    assert not errors


def test_cancel_solving_and_intro(page):
    page, errors = page
    stalled = []
    page.route("**/api/solve", lambda route: stalled.append(route))
    page.locator('[data-solve="bfs"]').click()
    page.wait_for_function('window.__bloxorz.mode === "SOLVING"')
    assert page.locator('[data-solve="bfs"]').is_disabled()
    page.evaluate("window.__bloxorz.restart()")
    page.wait_for_function('window.__bloxorz.mode === "IDLE"')
    stalled[0].fulfill(json={"found": False, "reason": "not_implemented"})
    page.evaluate(
        """async()=>{const g=window.__bloxorz;await Promise.all([g.load(12),g.load(3)]);}"""
    )
    assert page.evaluate("window.__bloxorz.level.id") == 3
    assert page.evaluate("window.__bloxorz.block.check(window.__bloxorz.state)")
    assert not errors


def test_real_server_restart(page, live_server):
    page, errors = page
    previous = page.evaluate("window.__bloxorz.session")
    live_server.restart()
    page.evaluate('window.__bloxorz.move("DOWN")')
    page.wait_for_function('window.__bloxorz.mode === "IDLE"')
    assert page.evaluate("window.__bloxorz.session") != previous
    assert page.evaluate("window.__bloxorz.moves") == 0
    assert all("404" in error for error in errors)
