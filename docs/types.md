# The seven types

GitHub Copilot's own customization cheat sheet lists seven kinds of building block: custom instructions, prompt files,
custom agents, subagents, agent skills, hooks and MCP. They overlap, so the hard part is knowing which one a job
belongs to. This page says what each is, when to pick it over the others, and how this repo's example uses it.

Checked against the GitHub and VS Code documentation on 2026-11-20. Both move quickly, so check before trusting a
detail here.

One thing to get straight before the list. In Copilot, **"does it support X" has no answer until you name the
surface**. The same file behaves differently in VS Code, in Copilot CLI, in the cloud agent and in code review, and
one type here does not work in two of them at all. [surfaces.md](surfaces.md) has the table, and it is the page to
read second.

## Choosing in one minute

Ask these in order. Stop at the first yes.

1. **Must this happen every time, whatever the model decides?** Use a **hook**.
2. **Is it a fact or a standard Copilot should keep in mind while working?** Use **instructions**.
3. **Is it a procedure with steps, needed only for one kind of task?** Use a **skill**.
4. **Should a whole session be restricted, for example to reading only?** Use a **custom agent**.
5. **Does Copilot need to reach data or actions outside itself?** Use **MCP**.
6. **Do you want one task you can run by hand, with an argument?** Use a **prompt file**, and read the warning in
   its section first.
7. **Is there no Copilot anywhere, or does your own program decide what happens next?** Call a model yourself.

| Type | Lives in | Who decides it runs | Can it stop the model? | Context it costs |
|---|---|---|---|---|
| Instructions | `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md`, `AGENTS.md` | Copilot loads it; the model chooses whether to follow it | No | All of it, whenever it applies |
| Prompt file | `.github/prompts/*.prompt.md` | You, by hand | No | Nothing until you run it |
| Skill | `.github/skills/<name>/SKILL.md` | Copilot, when the description looks relevant | No | The description, then the body on use |
| Custom agent | `.github/agents/<name>.md` | You pick it, or Copilot may select it | It limits the tools that exist | Its own prompt, while selected |
| Subagent | Nothing: it is a runtime behaviour | The main agent | No | Its own context, not yours |
| Hooks | `.github/hooks/*.json` | Copilot, at a fixed event | Yes | None, unless it speaks |
| MCP | `.vscode/mcp.json`, `.github/mcp.json`, repository settings | The model picks a tool | The server can refuse | The tool list |

The line that matters most runs between the hooks row and all the others. Instructions, skills, prompt files and
agent prompts are text the model reads. They ask. A hook is a program Copilot runs whether the model likes it or not.
It enforces.

## Instructions

**What it is.** Markdown that Copilot loads into context. Three kinds live in a repository:

- `.github/copilot-instructions.md` applies to everything.
- `.github/instructions/**/*.instructions.md` applies to the files matched by its `applyTo` globs.
- `AGENTS.md` is the cross-tool file, read by Copilot and by other agent tools. GitHub also reads `CLAUDE.md` and
  `GEMINI.md` in the same role, and `REVIEW.md` for code review on github.com.

There are also personal instructions, set in GitHub's settings or in `~/.copilot/`, and organization instructions set
on the website. Neither lives in the repo.

**Pick it over the others when** the content is a fact or a standard to keep in mind while doing something else. Not a
skill, because it has no steps and no moment when it starts. Not a hook, because a wrong outcome is cheap or a program
cannot judge it.

**In the example.** [copilot-instructions.md](../.github/copilot-instructions.md) holds what applies in every session,
including the rule against financial advice, which no code could check.
[AGENTS.md](../AGENTS.md) holds the repository's commands, rules and layout, in the place other tools look.
Three path-specific files scope the rest: [money](../.github/instructions/money.instructions.md) by folder,
[hooks](../.github/instructions/hooks.instructions.md) by folder, and
[python](../.github/instructions/python.instructions.md) by file type.

