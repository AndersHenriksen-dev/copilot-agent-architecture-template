"""Reading config files: paths mirror modules, and a typo fails."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from subfinder.lib.shared.settings import (
    CONFIG_DIR,
    SETTINGS,
    Settings,
    config_path,
    model_from_env,
    read_config,
    workspace_dir,
)


def test_config_path_mirrors_the_module() -> None:
    assert config_path("subfinder.lib.api.clean_merchants") == CONFIG_DIR / "api" / "clean_merchants.yaml"


def test_a_misspelled_key_fails(tmp_path: Path) -> None:
    file = tmp_path / "settings.yaml"
    file.write_text(
        "model: m\nworkspace_dir: w\nworkbook_file: a\naudit_file: b\nmodle: typo\n",
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        read_config(file, Settings)


def test_the_default_model_is_named_the_way_github_models_names_one() -> None:
    publisher, _, model = SETTINGS.model.partition("/")
    assert publisher and model, "GitHub Models ids are publisher/model, such as openai/gpt-4.1-mini"


def test_environment_overrides(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("SUBFINDER_MODEL", "openai/some-other-model")
    monkeypatch.setenv("SUBFINDER_WORKSPACE", str(tmp_path))
    assert model_from_env() == "openai/some-other-model"
    assert workspace_dir() == tmp_path
