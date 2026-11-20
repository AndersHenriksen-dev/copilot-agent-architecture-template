# AGENTS.md

A template for agentic development with GitHub Copilot. It holds one working example of each of Copilot's building
blocks (instructions, prompt file, skill, custom agent, hooks, MCP), all used by one small idea: finding subscriptions
in a made-up bank statement. Write for a reader who has never seen it.

This file is the repository's own description, in the place every agent tool looks. Copilot reads it alongside
`.github/copilot-instructions.md`, which covers the Copilot-specific half and does not repeat what is here.

## Run things

```bash
uv sync                      # install
uv run pre-commit install    # once: ruff, mypy, line endings and gitleaks on every commit
uv run subfinder demo        # every type end to end with a scripted model: free, what CI runs
uv run subfinder check       # run the checks against the current run and say what they found
uv run subfinder reset       # forget the current run in workspace/
uv run subfinder run         # prints the plan; --yes makes one real GitHub Models call: ask first
uv run subfinder serve-http  # the read tools over HTTP on this machine
uv run ruff check . && uv run ruff format --check . && uv run mypy src && uv run pytest   # what CI checks
```

## Rules

- Synthetic data only. Names, merchants and amounts are made up. Nothing from an employer goes in this repo: no code,
  prompts, documents, internal names or data.
- Never commit tokens or what a run writes: `.env` and `workspace/` are git-ignored. Never read `.env`.
- Tests and the demo never call a model. Run `run --yes` only when asked, and say what it sends first.
- Every write tool has a check in `lib/hooks/checks.py` and a `preToolUse` entry in
  `.github/hooks/subfinder-hooks.json`. The HTTP transport serves read tools only, because no hook of yours sees a
  call that Copilot makes from GitHub's side.
- Money is `Money` from `lib/statement/transactions.py`, never `float`.
- Prompts, tool descriptions, limits and data go in `config/`, not in code. A Python file that needs config has one
  YAML file at the same path under `config/`, read with `config_for(__name__, ...)` and checked by a Pydantic model.
- A statement in `docs/` about how Copilot works must match the current GitHub or VS Code documentation. Check it when
  changing one, rather than relying on memory. Both move quickly, and several of this repo's design choices exist only
  because something is undocumented today.
- When a type's behaviour changes, update the matching file in `docs/learn/`, including any numbers it quotes. Record
  design choices in `docs/decisions.md`.

## Attribution: the agent never credits itself

Anders is the only author of everything here: commits, pull request bodies, comments and docs. No `Co-Authored-By:`
trailer naming a tool, agent or model, no "Generated with" line, and no text that says an AI tool built or helped with
the work. Copilot is what this repo teaches, so naming it as the subject is fine. Never override `user.name`,
`user.email` or `--author`.

## Writing style (everything that is not Python)

- Never use em dashes anywhere: README, docs, comments, commit messages. Use commas, colons, full stops or
  parentheses.
- Plain English, short sentences, numbers instead of adjectives, no hype words. README in first person singular.
- Write about the code and the results as they are now, not about how they got there.
- Commits are `tag(scope): Header` with a body that says why. Branch per change, squash merge.

## Layout

```text
AGENTS.md                      INSTRUCTIONS: this file, read by Copilot and by other agent tools
.github/
|-- copilot-instructions.md    INSTRUCTIONS: repo-wide, Copilot only
|-- instructions/              INSTRUCTIONS: path-specific, each with an applyTo glob
|-- prompts/                   PROMPT FILE: one task, run on demand
|-- skills/                    SKILL: a procedure Copilot loads when it is relevant
|-- agents/                    CUSTOM AGENT: a persona with its own tool allowlist
|-- hooks/                     HOOKS: the only part here that can refuse something
`-- mcp.json                   MCP: for Copilot CLI
.vscode/mcp.json               MCP: the same server for VS Code, with different keys
src/subfinder/
|-- cli.py                the entry point: reads the command line and hands over
|-- lib/
|   |-- statement/        the domain: swap this folder to use the template for something else
|   |   |-- transactions.py   the statement and the Money type
|   |   |-- recurring.py      finding subscriptions: arithmetic, no model
|   |   |-- workbook.py       a run's state, in a file because several processes share it
|   |   `-- tools.py          the tools, as plain functions
|   |-- hooks/
|   |   |-- checks.py     what may be written: pure functions, callable without Copilot
|   |   |-- events.py     what runs on each hook event
|   |   `-- commands.py   the check command
|   |-- mcp_server/
|   |   |-- server.py     every tool over stdio, with read-only annotations
|   |   |-- http.py       the read tools over HTTP, for Copilot running on GitHub's side
|   |   `-- commands.py   the serve-http command
|   |-- api/              one model call with no Copilot at all, and the run around it
|   |-- demo/             the free walkthrough, and reading the Copilot config files
|   `-- shared/           reading config files: imports nothing else here
`-- config/               the same subfolders as lib/: prompts, limits, data
tests/                    the same subfolders again
workspace/                what a run writes: git-ignored
```
