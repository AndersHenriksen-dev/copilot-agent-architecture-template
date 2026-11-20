"""The one model call: turn messy statement descriptions into clean merchants and categories.

This is the part of the job a model is good at and code is not. It is one request with a fixed output shape, not an
agent: nothing here chooses what to do next. Everything after it is arithmetic.

The call goes to GitHub Models, which speaks the OpenAI chat-completions shape and takes a GitHub token with the
`models:read` permission. No Copilot is involved, so none of the seven types in this repo apply to it: no instructions
are loaded, no skill, no custom agent, and above all no hook. Whatever must hold here has to be called by this code.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import httpx2

from subfinder.lib.shared.settings import Strict, config_for, model_from_env
from subfinder.lib.statement.recurring import CleanedLine

TOKEN_VARIABLE = "GITHUB_MODELS_TOKEN"


class _Config(Strict):
    endpoint: str
    api_version: str
    schema_name: str
    max_tokens: int
    timeout_seconds: float
    system: str


CONFIG = config_for(__name__, _Config)


class CleanedLines(Strict):
    """The shape the model must answer in. A JSON schema on the request makes the API hold it to this."""

    lines: list[CleanedLine]


@dataclass(frozen=True)
class Cleaning:
    """What a cleaner produced, and the tokens it spent. The hand-written answer spends none."""

    lines: list[CleanedLine]
    input_tokens: int = 0
    output_tokens: int = 0


MerchantCleaner = Callable[[list[str]], Cleaning]
"""Anything that can clean descriptions: GitHub Models, or the hand-written answer in the demo and the tests."""


def token_from_env() -> str:
    """The GitHub token for the call.

    Returns:
        The token.

    Raises:
        ValueError: If it is not set, with the reason it cannot fall back to the `gh` CLI's own token.
    """
    token = os.environ.get(TOKEN_VARIABLE, "").strip()
    if not token:
        raise ValueError(
            f"{TOKEN_VARIABLE} is not set. Put a fine-grained token with the `models:read` permission in .env. "
            "The token `gh auth login` stores does not carry that permission, so it cannot be used instead.",
        )
    return token


def build_request(descriptions: list[str]) -> dict[str, Any]:
    """The request body, kept separate so a test can read it without making a call.

    Args:
        descriptions: The raw statement descriptions.

    Returns:
        The JSON body. Any, because it is a JSON document and not one of our own shapes.
    """
    return {
        "model": model_from_env(),
        "max_tokens": CONFIG.max_tokens,
        "messages": [
            {"role": "system", "content": CONFIG.system},
            {"role": "user", "content": json.dumps(descriptions, indent=0)},
        ],
        # strict makes the API hold the answer to the schema instead of asking the model nicely for JSON.
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": CONFIG.schema_name,
                "strict": True,
                "schema": CleanedLines.model_json_schema(),
            },
        },
    }


def _check_every_line_came_back(descriptions: list[str], lines: list[CleanedLine]) -> None:
    """The schema fixes the shape of the answer, not its content, so this checks that the content is complete."""
    answered = {line.description for line in lines}
    missing = sorted(set(descriptions) - answered)
    if missing:
        raise ValueError(f"The model did not clean these lines: {missing}")


def _read_answer(payload: dict[str, Any]) -> CleanedLines:
    """Pull the answer out of the response, failing loudly on a refusal or an empty choice."""
    choices = payload.get("choices") or []
    if not choices:
        raise ValueError(f"The response carried no answer: {payload}")
    message = choices[0].get("message") or {}
    if message.get("refusal"):
        raise ValueError(f"The model refused: {message['refusal']}")
    content = message.get("content")
    if not content:
        finish = choices[0].get("finish_reason")
        raise ValueError(f"The model returned no content (finish_reason: {finish}).")
    return CleanedLines.model_validate_json(content)


def clean_with_github_models(client: httpx2.Client, descriptions: list[str]) -> Cleaning:
    """Send every description in one request.

    Args:
        client: The HTTP client. Tests pass one wired to a stand-in, because the model is a boundary they must not
            cross.
        descriptions: The raw statement descriptions.

    Returns:
        A clean merchant and category for each description, and the tokens spent.

    Raises:
        ValueError: If the model refused, answered with nothing, or left out a line.
    """
    response = client.post(
        CONFIG.endpoint,
        headers={
            "Authorization": f"Bearer {token_from_env()}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": CONFIG.api_version,
        },
        json=build_request(descriptions),
        timeout=CONFIG.timeout_seconds,
    )
    response.raise_for_status()
    payload: dict[str, Any] = response.json()
    lines = _read_answer(payload).lines
    _check_every_line_came_back(descriptions, lines)
    usage = payload.get("usage") or {}
    return Cleaning(
        lines=lines,
        input_tokens=int(usage.get("prompt_tokens", 0)),
        output_tokens=int(usage.get("completion_tokens", 0)),
    )
