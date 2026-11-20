---
name: review-summary
description: Check one merchant's claimed monthly saving in the saved summary against its charges on the statement.
argument-hint: "[merchant name, such as Viewly]"
agent: agent
tools: ["subfinder/*"]
---

Check one claimed monthly saving against the statement, and report only what the charges support.

Merchant: ${input:merchant:A merchant from the saved summary, such as Viewly}

1. Call `get_summary`. Find the line for this merchant. If there is no saved summary, say so and stop.
2. Call `get_merchant` with the merchant name, and again with any other spelling you see in the results. The bank
   writes one merchant several ways, so one search is rarely enough.
3. Compare the claimed saving with the latest charge, and check the latest charge is in the statement's last month.

Answer in exactly three lines:

- `Claimed: <amount> DKK a month`
- `Latest charge: <amount> on <date>, from <transaction id>`
- `Verdict: supported` or `Verdict: overstated by <amount>` or `Verdict: already ended, so cancelling saves nothing`

Do not tag anything, do not save a summary, and do not say whether the subscription is worth keeping.

---

This file exists to show what a prompt file is: one task, run by hand, with an input variable. Two things about it are
worth knowing before copying the pattern.

The frontmatter fields above (`name`, `description`, `argument-hint`, `agent`, `tools`) and the `${input:...}` syntax
are documented by VS Code. GitHub's own prompt-files page documents no frontmatter at all, so a surface other than
VS Code may ignore some of this.

More importantly, VS Code's documentation says prompt files run only in its Local harness, which is deprecated and
due to be removed in February 2027, and recommends converting prompt files into skills for the Copilot harness. The
same job as a skill is `.github/skills/find-subscriptions/`. So this is the one type in this repo with an end date,
and a new project should think twice before putting anything load-bearing in a prompt file.