**Worth knowing.** GitHub documents `applyTo` and nothing else for these files, so this repo uses only that field.
On precedence, GitHub documents an order for Copilot Chat on github.com (personal, then repository, then
organization) and says plainly that most other surfaces combine the files **without defining a general precedence
order**. So you cannot resolve a contradiction by putting it in the more specific file. The documented advice is to
avoid writing contradictions at all, which is why `AGENTS.md` and `copilot-instructions.md` here are split by subject
and repeat nothing.

## Prompt file

**What it is.** A `.prompt.md` file in `.github/prompts/`, run by hand for one task. It can take an argument through
`${input:name}`.

**Pick it over the others when** you want to run the same focused job repeatedly with different inputs, and you want
to start it yourself rather than hope the model notices.

**In the example.** [review-summary.prompt.md](../.github/prompts/review-summary.prompt.md) checks one merchant's
claimed saving against its charges, and nothing else. Its `tools` list is only the `subfinder` server, so it cannot
save anything.

**Worth knowing, and it matters.** GitHub's cheat sheet marks prompt files as unsupported on github.com and in
Copilot CLI. More importantly, VS Code's documentation says prompt files run only in its **Local harness**, which is
deprecated and due to be removed in February 2027, and recommends converting prompt files into skills. This is the
one type in this repo with an end date. Treat a prompt file as a convenience, and put nothing load-bearing in one.

Its frontmatter is also the least settled. VS Code documents `name`, `description`, `argument-hint`, `agent`, `model`
and `tools`. GitHub's own prompt-files page documents no frontmatter at all.

## Skill

**What it is.** A folder with a `SKILL.md`: frontmatter with a `name` and `description`, then instructions. Copilot
decides from the description whether a task needs it, and injects the file when it does. Every other file in the
folder, scripts included, becomes available at the same time.

**Pick it over the others when** you keep explaining the same procedure, or a section of your instructions has turned
into steps. Not instructions, because those are in context whether today's task needs them or not. Not a prompt file,
because a skill loads itself and has no removal date.

**In the example.** [find-subscriptions](../.github/skills/find-subscriptions/SKILL.md) is the whole procedure for one
run: seven steps, the list of what the hooks will refuse, and two bundled files.
[summary-format.md](../.github/skills/find-subscriptions/summary-format.md) is the format of the result, and
[summarize-audit.py](../.github/skills/find-subscriptions/summarize-audit.py) is a standalone script that tallies the
audit log.

**Worth knowing.** `allowed-tools` pre-approves tools so Copilot can use them without asking, and GitHub warns
against listing `shell` or `bash` there unless you have read the skill and its scripts. This repo sets no
`allowed-tools`, so running the bundled script still asks. A template that taught the opposite would be teaching
people to approve scripts they have not read.

Skills are also the one type with a package manager: `gh skill search`, `gh skill install` and `gh skill publish`.
GitHub does not verify published skills, and says so.

## Custom agent

**What it is.** A Markdown file in `.github/agents/` with frontmatter and a prompt. `description` is required. The
useful field is `tools`, which is the list of tools that agent may use.

**Pick it over the others when** a whole session should work differently, and especially when it should not be able
to do something. A skill guides a model that still has every tool. A custom agent takes the tools away.

**In the example.** [statement-auditor](../.github/agents/statement-auditor.md) checks a finished run and reports what
the charges do not support. Its `tools` list holds `read`, `search` and the three `subfinder` read tools, so it cannot
tag, save, edit a file or run a command.

**Worth knowing.** `tools` is an **allowlist with no deny syntax**. Leaving it out allows everything, `["*"]` allows
everything, `[]` allows nothing, and anything else allows exactly what it lists. So what you leave out is what you
forbid, and an unrecognised name is ignored rather than reported. Aliases cover groups of built-in tools (`read`,
`edit`, `search`, `execute`, `web`, `agent`, `todo`), and an MCP tool is written `server/tool` or `server/*`.

