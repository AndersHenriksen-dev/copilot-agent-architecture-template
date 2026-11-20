---
name: find-subscriptions
description: Find the recurring subscriptions on the made-up bank statement in this repository, tag them and save one summary of what cancelling them would save. Use this whenever someone asks about subscriptions, recurring charges or what the statement costs each month.
---

# Find the subscriptions on the statement

The statement is three months of a made-up account in DKK. The same merchant is written differently from month to
month, which is the part that needs reading rather than arithmetic.

Use the `subfinder` MCP tools. Do not read `config/statement/transactions.yaml` directly: the tools are what the
hooks and the checks are wired around.

## Steps

1. **Read the whole statement.** Call `list_transactions`. There are 35 lines.

2. **Group the descriptions by real merchant.** Work out which raw descriptions are the same company. For example
   `TUNEBOX P2F3A1`, `TNBX*PREMIUM` and `TUNEBOX AB STHLM` are all Tunebox. Use `get_merchant` to collect every
   spelling: it ignores case, spaces and punctuation, so search for each spelling you have already seen.

3. **Decide which groups are subscriptions.** A subscription is charged by choice, roughly monthly, at a steady
   amount. Rent and a phone contract also recur, and groceries repeat at varying amounts, so neither is a
   subscription. Money in is never one.

4. **Tag each subscription.** Call `tag_subscription` once per merchant, with one clean merchant name and the ids of
   every charge that belongs to it. Tagging the same merchant again replaces its charges, so a correction is cheap.

5. **Work out each saving.** A merchant's monthly saving is its **latest** charge, not an average and not the sum.
   If a merchant's last charge is earlier than the statement's last month, it has already ended and its saving
   is `0.00`.

6. **Save one summary.** Follow [summary-format.md](summary-format.md) exactly, then call `save_summary` once.

7. **Confirm the run.** Run `uv run subfinder check` from the repository root. It runs the same functions the
   `preToolUse` hook runs, and prints every merchant and whether its numbers hold.

## What the hooks will refuse

These are not suggestions. `.github/hooks/subfinder-hooks.json` runs a check before `tag_subscription` and
`save_summary`, and the call never reaches the tool if it fails:

- a charge id that is not on the statement, or that is money in
- a charge already tagged under a different merchant, or listed twice under this one
- a saving larger than that merchant's latest charge
- a saving above `0.00` for a subscription whose last charge is not in the final month
- a total that does not equal the sum of the lines

A refusal comes back with the reason. Fix the numbers and call again.

The `agentStop` hook will also send you back if the run has tags but no saved summary, so finish step 6 before
ending the turn.

## Looking at what a run did

`summarize-audit.py` in this folder prints a tally of the audit log that the `postToolUse` hook writes. Run it from
the repository root with `python .github/skills/find-subscriptions/summarize-audit.py`. It needs nothing but the
standard library, and it is read-only.
