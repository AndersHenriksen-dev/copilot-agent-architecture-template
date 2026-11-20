"""The `run` command: the whole job with a real model and no Copilot. It prints its plan and stops unless told to go."""

from __future__ import annotations

from functools import partial

import httpx2
from dotenv import load_dotenv

from subfinder.lib.api.clean_merchants import clean_with_github_models
from subfinder.lib.api.run import RunResult, find_and_save
from subfinder.lib.api.scripted import CONFIG as REFERENCE
from subfinder.lib.api.scripted import count_agreeing
from subfinder.lib.shared.settings import model_from_env


def _print_result(result: RunResult) -> None:
    for item in result.recurring:
        state = f"{item.monthly_cost} a month" if item.active else "ended"
        rise = f", up {item.price_rise}" if item.price_rise else ""
        print(f"  {item.merchant}: {state}{rise}")
    print(f"Total if all active ones were cancelled: {result.summary.total_monthly_saving} DKK a month")
    agreeing = count_agreeing(result.cleaning.lines)
    print(f"Agreement with the hand-written answer: {agreeing} of {len(REFERENCE.lines)} descriptions")


def cmd_run(yes: bool) -> int:
    """Clean the names with GitHub Models, then find and save the subscriptions.

    Args:
        yes: Whether to make the real call. Without it, this only prints the plan.

    Returns:
        The exit code.
    """
    model = model_from_env()
    print(f"Plan: 1 chat-completions call to GitHub Models on {model}, roughly 1,100 input and 900 output tokens.")
    if not yes:
        print("Nothing was sent. Add --yes to make the call. `subfinder demo` needs no token and sends nothing.")
        return 0
    load_dotenv()
    with httpx2.Client() as client:
        result = find_and_save(partial(clean_with_github_models, client))
    _print_result(result)
    tokens = result.cleaning
    print(f"Tokens: {tokens.input_tokens} in, {tokens.output_tokens} out.")
    print("GitHub Models bills nothing for this. It counts against your account's rate limit for the model's tier.")
    return 0
