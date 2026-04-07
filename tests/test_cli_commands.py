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

    @patch("lark_agent_bridge.cli.detect.resolve_workspace")
    @patch("lark_agent_bridge.cli.copaw_rt.undeploy_from_workspace")
    @patch("lark_agent_bridge.cli.detect.lark_cli_config_dir")
    def test_uninstall_purge_lark_cli_config(
        self,
        mock_cfg_dir,
        mock_undeploy,
        mock_resolve,
        tmp_path,
    ):
        ws = tmp_path / "workspaces" / "default"
        ws.mkdir(parents=True)
        mock_resolve.return_value = [ws]

        cfg = tmp_path / ".lark-cli"
        cfg.mkdir(parents=True)
        (cfg / "config.json").write_text("{}", encoding="utf-8")
        mock_cfg_dir.return_value = cfg

        runner = CliRunner()
        result = runner.invoke(main, ["uninstall", "--skill-only", "-y", "--purge-lark-cli-config"])
        assert result.exit_code == 0
        assert not cfg.exists()
        mock_undeploy.assert_called_once()


class TestSetupInteractiveGuidance:
    @patch("lark_agent_bridge.cli.detect.run_full_detect")
    @patch("lark_agent_bridge.cli.detect.which_lark_cli", return_value="/usr/bin/lark-cli")
    @patch("lark_agent_bridge.cli.detect.which_npm", return_value=(True, "10.0.0"))
    @patch("lark_agent_bridge.cli.detect.which_node", return_value=(True, "20.0.0"))
    @patch("lark_agent_bridge.cli.detect.pip_show_copaw", return_value=(True, "1.0.2b1"))
    @patch("lark_agent_bridge.cli.detect.python_info", return_value=(True, "3.12.0"))
    def test_setup_stops_when_config_missing(
        self,
        _mock_py,
        _mock_copaw,
        _mock_node,
        _mock_npm,
        _mock_which,
        mock_detect,
    ):
        r = DetectReport()
        r.lark_config_ok = False
        r.lark_auth = LarkCliAuthInfo(raw={}, token_ok=False)
        mock_detect.return_value = r

        runner = CliRunner()
        result = runner.invoke(main, ["setup", "-y"])
        assert result.exit_code == 2
        assert "lark-cli config init --new" in result.output
        assert "lark-bridge setup --skip-lark-check" in result.output


class TestSetupAutoInstallLarkCli:
    @patch("lark_agent_bridge.cli.detect.resolve_workspace")
    @patch("lark_agent_bridge.cli.copaw_rt.deploy_to_workspace")
    @patch("lark_agent_bridge.cli.detect.run_full_detect", return_value=_mock_report())
    @patch("lark_agent_bridge.cli.install.npm_install_lark_cli_global", return_value=(True, "ok"))
    @patch("lark_agent_bridge.cli.detect.which_lark_cli", side_effect=[None, "/usr/bin/lark-cli"])
    @patch("lark_agent_bridge.cli.detect.which_npm", return_value=(True, "10.0.0"))
    @patch("lark_agent_bridge.cli.detect.which_node", return_value=(True, "20.0.0"))
    @patch("lark_agent_bridge.cli.detect.pip_show_copaw", return_value=(True, "1.0.2b1"))
    @patch("lark_agent_bridge.cli.detect.python_info", return_value=(True, "3.12.0"))
    def test_setup_auto_installs_lark_cli_when_missing(
        self,
        _mock_py,
        _mock_copaw,
        _mock_node,
        _mock_npm,
        _mock_which_lark,
        mock_install_lark,
        _mock_detect,
        mock_deploy,
        mock_resolve,
        tmp_path,
    ):
        ws = tmp_path / "workspaces" / "default"
        ws.mkdir(parents=True)
        mock_resolve.return_value = [ws]
        mock_deploy.return_value = ws / "skills" / "lark_cli_bridge"

        runner = CliRunner()
        result = runner.invoke(main, ["setup", "-y"])

        assert result.exit_code == 0
        assert "正在自动安装 lark-cli" in result.output
        mock_install_lark.assert_called_once()


class TestUpgradeAndPerms:
    @patch("lark_agent_bridge.cli.detect.resolve_workspace")
    @patch("lark_agent_bridge.cli.copaw_rt.deploy_to_workspace")
    @patch("lark_agent_bridge.cli.detect.run_full_detect", return_value=_mock_report())
    def test_upgrade_runs_and_prints_next_step(self, _mock_detect, mock_deploy, mock_resolve, tmp_path):
        ws = tmp_path / "workspaces" / "default"
        ws.mkdir(parents=True)
        mock_resolve.return_value = [ws]
        mock_deploy.return_value = ws / "skills" / "lark_cli_bridge"

        runner = CliRunner()
        result = runner.invoke(main, ["upgrade"])
        assert result.exit_code == 0
        assert "下一步建议：lark-bridge status" in result.output

    @patch("lark_agent_bridge.cli.detect.which_lark_cli", return_value="/usr/bin/lark-cli")
    @patch("lark_agent_bridge.cli.permissions.check_scopes", return_value={"wiki:wiki:readonly": False})
    def test_perms_check_missing_scope_guidance(self, _mock_check, _mock_which):
        runner = CliRunner()
        result = runner.invoke(main, ["perms", "check", "--scope", "wiki:wiki:readonly"])
        assert result.exit_code == 2
        assert "auth login --scope" in result.output

    @patch("lark_agent_bridge.cli.detect.which_lark_cli", return_value=None)
    def test_perms_sync_no_lark_cli(self, _mock_which):
        runner = CliRunner()
        result = runner.invoke(main, ["perms", "sync"])
        assert result.exit_code == 1
