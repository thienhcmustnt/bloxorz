from __future__ import annotations
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request
import pytest


class ServerAddress(str):
    """String URL with a restart hook available only to browser tests."""


@pytest.fixture(scope="session")
def live_server():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    root = Path(__file__).resolve().parents[2]
    address = ServerAddress(f"http://127.0.0.1:{port}")
    process = None

    def start():
        nonlocal process
        process = subprocess.Popen(
            [sys.executable, "main.py", "--no-browser", "--port", str(port)],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for _ in range(100):
            try:
                with urllib.request.urlopen(address + "/api/levels", timeout=0.2):
                    return
            except OSError:
                time.sleep(0.05)
        pytest.fail("Test server did not start")

    def stop():
        if process is None:
            return
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

    def restart():
        stop()
        start()

    address.restart = restart
    start()
    try:
        yield address
    finally:
        stop()


@pytest.fixture(scope="session")
def browser():
    playwright = pytest.importorskip("playwright.sync_api")
    with playwright.sync_playwright() as p:
        try:
            instance = p.chromium.launch(
                headless=True,
                executable_path=os.environ.get("BLOXORZ_BROWSER") or None,
                args=["--no-sandbox", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
            )
        except playwright.Error as exc:
            pytest.skip(f"Chromium unavailable; run python -m playwright install chromium: {exc}")
        yield instance
        instance.close()


@pytest.fixture
def page(browser, live_server):
    context = browser.new_context(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
    page.goto(live_server + "/?debug=1&unlock=all")
    page.wait_for_function('window.__bloxorz?.mode === "IDLE"', timeout=30000)
    page.evaluate("window.__bloxorz.holdTerminal=true")
    yield page, errors
    context.close()
