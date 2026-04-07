# -*- coding: utf-8 -*-
"""Tests for core.permissions helpers."""

from __future__ import annotations

import json

from lark_agent_bridge.core import permissions


def test_extract_scope_names_from_list_and_dict() -> None:
    payload = {
        "scopes": [
            "wiki:wiki:readonly",
            {"scope": "calendar:calendar:readonly"},
            {"name": "im:message"},
        ],
    }
    scopes = permissions._extract_scope_names(payload)
    assert "wiki:wiki:readonly" in scopes
    assert "calendar:calendar:readonly" in scopes
    assert "im:message" in scopes


def test_build_snapshot_with_mocked_calls(monkeypatch) -> None:
    monkeypatch.setattr(
        permissions,
        "auth_scopes",
        lambda _exe: (["wiki:wiki:readonly"], "ok"),
    )
    monkeypatch.setattr(
        permissions,
        "check_scopes",
        lambda _exe, scopes: {s: (s == "wiki:wiki:readonly") for s in scopes},
    )
    monkeypatch.setattr(permissions, "config_show", lambda _exe: {"appId": "cli_x"})
    monkeypatch.setattr(
        permissions,
        "auth_status",
        lambda _exe: {"tokenStatus": "valid", "identity": "u"},
    )

    snap = permissions.build_snapshot("/usr/bin/lark-cli")
    assert snap["summary"]["app_scope_count"] == 1
    assert snap["summary"]["checked_total"] >= 1
    assert "generated_at" in snap


def test_snapshot_read_write(tmp_path) -> None:
    ws = tmp_path / "workspaces" / "default"
    ws.mkdir(parents=True)
    data = {"generated_at": "x", "summary": {"checked_total": 1}}
    p = permissions.write_snapshot(ws, data)
    assert p.exists()
    loaded = permissions.read_snapshot(ws)
    assert loaded["summary"]["checked_total"] == 1


def test_auth_scopes_parses_stdout(monkeypatch) -> None:
    raw = json.dumps({"scopes": [{"scope": "wiki:wiki:readonly"}]})
    monkeypatch.setattr(
        permissions,
        "_run_capture",
        lambda _args, timeout=30.0: (0, raw, ""),
    )
    scopes, hint = permissions.auth_scopes("/usr/bin/lark-cli")
    assert scopes == ["wiki:wiki:readonly"]
    assert hint == "ok"
