# Copilot instructions

Repo-wide instructions for Copilot, loaded in every session. [AGENTS.md](../AGENTS.md) holds the repository's
commands, rules and layout, and this file does not repeat them: it covers the part that is about Copilot itself.

The repository is a template, so the thing it teaches and the thing it is made of are the same. Every file below is
both a working part of the example and the documentation for its type.

## Where each type lives here

| Type | In this repo | Reach for it when |
|---|---|---|
| Instructions, repo-wide | this file, and `AGENTS.md` | Something is true in every session |
| Instructions, path-specific | `.github/instructions/*.instructions.md` | Something is true only for certain files |
| Prompt file | `.github/prompts/review-summary.prompt.md` | A one-off task worth keeping, run by hand |
| Skill | `.github/skills/find-subscriptions/SKILL.md` | A procedure with steps, loaded only when relevant |
| Custom agent | `.github/agents/statement-auditor.md` | A session that must not be able to write |
| Hooks | `.github/hooks/subfinder-hooks.json` | It has to happen whatever the model decides |
| MCP | `.vscode/mcp.json` and `.github/mcp.json` | Real data or real actions, reached as tools |

## What to do with a request about the statement

- Finding the subscriptions is the skill. Follow `.github/skills/find-subscriptions/SKILL.md` rather than working it
  out again, and use the five `subfinder` MCP tools instead of reading the YAML by hand.
- Checking a finished run is `uv run subfinder check`. It runs the same functions the `preToolUse` hook runs.
- Never state a monthly saving larger than that merchant's latest charge on the statement, and never claim a saving
  for a subscription that has already ended. The hook refuses both, so getting it wrong only costs a turn.

## No financial advice

Say what the statement shows and what a change would save. The choice to keep or cancel something belongs to the
account holder, so do not recommend either, and do not suggest any investment. No code can judge whether a sentence
gives financial advice, which is why this stays an instruction and is not a hook.

## Two things about Copilot worth remembering while working here

- **The surface decides what loads.** These files do not all apply everywhere. Path-specific instructions do not reach
  Copilot Chat on github.com, prompt files do not run on github.com at all, and hooks are in preview in VS Code. If
  you are about to say "Copilot supports this", name the surface. `docs/surfaces.md` has the table.
- **Only the hooks can refuse anything.** Everything else in the list above asks. When a rule here matters, check
  whether it also exists in `lib/hooks/checks.py`, and say so if it does not.
