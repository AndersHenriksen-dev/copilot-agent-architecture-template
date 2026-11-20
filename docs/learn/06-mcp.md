# 6. MCP

## What the protocol does

The Model Context Protocol is a standard way for a program to offer tools to a model's client. The server lists its
tools, each with a name, a description and a JSON schema for its arguments, and runs them when asked. The client does
not need to know anything about your code.

It is the only one of the seven types that is a plain yes on every Copilot surface. It is also the one with the most
configuration files.

## A different file per surface

| Surface | File or place | Top-level key | `tools` allowlist |
|---|---|---|---|
| VS Code | `.vscode/mcp.json` | `servers` | not documented |
| Copilot CLI, project | `.github/mcp.json`, or `.mcp.json` | `mcpServers` | required |
| Copilot CLI, personal | `~/.copilot/mcp-config.json` | `mcpServers` | required |
| Cloud agent and code review | Repository settings on github.com | `mcpServers` | required |

**Copilot CLI will not read `.vscode/mcp.json`**, because of the `servers` key. There is no single file that works
for both, so this repository has both:

```json
{ "servers":    { "subfinder": { "type": "stdio", "command": "uv", "args": ["..."] } } }
{ "mcpServers": { "subfinder": { "type": "local", "command": "uv", "args": ["..."], "tools": ["*"] } } }
```

Note that `.gitignore` here ignores `.vscode/` **except** `mcp.json`, because without that exception VS Code gets no
server. And a test asserts the two files launch the same command with the same arguments, because two config files
that disagree are worse than one that is missing.

For a local server the CLI calls the type `local` where VS Code calls it `stdio`; GitHub's documentation notes the
mapping. The cloud agent accepts `local`, `stdio`, `http` and `sse`.

## Two transports, one server

[server.py](../../src/subfinder/lib/mcp_server/server.py) builds the server. There are two ways out of it:

- **stdio**, launched by whichever config file the surface read, for Copilot on your machine. All five tools.
- **HTTP**, in [http.py](../../src/subfinder/lib/mcp_server/http.py), for Copilot on GitHub's machines. The three read
  tools only.

The split is not about convenience. The cloud agent and code review call the server from GitHub's infrastructure, so
nothing on your machine is in the path and **no hook of yours sees those calls**. A write there would be unchecked.
Putting the checks inside the server would work, and a real system that must write that way would do it; here nothing
needs to, so the write tools are simply not served.

## The annotation that decides whether a tool exists

Copilot code review drops any tool whose `tools/list` entry does not set `annotations.readOnlyHint: true`.

That turns something most servers treat as a hint into the thing that decides whether a review can use a tool at all.
So the server sets it deliberately:

```python
annotations = ToolAnnotations(read_only_hint=True)
```

and [test_server.py](../../tests/mcp_server/test_server.py) asserts which tools carry it. Worth knowing in both
directions: the platform will also happily use a tool that sets the hint wrongly, so the annotation is a claim your
server makes and is responsible for.

## Tool descriptions are prompts

A tool's description is read by the model every time it decides what to call. So it is prompt text, and it belongs
with the other prompts, which is why all five live in
[config/mcp_server/server.yaml](../../src/subfinder/config/mcp_server/server.yaml) rather than in the code.

The useful ones say something the schema cannot:

```yaml
get_merchant: >-
  The statement lines whose raw description contains a name, ignoring case, spaces and punctuation.
  Raw descriptions vary from month to month, so search for each spelling you have seen.
```

The second sentence is there because the first time this ran, the model searched once and missed two months of
charges.

## Two rules for a server program

1. **Never print to stdout.** Stdout carries the protocol, so one stray line breaks the connection. The server here
   sets `log_level="WARNING"` and sends nothing else.
2. **Launch it from `__main__.py`.** Under `python -m`, `__name__` is `__main__`, so anything that derives a path
   from the module name breaks if the launch lives in the same file as the logic. This repo found that the hard way
   in its Claude counterpart, which is why
   [__main__.py](../../src/subfinder/lib/mcp_server/__main__.py) does nothing but launch.

## What a remote server cannot do

For the cloud agent and code review:

- Only MCP **tools** are supported, not resources or prompts.
- **No OAuth** from repository settings. The documented way to authenticate is a secret in a header, with a name
  prefixed `COPILOT_MCP_`, expanded as `$COPILOT_MCP_NAME` or `${{ secrets.COPILOT_MCP_NAME }}`.
- A `tools` allowlist is required. `["*"]` is allowed; the documentation recommends naming read-only tools instead.
- Up to 50 servers across personal and repository configuration.

That header rule is a real difference from Anthropic's claude.ai custom connectors, which accept no authentication or
OAuth and nothing in between. Here a fixed bearer token is a supported option, which is why
[http.py](../../src/subfinder/lib/mcp_server/http.py) asks for one by default and `serve-http` refuses to start
without either a token or an explicit `--no-auth`.

## In the code

- [server.py](../../src/subfinder/lib/mcp_server/server.py): five tools, with annotations
- [http.py](../../src/subfinder/lib/mcp_server/http.py): the read tools, a bearer token and a Host check
- [tools.py](../../src/subfinder/lib/statement/tools.py): the tools themselves, as plain functions that know nothing
  about MCP
- [.vscode/mcp.json](../../.vscode/mcp.json) and [.github/mcp.json](../../.github/mcp.json)
- [docs/surfaces.md](../surfaces.md#setting-up-the-repository-mcp-server-on-github): the JSON for repository settings
- [test_server.py](../../tests/mcp_server/test_server.py) and [test_http.py](../../tests/mcp_server/test_http.py)
