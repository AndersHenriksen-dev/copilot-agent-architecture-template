"""The one model call: the request it builds, and what it does with every answer it can get back.

No test reaches GitHub Models. The client is wired to a stand-in transport, because the model is a boundary the tests
must not cross.
"""

from __future__ import annotations

import json
from typing import Any

import httpx2
import pytest

from subfinder.lib.api.clean_merchants import (
    CONFIG,
    TOKEN_VARIABLE,
    CleanedLines,
    build_request,
    clean_with_github_models,
    token_from_env,
)
from subfinder.lib.api.scripted import CONFIG as REFERENCE

DESCRIPTIONS = ["TUNEBOX P2F3A1", "TNBX*PREMIUM"]


@pytest.fixture(autouse=True)
def _token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(TOKEN_VARIABLE, "test-token")


def _client(answer: dict[str, Any], status: int = 200) -> tuple[httpx2.Client, list[httpx2.Request]]:
    """A client whose requests are answered by `answer`, and the list the requests are recorded in."""
    seen: list[httpx2.Request] = []

    def handle(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        return httpx2.Response(status, json=answer)

    return httpx2.Client(transport=httpx2.MockTransport(handle)), seen


def _answer(lines: list[dict[str, str]]) -> dict[str, Any]:
    content = json.dumps({"lines": lines})
    return {
        "choices": [{"message": {"content": content}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 1118, "completion_tokens": 865},
    }


def _reference_lines() -> list[dict[str, str]]:
    return [line.model_dump() for line in REFERENCE.lines if line.description in DESCRIPTIONS]


def test_a_missing_token_says_why_the_gh_cli_token_will_not_do(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(TOKEN_VARIABLE, raising=False)
    with pytest.raises(ValueError, match="models:read"):
        token_from_env()


def test_the_request_asks_the_api_to_enforce_the_shape() -> None:
    body = build_request(DESCRIPTIONS)
    assert body["response_format"]["type"] == "json_schema"
    assert body["response_format"]["json_schema"]["strict"] is True
    schema = body["response_format"]["json_schema"]["schema"]
    assert schema == CleanedLines.model_json_schema()
    assert schema["properties"]["lines"]


def test_the_request_sends_no_sampling_parameters() -> None:
    """Keeping these out means a model that rejects one cannot fail the whole call."""
    body = build_request(DESCRIPTIONS)
    for parameter in ("temperature", "top_p", "top_k", "seed"):
        assert parameter not in body


def test_the_request_carries_the_descriptions_and_the_model() -> None:
    body = build_request(DESCRIPTIONS)
    assert body["messages"][0]["role"] == "system"
    assert json.loads(body["messages"][1]["content"]) == DESCRIPTIONS
    assert "/" in body["model"]


def test_a_good_answer_is_parsed_with_its_token_counts() -> None:
    client, seen = _client(_answer(_reference_lines()))
    with client:
        cleaning = clean_with_github_models(client, DESCRIPTIONS)
    assert {line.merchant for line in cleaning.lines} == {"Tunebox"}
    assert (cleaning.input_tokens, cleaning.output_tokens) == (1118, 865)
    assert str(seen[0].url) == CONFIG.endpoint
    assert seen[0].headers["authorization"] == "Bearer test-token"


def test_a_refusal_is_not_mistaken_for_an_answer() -> None:
    """A refusal arrives as an ordinary 200, so it has to be looked for before reading the content."""
    client, _ = _client({"choices": [{"message": {"refusal": "I cannot help with that."}}]})
    with client, pytest.raises(ValueError, match="refused"):
        clean_with_github_models(client, DESCRIPTIONS)


def test_an_empty_answer_fails_loudly() -> None:
    client, _ = _client({"choices": [{"message": {"content": ""}, "finish_reason": "length"}]})
    with client, pytest.raises(ValueError, match="no content"):
        clean_with_github_models(client, DESCRIPTIONS)


def test_no_choices_fails_loudly() -> None:
    client, _ = _client({"choices": []})
    with client, pytest.raises(ValueError, match="no answer"):
        clean_with_github_models(client, DESCRIPTIONS)


def test_a_missing_line_fails_rather_than_being_filled_in() -> None:
    """The schema fixes the shape of the answer, not its completeness."""
    client, _ = _client(_answer(_reference_lines()[:1]))
    with client, pytest.raises(ValueError, match="did not clean"):
        clean_with_github_models(client, DESCRIPTIONS)


def test_an_http_error_is_not_swallowed() -> None:
    client, _ = _client({"message": "Bad credentials"}, status=401)
    with client, pytest.raises(httpx2.HTTPStatusError):
        clean_with_github_models(client, DESCRIPTIONS)
