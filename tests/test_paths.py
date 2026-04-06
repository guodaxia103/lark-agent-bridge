# -*- coding: utf-8 -*-
import os
from pathlib import Path

from lark_agent_bridge.core.detect import copaw_working_dir, resolve_workspace


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
