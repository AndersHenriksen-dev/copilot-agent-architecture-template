# 11. Further reading

The documentation behind each idea, checked on 2026-11-20. Both GitHub's and VS Code's pages move quickly, so treat a
detail in this repository as something to verify rather than something to trust.

## Start here

- [Copilot customization cheat sheet](https://docs.github.com/en/copilot/reference/customization-cheat-sheet). The
  seven types, what each is for, and the support matrix by IDE. One page, and the one to re-read when something in
  this repository stops matching.
- [Copilot feature matrix](https://docs.github.com/en/copilot/reference/copilot-feature-matrix). The wider version,
  beyond customization.

## Instructions

- [About custom instructions](https://docs.github.com/en/copilot/concepts/prompting-and-context/custom-instructions).
  The three kinds, the precedence order for Chat on github.com, and the patterns that cause problems.
- [Custom instructions support](https://docs.github.com/en/copilot/reference/custom-instructions-support). Which
  instruction file reaches which surface. This is the table behind most of
  [chapter 7](07-where-copilot-runs.md).
- [Your first custom instructions](https://docs.github.com/en/copilot/tutorials/customization-library/custom-instructions/your-first-custom-instructions).
  Where `applyTo` is documented.

## Prompt files and skills

- [Prompt files](https://docs.github.com/en/copilot/concepts/prompting-and-context/prompt-files). GitHub's page, which
  documents no frontmatter.
- [Prompt files in VS Code](https://code.visualstudio.com/docs/copilot/customization/prompt-files). The frontmatter
  fields, the `${input:...}` syntax, and the notice that they run only in the Local harness.
- [About agent skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills). Folder layout,
  frontmatter, bundled files, `allowed-tools` and its warning, and `gh skill`.
- [Add skills to the cloud agent](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills).

## Custom agents

- [About custom agents](https://docs.github.com/copilot/concepts/agents/coding-agent/about-custom-agents).
- [Custom agents configuration](https://docs.github.com/en/copilot/reference/custom-agents-configuration). Every
  frontmatter field, the `tools` aliases, the MCP naming, and the fields that are cloud-only.
- [Subagents](https://docs.github.com/en/copilot/how-tos/copilot-in-your-ide/use-copilot-agents/use-subagents).

## Hooks

- [About hooks](https://docs.github.com/en/copilot/concepts/agents/hooks). What they are and where they live.
- [Hooks reference](https://docs.github.com/en/copilot/reference/hooks-reference). The full schema, every event, every
  payload field, the exit codes and the matcher rules. Worth reading in full before writing one. Note what it does
  **not** contain: any mention of MCP, which is the gap [chapter 5](05-hooks.md) is about.
- [Agent hooks in VS Code](https://code.visualstudio.com/docs/agent-customization/hooks). The VS Code side, including
  which events it supports and that the feature is in preview.

## MCP

- [MCP in Copilot](https://docs.github.com/en/copilot/concepts/customizations/mcp). The concepts, and which surface
  reads which config.
- [Configure MCP servers for your repository](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/configure-mcp-servers).
  The repository settings JSON, the `COPILOT_MCP_` secret rule, the tools-only limit, and the `readOnlyHint`
  requirement for code review.
- [Add MCP servers to Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-mcp-servers).
  Where the CLI looks, and why it will not read `.vscode/mcp.json`.
- [Extend Copilot Chat with MCP](https://docs.github.com/en/copilot/how-tos/copilot-in-your-ide/customize-copilot/extend-copilot-with-tools-and-context/extend-copilot-chat-with-mcp).
  The IDE side.
- [Model Context Protocol specification](https://modelcontextprotocol.io/). The protocol itself, including tool
  annotations.

## The model on its own

- [GitHub Models documentation](https://docs.github.com/en/github-models). The catalog, the endpoint, the `models:read`
  permission and the rate limits.
- [OpenAI structured outputs](https://platform.openai.com/docs/guides/structured-outputs). The `response_format`
  shape that GitHub Models' chat-completions endpoint follows.

## Other Copilot surfaces this repo touches but does not build on

- [Copilot code review](https://docs.github.com/en/copilot/concepts/code-review). Including `REVIEW.md` and the
  head-branch rule.
- [Customize Copilot code review](https://docs.github.com/en/copilot/tutorials/customize-code-review).
- [Copilot CLI](https://docs.github.com/en/copilot/concepts/agents/copilot-cli).
- [Copilot connectors](https://docs.github.com/en/copilot/concepts/customizations/copilot-connectors). In public
  preview, and not used here.

## The other half of the comparison

- [claude-agent-architecture-template](https://github.com/AndersHenriksen-dev/claude-agent-architecture-template). The
  same statement and the same answer, built with Claude's rules, skills, hooks, MCP, API and connectors. Its
  `docs/types.md` is the page to read beside this repo's.