Two fields are cloud-only: `mcp-servers` and `metadata` are not used by IDE custom agents. The prompt itself is
capped at 30,000 characters.

## Subagent

**What it is.** Not a file. A subagent is the main agent spawning a helper with its own context for a piece of work,
and handing back the result. You do not configure one in the repository, though a custom agent can be what a subagent
runs.

**Pick it when** a subtask would flood the main context, such as searching a large codebase. You ask for it in a
prompt rather than declaring it.

**In the example.** Nothing. It is in GitHub's list of seven, so it is in this page, but there is nothing to put in
the repo. The `statement-auditor` agent is the closest thing: a separate, restricted session doing one piece of work.

## Hooks

**What it is.** A JSON file in `.github/hooks/` wiring shell commands to events in the agent's lifecycle. A command
gets the event as JSON on stdin and answers with one JSON object on stdout. The model has no say.

**Pick it over the others when** the thing must happen every time. Anything you would be upset to see skipped belongs
here: refusing a write, keeping an audit log, refusing to stop before the work is done.

**In the example.** [subfinder-hooks.json](../.github/hooks/subfinder-hooks.json) wires four events to
[events.py](../src/subfinder/lib/hooks/events.py):

- `preToolUse` runs the [checks](../src/subfinder/lib/hooks/checks.py) and answers `permissionDecision: deny` with a
  reason the model reads. It refuses a charge that is not on the statement, a charge already tagged elsewhere, and a
  saving larger than the merchant's latest charge.
- `postToolUse` writes the audit log.
- `agentStop` answers `decision: block` when a run has tags but no summary, which sends the model back.
- `sessionStart` answers `additionalContext` describing what the last session left behind.

**Worth knowing.** `preToolUse` fails closed: a command that exits non-zero denies the call. A **timeout** does not,
on any event, so a slow hook is an open door rather than a closed one. `agentStop` must honour `stop_hook_active`, or
a session can never end. Event names in camelCase deliver camelCase payload fields (`toolName`, `toolArgs`); the
PascalCase aliases deliver snake_case fields instead, so the two spellings cannot be mixed.

The gap this repo had to design around: GitHub documents the names of built-in tools for matching, and says a tool
with no Claude equivalent keeps its runtime name, but **nowhere says how an MCP server's tools are spelled in
`toolName`**. A matcher is anchored as `^(?:PATTERN)$` against that string, so a confident guess would fail silently
and the write would go through unchecked. The matcher here allows any prefix, and `events.py` checks the tool name
itself.

## MCP

**What it is.** The Model Context Protocol: a standard way to offer tools to any client. A server lists its tools and
runs them. Copilot reads where to find one from a different file per surface:

| Surface | File | Top-level key |
|---|---|---|
| VS Code | `.vscode/mcp.json` | `servers` |
| Copilot CLI, project | `.github/mcp.json` or `.mcp.json` | `mcpServers` |
| Copilot CLI, personal | `~/.copilot/mcp-config.json` | `mcpServers` |
| Cloud agent and code review | Repository settings on github.com | `mcpServers` |

**Pick it over the others when** Copilot needs real data or real actions. Not a skill, because a skill can only say
what to do with tools that already exist.

**In the example.** [server.py](../src/subfinder/lib/mcp_server/server.py) serves five tools: three that read and two
that write. [http.py](../src/subfinder/lib/mcp_server/http.py) serves the three read tools over HTTP for Copilot
running on GitHub's side. The tools themselves are plain functions in
[tools.py](../src/subfinder/lib/statement/tools.py).

**Worth knowing.** Copilot CLI **will not read `.vscode/mcp.json`**, because that file uses the key `servers` and the
CLI does not accept it. One server, two files, and a test in this repo keeps them in step. The CLI and the cloud agent
also require a `tools` allowlist per server, which VS Code does not document.

Two limits shape what a remote server can do. The cloud agent and code review support MCP **tools only**, not
resources or prompts, and repository settings do not support OAuth. Code review goes further: it drops any tool whose
`tools/list` entry does not set `annotations.readOnlyHint: true`. That annotation is therefore not documentation, it
is the thing that decides whether a review can use a tool at all.

