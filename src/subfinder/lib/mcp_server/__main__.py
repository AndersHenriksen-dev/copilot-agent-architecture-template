"""Run the MCP server over stdio: `python -m subfinder.lib.mcp_server`. This is what the two mcp.json files launch."""

from __future__ import annotations

from subfinder.lib.mcp_server.server import build_server

build_server().run("stdio")
