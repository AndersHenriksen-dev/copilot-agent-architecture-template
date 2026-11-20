"""The free walkthrough: every type doing its real job, in the order a run uses them.

Nothing is simulated except the model. The MCP server is a real subprocess, each hook is a real process fed the JSON
Copilot sends, and the HTTP transport answers over real HTTP on this machine. It stops at the first result that is not
what it should be, so it doubles as an end-to-end check, and CI runs it on every pull request.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from decimal import Decimal
from typing import Any

import anyio
from mcp import Client, StdioServerParameters
from mcp.types import Tool

from subfinder.lib.api.scripted import clean_from_reference
from subfinder.lib.demo.project_files import (
    agent_files,
    always_on_instruction_files,
    hook_config,
    instruction_applies_to,
    mcp_server_commands,
    path_instruction_files,
    prompt_files,
    read_frontmatter,
    skill_bundled_files,
    skill_files,
)
from subfinder.lib.mcp_server.http import build_app, serving_in_background
from subfinder.lib.shared.settings import REPO_ROOT, audit_log_path
from subfinder.lib.statement.recurring import RULES, Recurring, find_recurring
from subfinder.lib.statement.transactions import STATEMENT
from subfinder.lib.statement.workbook import load_workbook

_STATEMENT_FILE = "src/subfinder/lib/statement/recurring.py"
_WRITE_TOOLS = ("tag_subscription", "save_summary")


def _heading(text: str) -> None:
    print(f"\n=== {text}")


def _expect(condition: bool, what: str) -> None:
    """Say a result is right, or stop the walkthrough."""
    if not condition:
        raise RuntimeError(f"Expected: {what}")
    print(f"  ok: {what}")


def _show_instructions() -> None:
    _heading("INSTRUCTIONS: text Copilot loads, which asks but does not enforce")
    for path in always_on_instruction_files():
        print(f"  {path.relative_to(REPO_ROOT).as_posix()}: every session")
    for path in path_instruction_files():
        globs = read_frontmatter(path)[0]["applyTo"]
        print(f"  {path.relative_to(REPO_ROOT).as_posix()}: applyTo {globs}")

    by_name = {path.name.removesuffix(".instructions.md"): path for path in path_instruction_files()}
    money, hooks, python = by_name["money"], by_name["hooks"], by_name["python"]
    _expect(instruction_applies_to(money, _STATEMENT_FILE), f"money loads for {_STATEMENT_FILE}")
    _expect(not instruction_applies_to(money, "README.md"), "money stays out of context for README.md")
    _expect(
        instruction_applies_to(hooks, "src/subfinder/lib/hooks/events.py")
        and not instruction_applies_to(hooks, _STATEMENT_FILE),
        "hooks loads for the hook code and not for the statement",
    )
    _expect(
        instruction_applies_to(python, _STATEMENT_FILE) and not instruction_applies_to(python, "docs/types.md"),
        "python is scoped by file type rather than by folder, so it covers both of the others",
    )


def _show_prompt_file() -> None:
    _heading("PROMPT FILE: one task, run by hand")
    prompt = prompt_files()[0]
    header, body = read_frontmatter(prompt)
    print(f"  /{header['name']}: {header['argument-hint']}")
    print(f"  Tools it may use: {header['tools']}")
    _expect("${input:merchant" in body, "the task takes its merchant as an input variable")
    _expect(
        all(tool not in str(header["tools"]) for tool in _WRITE_TOOLS),
        "the allowlist is the subfinder server, so it cannot save anything",
    )
    print("  VS Code runs prompt files only in its Local harness, which is due to go in February 2027.")


def _show_skill() -> None:
    _heading("SKILL: a procedure Copilot loads when it decides the task needs it")
    skill = skill_files()[0]
    header, body = read_frontmatter(skill)
    bundled = skill_bundled_files(skill)
    print(f"  {header['name']}")
    print(f"  Always in context: {len(header['description'])} characters of description")
    print(f"  Loaded on use: {len(body)} characters of steps, plus {len(bundled)} bundled files")
    for path in bundled:
        print(f"    {path.name}")
    _expect(header["name"] == skill.parent.name, "the skill's name matches its folder")
    _expect(len(header["description"]) < len(body), "the part always in context is the smaller part")
    _expect(
        "allowed-tools" not in header,
        "nothing is pre-approved, so running the bundled script still asks",
    )


def _show_custom_agent() -> None:
    _heading("CUSTOM AGENT: a persona with its own tool allowlist")
    agent = agent_files()[0]
    header, _ = read_frontmatter(agent)
    print(f"  {header['name']}: {len(header['tools'])} tools allowed")
    for tool in header["tools"]:
        print(f"    {tool}")
    _expect(
        all(not any(write in tool for write in _WRITE_TOOLS) for tool in header["tools"]),
        "no write tool is on the list, so the auditor cannot change a run",
    )
    _expect(
        all(alias not in header["tools"] for alias in ("edit", "execute")),
        "it cannot edit a file or run a command either",
    )


def _clean_with_scripted_model() -> list[Recurring]:
    _heading("THE MODEL: one call cleans the names (scripted here: `subfinder run` calls GitHub Models)")
    descriptions = sorted({line.description for line in STATEMENT.transactions})
    lines = clean_from_reference(descriptions).lines
    print(f"  {len(STATEMENT.transactions)} statement lines, {len(descriptions)} different descriptions")
    for line in lines:
        if line.merchant == "Viewly":
            print(f"  {line.description!r} -> {line.merchant} ({line.category})")
    recurring = find_recurring(STATEMENT.transactions, lines, RULES)
    print("  Then plain arithmetic, no model:")
    for item in recurring:
        state = f"{item.monthly_cost} a month" if item.active else "ended"
        rise = f", up {item.price_rise}" if item.price_rise else ""
        print(f"    {item.merchant}: {state}{rise}")
    _expect([item.merchant for item in recurring if not item.active] == ["NewsDaily"], "NewsDaily is seen as ended")
    return [item for item in recurring if item.active]


def _call_stdio_server(calls: list[tuple[str, dict[str, Any]]]) -> list[Tool]:
    """Launch the real MCP server, make the calls, and give back its tools. Any: tool arguments are JSON."""

    async def main() -> list[Tool]:
        parameters = StdioServerParameters(
            command=sys.executable,
            args=["-m", "subfinder.lib.mcp_server"],
            env=os.environ.copy(),
        )
        async with Client(parameters) as client:
            for tool, arguments in calls:
                result = await client.call_tool(tool, arguments)
                if result.is_error:
                    raise RuntimeError(f"{tool} failed: {result.content}")
            return list((await client.list_tools()).tools)

    return anyio.run(main)


def _tag_over_mcp(active: list[Recurring]) -> None:
    _heading("MCP: the tools, reached by a real client over stdio")
    calls = [
        ("tag_subscription", {"merchant": item.merchant, "transaction_ids": item.transaction_ids}) for item in active
    ]
    tools = _call_stdio_server(calls)
    read_only = sorted(tool.name for tool in tools if tool.annotations and tool.annotations.read_only_hint)
    print(f"  The server offers: {', '.join(sorted(tool.name for tool in tools))}")
    print(f"  Annotated read-only: {', '.join(read_only)}")
    _expect(len(read_only) == 3, "the three read tools say so, which is what lets code review use them")
    _expect(len(load_workbook().tags) == len(active), f"{len(active)} subscriptions tagged, in a file on disk")

    commands = mcp_server_commands()
    for relative, command in commands.items():
        print(f"  {relative}: {' '.join(command)}")
    _expect(len(set(map(tuple, commands.values()))) == 1, "both MCP config files launch the same server")


def _run_hook(event: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Run a hook the way Copilot does: a new process with the event as JSON on stdin. Any: payloads are JSON.

    The field names here are camelCase, which is the form Copilot sends for a camelCase event name.
    """
    message = json.dumps({"sessionId": "demo", "cwd": str(REPO_ROOT), "timestamp": 0, **payload})
    result = subprocess.run(
        [sys.executable, "-m", "subfinder.lib.hooks", event],
        input=message,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=os.environ.copy(),
        check=True,
    )
    answer: dict[str, Any] = json.loads(result.stdout)
    return answer


