# 10. Questions to test yourself

Short answers below each question; the other chapters have the details.

## The types

1. **What is the difference between an instruction and a hook?** An instruction is text the model is asked to follow.
   A hook is a command Copilot runs whatever the model decides. One asks, the other enforces.
2. **Which of GitHub's seven types is not a file you write?** A subagent. It is a runtime behaviour: the main agent
   spawning a helper with its own context.
3. **A section of `copilot-instructions.md` has become ten numbered steps. What should you do?** Move it into a skill,
   so it costs context only when Copilot decides the task needs it.
4. **Why is "give no financial advice" an instruction and not a hook?** No program can reliably judge whether a
   sentence is advice. It needs judgement, so it is asked for.
5. **What does a skill cost in context before it is used?** Its `description`. The body and the bundled files cost
   nothing until it loads.
6. **What can a custom agent do that a skill cannot?** Take tools away. A skill guides a model that still has
   everything.
7. **When would you call a model's API instead of using Copilot?** When no person and no Copilot are there, such as a
   nightly job, or when your own code should decide what happens next.

## Instructions

8. **Which frontmatter field does GitHub document for `*.instructions.md`?** `applyTo`, and only that.
9. **`applyTo` has three globs separated by commas. When does the file load?** When a file matching any one of them is
   in play.
10. **Two instruction files contradict each other in VS Code. Which wins?** Undefined. GitHub documents a precedence
    order for Copilot Chat on github.com only, and says most other surfaces combine the files without one. Remove the
    contradiction.
11. **What is `AGENTS.md` for, when `copilot-instructions.md` already exists?** It is the cross-tool file, read by
    Copilot and by other agent tools. In this repo the two are split by subject so neither repeats the other.
12. **Why is `python.instructions.md` eight lines rather than a link to a style guide?** GitHub lists referring to
    external resources as a pattern that causes problems. Instructions go out with every matching request, so they
    should say the thing.
13. **For a pull request review, which branch do instructions come from?** The head branch, not the base.

## Prompt files and skills

14. **Where do prompt files not work?** On github.com and in Copilot CLI. In VS Code they run only in the Local
    harness, which is deprecated and due to be removed in February 2027.
15. **So what should hold a procedure you want to keep?** A skill. VS Code's own documentation recommends converting
    prompt files into skills.
16. **How does Copilot decide to load a skill?** From the `description`, which is why it has to say when to use the
    skill and not only what it does.
17. **How does a skill refer to a script in its own folder?** In prose. Every file in the folder becomes available
    when the skill loads; there is no include syntax.
18. **What does `allowed-tools: shell` do, and why does this repo not use it?** It lets Copilot run terminal commands
    without asking. GitHub warns against it unless you have read the skill and its scripts, and a template that
    pre-approved a shell would teach the wrong habit.

## Custom agents

19. **How do you write "every tool except `save_summary`" in a `tools` list?** You cannot. It is an allowlist with no
    deny syntax, so you list what is allowed.
20. **What happens to a misspelled tool name in that list?** It is ignored, not reported. So a typo silently changes
    the restriction.
21. **How is an MCP tool written in a `tools` list?** `server/tool`, or `server/*`. The server name is the key in
    your MCP config, so renaming the server changes every agent that referred to it.
22. **Why can the auditor not call `save_summary`?** It is not in the list, so for that session it does not exist. A
    session that can only read cannot quietly fix what it was asked to report on.

## Hooks

23. **What does a hook process get as input, and how long does it live?** The event as JSON on stdin. It lives for
    one event.
24. **`preToolUse` and `PreToolUse`: what is the difference?** The payload. camelCase names deliver camelCase fields
    (`toolName`, `toolArgs`); PascalCase names deliver snake_case fields and Claude-style tool names. They cannot be
    mixed.
25. **What does an empty JSON object on stdout mean?** No decision. Copilot's own permission rules decide.
26. **A `preToolUse` command exits non-zero. Does the tool run?** No. It fails closed.
27. **A `preToolUse` command times out. Does the tool run?** Possibly, yes. A timeout falls through to the normal
    permission rules, on every event. A slow hook is a hole; a broken one is not.
