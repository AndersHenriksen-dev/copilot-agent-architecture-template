"""What runs on each Copilot hook event: the event as JSON in, one JSON object out.

Copilot starts a new process per event, writes the event to its stdin and reads one JSON object from its stdout.
`.github/hooks/subfinder-hooks.json` says which event runs which command. An empty object means "no decision", which
leaves Copilot's normal permission rules in charge.

The event names used here are camelCase, which is the form that delivers camelCase payload fields such as `toolName`.
The PascalCase aliases (`PreToolUse`) switch the payload to snake_case instead, so the two spellings cannot be mixed.
See https://docs.github.com/en/copilot/reference/hooks-reference.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from subfinder.lib.hooks.checks import Decision, check_summary, check_tag
from subfinder.lib.shared.settings import Strict, audit_log_path, config_for
from subfinder.lib.statement.transactions import STATEMENT
from subfinder.lib.statement.workbook import Summary, Tag, load_workbook


class _Config(Strict):
    stop_reason: str
    session_note_prefix: str


CONFIG = config_for(__name__, _Config)


class _Event(BaseModel):
    """The fields every event shares. Copilot sends more, and may add others, so the rest are ignored."""

    model_config = ConfigDict(populate_by_name=True)

    session_id: str = Field(default="", alias="sessionId")


class _ToolEvent(_Event):
    """A tool event. `toolArgs` differs per tool, so it is parsed into a typed model before use, in `_check_call`."""

    tool_name: str = Field(alias="toolName")
    # Any: arguments differ per tool.
    tool_args: dict[str, Any] = Field(default_factory=dict, alias="toolArgs")


class _StopEvent(_Event):
    """An `agentStop` event. GitHub documents `stop_hook_active` under that name in both payload formats."""

    stop_hook_active: bool = Field(default=False, alias="stopHookActive")


def bare_tool_name(name: str) -> str:
    """The tool's own name, without whatever prefix the surface puts in front of it.

    GitHub names Copilot's built-in tools and says a tool with no Claude equivalent keeps its runtime name, but it
    does not say how an MCP server's tools are spelled in `toolName`. So every plausible spelling is accepted:
    `save_summary`, `subfinder/save_summary` and `mcp__subfinder__save_summary` all give `save_summary`.

    Args:
        name: The tool name as the event spelled it.

    Returns:
        The last segment, which is the tool's own name.
    """
    return re.split(r"/|__", name)[-1]


def _check_call(event: _ToolEvent) -> Decision:
    """Run the check for a tool. A tool with no check is allowed, and arguments that do not parse are denied."""
    tool = bare_tool_name(event.tool_name)
    try:
        if tool == "tag_subscription":
            return check_tag(Tag.model_validate(event.tool_args), load_workbook().tags, STATEMENT)
        if tool == "save_summary":
            return check_summary(Summary.model_validate(event.tool_args), load_workbook().tags, STATEMENT)
    except ValidationError as error:
        return Decision(allowed=False, reason=f"The arguments are not valid: {error}")
    return Decision(allowed=True)


def _audit(outcome: str, event: _ToolEvent) -> None:
    """Add one line to the audit log. The model cannot skip it, because it does not run this."""
    entry = {
        "time": datetime.now(UTC).isoformat(timespec="seconds"),
        "outcome": outcome,
        "tool": event.tool_name,
        "args": event.tool_args,
    }
    path = audit_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(entry) + "\n")


def _nothing_to_say() -> str:
    """No decision, which leaves Copilot's own permission rules in charge."""
    return json.dumps({})


def on_pre_tool_use(raw: str) -> str:
    """Before a tool runs: deny it if its check fails.

    Anything unreadable is denied. This hook stands between the model and a write, so it fails closed, which is also
    what Copilot does by itself when a `preToolUse` command hook exits non-zero.
    """
    try:
        event = _ToolEvent.model_validate_json(raw)
    except ValidationError as error:
        reason = f"The subfinder hook could not read this event: {error}"
        return json.dumps({"permissionDecision": "deny", "permissionDecisionReason": reason})
    decision = _check_call(event)
    if decision.allowed:
        return _nothing_to_say()
    _audit("denied", event)
    return json.dumps({"permissionDecision": "deny", "permissionDecisionReason": decision.reason})


def on_post_tool_use(raw: str) -> str:
    """After a tool has run: record it. The tool has already happened, so this hook cannot stop anything."""
    _audit("ran", _ToolEvent.model_validate_json(raw))
    return _nothing_to_say()


def on_agent_stop(raw: str) -> str:
    """When the model wants to finish: send it back if the run is half done.

    A session with no tags is not a run, so ordinary work in this repo is never held up. `stop_hook_active` means this
    hook already sent the model back once, and asking again could loop forever.
    """
    if _StopEvent.model_validate_json(raw).stop_hook_active:
        return _nothing_to_say()
    workbook = load_workbook()
    if workbook.tags and workbook.summary is None:
        return json.dumps({"decision": "block", "reason": CONFIG.stop_reason})
    return _nothing_to_say()


def on_session_start(raw: str) -> str:
    """When a session begins: tell the model what the last one left behind, so it does not tag the same charge twice.

    `additionalContext` is the only thing this event can do. It is the one hook here that adds context rather than
    taking a decision, and nothing is added when there is no run to describe.
    """
    _Event.model_validate_json(raw)
    workbook = load_workbook()
    if not workbook.tags:
        return _nothing_to_say()
    tagged = ", ".join(tag.merchant for tag in workbook.tags)
    saved = "a summary is saved" if workbook.summary else "no summary is saved yet"
    return json.dumps({"additionalContext": f"{CONFIG.session_note_prefix} {tagged} tagged, and {saved}."})


EVENTS: dict[str, Callable[[str], str]] = {
    "sessionStart": on_session_start,
    "preToolUse": on_pre_tool_use,
    "postToolUse": on_post_tool_use,
    "agentStop": on_agent_stop,
}
