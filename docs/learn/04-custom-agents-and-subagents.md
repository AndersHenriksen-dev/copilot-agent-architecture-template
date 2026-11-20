# 4. Custom agents and subagents

## What a custom agent is for

A skill guides a model that still has every tool. A custom agent **takes tools away**. That is the one thing it can do
that nothing else in Copilot's list can, and it is the reason to reach for one.

A Markdown file in `.github/agents/`, with frontmatter and a prompt:

```markdown
---
name: statement-auditor
description: Audits a finished subscription run against the statement and reports every claim the charges do not
  support. It cannot tag, save, edit a file or run a command.
tools: ["read", "search", "subfinder/list_transactions", "subfinder/get_merchant", "subfinder/get_summary"]
---
```

`description` is the only required field. The prompt below the frontmatter is capped at 30,000 characters.

## `tools` is an allowlist, and there is no deny syntax

This is the part to understand before you trust a restricted agent.

| `tools` | Effect |
|---|---|
| left out | every tool |
| `["*"]` | every tool |
| `[]` | no tools at all |
| `["read", "search"]` | exactly those |

There is no way to write "everything except X". A restriction is defined entirely by what you leave out, which means
**a typo quietly widens or narrows the list rather than failing**: an unrecognised name is ignored, not reported.

Names come in three forms:

- **Aliases** for groups of built-in tools, case-insensitive: `execute` (shell, bash, powershell), `read`, `edit`,
  `search`, `agent`, `web`, `todo`.
- **MCP tools**, as `server/tool`, or `server/*` for all of one server's. The server name is the key in your MCP
  config, so renaming the server silently changes every agent that referred to it.
- **Built-in servers**: `github` and `playwright`, which the cloud agent configures by default.

The auditor here lists `read`, `search` and the three `subfinder` read tools. `tag_subscription` and `save_summary`
are absent, so they do not exist for that session. Neither does `edit`, so it cannot change a file, and neither does
`execute`, so it cannot run a command to get around either.

Two tests pin that down: one asserts the exact list, and one asserts that no write tool, `edit` or `execute` appears
in it. The second is the one that matters when someone adds a tool later.

## Why auditing is the right job for it

Reading an audit is exactly the task where a tool allowlist earns its keep. A session that can only read **cannot
quietly fix what it was asked to report on**. If the auditor could call `save_summary`, a model that found an
overstated saving might helpfully correct it, and the finding would disappear along with the problem.

The same checks already run in [checks.py](../../src/subfinder/lib/hooks/checks.py), where a hook enforces them during
a run. The agent is the other half: a session that can look at a finished run, and at the code around it, and reach a
judgement in words.

## The cloud-only fields

Two frontmatter fields are not used by IDE custom agents:

- `mcp-servers`, which lets one agent bring its own MCP servers. For the cloud agent, these are merged after the
  built-in servers and before the repository's own settings.
- `metadata`, name and value pairs.

Others worth knowing: `target` limits an agent to `vscode` or `github-copilot` and defaults to both;
`disable-model-invocation: true` stops Copilot selecting the agent by itself; `user-invocable: false` hides it from
the picker so it can only be reached programmatically. `infer` is retired, replaced by those two.

Levels deduplicate by file name, and the lowest level wins: a repository agent overrides an organization one, which
overrides an enterprise one.

## Subagents

A subagent is the main agent spawning a helper with its own context, doing a piece of work, and handing back the
result. **There is nothing to put in the repository.** It is a runtime behaviour, not a file, which is why this
chapter covers it in a paragraph and the repo has no example.

Use one when a subtask would flood the main context: searching a large codebase, running a test suite and reading the
output. You ask for it in a prompt rather than configuring it. A custom agent can be what a subagent runs, which is
where the two meet.

Supported in VS Code and Copilot CLI, not on github.com, not in Visual Studio.

It is in GitHub's list of seven, so leaving it out of this guide would hide the fact that one of the seven is not
something you write.

## In the code

- [.github/agents/statement-auditor.md](../../.github/agents/statement-auditor.md)
- [config/mcp_server/server.yaml](../../src/subfinder/config/mcp_server/server.yaml): the server's `name`, which is
  the prefix the allowlist uses
- [test_project_files.py](../../tests/demo/test_project_files.py):
  `test_the_custom_agents_allowlist_has_no_way_to_write`
