# The format of the summary

A supporting file of the `find-subscriptions` skill. Copilot makes every file in a skill's folder available once the
skill is in use, so this text costs nothing in a session that never asks about subscriptions.

`save_summary` takes two arguments.

## `lines`

One entry per tagged subscription, in alphabetical order by merchant:

| Field | What goes in it |
|---|---|
| `merchant` | The clean merchant name, spelled exactly as it was tagged |
| `monthly_saving` | A string with two decimals, such as `"119.00"`. The merchant's latest charge, or `"0.00"` if it has ended |
| `note` | One short sentence. Say if the price rose during the statement, and by how much. Otherwise say the price was unchanged |

## `total_monthly_saving`

A string with two decimals. It must equal the sum of the `monthly_saving` values exactly. The check adds them up and
refuses the call if the total disagrees, so do not round.

## What a finished summary looks like

```json
{
  "lines": [
    { "merchant": "CloudVault", "monthly_saving": "29.00", "note": "Price unchanged." },
    { "merchant": "FitZone", "monthly_saving": "249.00", "note": "Price unchanged." },
    { "merchant": "Tunebox", "monthly_saving": "109.00", "note": "Price unchanged." },
    { "merchant": "Viewly", "monthly_saving": "119.00", "note": "Rose by 20.00 during the statement." }
  ],
  "total_monthly_saving": "506.00"
}
```

## How to talk about it afterwards

Report what the statement shows and what cancelling would save. Do not say which subscriptions to keep or cancel:
that is the account holder's decision, and `.github/copilot-instructions.md` asks for the same thing in every session.
