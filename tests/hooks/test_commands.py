"""The `check` command: the same checks the hook runs, run by hand."""

from __future__ import annotations

from decimal import Decimal

import pytest

from subfinder.lib.hooks.commands import cmd_check
from subfinder.lib.statement.tools import save_summary, tag_subscription
from subfinder.lib.statement.workbook import SummaryLine


def test_an_empty_run_has_nothing_to_check(capsys: pytest.CaptureFixture[str]) -> None:
    assert cmd_check() == 0
    assert "nothing to check" in capsys.readouterr().out


def test_tags_with_no_summary_are_reported_as_unfinished(capsys: pytest.CaptureFixture[str]) -> None:
    tag_subscription("Tunebox", ["T05", "T18", "T30"])
    assert cmd_check() == 1
    output = capsys.readouterr().out
    assert "Tunebox" in output
    assert "No summary saved yet" in output


def test_a_good_run_passes(capsys: pytest.CaptureFixture[str]) -> None:
    tag_subscription("Tunebox", ["T05", "T18", "T30"])
    save_summary(
        [SummaryLine(merchant="Tunebox", monthly_saving=Decimal("109.00"), note="Music.")],
        total_monthly_saving=Decimal("109.00"),
    )
    assert cmd_check() == 0
    assert "Every check passes." in capsys.readouterr().out


def test_an_overstated_summary_fails(capsys: pytest.CaptureFixture[str]) -> None:
    """The workbook can hold a bad summary: `save_summary` is only guarded by the hook, not by itself."""
    tag_subscription("Tunebox", ["T05", "T18", "T30"])
    save_summary(
        [SummaryLine(merchant="Tunebox", monthly_saving=Decimal("999.00"), note="Too much.")],
        total_monthly_saving=Decimal("999.00"),
    )
    assert cmd_check() == 1
    assert "Summary FAILS" in capsys.readouterr().out
