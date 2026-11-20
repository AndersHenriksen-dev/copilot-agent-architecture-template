# 2. Instructions

## The three kinds in a repository

| File | Applies to | In git? |
|---|---|---|
| `.github/copilot-instructions.md` | Everything | Yes |
| `.github/instructions/**/*.instructions.md` | The files matched by its `applyTo` globs | Yes |
| `AGENTS.md` | Everything, and read by other agent tools too | Yes |

GitHub also reads `CLAUDE.md` and `GEMINI.md` in the same role as `AGENTS.md` on the cloud agent, code review and the
CLI, and `REVIEW.md` for code review on github.com. There are two more scopes that are not files in your repository:
**personal** instructions, set in GitHub's settings or under `~/.copilot/`, and **organization** instructions, set on
the website.

## Scoping with `applyTo`

A path-specific file carries one frontmatter field:

```markdown
---
applyTo: "src/subfinder/lib/statement/**,src/subfinder/config/statement/**,tests/statement/**"
---
```

Globs, comma-separated. The file is loaded only when a matching file is in play, so it costs nothing the rest of the
time. That is the entire reason to use one instead of another paragraph in the repo-wide file.

This repo has three, and they show the two ways to scope:

- [money.instructions.md](../../.github/instructions/money.instructions.md) and
  [hooks.instructions.md](../../.github/instructions/hooks.instructions.md) scope **by folder**. The money rule covers
  `lib/`, `config/` and `tests/`, which no single folder could.
- [python.instructions.md](../../.github/instructions/python.instructions.md) scopes **by file type**, with
  `**/*.py`. It therefore covers both of the others, and that is fine: they are about different subjects.

`applyTo` is the only frontmatter field GitHub documents for these files, so it is the only one this repo uses.

## There is no precedence to rely on

This is the part worth getting right, because it is the opposite of what you would guess.

GitHub documents an order for **Copilot Chat on github.com only**: personal instructions, then repository
instructions (path-specific, then repo-wide, then agent files), then organization instructions. For everything else,
the documentation says most surfaces, including Copilot CLI, VS Code and Visual Studio, combine the applicable files
**without defining a general precedence order**.

So you cannot settle a contradiction by putting the winning version in the more specific file. There is no documented
winner. GitHub's own advice is to avoid writing contradictions, and to turn repository instructions off temporarily if
answers get worse.

That is why this repository splits `AGENTS.md` and `.github/copilot-instructions.md` **by subject** and has them
repeat nothing:

- `AGENTS.md` describes the repository: the commands, the hard rules, the layout. It is in the place every agent tool
  looks, so it is the file to write if you want a tool other than Copilot to understand the project.
- `.github/copilot-instructions.md` is about Copilot: where each type lives here, which to reach for, and the two
  things worth remembering while working.

A test asserts that neither has frontmatter, because frontmatter on a file that always loads would only mislead.

## Writing them so they work

GitHub's guidance is that instructions work best as short, self-contained statements, and that they are sent with
every matching request. Three patterns it names as causing problems in large repositories:

- referring to external resources, rather than saying the thing
- instructions about style and tone
- demanding a fixed level of detail in every answer

The first one shaped this repo. [python.instructions.md](../../.github/instructions/python.instructions.md) is eight
lines of rules rather than a link to a longer style guide, and says so at the bottom. The reasoning lives in `docs/`,
which Copilot reads when a task needs it rather than on every request.

There is no documented size limit. There is a documented warning that Copilot "may not always follow your custom
instructions in exactly the same way every time", which is the whole difference between this chapter and
[chapter 5](05-hooks.md).

## What cannot be an instruction

"Give no financial advice" is in [copilot-instructions.md](../../.github/copilot-instructions.md) and will stay
there, because no program can reliably judge whether a sentence is advice. It needs judgement, so it is asked for.

"Never state a saving larger than the latest charge" is in the same file **and** in
[checks.py](../../src/subfinder/lib/hooks/checks.py), because a program can judge it perfectly. The instruction is
there so the model usually gets it right the first time. The check is there so that being wrong costs a turn instead
of a wrong answer.

## One gotcha for pull requests

For code review, Copilot reads repository instructions, agent instructions and skills from the **head** branch of the
pull request, not the base. A change to your instructions takes effect on the pull request that contains it, which is
convenient and occasionally surprising.

## In the code

- [.github/copilot-instructions.md](../../.github/copilot-instructions.md) and [AGENTS.md](../../AGENTS.md)
- [.github/instructions/](../../.github/instructions/): the three scoped files
- [project_files.py](../../src/subfinder/lib/demo/project_files.py): `instruction_applies_to` matches `applyTo` the
  way the demo and the tests need it
- [test_project_files.py](../../tests/demo/test_project_files.py): every `applyTo` glob has to match something that
  exists, so a typo cannot sit there silently never firing
