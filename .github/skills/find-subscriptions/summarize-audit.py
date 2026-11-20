"""Print a tally of the audit log that the `postToolUse` hook writes.

A bundled file of the `find-subscriptions` skill. Copilot makes every file in a skill's folder available once the
skill is in use, so a skill can ship a script and not only instructions.

It uses the standard library only and finds the repository by its own location, so it runs with plain `python` from
anywhere and needs no installed package. It reads one file and writes nothing.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

AUDIT_LOG = Path(__file__).resolve().parents[3] / "workspace" / "audit.jsonl"


def bare_tool_name(name: str) -> str:
    """The tool's own name, without whatever prefix the surface put in front of it.

    The log keeps what the hook was sent, and GitHub does not document how an MCP tool is spelled there, so the same
    tool can appear as `save_summary`, `subfinder/save_summary` or `mcp__subfinder__save_summary`. Counting those as
    three tools would make the tally useless.

    Args:
        name: The tool name as the log recorded it.

    Returns:
        The last segment.
    """
    return re.split(r"/|__", name)[-1]


def read_entries(path: Path) -> list[dict[str, object]]:
    """Read the audit log, skipping blank lines.

    Args:
        path: The log file.

    Returns:
        One dictionary per line. Any line that is not valid JSON stops the script, because a half-read audit log is
        worse than none.
    """
    entries = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError as error:
            raise SystemExit(f"{path} line {number} is not valid JSON: {error}") from error
    return entries


def tally(entries: list[dict[str, object]]) -> str:
    """Describe the log: how many calls, which tools, and which were refused.

    Args:
        entries: The parsed log lines.

    Returns:
        The report, ready to print.
    """
    outcomes = Counter(str(entry.get("outcome", "unknown")) for entry in entries)
    tools = Counter(bare_tool_name(str(entry.get("tool", "unknown"))) for entry in entries)
    lines = [f"{len(entries)} tool calls recorded in {AUDIT_LOG.name}", ""]
    lines += [f"  {outcome:<8} {count}" for outcome, count in sorted(outcomes.items())]
    lines += ["", "By tool:"]
    lines += [f"  {tool:<20} {count}" for tool, count in sorted(tools.items())]
    refused = [entry for entry in entries if entry.get("outcome") == "denied"]
    if refused:
        lines += ["", f"{len(refused)} call(s) were refused before reaching the tool:"]
        lines += [f"  {json.dumps(entry.get('args'))[:140]}" for entry in refused]
    return "\n".join(lines)


def main() -> int:
    """Print the tally, or say that nothing has run yet.

    Returns:
        The exit code.
    """
    if not AUDIT_LOG.exists():
        print(f"No audit log at {AUDIT_LOG}. Nothing has called a tool in this repository yet.")
        return 0
    print(tally(read_entries(AUDIT_LOG)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
