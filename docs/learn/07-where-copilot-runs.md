# 7. Where Copilot runs

This is the chapter with no equivalent in a guide to any single-surface tool, and it is the hardest part of building
with Copilot.

## Copilot is four or five products

They read the same repository and do not support the same things.

| Surface | What it is | Where it runs |
|---|---|---|
| IDE extensions | VS Code, Visual Studio, JetBrains, Eclipse, Xcode | Your machine |
| Copilot CLI | The `copilot` command | Your machine |
| Cloud agent | Assign an issue, get a pull request | GitHub's machines |
| Code review | Reviews a pull request | GitHub's machines |

So "does Copilot support hooks" has four answers, and two of them are different again depending on the IDE.

## The table

From GitHub's customization cheat sheet. "Preview" means public preview.

| Type | VS Code | Visual Studio | JetBrains | Eclipse | Xcode | github.com | Copilot CLI |
|---|---|---|---|---|---|---|---|
| Custom instructions | yes | yes | preview | preview | preview | yes | yes |
| Prompt files | yes | yes | preview | **no** | preview | **no** | **no** |
| Custom agents | yes | yes | preview | preview | preview | yes | yes |
| Subagents | yes | **no** | preview | preview | preview | **no** | yes |
| Agent skills | yes | yes | preview | **no** | **no** | yes | yes |
| Hooks | **preview** | **no** | **no** | **no** | **no** | yes | yes |
| MCP servers | yes | yes | yes | yes | yes | yes | yes |

[docs/surfaces.md](../surfaces.md) has the finer version, including which **kinds** of instruction file reach which
surface, which is a second table because github.com Chat, the cloud agent and code review do not agree either.

## The four that caught me

**Prompt files are an IDE feature with an end date.** Not on github.com, not in the CLI, and in VS Code only in the
Local harness, which VS Code says goes in February 2027. A procedure you want to survive belongs in a skill.

**Hooks are weakest where you work.** Full support in the CLI, most events on GitHub's side, public preview in VS
Code, absent from every other IDE. The type that enforces things is the type least available in an editor. So a rule
you need to hold cannot rely on hooks alone: it has to exist in the code and in CI as well, which is why
[checks.py](../../src/subfinder/lib/hooks/checks.py) is callable three ways.

**Path-specific instructions do not reach Chat on github.com**, although they do reach the cloud agent and code
review. So scoping with `applyTo` is a context saving on some surfaces and an invisibility on one.

**MCP is configured per surface.** A different file, a different top-level key, and the CLI refuses VS Code's. See
[chapter 6](06-mcp.md).

## What to do about it

**Name the surface.** In your own documentation, in code review, and in your head. A sentence that starts "Copilot
does X" is incomplete. This repo's
[copilot-instructions.md](../../.github/copilot-instructions.md) asks for that explicitly, because the model will
otherwise cheerfully claim support that does not exist on the surface you are on.

**Put what must hold in more than one place.** Not out of paranoia, but because no single place is read everywhere:

| Where | Covers |
|---|---|
| `preToolUse` hook | Copilot CLI, the cloud agent, VS Code in preview |
| `lib/api/run.py` calling the checks | any path with no Copilot at all |
| `uv run subfinder check` | a person or a script, by hand |
| CI | every pull request, whatever wrote it |

**Write the table down.** Whatever you build, "which surface does this actually work on" will come up, and having the
answer in the repository is most of the work. [docs/surfaces.md](../surfaces.md) is also where this repo records what
it has actually run, which is a short list: the demo and the tests, with VS Code to be confirmed by hand and the CLI,
the cloud agent, code review and the GitHub Models call not run at all.

## One more asymmetry worth knowing

For code review, Copilot reads instructions, agent files and skills from the **head** branch of a pull request, not
the base. So a change to your instructions applies to the pull request that introduces it.

## In the code

- [docs/surfaces.md](../surfaces.md): both tables, and what has been run
- [copilot-instructions.md](../../.github/copilot-instructions.md): the instruction to name the surface
- [checks.py](../../src/subfinder/lib/hooks/checks.py): the functions that are called from three directions, because
  no single direction is always available
