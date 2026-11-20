# Where Copilot runs, and what works there

Copilot is not one program. It is an IDE extension, a command-line tool, an agent that runs on GitHub's own machines,
and a pull request reviewer. They read the same repository and do not support the same things.

This is the page I wish I had read first. Every file in this repository is in the right place, and several of them
still do nothing on some surfaces.

Checked against the GitHub and VS Code documentation on 2026-11-20. These tables change, so check before relying on a
cell.

## The short version

Four things that catch people out:

1. **Prompt files do not run on github.com or in Copilot CLI at all.** In VS Code they run only in the Local harness,
   which VS Code says is deprecated and due to be removed in February 2027.
2. **Hooks are in preview in VS Code**, and supported in Copilot CLI and on GitHub's side. They are the only type
   that can refuse anything, so the surface that enforces your rules is not the surface most people work in.
3. **Path-specific instructions do not reach Copilot Chat on github.com**, though they do reach the cloud agent and
   code review.
4. **MCP is configured in a different file per surface**, and Copilot CLI refuses to read VS Code's.

## The types, by surface

Taken from GitHub's customization cheat sheet. "Preview" means public preview.

| Type | VS Code | Visual Studio | JetBrains | Eclipse | Xcode | github.com | Copilot CLI |
|---|---|---|---|---|---|---|---|
| Custom instructions | yes | yes | preview | preview | preview | yes | yes |
| Prompt files | yes | yes | preview | **no** | preview | **no** | **no** |
| Custom agents | yes | yes | preview | preview | preview | yes | yes |
| Subagents | yes | **no** | preview | preview | preview | **no** | yes |
| Agent skills | yes | yes | preview | **no** | **no** | yes | yes |
| Hooks | **preview** | **no** | **no** | **no** | **no** | yes | yes |
| MCP servers | yes | yes | yes | yes | yes | yes | yes |

MCP is the only row that is a plain yes everywhere, and even there the configuration file differs.

## Which instruction files reach which surface

The github.com column splits into three, because Chat, the cloud agent and code review do not read the same set.

| Surface | Repo-wide | Path-specific | `AGENTS.md` | Personal | Organization |
|---|---|---|---|---|---|
| github.com Chat | yes | **no** | **no** | yes | yes |
| github.com cloud agent | yes | yes | yes | no | yes |
| github.com code review | yes | yes | yes, plus `REVIEW.md` | no | yes |
| VS Code Chat | yes | yes | `AGENTS.md` only | no | no |
| VS Code code review | yes | **no** | **no** | no | no |
| Visual Studio Chat | yes | yes | no | no | no |
| JetBrains Chat | yes | yes | no | yes | no |
| Eclipse Chat | yes | **no** | **no** | no | no |
| Xcode Chat | yes | yes | no | no | no |
| Copilot CLI | yes | yes | yes | yes | no |

Where a row says `AGENTS.md`, the cloud agent and the CLI also read `CLAUDE.md` and `GEMINI.md` in the same role.

**Precedence.** GitHub documents an order for Copilot Chat on github.com only: personal instructions, then repository
instructions (path-specific, then repo-wide, then agent files), then organization instructions. For everything else
it says most surfaces combine the applicable files **without defining a general precedence order**. So do not plan on
a more specific file winning a disagreement. Write files that do not disagree.

## Where MCP is configured

| Surface | File or place | Top-level key | `tools` allowlist |
|---|---|---|---|
| VS Code | `.vscode/mcp.json` | `servers` | not documented |
| Copilot CLI, project | `.github/mcp.json`, or `.mcp.json` | `mcpServers` | required |
| Copilot CLI, personal | `~/.copilot/mcp-config.json` | `mcpServers` | required |
| Cloud agent and code review | Repository settings on github.com | `mcpServers` | required |
| One custom agent, cloud only | `mcp-servers` in its frontmatter | server name as key | required |

