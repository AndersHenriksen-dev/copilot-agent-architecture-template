# 5. Hooks

## What a hook is

A hook is a command Copilot runs at a fixed point in its loop. The model does not choose it, does not see it unless
it speaks, and cannot talk it out of anything. That is the whole reason to use one.

It is also the only type in [chapter 1](01-the-seven-types.md)'s list that can refuse something.

## The events

Copilot has more than a dozen. These four do most of the useful work, and are the four this repo wires:

| Event | When | What it can do |
|---|---|---|
| `sessionStart` | A session begins or resumes | Add context |
| `preToolUse` | Before a tool runs | Allow, deny, ask, or change the arguments |
| `postToolUse` | After a tool succeeded | Log, or add context. It cannot undo the call |
| `agentStop` | The model wants to finish a turn | Send it back to work |

Others you will meet: `userPromptSubmitted`, `userPromptTransformed`, `postToolUseFailure`, `subagentStart`,
`subagentStop`, `sessionEnd`, `preCompact`, `errorOccurred`, and two that are Copilot CLI only,
`permissionRequest` and `notification`.

## camelCase or PascalCase, and why it is not cosmetic

Every event name has two spellings, and they change the payload:

- `preToolUse` delivers **camelCase** fields: `toolName`, `toolArgs`, `sessionId`, `cwd`.
- `PreToolUse` delivers **snake_case** fields, to match the VS Code extension's older format, and reports
  Claude-style tool names such as `Read`, `Write` and `Edit`.

So the two cannot be mixed in one config, and a handler written for one will quietly read `None` from the other. This
repo uses camelCase throughout and says so in
[hooks.instructions.md](../../.github/instructions/hooks.instructions.md).

## The config

A JSON file in `.github/hooks/`:

```json
{
  "version": 1,
  "hooks": {
    "preToolUse": [
      {
        "matcher": ".*(?:tag_subscription|save_summary)",
        "command": "uv run --quiet --project . python -m subfinder.lib.hooks preToolUse",
        "cwd": ".",
        "timeoutSec": 30
      }
    ]
  }
}
```

`version` must be 1. Each entry needs one of `bash`, `powershell`, `command` (the cross-platform fallback, copied to
both) or `exec` with `args`. `cwd` is relative to the repository root. `timeoutSec` defaults to 30.

Hooks also load from `~/.copilot/hooks/`, from an inline `hooks` block in `.github/copilot/settings.json`, from
`.claude/settings.json`, and from admin policy files. They all run: a repository hook does not replace a user hook on
the same event.

## In and out

A hook process gets the event as JSON and answers with **one JSON object** on stdout. An empty object means no
decision, which leaves Copilot's own permission rules in charge. Diagnostics go to stderr.

| Event | Keys it can answer with |
|---|---|
| `preToolUse` | `permissionDecision` (`allow`, `deny`, `ask`), `permissionDecisionReason`, `modifiedArgs` |
| `postToolUse` | `additionalContext`, `modifiedResult` |
| `agentStop` | `decision` (`block`, `allow`), `reason` |
| `sessionStart` | `additionalContext` |

`permissionDecisionReason` is required with a deny, and it is what the model reads, so it should say what to do
differently. The one here names the number and the charge behind it:

```text
CloudVault: a saving of 529.00 is more than its latest charge of 29.00.
```

`ask` is treated as a deny on the cloud agent, so do not rely on it there.

## Failing closed, and the hole

A `preToolUse` command that **exits non-zero** denies the call. That is Copilot's own behaviour, and this repo's
handler adds to it: an event it cannot parse is answered with an explicit deny.

A `preToolUse` command that **times out** does not deny. It falls through to the normal permission rules, on every
event. So a hook that is broken is safe and a hook that is slow is an open door, which is the opposite of the
intuition. The only defence is to keep the hook fast: the one here does a file read and some arithmetic, and nothing
else.

`postToolUse` does not fail closed either, and should not: the tool has already run, so blocking the model would
protect nothing.

## `agentStop` and the loop you must not write

```python
if _StopEvent.model_validate_json(raw).stop_hook_active:
    return _nothing_to_say()
```

`stop_hook_active` is true when a stop hook already sent the model back once. Without that check, a condition the
model cannot satisfy would block forever. Copilot ends the turn after eight consecutive blocks, which is a backstop
and not a design.

The hook here also does nothing when the workbook has no tags, because it fires at the end of every turn in this
repository, including ordinary coding. Only a half-done run should be held up.

## The matcher problem

A `matcher` is compiled as `^(?:PATTERN)$` and tested against `toolName`. GitHub documents the names of the built-in
tools (`bash`, `powershell`, `view`, `create`, `edit`, `grep`, `glob`, `web_fetch`, `ask_user`, `task`) and says a
tool with no Claude equivalent keeps its runtime name.

It does not say, anywhere, **how an MCP server's tools are spelled in that field.** Claude Code's `mcp__server__tool`
and the `server/tool` form that custom agent allowlists use are both plausible. Neither is documented for this.

A wrong guess is the worst kind of wrong, because it fails silently: the matcher never fires, no hook runs, and the
write goes through unchecked. There is no error to notice.

So this repo does two things:

```json
"matcher": ".*(?:tag_subscription|save_summary)"
```

Any prefix matches. And the handler works out the tool name itself:

```python
def bare_tool_name(name: str) -> str:
    return re.split(r"/|__", name)[-1]
```

`save_summary`, `subfinder/save_summary` and `mcp__subfinder__save_summary` all give `save_summary`, and a tool the
handler does not recognise is allowed. Running the hook slightly too often costs milliseconds. Running it too rarely
costs the whole guarantee.

GitHub's own suggestion, when the name is unknown, is to use no matcher and check in the script. That would run a
subprocess on every file read and shell command, which is too slow for something inside the model's turn, so the
matcher narrows it and the script confirms it.

## The check and the hook are two things

- **The check** decides. [checks.py](../../src/subfinder/lib/hooks/checks.py) holds pure functions that know nothing
  about Copilot.
- **The hook** decides when. [events.py](../../src/subfinder/lib/hooks/events.py) reads the JSON and calls a check.

That split earns its keep twice: [the model path](08-the-model-on-its-own.md) has no hooks and calls the same
functions directly, and `uv run subfinder check` runs them by hand.

## Where hooks actually work

In Copilot CLI, fully. On GitHub's side, most events, Linux only. In VS Code, **public preview**. In every other IDE,
not at all.

That is worth sitting with. The type that enforces your rules is in preview in the place most people work, which is
why the same checks here also run in the code and in CI. [Chapter 7](07-where-copilot-runs.md) is about this.

## In the code

- [.github/hooks/subfinder-hooks.json](../../.github/hooks/subfinder-hooks.json): the wiring
- [events.py](../../src/subfinder/lib/hooks/events.py): one function per event
- [__main__.py](../../src/subfinder/lib/hooks/__main__.py): what Copilot actually launches
- [checks.py](../../src/subfinder/lib/hooks/checks.py): the decisions, as pure functions
- [test_events.py](../../tests/hooks/test_events.py): every spelling of a tool name, an unreadable event, the
  `stop_hook_active` loop, and each event run as its own subprocess