28. **Can a `postToolUse` hook stop the tool?** No, it has already run. It can log, or add context.
29. **Why does the `agentStop` hook check `stop_hook_active`?** It is true when a stop hook already sent the model
    back. Without the check, a condition the model cannot satisfy would block forever.
30. **Why does `agentStop` do nothing when there are no tags?** It fires at the end of every turn in this repository,
    including ordinary coding. Only a half-done run should be held up.
31. **What string does a matcher see for a tool from an MCP server?** Undocumented. GitHub names the built-in tools
    and says a tool with no Claude equivalent keeps its runtime name, but never says how an MCP tool is spelled.
32. **So why is the matcher `.*(?:tag_subscription|save_summary)`?** Any prefix matches, so the hook fires whatever
    the spelling, and the handler checks the real name. A narrower guess would fail silently, with the write going
    through unchecked.
33. **Where are hooks actually supported?** Fully in Copilot CLI, most events on GitHub's side, public preview in VS
    Code, and nowhere else.

## MCP

34. **Why does this repo have two `mcp.json` files?** VS Code reads `.vscode/mcp.json` with the key `servers`.
    Copilot CLI reads `.github/mcp.json` with `mcpServers` and refuses VS Code's file.
35. **Why is there a `!.vscode/mcp.json` line in `.gitignore`?** The rest of `.vscode/` is ignored, and without the
    exception VS Code would get no MCP server from a fresh clone.
36. **Why must a stdio server never print to stdout?** Stdout carries the protocol, so one stray line breaks the
    connection.
37. **What does `annotations.readOnlyHint: true` decide?** Whether Copilot code review can use the tool at all. It
    drops any tool that does not set it.
38. **Why are no write tools served over HTTP here?** The cloud agent and code review call the server from GitHub's
    side, so no hook of yours is in the path. A write there would be unchecked.
39. **If a remote server really had to write, where would the check go?** Inside the server, as that is the only code
    in the path.
40. **Why list the read tools in the repository settings `tools` allowlist, when the server serves only those
    anyway?** Two independent layers, so one mistake does not expose a write. It also keeps tools added later switched
    off.
41. **Can a repository-level MCP server use OAuth?** No. A secret in a header, named `COPILOT_MCP_*`, is the
    documented way.

## The model on its own

42. **Why is the merchant cleaning one call and not an agent?** The input and the output are known and nothing has to
    choose a next step. A loop would add cost and failure modes for no gain.
43. **A refusal comes back. What is the HTTP status?** 200. It has to be looked for in `message.refusal` before
    reading the content.
44. **The schema was `strict`. Why check the answer at all?** The schema fixes the shape, not the content. A valid
    answer can still leave a line out.
45. **Why is no `temperature` sent?** GitHub Models serves many models from several publishers, and one that rejects
    an unsupported parameter would fail the whole call for no gain.
46. **Which parts of this repository have not been run?** Copilot CLI, the cloud agent, code review, and the GitHub
    Models call. `docs/surfaces.md` keeps the list.

## Exercises

Each one changes the code. The tests will tell you what you broke.

1. **Add a check.** Refuse a summary whose `note` is empty. Put it in `checks.py`, add a test, and watch it apply in
   the hook and in the no-Copilot run without touching either.
2. **Break the matcher on purpose.** Change the `preToolUse` matcher to `save_summary` with no `.*`, then run
   `subfinder demo`. Work out from the failure what would have happened in a real session, and why nothing would have
   told you.
3. **Add a fourth instruction file.** Scope it to `tests/**` and have it say something about how tests are written.
   Check with the demo that it does not overlap the other three, and work out which surfaces will ignore it.
4. **Make the custom agent useless.** Set its `tools` to `[]`, then ask it to audit a run. Then set it to `["*"]` and
   notice that nothing warns you.
5. **Add a `postToolUseFailure` hook.** Have it write the failure to the audit log with its own outcome. Wire it in
   the JSON, add it to `EVENTS`, and let the test that compares the two find your mistake if you forget one.
6. **Convert the prompt file into a skill.** It is what VS Code recommends. Decide what its `description` has to say
   for Copilot to load it at the right moment, and what you lose by giving up `${input:merchant}`.
7. **Serve a write tool over HTTP**, then write down what now has no check in front of it. Put it back.