def _summary_arguments(active: list[Recurring], extra: Decimal = Decimal("0.00")) -> dict[str, Any]:
    """The arguments of a save_summary call. With `extra`, its first line overclaims. Any: tool arguments are JSON."""
    savings = [item.monthly_cost + (extra if index == 0 else 0) for index, item in enumerate(active)]
    lines = [
        {"merchant": item.merchant, "monthly_saving": f"{saving:.2f}", "note": "Note."}
        for item, saving in zip(active, savings, strict=True)
    ]
    return {"lines": lines, "total_monthly_saving": f"{sum(savings):.2f}"}


def _save_through_hooks(active: list[Recurring]) -> None:
    _heading("HOOKS: code that runs at fixed points, whatever the model decides")

    note = _run_hook("sessionStart", {"source": "startup"})
    print(f"  sessionStart, additionalContext: {note['additionalContext']}")
    _expect("tagged" in note["additionalContext"], "a new session is told what the last one left behind")

    stopping_early = _run_hook("agentStop", {"stop_hook_active": False})
    print(f"  agentStop, tags but no summary: {stopping_early['decision']}")
    _expect(stopping_early["decision"] == "block", "a half-done run is sent back to finish")

    overclaim = _summary_arguments(active, extra=Decimal("500.00"))
    # The prefix is deliberate: GitHub does not document how an MCP tool is spelled in toolName.
    denied = _run_hook("preToolUse", {"toolName": "subfinder/save_summary", "toolArgs": overclaim})
    print(f"  preToolUse, saving overstated by 500.00: {denied['permissionDecision']}")
    print(f"    Reason the model reads: {denied['permissionDecisionReason']}")
    _expect(denied["permissionDecision"] == "deny", "a saving above the latest charge never reaches the tool")

    honest = _summary_arguments(active)
    passed = _run_hook("preToolUse", {"toolName": "mcp__subfinder__save_summary", "toolArgs": honest})
    _expect(passed == {}, "an honest summary gets no decision, however the tool name is spelled")
    _call_stdio_server([("save_summary", honest)])
    _run_hook("postToolUse", {"toolName": "subfinder/save_summary", "toolArgs": honest})

    audit = audit_log_path().read_text(encoding="utf-8").splitlines()
    outcomes = [json.loads(line)["outcome"] for line in audit]
    print(f"  postToolUse, audit log: {outcomes}")
    _expect(outcomes == ["denied", "ran"], "the audit log has the refused call and the one that ran")
    _expect(_run_hook("agentStop", {"stop_hook_active": False}) == {}, "the finished run may stop")
    _expect(
        _run_hook("agentStop", {"stop_hook_active": True}) == {},
        "stop_hook_active is honoured, so a session can always end",
    )