Copilot CLI explicitly does not read `.vscode/mcp.json`, because of the `servers` key. Both files are in this repo,
and `test_both_mcp_config_files_launch_this_module` keeps them from drifting apart.

For the cloud agent and code review, there are two further limits. Only MCP **tools** are supported, not resources or
prompts. And a remote server cannot use OAuth from repository settings: a secret in a header is the documented way,
with the name prefixed `COPILOT_MCP_`.

**Code review has one more rule, and it is easy to miss.** It drops any tool whose `tools/list` entry does not set
`annotations.readOnlyHint: true`. The server in this repo sets it on the three read tools, which is why
`test_read_tools_are_marked_read_only` exists.

## Hooks, by surface

| Surface | Support | Notes |
|---|---|---|
| Copilot CLI | Full | Every event. Policy hooks, `exec`/`args`, prompt hooks, `permissionRequest` and `notification` are CLI only |
| Cloud agent | Most events | Linux only, so `bash` or `command`, never `powershell`. `ask` is treated as deny. Files it writes are discarded when the job ends |
| VS Code | Preview | Reads `.github/hooks/*.json`. Events: `sessionStart`, `userPromptSubmitted`, `preToolUse`, `postToolUse`, `preCompact`, `subagentStart`, `subagentStop`, `agentStop`, `sessionEnd` |
| Visual Studio, JetBrains, Eclipse, Xcode | No | |

Hooks from several places run together rather than replacing each other: policy, then user, then project, then
plugins. A repository hook does not cancel a user hook on the same event.

**Failure behaviour is not uniform, and this is the part worth remembering.** A `preToolUse` command that exits
non-zero denies the call, which fails closed. A `preToolUse` command that **times out** does not: it falls through to
the normal permission rules. So a hook that is slow is a hole, while a hook that is broken is not.

## What this repository has actually been run on

The same honesty this repo asks for in its own instructions.

| Path | State |
|---|---|
| `uv run subfinder demo`, the whole wiring with a scripted model | Run, and CI runs it on every pull request |
| The test suite, including real subprocesses and real HTTP | Run |
| VS Code: instructions, skill, custom agent, MCP over stdio | To be confirmed by hand |
| VS Code: hooks, which are in preview there | To be confirmed by hand |
| Copilot CLI | Not run |
| Cloud agent and code review, including repository MCP settings | Not run. A repository-level MCP server needs a public URL, and nothing here has had one |
| `uv run subfinder run`, the GitHub Models call | Not run. The endpoint is unreachable from the machine this was built on, so the model id and request shape are written from the documentation and checked by tests against a stand-in, not against the live API |

Where a claim in this repository has not been run, it says so. A template that quietly overstated what it had tested
would be a bad one to copy.

## Setting up the repository MCP server on GitHub

Not run, so treat it as a starting point rather than a recipe.

The cloud agent and code review reach an MCP server over HTTP from GitHub's side. Serve the read tools, with a token:

```bash
uv run subfinder serve-http --public-host your-name.example.com
```

The server has to be reachable from the internet, so it needs a public URL, which a tunnel can give it. Then, under
the repository's Settings, Copilot, MCP servers, paste this, having first added an Agents secret called
`COPILOT_MCP_SUBFINDER_TOKEN` holding the same value as `SUBFINDER_HTTP_TOKEN`:

```json
{
  "mcpServers": {
    "subfinder": {
      "type": "http",
      "url": "https://your-name.example.com/mcp",
      "tools": ["list_transactions", "get_merchant", "get_summary"],
      "headers": {
        "Authorization": "Bearer $COPILOT_MCP_SUBFINDER_TOKEN"
      }
    }
  }
}
```

The `tools` list repeats what the server already enforces. That is on purpose: the server serves no write tool, and
the allowlist would not let one through either. Either alone would do, and one mistake is then not enough.

Only do this with made-up data, and stop the tunnel when you are finished.
