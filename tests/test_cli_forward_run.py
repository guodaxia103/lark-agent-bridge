# -*- coding: utf-8 -*-
"""Tests for cli_forward.run_lark_cli_forward with subprocess mocked."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from lark_agent_bridge.cli_forward import run_lark_cli_forward


class TestRunLarkCliForward:
    @patch("lark_agent_bridge.cli_forward.subprocess.run")
    def test_forwards_args(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        code = run_lark_cli_forward("/usr/bin/lark-cli", ["prog", "cli", "--version"])
        assert code == 0
        mock_run.assert_called_once_with(["/usr/bin/lark-cli", "--version"], shell=False)

    @patch("lark_agent_bridge.cli_forward.subprocess.run")
    def test_default_help_when_no_args(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        code = run_lark_cli_forward("/usr/bin/lark-cli", ["prog", "cli"])
        assert code == 0
        mock_run.assert_called_once_with(["/usr/bin/lark-cli", "--help"], shell=False)

    @patch("lark_agent_bridge.cli_forward.subprocess.run")
    def test_nonzero_exit(self, mock_run):
        mock_run.return_value = MagicMock(returncode=2)
        code = run_lark_cli_forward("/usr/bin/lark-cli", ["prog", "cli", "bad"])
        assert code == 2

    @patch("lark_agent_bridge.cli_forward.subprocess.run", side_effect=OSError("not found"))
    def test_os_error(self, mock_run):
        code = run_lark_cli_forward("/no/such/bin", ["prog", "cli", "--help"])
        assert code == 1
