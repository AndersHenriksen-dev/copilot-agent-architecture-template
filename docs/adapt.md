# Using this as a template

Click **Use this template** on GitHub, then replace the example with your own idea. Most of the change is in one
folder and its matching config. The tests check that the wiring still lines up, so they tell you what you missed.

## What to change

1. **The domain.** Replace `src/subfinder/lib/statement/` and `src/subfinder/config/statement/`. Keep the split: data
   and pure functions in one place, and the tools as plain functions in `tools.py`.
2. **The tools.** List your read and write tools in `lib/mcp_server/server.py`, with their descriptions in
   `config/mcp_server/server.yaml`. Keep `read_only_hint` honest: Copilot code review drops any tool that does not
   set it, and will happily use one that sets it wrongly.
3. **The checks.** Replace `lib/hooks/checks.py` with what must never happen in your domain. Keep them as pure
   functions: the model path in `lib/api/run.py` has no hooks and calls the same ones.
4. **The hook wiring.** In `.github/hooks/subfinder-hooks.json`, put your write tools in the `preToolUse` matcher and
   your read tools in the `postToolUse` one. Leave the leading `.*`, for the reason in
   [decisions.md](decisions.md#the-pretooluse-matcher-allows-any-prefix). Add or remove events in `events.py`, and
   keep the two in step: a test asserts every configured event has a handler.
5. **The instructions.** Rewrite `AGENTS.md` and `.github/copilot-instructions.md`, keeping them about different
   subjects so neither repeats the other. Scope what you can with `applyTo` in
   `.github/instructions/`, by folder or by file type. Keep each file short and self-contained.
6. **The skill.** Rename `.github/skills/find-subscriptions/` and rewrite its steps. The `name` in the frontmatter
   must match the folder, lowercase with hyphens. Say in the body what the hooks will refuse, so a refusal is not a
   surprise. Name every file you bundle: a test checks that you did.
7. **The custom agent.** Rewrite `.github/agents/statement-auditor.md`. Remember `tools` is an allowlist with no deny
   syntax, so the list is the whole restriction, and an unrecognised name is ignored rather than reported.
8. **The prompt file.** Rewrite or delete `.github/prompts/`. Read its note about the Local harness first and decide
   whether you want the type at all.
9. **The model call.** Change the output shape and the prompt in `lib/api/clean_merchants.py` and its config, or
   delete `lib/api/` if nothing runs without Copilot. If you keep it, check the model id against the catalog: the one
   here has not been run.
10. **The HTTP transport.** Decide what may be reached from GitHub's side. Delete `lib/mcp_server/http.py` if nothing
    may, and remember that whatever you do serve has no hook of yours in front of it.
11. **The names.** Replace `subfinder` in `pyproject.toml`, both `mcp.json` files, `config/mcp_server/server.yaml`
    and the imports. The server's name is the prefix in a custom agent's `tools` list, so changing it means changing
    `.github/agents/` too.

## What to keep as it is

- `lib/shared/settings.py` and the mirrored `lib/`, `config/` and `tests/` folders.
- `.pre-commit-config.yaml`, `.gitleaks.toml` and the CI workflow.
- The `.gitignore` exception that commits `.vscode/mcp.json`. Without it, VS Code gets no MCP server.
- Both MCP config files, and the test that keeps them in step.
- The demo idea: one free command that runs every part for real with only the model scripted.
- `docs/surfaces.md`, updated. Whatever you build, the question "which surface does this actually work on" will come
  up, and having the table written down is most of the answer.

## Questions to answer for your own project

- **What is the worst thing the model could write?** That is your first `preToolUse` check.
- **Which surface will your team actually use?** If it is one where hooks are preview or missing, your checks are
  guidance, not guarantees, and something else has to enforce them. CI is the usual answer.
- **What would you need to see afterwards to trust a run?** That is your `postToolUse` log.
- **What does "finished" mean?** That is your `agentStop` hook.
- **Which part needs judgement, and which part is arithmetic?** Only the first needs a model.
- **Is there a session that should not be able to write?** That is a custom agent with a short `tools` list.
- **Who calls your tools from outside your machine?** Whatever they reach has no hooks around it.
