"""Cross-platform local entry point. No Node/bundler required."""

from __future__ import annotations
import argparse
import multiprocessing
import threading
import webbrowser
import uvicorn


def main() -> None:
    """Start local API and static frontend, optionally opening the browser."""
    parser = argparse.ArgumentParser(description="Bloxorz Solver")
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if not args.no_browser:
        timer = threading.Timer(1.2, lambda: webbrowser.open(f"http://127.0.0.1:{args.port}"))
        timer.daemon = True
        timer.start()
    uvicorn.run("api.server:app", host="127.0.0.1", port=args.port, log_level="info")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
