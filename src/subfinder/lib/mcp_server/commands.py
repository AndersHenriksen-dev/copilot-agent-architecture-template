"""The `serve-http` command: the read tools over HTTP, for Copilot reaching them from GitHub's side."""

from __future__ import annotations

import os

from dotenv import load_dotenv

from subfinder.lib.mcp_server.http import CONFIG, build_app, serve

TOKEN_VARIABLE = "SUBFINDER_HTTP_TOKEN"


def cmd_serve(port: int, public_host: str | None, no_auth: bool) -> int:
    """Serve the read tools over HTTP until stopped.

    Args:
        port: The port to listen on.
        public_host: The host name a tunnel in front of this server answers to. The MCP library refuses any other
            Host header, so a tunnel without this will be turned away.
        no_auth: Serve with no token. Only for a local demo on made-up data.

    Returns:
        The exit code.
    """
    load_dotenv()
    token = None if no_auth else os.environ.get(TOKEN_VARIABLE, "").strip()
    if not no_auth and not token:
        print(f"{TOKEN_VARIABLE} is not set. Set it in .env, or pass --no-auth to serve with no token at all.")
        return 1
    where = f"http://{CONFIG.host}:{port}{CONFIG.path}"
    guard = "no authentication" if no_auth else "a bearer token"
    print(f"Serving the three read tools at {where} with {guard}. Stop with Ctrl+C.")
    if public_host:
        print(f"Also answering to Host {public_host}.")
    serve(build_app(token, public_host), port)
    return 0
