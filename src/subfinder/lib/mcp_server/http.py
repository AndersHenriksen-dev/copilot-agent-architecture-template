"""The read tools over HTTP, for Copilot running on GitHub's side rather than on your machine.

The cloud agent and code review reach an MCP server from GitHub's infrastructure. Nothing on your machine is in that
path, so no hook of yours sees those calls. Two things follow, and both are in this file:

1. Only the read tools are served. A write that no hook can check does not get an entrance.
2. The server asks for a bearer token. Repository MCP settings can send one, because `headers` there expands
   `$COPILOT_MCP_*` secrets, so a fixed token is a real option and not a stand-in for OAuth.

Repository settings also take a `tools` allowlist, which is a second, independent layer. `docs/surfaces.md` has the
JSON to paste in.
"""

from __future__ import annotations

import secrets
import socket
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager

import uvicorn
from mcp.server.transport_security import TransportSecuritySettings
from starlette.responses import PlainTextResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from subfinder.lib.mcp_server.server import build_read_only_server
from subfinder.lib.shared.settings import Strict, config_for


class _Config(Strict):
    path: str
    default_port: int
    host: str


CONFIG = config_for(__name__, _Config)


class _RequireBearerToken:
    """Refuse any HTTP request without the token. It wraps the whole app, so nothing behind it needs to know."""

    def __init__(self, app: ASGIApp, token: str) -> None:
        self._app = app
        self._expected = f"Bearer {token}".encode()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Pass the request on only if its Authorization header matches."""
        if scope["type"] == "http":
            sent = dict(scope["headers"]).get(b"authorization", b"")
            if not secrets.compare_digest(sent, self._expected):
                await PlainTextResponse("Missing or wrong token.", status_code=401)(scope, receive, send)
                return
        await self._app(scope, receive, send)


def build_app(token: str | None, public_host: str | None) -> ASGIApp:
    """Build the web app.

    Args:
        token: The bearer token every request must carry. None serves with no authentication, which is only for a
            local demo on made-up data.
        public_host: The host name the server is reached at through a tunnel, if any. The MCP library refuses other
            Host headers, which is its protection against DNS rebinding.

    Returns:
        The app, ready to give to uvicorn.
    """
    hosts = [f"{CONFIG.host}:*", "localhost:*"] + ([public_host] if public_host else [])
    app = build_read_only_server().streamable_http_app(
        streamable_http_path=CONFIG.path,
        # Each request stands alone, so the server can restart and sit behind a proxy with nothing to lose.
        stateless_http=True,
        transport_security=TransportSecuritySettings(allowed_hosts=hosts),
    )
    return _RequireBearerToken(app, token) if token else app


def serve(app: ASGIApp, port: int) -> None:
    """Serve until stopped."""
    uvicorn.run(app, host=CONFIG.host, port=port, log_level="warning")


@contextmanager
def serving_in_background(app: ASGIApp) -> Iterator[str]:
    """Serve on a free local port for the length of a `with` block, and give back the URL. For the demo and the tests.

    Yields:
        The URL to connect to.
    """
    with socket.socket() as probe:
        probe.bind((CONFIG.host, 0))
        port: int = probe.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, host=CONFIG.host, port=port, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    while not server.started:
        time.sleep(0.01)
    try:
        yield f"http://{CONFIG.host}:{port}{CONFIG.path}"
    finally:
        server.should_exit = True
        thread.join(timeout=10)
