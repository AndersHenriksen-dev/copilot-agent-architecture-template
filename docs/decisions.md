# Decisions

Why things are built the way they are.

## One idea that uses every type

Seven small examples would show the syntax of each type and nothing about how they work together. One idea forces
real questions, such as what a hook can do that a skill cannot, and what happens to your checks when Copilot runs on
GitHub's machines instead of yours. Finding subscriptions fits because each type has a job the others cannot do:
messy text needs a model, money needs code, and the result is easy to judge. The data is made up.

## The same example as the Claude template

This repository solves the job that [claude-agent-architecture-template](https://github.com/AndersHenriksen-dev/claude-agent-architecture-template)
solves, with the same made-up statement, the same four subscriptions and the same 506.00 total. Holding the problem
still is what makes the two toolkits comparable. The domain code, the checks and the statement are shared on purpose;
everything about Copilot is written from scratch.

## GitHub's seven types, not a list of my own

The types here are the ones GitHub's own customization cheat sheet lists: instructions, prompt files, custom agents,
subagents, agent skills, hooks and MCP. Inventing a tidier taxonomy would read better and would stop matching the
documentation within a release. Subagents get a section with nothing in the repository, because they are a runtime
behaviour and not a file, and leaving the row out would hide that.

## The surface matrix is a page, not a footnote

In Claude Code, roughly one set of files does one thing. In Copilot, the same file does different things in VS Code,
in the CLI, in the cloud agent and in code review, and two of the seven types are missing on some of them. A note at
the bottom of the README would have been the wrong size for that, so [surfaces.md](surfaces.md) is its own page and
the README points at it twice.

## The `preToolUse` matcher allows any prefix

A matcher is compiled as `^(?:PATTERN)$` and tested against `toolName`. GitHub documents the names of Copilot's
built-in tools, and says a tool with no Claude equivalent keeps its runtime name, but it does not say anywhere how an
MCP server's tools are spelled in that field. Claude Code's `mcp__server__tool` and the `server/tool` form used in
custom agent allowlists are both plausible, and neither is documented for this.

A wrong guess here is the worst kind of wrong: the matcher silently never fires, no hook runs, and the write goes
through unchecked. So the matcher is `.*(?:tag_subscription|save_summary)`, which matches any prefix, and
`events.py` works out the real tool name itself and allows anything it does not recognise. Running the hook slightly
too often costs milliseconds. Running it too rarely costs the whole guarantee.

The alternative was no matcher at all, which GitHub's own documentation suggests when the name is unknown. That would
run a subprocess on every file read and every shell command, which is too slow for something inside the model's turn.

## camelCase event names, not the PascalCase aliases

Copilot accepts both `preToolUse` and `PreToolUse`, and they are not the same thing: the camelCase names deliver
camelCase payload fields (`toolName`, `toolArgs`), and the PascalCase ones deliver snake_case fields and Claude-style
tool names. Picking one and saying so in [hooks.instructions.md](../.github/instructions/hooks.instructions.md) is
cheaper than handling both. camelCase is the native form, so that is the one.

## `preToolUse` fails closed, and a timeout does not

An unreadable event is denied, and Copilot denies the call by itself when the command exits non-zero. But a hook that
times out falls through to the normal permission rules, on every event. That is a real hole, and the only defence is
to keep the hook fast, which is why it does one file read and some arithmetic and nothing else.

## `agentStop` ignores a session with no tags

The hook runs at the end of every turn in this repository, including ordinary coding. It only acts on a half-done
run, so nobody working on the code is sent back to save a summary. It also honours `stop_hook_active`, because a
hook that always blocked would make a session impossible to end.

## The skill pre-approves nothing

`allowed-tools` lets a skill use listed tools without asking, and GitHub warns against putting `shell` or `bash`
there unless you have read the skill and its scripts. This skill ships a script, so it is exactly the case where the
field is tempting. Leaving it out means running the script still asks. A template that pre-approved a shell would be
teaching a habit that is wrong as soon as someone installs a skill they have not read.

## `AGENTS.md` and `copilot-instructions.md` are split by subject

Both load in every Copilot session, so anything written twice is paid for twice and can contradict itself. GitHub
documents no precedence between them outside github.com, so a contradiction would have no defined winner. They are
split instead: `AGENTS.md` describes the repository, in the place other agent tools look, and
`copilot-instructions.md` covers Copilot itself. Neither repeats the other.

## Instructions are self-contained, not links to a longer guide

GitHub's own guidance lists referring to external resources as a pattern that causes problems in large repositories.
So [python.instructions.md](../.github/instructions/python.instructions.md) is eight lines of rules rather than a
pointer to a style guide. The longer reasoning lives in `docs/`, which Copilot reads when a task needs it rather than
on every request.

## The prompt file is the small one

A prompt file and a skill could both hold the procedure. The skill holds it, because VS Code says prompt files run
only in its Local harness, which is deprecated and due to go in February 2027, and recommends converting them to
skills. The prompt file keeps a job small enough to lose: checking one merchant. The type is in the repository
because GitHub lists it, and the file says plainly that it has an end date.

## The custom agent is read-only

`tools` is an allowlist with no deny syntax, so a restricted agent is defined by what you leave out. The auditor's
job, reading a finished run and reporting on it, is the clearest case for that: a session that can only read cannot
quietly fix what it was asked to report on. It also means the repository shows the one thing a custom agent can do
that a skill cannot, which is take a tool away.

## Two MCP config files, kept in step by a test

VS Code reads `.vscode/mcp.json` with the key `servers`. Copilot CLI reads `.github/mcp.json` with the key
`mcpServers`, and does not accept VS Code's file. There is no single file that works for both, so the repository has
both, `.gitignore` makes an exception to commit the one inside `.vscode/`, and a test asserts they launch the same
server with the same arguments. Two files that disagree would be worse than one file that is missing.

## The read tools declare `readOnlyHint`

Copilot code review drops any MCP tool whose `tools/list` entry does not set `annotations.readOnlyHint: true`. That
turns an annotation most servers treat as a hint into the thing that decides whether a tool exists for a review at
all, so the server sets it deliberately and a test checks it.

## Nothing that writes is served over HTTP

The cloud agent and code review call an MCP server from GitHub's infrastructure. Nothing on your machine is in that
path, so none of your hooks see those calls. Putting the checks inside the server would work, and a real system that
must write that way would do it. Here nothing needs to, so the write tools are simply not served, and the
repository-settings JSON in [surfaces.md](surfaces.md) also lists the read tools by name. Either alone would be
enough, and having both means one mistake does not expose a write.

This is the same conclusion the Claude template reached about connectors, for the same reason, which suggests it is a
property of remote tool calling rather than of either product.

## The HTTP transport asks for a token by default

It has to be public to be useful, so an open default would be a mistake waiting to happen. `--no-auth` exists for a
local demo on made-up data, and `serve-http` refuses to start if neither a token nor `--no-auth` is given.

Unlike a claude.ai custom connector, which takes no authentication or OAuth and nothing in between, GitHub's
repository MCP settings expand a `COPILOT_MCP_` secret inside a header. So a fixed bearer token is a supported option
here rather than a workaround.

## GitHub Models for the model call, and it is marked unverified

The point of that path is that no Copilot is involved, so any provider would do. GitHub Models fits the repository,
speaks the OpenAI chat-completions shape, and costs nothing within its rate limits, so a reader can try it without a
bill.

It has not been run. `models.github.ai` was unreachable from the machine this was built on: every path returned a
bare `OK`. So the model id, the endpoint and the request shape come from the documentation, and the tests check the
code against a stand-in transport rather than against the live API. The model id is in config and overridable with
`SUBFINDER_MODEL`, because catalogs change. The README says all of this rather than implying a tested path.

## No sampling parameters

No `temperature`, `top_p` or `seed` is sent. GitHub Models serves many models from several publishers, and one that
rejects a parameter it does not support would fail the whole call for no gain. A test asserts they stay out, so this
does not quietly come back.

## Model for text, code for money

The model turns `TNBX*PREMIUM` into Tunebox. It never adds up an amount in the model path, and in the Copilot path
every amount it writes is checked against the statement. A model is good at the first job and has no business being
trusted with the second. A wrong answer can put a merchant in the wrong category; it cannot invent a charge.

## The model call is one call, not an agent

Nothing in that job has to decide what to do next, so a loop would add cost and ways to fail with no gain. It shows
the cheapest tier on purpose.

## Money crosses JSON as a string

A JSON number becomes a Python float, and 99.10 as a float is not 99.10. `Money` refuses floats and any string that is
not an amount with two decimals, such as `1e5`, and its schema tells clients to send a string. So a bad value fails at
the boundary instead of somewhere in the arithmetic.

## The workbook is a file

The MCP server and each hook are separate processes, and a hook process lives for milliseconds. A file is the
simplest thing they can all read. A real system would use a database, and only `workbook.py` would change.

## `subfinder check` reports an unfinished run as a failure

A run with tags and no summary breaks none of the checks, but it is not a run anyone should trust, and the
`agentStop` hook would send the model back for exactly that reason. Returning 0 there would let CI or a script treat
a half-done run as a good one.

## `reset` keeps the audit log

`subfinder reset` deletes the workbook and leaves `audit.jsonl`. An audit log is only worth having if the thing it
records cannot wipe it, so it is append-only. Delete the file by hand to start a clean log.

## Hooks do not protect the stdio server from another client

The checks on writes run in Copilot's hooks. Another MCP client on the same machine could call `save_summary` with no
check at all. Here that risks one local file of made-up data, and a server that also checked would hide what a hook
does. A real system that writes something that matters should run the check inside the server too.

## Classes hold data, functions do the work

Pydantic models check what comes in: config, tool arguments, hook payloads and the model's answer. Inside, results
are frozen dataclasses. The cleaners are plain functions with one signature, not classes, because neither keeps state.

## Tests run real processes

The hooks and the MCP server are programs that another program starts, and tests that called their functions directly
would miss how they fail. Each hook event is run as a subprocess under `python -m`, and the MCP server is launched the
way a client launches it. Only the model is replaced, because it costs a rate limit and cannot be asserted on.

## The demo is also a check

`subfinder demo` stops at the first wrong result and CI runs it. So what a stranger sees on a fresh clone is tested
on every pull request, and the checks it makes are about the Copilot files too: that the two MCP configs agree, that
the custom agent has no write tool, that every configured hook event has a handler, and that the path-specific
instruction files do not overlap.
