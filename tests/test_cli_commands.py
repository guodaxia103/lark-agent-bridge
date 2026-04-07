# -*- coding: utf-8 -*-
"""CLI subcommand tests via click.testing.CliRunner (no real lark-cli needed)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from lark_agent_bridge.cli import main
from lark_agent_bridge.core.detect import DetectReport, LarkCliAuthInfo


def _mock_report(*, all_ok: bool = True) -> DetectReport:
    r = DetectReport()
    r.python_ok = True
    r.python_version = "3.12.0"
    r.copaw_installed = True
    r.copaw_version = "1.0.2b1"
    r.node_ok = True
    r.node_version = "20.0.0"
    r.npm_ok = True
    r.npm_version = "10.0.0"
    if all_ok:
        r.lark_cli_path = "/usr/bin/lark-cli"
        r.lark_cli_version = "1.0.0"
        r.lark_config_ok = True
        r.lark_auth = LarkCliAuthInfo(raw={"tokenStatus": "valid"}, token_ok=True)
    return r


class TestVersion:
    def test_version_flag(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "lark-bridge" in result.output


class TestStatus:
    @patch("lark_agent_bridge.cli.detect.run_full_detect", return_value=_mock_report())
    def test_status_prints_environment(self, mock_detect):
        runner = CliRunner()
        result = runner.invoke(main, ["status"])
        assert result.exit_code == 0
        assert "Python" in result.output


class TestDoctor:
    @patch("lark_agent_bridge.cli.detect.run_full_detect", return_value=_mock_report())
    def test_doctor_runs(self, mock_detect):
        runner = CliRunner()
        result = runner.invoke(main, ["doctor"])
        assert result.exit_code == 0


class TestVerify:
    @patch("lark_agent_bridge.cli.detect.which_lark_cli", return_value=None)
    def test_verify_no_cli(self, mock_which):
        runner = CliRunner()
        result = runner.invoke(main, ["verify"])
        assert result.exit_code != 0

    @patch("lark_agent_bridge.cli.self_check.run_verify_suite")
    @patch("lark_agent_bridge.cli.detect.which_lark_cli", return_value="/usr/bin/lark-cli")
    def test_verify_with_cli(self, mock_which, mock_suite):
        from lark_agent_bridge.self_check import StepResult
        mock_suite.return_value = [
            StepResult(name="--version", ok=True, detail="1.0.0"),
            StepResult(name="--help", ok=True, detail="ok"),
            StepResult(name="config show", ok=True, detail="parsed appId"),
            StepResult(name="auth status", ok=True, detail="ok"),
            StepResult(name="doctor", ok=True, detail="ok"),
        ]
        runner = CliRunner()
        result = runner.invoke(main, ["verify"])
        assert result.exit_code == 0


class TestFix:
    @patch("lark_agent_bridge.cli.detect.run_full_detect", return_value=_mock_report())
    @patch("lark_agent_bridge.cli.detect.resolve_workspace")
    @patch("lark_agent_bridge.cli.copaw_rt.deploy_to_workspace")
    def test_fix_deploys(self, mock_deploy, mock_resolve, mock_detect, tmp_path):
        ws = tmp_path / "workspaces" / "default"
        ws.mkdir(parents=True)
        skills_dir = ws / "skills" / "lark_cli_bridge"
        skills_dir.mkdir(parents=True)
        (skills_dir / "SKILL.md").write_text("test", encoding="utf-8")
        mock_resolve.return_value = [ws]
        mock_deploy.return_value = skills_dir

        runner = CliRunner()
        result = runner.invoke(main, ["fix", "-y"])
        assert result.exit_code == 0


class TestUninstall:
    @patch("lark_agent_bridge.cli.detect.resolve_workspace")
    @patch("lark_agent_bridge.cli.copaw_rt.undeploy_from_workspace")
    def test_uninstall_skill_only(self, mock_undeploy, mock_resolve, tmp_path):
        ws = tmp_path / "workspaces" / "default"
        ws.mkdir(parents=True)
        mock_resolve.return_value = [ws]

        runner = CliRunner()
        result = runner.invoke(main, ["uninstall", "--skill-only", "-y"])
        assert result.exit_code == 0
        mock_undeploy.assert_called_once()
