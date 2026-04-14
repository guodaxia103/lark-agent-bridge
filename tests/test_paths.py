# -*- coding: utf-8 -*-
import os
from pathlib import Path

from lark_agent_bridge.core.detect import (
    copaw_working_dir,
    lark_cli_config_dir,
    resolve_workspace,
)


def test_copaw_working_dir_default(monkeypatch, tmp_path):
    monkeypatch.delenv("QWENPAW_WORKING_DIR", raising=False)
    monkeypatch.delenv("COPAW_WORKING_DIR", raising=False)
    monkeypatch.setattr("lark_agent_bridge.core.detect.Path.home", lambda: tmp_path)
    assert copaw_working_dir() == (tmp_path / ".qwenpaw").resolve()


def test_copaw_working_dir_qwenpaw_env_precedence(monkeypatch, tmp_path):
    q_root = tmp_path / "q_root"
    c_root = tmp_path / "c_root"
    monkeypatch.setenv("QWENPAW_WORKING_DIR", str(q_root))
    monkeypatch.setenv("COPAW_WORKING_DIR", str(c_root))
    assert copaw_working_dir() == q_root.resolve()


def test_resolve_default(monkeypatch, tmp_path):
    monkeypatch.setenv("QWENPAW_WORKING_DIR", str(tmp_path))
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
