# Copilot agent architecture template

[![CI](https://github.com/AndersHenriksen-dev/copilot-agent-architecture-template/actions/workflows/ci.yml/badge.svg)](https://github.com/AndersHenriksen-dev/copilot-agent-architecture-template/actions/workflows/ci.yml)

GitHub Copilot gives you seven ways to shape what it does: instructions, prompt files, custom agents, subagents,
agent skills, hooks and MCP. The docs explain each one on its own page. I wanted to see them work together, so I built
one small example that uses all of them, and kept it as a template to start new projects from.

The example finds the subscriptions in a made-up bank statement. It is a good fit because the job splits cleanly: the
bank writes one merchant as `TUNEBOX P2F3A1`, `TNBX*PREMIUM` and `TUNEBOX AB STHLM`, which needs a model to read. The
money needs code, because a model should not be trusted to add up or to state a saving nobody checked.

This is the same job as my [Claude agent architecture template](https://github.com/AndersHenriksen-dev/claude-agent-architecture-template),
with the same statement and the same answer. Holding the problem still is what makes the two toolkits comparable.

## The seven types

| Type | What it is | How the example uses it |
|---|---|---|
| **Instructions** | Markdown Copilot loads and asks the model to follow | [Repo-wide](.github/copilot-instructions.md) and [cross-tool](AGENTS.md), plus three scoped by `applyTo`: [money](.github/instructions/money.instructions.md), [hooks](.github/instructions/hooks.instructions.md) and [python](.github/instructions/python.instructions.md) |
| **Prompt file** | One task, run by hand, with an argument | [`/review-summary`](.github/prompts/review-summary.prompt.md): check one merchant's claimed saving |
| **Skill** | A procedure Copilot loads when it looks relevant | [find-subscriptions](.github/skills/find-subscriptions/SKILL.md): the steps, the summary format and a script |
| **Custom agent** | A persona with its own tool allowlist | [statement-auditor](.github/agents/statement-auditor.md): reads a finished run and cannot change it |
| **Subagent** | A helper with its own context, not a file you write | Nothing in the repo. It is in GitHub's list, so [docs/types.md](docs/types.md#subagent) says why there is nothing to put here |
| **Hooks** | Commands Copilot runs at a fixed event, whatever the model wants | [Deny an overstated saving, log every call, refuse to stop with no summary, and tell a new session what the last one left](src/subfinder/lib/hooks/events.py) |
| **MCP** | A standard way to offer tools to any client | [Five tools over stdio](src/subfinder/lib/mcp_server/server.py), and [the three read tools over HTTP](src/subfinder/lib/mcp_server/http.py) for Copilot running on GitHub's side |

[docs/types.md](docs/types.md) says when to pick each one over the others. If you only read one page, read that one.
Then read [docs/surfaces.md](docs/surfaces.md), because in Copilot the answer to "is this supported" depends entirely
on where it is running.

There is also a path with no Copilot in it at all: [one model call](src/subfinder/lib/api/clean_merchants.py) to
GitHub Models, with the arithmetic around it in plain code. Nothing is loaded there, hooks included, so that code
calls the same checks itself.

## What I learned

**In Copilot, "is this supported" is not a question you can answer without naming the surface.** Prompt files do not
run on github.com or in the CLI, and in VS Code they run only in a harness that is deprecated. Hooks are in preview
in VS Code but supported in the CLI and on GitHub's side. Path-specific instructions reach the cloud agent and code
review but not Chat on github.com. MCP needs a different config file per surface, and the CLI refuses to read VS
Code's. One repository, seven types, and no two surfaces that read all of it.

**Copilot has hooks now, so it can enforce and not only ask, but not everywhere you work.** A `preToolUse` hook
denies a call and fails closed when it crashes. It does not fail closed when it times out, on any event, so a slow
hook is an open door. And the surface where hooks are weakest is the IDE, which is where most of the work happens. So
the same check lives in three places here: the hook, the code in the model path, and the tests that CI runs.

**The one thing GitHub does not document turned out to be the thing I needed.** A hook matcher is tested against
`toolName`, and the docs name every built-in tool but never say how an MCP server's tools are spelled. A confident
guess would have failed silently, with no hook running and the write going through. So the matcher allows any prefix
and the hook works out the tool name itself. Designing around a documentation gap was the most instructive hour of
this.

**Restricting a tool list is an allowlist with no deny syntax.** A custom agent's `tools` field is the whole
restriction: leave it out and everything is allowed, and an unrecognised name is ignored rather than reported. So a
read-only agent is defined by what is absent from a list, which is worth knowing before you trust one.

**An annotation I would have treated as a hint decides whether a tool exists.** Copilot code review drops any MCP
tool that does not set `annotations.readOnlyHint: true`. That is the platform enforcing read-only on its own side,
which is the opposite of the usual arrangement where the server has to defend itself.

**Reaching tools from a vendor's cloud goes around your hooks, whichever vendor it is.** The cloud agent and code
review call an MCP server from GitHub's machines, so nothing of mine is in the path. I reached the same conclusion
about Anthropic's connectors for the same reason, which suggests it is a property of remote tool calling and not of
either product.

## Try it

You need [uv](https://docs.astral.sh/uv/). The tests and the demo need no token, send nothing anywhere and cost
nothing.

```bash
git clone https://github.com/AndersHenriksen-dev/copilot-agent-architecture-template.git
```

```bash
cd copilot-agent-architecture-template
```

```bash
uv sync
```

```bash
uv run pytest
```

```bash
uv run subfinder demo
```

The demo runs every type for real, with only the model scripted: the MCP server as a subprocess, each hook as a
process fed the JSON Copilot sends, and the HTTP transport over real HTTP on your machine. It stops at the first wrong
result, so it is also an end-to-end check, and CI runs it on every pull request. Part of its output:

```text
=== HOOKS: code that runs at fixed points, whatever the model decides
  sessionStart, additionalContext: subfinder run state: CloudVault, FitZone, Tunebox, Viewly tagged, and no summary is saved yet.
  ok: a new session is told what the last one left behind
  agentStop, tags but no summary: block
  ok: a half-done run is sent back to finish
  preToolUse, saving overstated by 500.00: deny
    Reason the model reads: CloudVault: a saving of 529.00 is more than its latest charge of 29.00.
  ok: a saving above the latest charge never reaches the tool
  ok: an honest summary gets no decision, however the tool name is spelled
  postToolUse, audit log: ['denied', 'ran']
  ok: the audit log has the refused call and the one that ran
  ...

=== RESULT
  CloudVault      29.00 a month
  FitZone        249.00 a month
  Tunebox        109.00 a month
  Viewly         119.00 a month
  Total          506.00 DKK a month if all were cancelled
```

Several of its checks are about the Copilot files rather than the statement: that both MCP configs launch the same
server, that the custom agent has no write tool, that every configured hook event has a handler, and that the
path-specific instruction files do not overlap.

## Use it with Copilot

### In VS Code

Open the folder in VS Code, let it start the `subfinder` MCP server from [.vscode/mcp.json](.vscode/mcp.json), and
ask Copilot about the subscriptions on the statement. The instructions, the skill and the custom agent all load from
the repository. To pick the read-only agent, choose `statement-auditor` in the agent picker. To start again:

```bash
uv run subfinder reset
```

Hooks are in public preview in VS Code. If they do not fire for you, the demo still proves they work, because it runs
each one as a real process with the real payload.

### In Copilot CLI

The CLI reads [.github/mcp.json](.github/mcp.json) rather than VS Code's file, and has the fullest hook support of
any surface. I have not run it.

### On GitHub

Assigning an issue to Copilot uses the cloud agent, which reads the instructions, the skill and the hooks from the
repository, and reaches an MCP server from GitHub's side rather than yours. That needs a public URL and a token.
[docs/surfaces.md](docs/surfaces.md#setting-up-the-repository-mcp-server-on-github) has the JSON and the steps. I have
not run them, so treat them as a starting point.

## Without Copilot

```bash
uv run subfinder run
```

That prints its plan and stops. With `--yes` it makes one chat-completions call to GitHub Models, which is free
within your account's rate limits and needs a fine-grained token with the `models:read` permission in `.env`. The
token `gh auth login` stores does not carry that permission.

**I have not run this.** `models.github.ai` is unreachable from the machine I built this on: every path returns a bare
`OK`. So the endpoint, the model id and the request shape come from the documentation, and the tests check the code
against a stand-in rather than the live API. The model id is in config and overridable with `SUBFINDER_MODEL`, since
catalogs change. Check it against `gh models list` before you spend a request on it.

## Start your own project from it

Click **Use this template**, then follow [docs/adapt.md](docs/adapt.md). Most of the change is in one folder. The
tests check that the wiring still lines up, so they tell you what you missed.

## Learn more

- [docs/types.md](docs/types.md): what each type is and when to use it.
- [docs/surfaces.md](docs/surfaces.md): which surface supports what, and what I have actually run.
- [docs/learn/](docs/learn/README.md): a study guide with one chapter per type, one run traced from start to finish,
  self-test questions and exercises.
- [docs/decisions.md](docs/decisions.md): why it is built this way.

## Layout

```text
AGENTS.md                      INSTRUCTIONS: the cross-tool file, read by Copilot and others
.github/
|-- copilot-instructions.md    INSTRUCTIONS: repo-wide, Copilot only
|-- instructions/              INSTRUCTIONS: three files, each scoped by an applyTo glob
|-- prompts/                   PROMPT FILE
|-- skills/find-subscriptions/ SKILL: SKILL.md, the summary format and a script
|-- agents/                    CUSTOM AGENT
|-- hooks/                     HOOKS: the only part here that can refuse anything
`-- mcp.json                   MCP: for Copilot CLI, key "mcpServers"
.vscode/mcp.json               MCP: the same server for VS Code, key "servers"
src/subfinder/
|-- cli.py                     the entry point
|-- lib/
|   |-- statement/             the made-up data, tools and arithmetic (swap this)
|   |-- hooks/                 checks.py decides, events.py runs them, commands.py is `check`
|   |-- mcp_server/            the server over stdio, and the read tools over HTTP
|   |-- api/                   one GitHub Models call, and the run with no Copilot
|   |-- demo/                  the free walkthrough, and reading the Copilot config files
|   `-- shared/                reading config files
`-- config/                    the same folders as lib/: prompts, limits, data
tests/                         the same folders again
docs/                          types.md, surfaces.md, decisions.md, adapt.md, learn/
```

All data is made up: the person, the merchants and the amounts. MIT licence.
