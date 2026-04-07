# -*- coding: utf-8 -*-
import os
from pathlib import Path

from lark_agent_bridge.core.detect import (
    copaw_working_dir,
    lark_cli_config_dir,
    resolve_workspace,
)


def test_copaw_working_dir_default(monkeypatch):
    monkeypatch.delenv("COPAW_WORKING_DIR", raising=False)
    h = Path.home()
    assert copaw_working_dir() == h / ".copaw"


def test_resolve_default(monkeypatch, tmp_path):
    monkeypatch.setenv("COPAW_WORKING_DIR", str(tmp_path))
    (tmp_path / "workspaces" / "default").mkdir(parents=True)
    ws = resolve_workspace(None, all_workspaces=False)
    assert len(ws) == 1
    assert ws[0].name == "default"


def test_lark_cli_config_dir_default(monkeypatch):
    monkeypatch.delenv("LARK_CLI_HOME", raising=False)
    h = Path.home()
    assert lark_cli_config_dir() == h / ".lark-cli"


def test_lark_cli_config_dir_env(monkeypatch, tmp_path):
    monkeypatch.setenv("LARK_CLI_HOME", str(tmp_path))
    assert lark_cli_config_dir() == tmp_path.resolve()
