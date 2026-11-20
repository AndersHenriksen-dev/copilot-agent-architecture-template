"""The `run` command: it sends nothing without --yes, and it reports what the model agreed with."""

from __future__ import annotations

import json
from typing import Any

import httpx2
import pytest

from subfinder.lib.api.clean_merchants import TOKEN_VARIABLE
from subfinder.lib.api.commands import cmd_run
from subfinder.lib.api.scripted import CONFIG as REFERENCE


def test_only_prints_the_plan_without_yes(capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    def no_client(*_: object, **__: object) -> None:
        raise AssertionError("a client was created without --yes")

    monkeypatch.setattr("subfinder.lib.api.commands.httpx2.Client", no_client)
    assert cmd_run(yes=False) == 0
    output = capsys.readouterr().out
    assert "Nothing was sent" in output
    assert "GitHub Models" in output


def test_with_yes_the_whole_path_runs_and_reports(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    answer: dict[str, Any] = {
        "choices": [{"message": {"content": json.dumps({"lines": [line.model_dump() for line in REFERENCE.lines]})}}],
        "usage": {"prompt_tokens": 1118, "completion_tokens": 865},
    }

    def handle(_: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, json=answer)

    # Captured before the patch, because patching the attribute on the module would make the lambda call itself.
    real_client = httpx2.Client
    monkeypatch.setenv(TOKEN_VARIABLE, "test-token")
    monkeypatch.setattr("subfinder.lib.api.commands.load_dotenv", lambda: None)
    monkeypatch.setattr(
        "subfinder.lib.api.commands.httpx2.Client",
        lambda: real_client(transport=httpx2.MockTransport(handle)),
    )
    assert cmd_run(yes=True) == 0
    output = capsys.readouterr().out
    assert "506.00" in output
    assert f"{len(REFERENCE.lines)} of {len(REFERENCE.lines)} descriptions" in output
    assert "1118 in, 865 out" in output
    assert "bills nothing" in output
