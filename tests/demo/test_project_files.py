"""The Copilot configuration files on disk: the shapes GitHub documents, and the claims this repo makes about them.

None of these files are Python, so nothing would notice a mistake in them. These tests are what notices.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from subfinder.lib.demo.project_files import (
    GITHUB_DIR,
    agent_files,
    always_on_instruction_files,
    hook_config,
    instruction_applies_to,
    mcp_server_commands,
    path_instruction_files,
    prompt_files,
    read_frontmatter,
    skill_bundled_files,
    skill_files,
)
from subfinder.lib.hooks.events import EVENTS
from subfinder.lib.shared.settings import REPO_ROOT

WRITE_TOOLS = ("tag_subscription", "save_summary")
FILES = sorted(path for path in (REPO_ROOT / "src").rglob("*") if path.is_file())


def test_the_always_on_instruction_files_exist() -> None:
    assert [path.name for path in always_on_instruction_files()] == ["copilot-instructions.md", "AGENTS.md"]
    for path in always_on_instruction_files():
        assert path.exists()


def test_the_always_on_files_have_no_frontmatter() -> None:
    """Only `*.instructions.md` files take an applyTo. These two always load, so frontmatter would mislead."""
    for path in always_on_instruction_files():
        assert read_frontmatter(path)[0] == {}


@pytest.mark.parametrize("path", path_instruction_files(), ids=lambda path: path.name)
def test_every_path_specific_file_declares_an_apply_to(path: Path) -> None:
    header = read_frontmatter(path)[0]
    assert "applyTo" in header, "a file without applyTo would load everywhere, which defeats the point"
    assert isinstance(header["applyTo"], str)
    assert header["applyTo"].strip()


@pytest.mark.parametrize("path", path_instruction_files(), ids=lambda path: path.name)
def test_apply_to_globs_match_files_that_exist(path: Path) -> None:
    """A glob with a typo silently never fires, so each one has to match something in the repo.

    Only the globs that name a folder are checked this way. A file-type glob such as `**/*.py` names no folder, so it
    is checked by matching it against the repository's own files instead.
    """
    for raw in read_frontmatter(path)[0]["applyTo"].split(","):
        glob = raw.strip()
        prefix = glob.removesuffix("/**")
        if "*" in prefix:
            assert any(instruction_applies_to(path, found.relative_to(REPO_ROOT).as_posix()) for found in FILES), (
                f"{path.name}: applyTo {glob} matches nothing in the repository"
            )
            continue
        assert (REPO_ROOT / prefix).exists(), f"{path.name}: applyTo points at {prefix}, which is not here"


def test_the_money_rule_is_scoped_to_the_statement() -> None:
    money = GITHUB_DIR / "instructions" / "money.instructions.md"
    assert instruction_applies_to(money, "src/subfinder/lib/statement/recurring.py")
    assert instruction_applies_to(money, "tests/statement/test_recurring.py")
    assert not instruction_applies_to(money, "README.md")
    assert not instruction_applies_to(money, "src/subfinder/lib/hooks/events.py")


def test_the_money_rule_says_what_the_code_does() -> None:
    """The part of the rule a machine can check is checked here, so the two cannot drift apart."""
    text = (GITHUB_DIR / "instructions" / "money.instructions.md").read_text(encoding="utf-8")
    assert "Decimal" in text
    assert "never" in text.lower() and "float" in text
    source = (REPO_ROOT / "src" / "subfinder" / "lib" / "statement" / "transactions.py").read_text(encoding="utf-8")
    assert "not a float" in source


def test_the_prompt_file_is_named_and_scoped() -> None:
    header, body = read_frontmatter(prompt_files()[0])
    assert header["name"] == "review-summary"
    assert header["tools"] == ["subfinder/*"]
    assert "${input:merchant" in body
    assert all(write not in str(header["tools"]) for write in WRITE_TOOLS)


def test_the_prompt_file_records_that_it_has_an_end_date() -> None:
    """VS Code runs prompt files only in its Local harness, which it says goes in February 2027."""
    body = read_frontmatter(prompt_files()[0])[1]
    assert "Local harness" in body
    assert "February 2027" in body


def test_the_skill_follows_the_documented_shape() -> None:
    skill = skill_files()[0]
    header, body = read_frontmatter(skill)
    assert header["name"] == skill.parent.name == "find-subscriptions"
    assert header["name"] == header["name"].lower().replace(" ", "-")
    assert header["description"].strip()
    assert len(header["description"]) < len(body), "the description is always in context, so it stays the smaller part"


def test_the_skill_pre_approves_nothing() -> None:
    """`allowed-tools` would skip the confirmation on a terminal command, which a template should not teach."""
    assert "allowed-tools" not in read_frontmatter(skill_files()[0])[0]


def test_the_skill_bundles_its_supporting_files() -> None:
    bundled = {path.name for path in skill_bundled_files(skill_files()[0])}
    assert bundled == {"summary-format.md", "summarize-audit.py"}


def test_the_skill_names_the_files_it_bundles() -> None:
    skill = skill_files()[0]
    body = read_frontmatter(skill)[1]
    for path in skill_bundled_files(skill):
        assert path.name in body, f"{path.name} is in the folder but the skill never mentions it"


def test_the_custom_agent_can_only_read() -> None:
    header = read_frontmatter(agent_files()[0])[0]
    assert header["name"] == "statement-auditor"
    assert header["description"].strip()
    assert set(header["tools"]) == {
        "read",
        "search",
        "subfinder/list_transactions",
        "subfinder/get_merchant",
        "subfinder/get_summary",
    }


def test_the_custom_agents_allowlist_has_no_way_to_write() -> None:
    """`tools` is an allowlist with no deny syntax, so what is absent is what is forbidden."""
    tools = read_frontmatter(agent_files()[0])[0]["tools"]
    assert all(write not in tool for tool in tools for write in WRITE_TOOLS)
    assert "edit" not in tools
    assert "execute" not in tools


def test_the_hook_config_is_version_one_and_wires_every_handler() -> None:
    config = hook_config()
    assert config["version"] == 1
    assert set(config["hooks"]) == set(EVENTS)


@pytest.mark.parametrize("event", sorted(hook_config()["hooks"]))
def test_every_hook_entry_runs_this_package(event: str) -> None:
    entry = hook_config()["hooks"][event][0]
    assert entry["command"].endswith(f"python -m subfinder.lib.hooks {event}")
    assert entry["cwd"] == "."
    assert entry["timeoutSec"] >= 10


def test_the_tool_events_have_a_matcher_and_the_others_do_not() -> None:
    """A matcher is tested against a tool name, so it means nothing on sessionStart or agentStop."""
    hooks = hook_config()["hooks"]
    assert "matcher" in hooks["preToolUse"][0]
    assert "matcher" in hooks["postToolUse"][0]
    assert "matcher" not in hooks["sessionStart"][0]
    assert "matcher" not in hooks["agentStop"][0]


def test_both_write_tools_sit_behind_the_pre_tool_use_matcher() -> None:
    matcher = hook_config()["hooks"]["preToolUse"][0]["matcher"]
    assert matcher.startswith(".*"), "GitHub does not document the MCP spelling, so any prefix has to match"
    for write in WRITE_TOOLS:
        assert write in matcher


def test_the_two_mcp_config_files_agree() -> None:
    commands = mcp_server_commands()
    assert set(commands) == {".vscode/mcp.json", ".github/mcp.json"}
    assert len({tuple(command) for command in commands.values()}) == 1


def test_the_vscode_config_is_committed_despite_the_ignore_rule() -> None:
    """`.vscode/` is ignored apart from this one file, which is this repo's MCP config for VS Code."""
    ignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "!.vscode/mcp.json" in ignore
    assert json.loads((REPO_ROOT / ".vscode" / "mcp.json").read_text(encoding="utf-8"))["servers"]
