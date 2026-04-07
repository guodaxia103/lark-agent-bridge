# -*- coding: utf-8 -*-
"""Tests for lark-bridge cli / lark passthrough argv parsing."""

from __future__ import annotations

from lark_agent_bridge.cli_forward import argv_after_cli


def test_argv_after_cli_token() -> None:
    assert argv_after_cli(["lark-bridge", "cli", "--version"]) == ["--version"]
    assert argv_after_cli(["lark-bridge", "cli", "auth", "login"]) == ["auth", "login"]


def test_argv_after_lark_token() -> None:
    assert argv_after_cli(["x", "lark", "wiki", "--help"]) == ["wiki", "--help"]


def test_argv_empty() -> None:
    assert argv_after_cli(["lark-bridge", "setup"]) == []
