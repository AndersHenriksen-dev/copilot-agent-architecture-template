# Learning guide

A study guide to GitHub Copilot's building blocks, and to what the code here actually does. Read the files in order
once; afterwards each one works as a reference. Every file ends with where to find its ideas in the code.

| # | File | What it covers |
|---|---|---|
| 1 | [The seven types](01-the-seven-types.md) | The map: who decides what runs, what enforces and what only asks, and what each type costs in context |
| 2 | [Instructions](02-instructions.md) | Every place instructions can live, `applyTo` scoping, `AGENTS.md`, and why there is no precedence to rely on |
| 3 | [Prompt files and skills](03-prompt-files-and-skills.md) | Two ways to keep a procedure, how Copilot decides to load a skill, bundled files, and the one type with an end date |
| 4 | [Custom agents and subagents](04-custom-agents-and-subagents.md) | Taking tools away, an allowlist with no deny syntax, and what a subagent is |
| 5 | [Hooks](05-hooks.md) | Events, the JSON in and out, the four hooks here, failing closed, and the matcher problem |
| 6 | [MCP](06-mcp.md) | What the protocol does, two transports, a different config file per surface, and the annotation that decides whether a tool exists |
| 7 | [Where Copilot runs](07-where-copilot-runs.md) | The surface matrix, why it is the hardest part of Copilot, and what to do about it |
| 8 | [The model on its own](08-the-model-on-its-own.md) | One call instead of an agent, a schema the API enforces, and what is missing when no Copilot is there |
| 9 | [One run, traced](09-one-run.md) | The whole example, step by step, in VS Code and with no Copilot |
| 10 | [Questions to test yourself](10-questions.md) | Short questions with answers, and exercises that change the code |
| 11 | [Further reading](11-further-reading.md) | The docs behind each idea |

Two ideas to take away.

**An instruction can be ignored, and a hook cannot.** So decide first what must always hold, and put that in code.
Then ask of every path to your tools what is still checking it.

**Nothing in Copilot is supported everywhere.** The surface decides. Before you rely on a file, find out whether the
place your team works actually reads it, because two of the seven types are missing on some surfaces and the one that
enforces things is in preview in the IDE.

To see all of it working, run this. It needs no token and sends nothing anywhere.

```bash
uv run subfinder demo
```
