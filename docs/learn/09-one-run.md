# 9. One run, traced

The same job twice: once with Copilot in VS Code, once with no Copilot at all.

## The statement

35 lines, three months, one made-up account in DKK. What is in it on purpose:

- **Four active subscriptions**, each written differently from month to month. Tunebox appears as
  `TUNEBOX P2F3A1`, `TNBX*PREMIUM` and `TUNEBOX AB STHLM`.
- **A price rise.** Viewly goes from 99.00 in August to 119.00 in October.
- **A subscription that ended.** NewsDaily stops after September.
- **Three traps.** Rent and a phone bill recur but are not subscriptions. Groceries repeat at varying amounts. The
  salary is money in.

The right answer is four subscriptions totalling 506.00 a month.

## With Copilot, in VS Code

### 1. Before anything is asked

VS Code starts the `subfinder` MCP server from [.vscode/mcp.json](../../.vscode/mcp.json) and lists its five tools.

In context: [AGENTS.md](../../AGENTS.md) and
[copilot-instructions.md](../../.github/copilot-instructions.md). The three path-specific files are not, yet, because
no matching file is in play. The skill is not, but its `description` is.

The `sessionStart` hook runs and answers `additionalContext`. With an empty workbook it says nothing. After a previous
run it says what was left behind:

```text
subfinder run state: CloudVault, FitZone, Tunebox, Viewly tagged, and no summary is saved yet.
```

### 2. "Which subscriptions are on this statement?"

Copilot reads the skill's description, decides the task matches, and loads
[SKILL.md](../../.github/skills/find-subscriptions/SKILL.md). Its seven steps and its list of what the hooks will
refuse are now in context, as are the two bundled files if it reads them.

### 3. Reading

It calls `list_transactions`, then `get_merchant` several times, once per spelling it notices. Each call fires the
`postToolUse` hook, which appends a line to `workspace/audit.jsonl`. No read is ever blocked.

### 4. Tagging, and a refusal

It calls `tag_subscription` for each merchant. The `preToolUse` hook runs first.

Suppose it offers Tunebox with a charge from the rent line. The hook's matcher allows any prefix, so it fires
whatever Copilot calls the tool. [checks.py](../../src/subfinder/lib/hooks/checks.py) finds that the charge belongs to
another merchant, and the hook answers:

```json
{
  "permissionDecision": "deny",
  "permissionDecisionReason": "T01 is already tagged under another merchant."
}
```

The tool never runs. The model reads the reason, fixes the call, and tries again. The refusal is in the audit log with
outcome `denied`.

### 5. The summary, and the useful refusal

It works out each saving and calls `save_summary`. If it claims 529.00 for CloudVault, whose latest charge is 29.00:

```text
CloudVault: a saving of 529.00 is more than its latest charge of 29.00.
```

Also refused: a total that does not equal the sum of the lines, a merchant listed twice, and any saving above 0.00 for
NewsDaily, which has already ended.

### 6. Trying to stop too early

If it tries to finish with tags and no summary, the `agentStop` hook answers:

```json
{ "decision": "block", "reason": "Subscriptions are tagged but no summary is saved. Call save_summary before finishing." }
```

It goes back and saves one. On the second attempt `stop_hook_active` is true, so the hook stands down rather than
risking a loop.

### 7. Confirming

```bash
uv run subfinder check
```

The same functions the hook runs, by hand. Every merchant, its charge count, and whether the numbers hold. It exits 1
on an unfinished or failing run, so a script can trust it.

### 8. Afterwards

The `statement-auditor` custom agent can be pointed at the finished run. Its `tools` list has the three read tools and
nothing that writes, so it reports on the run and cannot change it. `/review-summary Viewly` checks one merchant, in
VS Code only.

## With no Copilot

```bash
uv run subfinder run --yes
```

1. `reset_workbook()`. A run starts from nothing.
2. The 35 lines give 22 distinct descriptions. One GitHub Models call turns them into a merchant and a category each,
   with a JSON schema the API enforces. See [chapter 8](08-the-model-on-its-own.md).
3. `find_recurring` does the arithmetic. No model. Category keeps rent and the phone bill out, and `min_months: 2`
   keeps one-offs out.
4. For each active subscription, `tag_checked` calls `check_tag` **itself**, because no hook exists here, and only
   then writes.
5. `build_summary` sets each saving to the latest charge, and `save_checked` calls `check_summary` before writing.
6. It prints what it found, and how many of the 22 descriptions agree with the hand-written answer in
   [scripted.yaml](../../src/subfinder/config/api/scripted.yaml).

The shape of the two runs is the same. What differs is who calls the check: a hook in the first, the code itself in
the second.

## The same run, for free

```bash
uv run subfinder demo
```

Every part is real except the model, which is replaced by the hand-written answer. The MCP server is a subprocess, each
hook is a process fed the JSON Copilot sends, and the HTTP transport answers over real HTTP. It stops at the first
wrong result, and CI runs it on every pull request.

Several of its checks are about the Copilot files rather than the statement: both MCP configs launch the same server,
the custom agent has no write tool, every configured hook event has a handler, and the path-specific instruction files
do not overlap.

## What each type contributed

| Type | Its part of this run |
|---|---|
| Instructions | Never overstate a saving. Give no advice. Money is `Decimal` |
| Skill | The seven steps, the summary format, and what the hooks refuse |
| Prompt file | Checking one merchant afterwards, in an IDE |
| Custom agent | A session that can audit the run and not change it |
| Hooks | The refusals, the audit log, and being sent back for the summary |
| MCP | The five tools, and the three served over HTTP |
| The model's API | Turning `TNBX*PREMIUM` into Tunebox, and nothing else |

Each one has a job the others cannot do. That is the point of building the example this way rather than seven ways.

## In the code

- [walkthrough.py](../../src/subfinder/lib/demo/walkthrough.py): this chapter, as a program that checks itself
- [run.py](../../src/subfinder/lib/api/run.py): the version with no Copilot
- [recurring.py](../../src/subfinder/lib/statement/recurring.py): the arithmetic
- [transactions.yaml](../../src/subfinder/config/statement/transactions.yaml): the statement, and a comment saying
  what each trap is for
