"""The `check` command: run the checks against whatever the current run has written, and say what they found.

The same functions the `preToolUse` hook calls, run by hand. The skill uses it to confirm a run before it finishes,
and it is the quickest way to see why a write was refused.
"""

from __future__ import annotations

from subfinder.lib.hooks.checks import check_summary, check_tag
from subfinder.lib.statement.transactions import STATEMENT
from subfinder.lib.statement.workbook import load_workbook


def cmd_check() -> int:
    """Print the current run and whether the checks pass.

    Returns:
        0 if every check passes, 1 if any fails. Nothing written is changed either way.
    """
    workbook = load_workbook()
    if not workbook.tags:
        print("Nothing tagged yet, so there is nothing to check.")
        return 0

    failures = []
    print(f"Tagged: {len(workbook.tags)} merchants")
    for tag in workbook.tags:
        others = [other for other in workbook.tags if other.merchant != tag.merchant]
        decision = check_tag(tag, others, STATEMENT)
        state = "ok" if decision.allowed else f"FAILS: {decision.reason}"
        print(f"  {tag.merchant:<14} {len(tag.transaction_ids)} charges  {state}")
        failures += [] if decision.allowed else [tag.merchant]

    if workbook.summary is None:
        # Not a failed check, but not a run anyone should trust either, so it does not report success.
        print("No summary saved yet. The agentStop hook will send the model back for one.")
        return 1

    decision = check_summary(workbook.summary, workbook.tags, STATEMENT)
    total = workbook.summary.total_monthly_saving
    print(f"Summary: {len(workbook.summary.lines)} lines, {total} DKK a month in total")
    if decision.allowed:
        print("Every check passes.")
        return 1 if failures else 0
    print(f"Summary FAILS: {decision.reason}")
    return 1