## Calling a model yourself

Not one of the seven, because no Copilot is involved. Your program calls a model's API, chooses the prompt and the
output shape, and nothing else is loaded: no instructions, no skill, no custom agent, and above all no hook.

**Pick it when** no person and no Copilot are there, such as a nightly job, or when your code should decide what
happens next. Start with one call. An agent loop is worth it only when the steps cannot be known in advance.

**In the example.** [clean_merchants.py](../src/subfinder/lib/api/clean_merchants.py) makes one GitHub Models call
that turns `TNBX*PREMIUM` into Tunebox, with a JSON schema the API enforces. [run.py](../src/subfinder/lib/api/run.py)
does the rest as arithmetic, and calls the same check functions itself, because no hook is there to.

## Where each thing goes

Two families of file configure Copilot in a repository, and they behave differently.

**Instruction files stack.** Copilot reads all of them, and outside github.com there is no documented order between
them. Remove a contradiction rather than relying on one file winning.

**Everything else is addressed to a surface.** Hooks, MCP and the agent, prompt and skill folders are read by
whichever surfaces support them, and ignored by the rest. There is no single settings file that turns a feature on or
off for every surface at once.

| File | What it holds | Read by |
|---|---|---|
| [AGENTS.md](../AGENTS.md) | Commands, rules, layout | Copilot and other agent tools |
| [.github/copilot-instructions.md](../.github/copilot-instructions.md) | What is true in every Copilot session | Every Copilot surface |
| [.github/instructions/](../.github/instructions/) | What is true for some files | Most surfaces, not github.com Chat |
| [.github/prompts/](../.github/prompts/) | One task, run by hand | IDEs only |
| [.github/skills/](../.github/skills/) | Procedures loaded when relevant | Most surfaces |
| [.github/agents/](../.github/agents/) | Restricted personas | Most surfaces |
| [.github/hooks/](../.github/hooks/) | What runs whatever the model decides | CLI and cloud agent, preview in VS Code |
| [.github/mcp.json](../.github/mcp.json) | The server, for Copilot CLI | Copilot CLI |
| [.vscode/mcp.json](../.vscode/mcp.json) | The same server, for VS Code | VS Code |

## How they fit in one run

```text
          always in context                 loaded when it looks relevant
          -----------------                 -----------------------------
          AGENTS.md, copilot-instructions   SKILL.md and its bundled files
          *.instructions.md (if it matches)
                        \                      /
                         v                    v
                      [ the model, inside the chosen agent ]
                       tools limited by that agent's allowlist
                                   |
                        wants to call a tool
                                   |
                        preToolUse hook -----> deny: the model reads why
                                   | no decision
                                   v
                     MCP server over stdio  <-- all five tools
                                   |
                        postToolUse hook ----> audit log
                                   |
                        wants to finish
                                   |
                        agentStop hook ------> no summary yet: back to work


[ cloud agent, code review ] --- from GitHub --> MCP over HTTP     three read tools,
                                                                   no hook in the path

[ your own program ] --- a model's API ---> [ a model ]   no Copilot, so your code
       |                                                  calls the same checks itself
       `-- the same checks, the same tools
```

## What is not here

- **Copilot connectors.** In public preview: they bring in context from services outside the repository. Not built
  here, because a preview feature in a template would age badly.
- **Copilot code review.** Not a type you configure so much as a surface that reads several of them. It reads
  instructions, `AGENTS.md`, `REVIEW.md` and skills from the **head** branch of a pull request, not the base.
  [surfaces.md](surfaces.md) covers it.
- **Organization and enterprise levels.** Instructions, agents and MCP servers can all be set above the repository.
  Nothing in a template can show that.
- **The GitHub MCP server and Playwright**, which the cloud agent configures by default. This repo adds a server; it
  does not replace those.
