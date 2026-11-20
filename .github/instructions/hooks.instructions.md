---
applyTo: "src/subfinder/lib/hooks/**,src/subfinder/config/hooks/**,tests/hooks/**,.github/hooks/**"
---

# Working on the hooks

- `checks.py` holds pure functions and imports nothing about Copilot. Keep it that way: `lib/api/run.py` calls the
  same functions where no hook exists, and the tests call them directly.
- `events.py` turns one event into one JSON object on stdout. An empty object means no decision. Anything else is a
  decision, and the key names differ per event: `permissionDecision` and `permissionDecisionReason` for `preToolUse`,
  `decision` and `reason` for `agentStop`, `additionalContext` for `sessionStart`.
- Event names here are camelCase, which is what delivers camelCase payload fields such as `toolName` and `toolArgs`.
  The PascalCase aliases deliver snake_case fields instead. Do not mix the two spellings in one config.
- `preToolUse` fails closed. An unreadable event is denied, and Copilot itself denies the call when the command exits
  non-zero. Keep it that way, and keep it fast: a hook runs inside the model's turn.
- `agentStop` must honour `stop_hook_active`, or a session can never end.
- Do not narrow the `preToolUse` matcher to an exact tool name. GitHub does not document how an MCP server's tools are
  spelled in `toolName`, so the matcher allows any prefix and `events.py` checks the name itself.
