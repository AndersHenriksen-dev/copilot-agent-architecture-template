"""The HTTP transport: what Copilot can reach from GitHub's side, and what it has to prove first."""

from __future__ import annotations

import anyio
import httpx2
import pytest
from mcp import Client

from subfinder.lib.mcp_server.commands import TOKEN_VARIABLE, cmd_serve
from subfinder.lib.mcp_server.http import build_app, serving_in_background


def _tool_names(url: str) -> set[str]:
    async def names() -> set[str]:
        async with Client(url) as client:
            return {tool.name for tool in (await client.list_tools()).tools}

    return anyio.run(names)


def test_only_the_read_tools_are_served() -> None:
    """A write that no hook of yours can see does not get an entrance."""
    with serving_in_background(build_app(None, None)) as url:
        assert _tool_names(url) == {"list_transactions", "get_merchant", "get_summary"}


def test_a_request_without_the_token_is_refused() -> None:
    with serving_in_background(build_app("secret-token", None)) as url, httpx2.Client() as client:
        assert client.post(url, json={}).status_code == 401
        assert client.post(url, json={}, headers={"Authorization": "Bearer wrong"}).status_code == 401


def test_the_right_token_gets_through() -> None:
    with serving_in_background(build_app("secret-token", None)) as url, httpx2.Client() as client:
        response = client.post(
            url,
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
            headers={
                "Authorization": "Bearer secret-token",
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
            },
        )
        assert response.status_code != 401


def test_serving_without_a_token_or_no_auth_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    """Serving an open port by accident should not be one forgotten environment variable away."""
    monkeypatch.delenv(TOKEN_VARIABLE, raising=False)
    monkeypatch.setattr("subfinder.lib.mcp_server.commands.load_dotenv", lambda: None)
    assert cmd_serve(port=0, public_host=None, no_auth=False) == 1
