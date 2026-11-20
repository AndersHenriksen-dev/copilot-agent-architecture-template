# 1. The seven types

GitHub's own customization cheat sheet lists seven kinds of building block. This chapter is the map. Later chapters
take them one at a time.

| Type | Where it lives | Who decides it runs |
|---|---|---|
| Custom instructions | `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md`, `AGENTS.md` | Copilot loads it; the model chooses whether to follow |
| Prompt file | `.github/prompts/*.prompt.md` | You, by hand |
| Agent skill | `.github/skills/<name>/SKILL.md` | Copilot, from the description |
| Custom agent | `.github/agents/<name>.md` | You pick it, or Copilot may select it |
| Subagent | Nowhere: a runtime behaviour | The main agent |
| Hooks | `.github/hooks/*.json` | Copilot, at a fixed event |
| MCP | A config file per surface, plus a server program | The model picks a tool |

## The one line that matters

Six of these seven are text. Instructions, a prompt file, a skill and a custom agent's prompt are all words the model
reads and may or may not act on. A subagent is a model too. **Only a hook is a program that Copilot runs whether the
model likes it or not.**

So when you find yourself writing "never do X" in an instructions file, the honest question is: what happens if it
does X anyway? If the answer is "something expensive", the sentence belongs in a hook, and the instructions file
should say that the hook exists.

This repository writes the same rule in three places on purpose. "Never overstate a saving" appears in
[the skill](../../.github/skills/find-subscriptions/SKILL.md), in the tool's own description in
[server.yaml](../../src/subfinder/config/mcp_server/server.yaml), and in
[checks.py](../../src/subfinder/lib/hooks/checks.py). Only the last one holds if the model gets it wrong.

## What each one costs you

Context is the budget nobody mentions until it runs out.

- **Instructions** are the expensive ones. Repo-wide instructions go out with every request. Path-specific ones go
  out whenever a matching file is in play. Both are paid for whether today's task needs them or not, which is why
  this repo scopes three of its five instruction files with `applyTo`.
- **A skill** costs its `description` always, and its body only when Copilot decides the task needs it. The bundled
  files cost nothing until then. This is the cheapest way to keep a long procedure.
- **A prompt file** costs nothing until you run it.
- **A custom agent** costs its own prompt, while it is selected.
- **A hook** costs no context at all, unless it chooses to speak. It costs wall-clock time instead, inside the
  model's turn.
- **MCP** costs the tool list: every tool's name, description and schema, for every connected server.

## The second axis: where it runs

In most tools, a config file either works or does not. In Copilot there is a second question, and it is the one that
catches people: **which surface are you on?** The same repository is read by the VS Code extension, Copilot CLI, the
cloud agent that opens pull requests, and Copilot code review, and they do not support the same types.

Two of the seven are missing somewhere that matters. Prompt files do not work on github.com or in the CLI. Hooks are
in public preview in VS Code and absent from every other IDE.

[Chapter 7](07-where-copilot-runs.md) is about nothing else, and [docs/surfaces.md](../surfaces.md) has the tables.
Keep the question in mind until then: it changes the answer to almost everything.

## Choosing, in order

1. Must this happen every time, whatever the model decides? **Hook.**
2. Is it a fact or a standard to keep in mind while working? **Instructions.**
3. Is it a procedure with steps, for one kind of task? **Skill.**
4. Should a whole session be unable to do something? **Custom agent.**
5. Does Copilot need to reach real data or actions? **MCP.**
6. Do you want one task you can start by hand with an argument? **Prompt file**, after reading its end date.
7. Is there no Copilot anywhere? **Call a model yourself**, and call your own checks too.

## In the code

- [docs/types.md](../types.md) is the reference version of this chapter.
- [walkthrough.py](../../src/subfinder/lib/demo/walkthrough.py) prints one section per type, in the order a run uses
  them.
- [test_project_files.py](../../tests/demo/test_project_files.py) is where the claims about each file are checked
  against the file on disk.
