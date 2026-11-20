"""The hook events: what each one answers, in the shape Copilot reads.

The payloads here use camelCase field names, which is what Copilot sends for a camelCase event name.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from subfinder.lib.demo.project_files import hook_config
from subfinder.lib.hooks.events import EVENTS, bare_tool_name, on_agent_stop, on_pre_tool_use, on_session_start
from subfinder.lib.statement.tools import save_summary, tag_subscription

_TAGGED = ["T05", "T18", "T30"]


def _event(**payload: Any) -> str:  # noqa: ANN401 - event payloads are arbitrary JSON
    return json.dumps({"sessionId": "test", "cwd": ".", "timestamp": 0, **payload})


def _pre_tool_use(tool: str, args: dict[str, Any]) -> dict[str, Any]:
    answer: dict[str, Any] = json.loads(on_pre_tool_use(_event(toolName=tool, toolArgs=args)))
    return answer


def _tag_tunebox() -> None:
    tag_subscription("Tunebox", _TAGGED)


@pytest.mark.parametrize(
    ("spelling", "expected"),
    [
        ("save_summary", "save_summary"),
        ("subfinder/save_summary", "save_summary"),
        ("mcp__subfinder__save_summary", "save_summary"),
        ("bash", "bash"),
    ],
)
def test_every_plausible_spelling_of_a_tool_name_is_understood(spelling: str, expected: str) -> None:
    """GitHub does not document how an MCP tool is spelled in toolName, so the hook accepts the lot."""
    assert bare_tool_name(spelling) == expected


def test_a_tool_with_no_check_gets_no_decision() -> None:
    assert _pre_tool_use("bash", {"command": "ls"}) == {}


def test_a_charge_that_is_not_on_the_statement_is_denied() -> None:
    answer = _pre_tool_use("subfinder/tag_subscription", {"merchant": "Ghost", "transaction_ids": ["T99"]})
    assert answer["permissionDecision"] == "deny"
    assert "T99 is not on the statement" in answer["permissionDecisionReason"]


def test_an_overstated_saving_is_denied_however_the_tool_is_spelled() -> None:
    _tag_tunebox()
    args = {
        "lines": [{"merchant": "Tunebox", "monthly_saving": "999.00", "note": "Too much."}],
        "total_monthly_saving": "999.00",
    }
    for spelling in ("save_summary", "subfinder/save_summary", "mcp__subfinder__save_summary"):
        answer = _pre_tool_use(spelling, args)
        assert answer["permissionDecision"] == "deny"
        assert "more than its latest charge of 109.00" in answer["permissionDecisionReason"]


def test_an_honest_summary_gets_no_decision() -> None:
    _tag_tunebox()
    args = {
        "lines": [{"merchant": "Tunebox", "monthly_saving": "109.00", "note": "Music."}],
        "total_monthly_saving": "109.00",
    }
    assert _pre_tool_use("subfinder/save_summary", args) == {}


def test_arguments_that_do_not_parse_are_denied() -> None:
    answer = _pre_tool_use("subfinder/tag_subscription", {"merchant": "Tunebox"})
    assert answer["permissionDecision"] == "deny"
    assert "not valid" in answer["permissionDecisionReason"]


def test_an_unreadable_event_is_denied() -> None:
    """This hook stands between the model and a write, so anything it cannot read fails closed."""
    answer = json.loads(on_pre_tool_use("not json at all"))
    assert answer["permissionDecision"] == "deny"


def test_a_denied_call_is_logged_and_the_tool_never_runs(workspace: Path) -> None:
    _pre_tool_use("subfinder/tag_subscription", {"merchant": "Ghost", "transaction_ids": ["T99"]})
    entries = [json.loads(line) for line in (workspace / "audit.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [entry["outcome"] for entry in entries] == ["denied"]
    assert not (workspace / "workbook.json").exists()


def test_agent_stop_sends_a_half_done_run_back() -> None:
    _tag_tunebox()
    answer = json.loads(on_agent_stop(_event(stop_hook_active=False)))
    assert answer["decision"] == "block"
    assert "save_summary" in answer["reason"]


def test_agent_stop_leaves_a_finished_run_alone() -> None:
    _tag_tunebox()
    save_summary([], total_monthly_saving=Decimal("0.00"))
    assert json.loads(on_agent_stop(_event(stop_hook_active=False))) == {}


def test_agent_stop_leaves_ordinary_work_alone() -> None:
    """The hook runs at the end of every turn, so a session that never tagged anything is not a run."""
    assert json.loads(on_agent_stop(_event(stop_hook_active=False))) == {}


def test_agent_stop_honours_stop_hook_active() -> None:
    _tag_tunebox()
    assert json.loads(on_agent_stop(_event(stop_hook_active=True))) == {}


def test_agent_stop_accepts_either_spelling_of_stop_hook_active() -> None:
    _tag_tunebox()
    assert json.loads(on_agent_stop(_event(stopHookActive=True))) == {}


def test_session_start_says_nothing_when_there_is_no_run() -> None:
    assert json.loads(on_session_start(_event(source="startup"))) == {}


def test_session_start_describes_the_run_it_finds() -> None:
    _tag_tunebox()
    answer = json.loads(on_session_start(_event(source="resume")))
    assert "Tunebox" in answer["additionalContext"]
    assert "no summary is saved yet" in answer["additionalContext"]


def test_every_configured_event_has_a_handler() -> None:
    assert set(hook_config()["hooks"]) == set(EVENTS)


@pytest.mark.parametrize("event", sorted(EVENTS))
def test_each_event_runs_as_its_own_process(event: str) -> None:
    """Copilot starts a process per event, so the entry point has to work under `python -m`."""
    result = subprocess.run(
        [sys.executable, "-m", "subfinder.lib.hooks", event],
        input=_event(toolName="bash", toolArgs={}, stop_hook_active=True, source="startup"),
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=dict(os.environ),
        check=True,
    )
    assert json.loads(result.stdout) == {}
