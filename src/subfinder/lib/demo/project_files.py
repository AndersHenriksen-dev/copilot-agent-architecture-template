"""Reading the Copilot configuration files the way Copilot does: YAML frontmatter on top, Markdown under it.

None of these files are Python, so nothing imports them. This is what lets the demo and the tests see them at all,
and check that what the docs claim about them is still true of the files on disk.
"""

from __future__ import annotations

import json
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

import yaml

from subfinder.lib.shared.settings import REPO_ROOT

GITHUB_DIR = REPO_ROOT / ".github"


def read_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    """Split a Markdown file into its frontmatter and its body.

    Args:
        path: An instructions, prompt, skill or agent file. Frontmatter must start on the first line.

    Returns:
        The frontmatter (empty if the file has none; Any because each kind of file has its own fields) and the body.
    """
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, text
    header, body = text.removeprefix("---\n").split("\n---\n", maxsplit=1)
    return yaml.safe_load(header), body


def always_on_instruction_files() -> list[Path]:
    """The instruction files that load in every session: the repo-wide one, and AGENTS.md beside it."""
    return [GITHUB_DIR / "copilot-instructions.md", REPO_ROOT / "AGENTS.md"]


def path_instruction_files() -> list[Path]:
    """Every path-specific instruction file. Copilot looks within and below `.github/instructions`."""
    return sorted((GITHUB_DIR / "instructions").rglob("*.instructions.md"))


def prompt_files() -> list[Path]:
    """Every prompt file."""
    return sorted((GITHUB_DIR / "prompts").glob("*.prompt.md"))


def skill_files() -> list[Path]:
    """Every skill's SKILL.md. The file name is fixed, and the folder name is the skill's name."""
    return sorted((GITHUB_DIR / "skills").glob("*/SKILL.md"))


def skill_bundled_files(skill: Path) -> list[Path]:
    """The other files in a skill's folder, which Copilot makes available once the skill is in use.

    Args:
        skill: A skill's SKILL.md.

    Returns:
        Every sibling file, SKILL.md itself left out.
    """
    return sorted(path for path in skill.parent.iterdir() if path.is_file() and path.name != skill.name)


def agent_files() -> list[Path]:
    """Every custom agent definition."""
    return sorted((GITHUB_DIR / "agents").glob("*.md"))


def hook_config() -> dict[str, Any]:
    """The hook configuration, read from `.github/hooks/`.

    Returns:
        The parsed JSON. Any, because it is a JSON document whose shape GitHub defines, not one of ours.

    Raises:
        ValueError: If there is not exactly one hook file, which would make this repo's own documentation wrong.
    """
    files = sorted((GITHUB_DIR / "hooks").glob("*.json"))
    if len(files) != 1:
        raise ValueError(f"Expected one hook config in .github/hooks/, found {len(files)}.")
    parsed: dict[str, Any] = json.loads(files[0].read_text(encoding="utf-8"))
    return parsed


def mcp_server_commands() -> dict[str, list[str]]:
    """How each MCP config file launches the server, so the demo can check the two agree.

    VS Code reads `.vscode/mcp.json` and puts its servers under `servers`. Copilot CLI reads `.github/mcp.json` and
    puts them under `mcpServers`, and refuses VS Code's file for exactly that reason. One server, two files.

    Returns:
        The command and arguments found in each file, keyed by the file's path relative to the repo root.
    """
    places = {
        ".vscode/mcp.json": "servers",
        ".github/mcp.json": "mcpServers",
    }
    commands = {}
    for relative, key in places.items():
        config = json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))
        server = config[key]["subfinder"]
        commands[relative] = [server["command"], *server["args"]]
    return commands


def instruction_applies_to(instructions: Path, relative_path: str) -> bool:
    """Whether a path-specific instruction file loads for a file.

    Args:
        instructions: An `*.instructions.md` file.
        relative_path: A path from the repo root, with forward slashes.

    Returns:
        True if one of the file's `applyTo` globs matches. A file with no `applyTo` applies everywhere.
    """
    patterns = read_frontmatter(instructions)[0].get("applyTo", "")
    globs = [pattern.strip() for pattern in str(patterns).split(",") if pattern.strip()]
    return not globs or any(fnmatch(relative_path, glob) for glob in globs)
