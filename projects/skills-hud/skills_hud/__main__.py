"""Entry point: starts FastAPI on a background thread, opens a PyWebView window."""

from __future__ import annotations

import socket
import threading
import time

import uvicorn

from .server import create_app

DEFAULT_PORT = 8731


def _pick_port(preferred: int = DEFAULT_PORT) -> int:
    """Return the preferred port if free, otherwise an OS-assigned one."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", preferred))
        except OSError:
            s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _run_server(port: int) -> None:
    uvicorn.run(create_app(), host="127.0.0.1", port=port, log_level="warning")


def main() -> None:
    import webview  # imported lazily so headless mode does not require pyobjc

    port = _pick_port()
    threading.Thread(target=_run_server, args=(port,), daemon=True).start()
    time.sleep(0.6)  # give uvicorn a beat to bind

    webview.create_window(
        "Skills HUD",
        f"http://127.0.0.1:{port}/",
        width=1100,
        height=720,
        min_size=(820, 480),
    )
    webview.start()


def serve_only() -> None:
    """Run just the FastAPI server (no window). Useful for debugging the parser."""
    port = _pick_port()
    print(f"Skills HUD server on http://127.0.0.1:{port}/  (Ctrl-C to stop)")
    _run_server(port)


if __name__ == "__main__":
    main()