def _read_from_githubs_side() -> None:
    _heading("FROM GITHUB'S SIDE: the same server over HTTP, which no hook of yours can see")

    async def read(url: str) -> tuple[set[str], object]:
        async with Client(url) as client:
            tools = {tool.name for tool in (await client.list_tools()).tools}
            return tools, (await client.call_tool("get_summary", {})).structured_content

    with serving_in_background(build_app(None, None)) as url:
        tools, summary = anyio.run(read, url)
    print(f"  Over HTTP the server offers: {', '.join(sorted(tools))}")
    print("  The cloud agent and code review call it from GitHub, so your hooks are not in the path.")
    _expect(all(write not in tools for write in _WRITE_TOOLS), "no write tool is served over HTTP")
    _expect(
        isinstance(summary, dict) and summary["result"]["total_monthly_saving"] == "506.00",
        "the summary reads back",
    )


def _show_hook_wiring() -> None:
    _heading("WHAT IS WIRED TO WHAT")
    config = hook_config()
    for event, entries in config["hooks"].items():
        # A matcher is tested against a tool name, so only the two tool events have one.
        matcher = entries[0].get("matcher", "no matcher: this event is not about a tool")
        print(f"  {event:<14} {matcher}")
    _expect(config["version"] == 1, "the hook config declares version 1")
    _expect(
        all(write in config["hooks"]["preToolUse"][0]["matcher"] for write in _WRITE_TOOLS),
        "both write tools are behind the preToolUse matcher",
    )


def _show_result() -> None:
    _heading("RESULT")
    summary = load_workbook().summary
    if summary is None:
        raise RuntimeError("Expected a saved summary")
    for line in summary.lines:
        print(f"  {line.merchant:<12} {line.monthly_saving:>8} a month")
    print(f"  {'Total':<12} {summary.total_monthly_saving:>8} DKK a month if all were cancelled")
    print("\nEvery type did its job, and nothing here called a model or sent anything anywhere.")


def run_walkthrough() -> None:
    """Run every step in a throwaway workspace, so the demo never touches a real run."""
    with tempfile.TemporaryDirectory() as folder:
        os.environ["SUBFINDER_WORKSPACE"] = folder
        _show_instructions()
        _show_prompt_file()
        _show_skill()
        _show_custom_agent()
        active = _clean_with_scripted_model()
        _tag_over_mcp(active)
        _save_through_hooks(active)
        _read_from_githubs_side()
        _show_hook_wiring()
        _show_result()
