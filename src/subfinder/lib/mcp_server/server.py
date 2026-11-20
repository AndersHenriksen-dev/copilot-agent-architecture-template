"""The MCP server: the statement tools, served to whoever launches it.

One server, two transports, because Copilot reaches it from two directions. On your machine it is stdio, launched from
`.vscode/mcp.json` or `.github/mcp.json`. From GitHub's side it is HTTP, configured in the repository's own Copilot
settings. `http.py` holds that half.

Every read tool is annotated `read_only_hint`. Copilot code review drops any tool whose `tools/list` entry does not
set `annotations.readOnlyHint: true`, so the annotation is what decides whether a review can use a tool at all.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

from subfinder.lib.shared.settings import Strict, config_for
from subfinder.lib.statement import tools


class _Config(Strict):
    name: str
    instructions: str
    read_tools: dict[str, str]
    write_tools: dict[str, str]


CONFIG = config_for(__name__, _Config)

# Any: tools have different signatures, and MCPServer reads each one's own to build its schema.
_READ_FUNCTIONS: dict[str, Callable[..., Any]] = {
    "list_transactions": tools.list_transactions,
    "get_merchant": tools.get_merchant,
    "get_summary": tools.get_summary,
}
_WRITE_FUNCTIONS: dict[str, Callable[..., Any]] = {
    "tag_subscription": tools.tag_subscription,
    "save_summary": tools.save_summary,
}


def _new_server() -> MCPServer:
    return MCPServer(CONFIG.name, instructions=CONFIG.instructions, log_level="WARNING")


def add_read_tools(server: MCPServer) -> None:
    """Add the tools that change nothing. These are the only ones served over HTTP."""
    annotations = ToolAnnotations(read_only_hint=True)
    for name, function in _READ_FUNCTIONS.items():
        server.add_tool(function, name=name, description=CONFIG.read_tools[name], annotations=annotations)


def _add_write_tools(server: MCPServer) -> None:
    annotations = ToolAnnotations(read_only_hint=False)
    for name, function in _WRITE_FUNCTIONS.items():
        server.add_tool(function, name=name, description=CONFIG.write_tools[name], annotations=annotations)


def build_server() -> MCPServer:
    """The full server: every tool, for a client on this machine with your hooks around it."""
    server = _new_server()
    add_read_tools(server)
    _add_write_tools(server)
    return server


def build_read_only_server() -> MCPServer:
    """The same server with the write tools left out, for anything reached from outside this machine."""
    server = _new_server()
    add_read_tools(server)
    return server
