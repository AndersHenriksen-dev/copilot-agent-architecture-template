# 3. Prompt files and skills

Both keep a procedure out of your instructions file. They differ in who starts them, and in whether they have a
future.

## Prompt files

A `.prompt.md` file in `.github/prompts/`, run by hand. It can take an argument.

```markdown
---
name: review-summary
description: Check one merchant's claimed monthly saving against its charges on the statement.
argument-hint: "[merchant name, such as Viewly]"
agent: agent
tools: ["subfinder/*"]
---

Merchant: ${input:merchant:A merchant from the saved summary, such as Viewly}
```

In VS Code you run it by typing `/review-summary` in chat, through **Chat: Run Prompt**, or with the play button in
the editor. `${input:name}` and `${input:name:placeholder}` are how it asks for an argument.

**Read this before you build on one.** Two things limit prompt files:

1. GitHub's cheat sheet marks them unsupported on github.com and in Copilot CLI. They are an IDE feature.
2. VS Code's documentation says they run only in its **Local harness**, which is deprecated and due to be removed in
   February 2027, and recommends converting prompt files into skills for the Copilot harness.

So this is the one type in this repository with an end date, and
[review-summary.prompt.md](../../.github/prompts/review-summary.prompt.md) says so in its own body. A test asserts
that the warning is still there, which is an odd thing to test until you consider how easy it would be to tidy away.

The frontmatter is also the least settled part of Copilot's customization. VS Code documents `name`, `description`,
`argument-hint`, `agent`, `model` and `tools`. GitHub's own prompt-files page documents no frontmatter at all. So the
fields above are a VS Code contract, not a Copilot one.

## Skills

A folder with a `SKILL.md`. Copilot reads the `description`, decides whether the task needs it, and injects the file
when it does.

```markdown
---
name: find-subscriptions
description: Find the recurring subscriptions on the made-up bank statement in this repository, tag them and save
  one summary of what cancelling them would save. Use this whenever someone asks about subscriptions, recurring
  charges or what the statement costs each month.
---
```

Required: `name` (lowercase with hyphens, normally matching the folder) and `description`. Optional: `license`, and
`allowed-tools`.

**The description is the whole trigger.** It is what is always in context, and it is what Copilot decides from, so it
has to say both what the skill does and when to use it. The one here names the words a person would actually use:
subscriptions, recurring charges, what the statement costs. A description that only said "finds subscriptions" would
load less often than it should.

A test asserts the description is shorter than the body, which is the cheap way to check the expensive part stayed
small.

### Bundled files

Every file in the skill's folder becomes available when the skill is used, and costs nothing before. There is no
include syntax: you refer to them in prose, and Copilot can read or run them.

[find-subscriptions](../../.github/skills/find-subscriptions/) bundles two:

- [summary-format.md](../../.github/skills/find-subscriptions/summary-format.md), the format of the result
- [summarize-audit.py](../../.github/skills/find-subscriptions/summarize-audit.py), a standalone script that tallies
  the audit log

The script uses the standard library only and finds the repository from its own location, so it runs with plain
`python` from anywhere and needs nothing installed. That is deliberate: a bundled script that needs the project's
virtual environment is a bundled script that fails on someone else's machine.

A test checks that the skill mentions every file in its folder by name, because a bundled file nothing refers to is
a file Copilot will never use.

### `allowed-tools`, and why this repo leaves it out

`allowed-tools` pre-approves tools so Copilot can use them without asking. GitHub warns against listing `shell` or
`bash` there unless you have read the skill and its scripts, because it removes the confirmation step for terminal
commands.

This skill ships a script, so it is exactly the case where the field is tempting. It is left out, and a test asserts
it stays out. Running the script still asks. A template that pre-approved a shell would be teaching the habit that
makes installing someone else's skill dangerous, and skills have a package manager now: `gh skill search`,
`gh skill install`, `gh skill publish`. GitHub does not verify what people publish, and says so.

## Which one to use

| | Prompt file | Skill |
|---|---|---|
| Who starts it | You | Copilot, from the description |
| Takes an argument | Yes, `${input:...}` | No, it reads the conversation |
| Can bundle files | No | Yes |
| Works on github.com | No | Yes |
| Works in Copilot CLI | No | Yes |
| Has a removal date | In VS Code, yes | No |

In this repository the skill holds the real procedure and the prompt file holds a job small enough to lose. If you are
choosing today for a new project, choose the skill.

## In the code

- [.github/skills/find-subscriptions/](../../.github/skills/find-subscriptions/): the skill and its two bundled files
- [.github/prompts/review-summary.prompt.md](../../.github/prompts/review-summary.prompt.md)
- [project_files.py](../../src/subfinder/lib/demo/project_files.py): `skill_files` and `skill_bundled_files`
- [test_project_files.py](../../tests/demo/test_project_files.py): the name matches the folder, the description stays
  smaller than the body, nothing is pre-approved, and every bundled file is mentioned
