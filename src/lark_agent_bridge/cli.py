# -*- coding: utf-8 -*-
"""CLI entry: lark-bridge."""

from __future__ import annotations

import shutil
import sys

import click

from lark_agent_bridge import SKILL_DIR_NAME, __version__
from lark_agent_bridge.core import detect, install
from lark_agent_bridge.manifest.merge import load_manifest
from lark_agent_bridge.runtimes import copaw as copaw_rt
from lark_agent_bridge import self_check


def _print_header(title: str) -> None:
    click.echo()
    click.secho(f"  {title}", fg="cyan", bold=True)
    click.echo()


@click.group(invoke_without_command=True)
@click.version_option(__version__, prog_name="lark-bridge")
@click.pass_context
def main(ctx: click.Context) -> None:
    """Lark Agent Bridge — 将 lark-cli 能力接入 CoPaw。"""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@main.command("setup")
@click.option("--workspace", "-w", default=None, help="CoPaw 工作区目录名，默认 default")
@click.option(
    "--all-workspaces",
    is_flag=True,
    help="为 ~/.copaw/workspaces 下所有工作区安装技能",
)
@click.option("--cn", is_flag=True, help="使用国内 npm 镜像（npmmirror）")
@click.option("-y", "--yes", "assume_yes", is_flag=True, help="非交互：默认同意安装命令")
@click.option(
    "--force",
    is_flag=True,
    help="覆盖已存在的技能目录并重新合并 skill.json",
)
@click.option(
    "--skip-lark-check",
    is_flag=True,
    help="跳过 lark-cli 安装与登录检测，仅部署技能（你已自行配置好 lark-cli）",
)
def setup_cmd(
    workspace: str | None,
    all_workspaces: bool,
    cn: bool,
    assume_yes: bool,
    force: bool,
    skip_lark_check: bool,
) -> None:
    """一键检查环境、安装 lark-cli（可选）、并把技能写入 CoPaw 工作区。"""
    _print_header("lark-bridge setup")

    report = detect.run_full_detect()

    def _ok(msg: str) -> None:
        click.secho(f"  [✓] {msg}", fg="green")

    def _warn(msg: str) -> None:
        click.secho(f"  [!] {msg}", fg="yellow")

    def _err(msg: str) -> None:
        click.secho(f"  [×] {msg}", fg="red")

    py_ok, py_ver = detect.python_info()
    if py_ok:
        _ok(f"Python {py_ver}")
    else:
        _err(f"Python 版本过低: {py_ver}，需要 >= 3.10")
        raise SystemExit(1)

    copaw_ok, copaw_ver = detect.pip_show_copaw()
    if copaw_ok:
        _ok(f"CoPaw 包已安装 ({copaw_ver or '?'})")
    else:
        _warn("未检测到 copaw（pip show copaw）")
        if assume_yes or click.confirm("是否现在执行 pip install -U copaw？", default=True):
            ok, msg = install.pip_install_copaw_upgrade()
            if ok:
                _ok("pip install -U copaw 完成")
            else:
                _err(msg)
                raise SystemExit(1)
        else:
            raise SystemExit(1)

    if not skip_lark_check:
        node_ok, node_ver = detect.which_node()
        npm_ok, npm_ver = detect.which_npm()
        if node_ok:
            _ok(f"Node.js v{node_ver}")
        else:
            _err("未找到 Node.js。请先安装: https://nodejs.org/ （Windows 可用 winget install OpenJS.NodeJS.LTS）")
            raise SystemExit(1)
        if npm_ok:
            _ok(f"npm {npm_ver}")
        else:
            _err("未找到 npm")
            raise SystemExit(1)
    else:
        _warn("已跳过 Node/npm 与 lark-cli 检测（--skip-lark-check），仅部署技能文件")

    if not skip_lark_check:
        path = detect.which_lark_cli()
        if not path:
            _warn("未找到 lark-cli")
            if assume_yes or click.confirm("是否执行 npm install -g @larksuite/cli ？", default=True):
                ok, msg = install.npm_install_lark_cli_global(cn_mirror=cn)
                if ok:
                    _ok("lark-cli 安装流程完成")
                else:
                    _err(msg)
                    raise SystemExit(1)
            else:
                raise SystemExit(1)
            report = detect.run_full_detect()

        path = detect.which_lark_cli()
        if not path:
            _err("安装后仍未找到 lark-cli，请确认 npm 全局 bin 在 PATH 中")
            raise SystemExit(1)
        _ok(f"lark-cli: {path}")

        report = detect.run_full_detect()
        if not report.lark_config_ok:
            _warn("未检测到有效的 lark-cli 应用配置")
            click.echo("  请在终端执行（将打开浏览器完成配置）：")
            click.echo(click.style("    lark-cli config init --new", fg="bright_white"))
            if not assume_yes:
                click.pause("  完成后按 Enter 继续…")
            report = detect.run_full_detect()
            if not report.lark_config_ok:
                _err("仍未检测到配置，请确认 config 成功后再运行 lark-bridge setup --skip-lark-check")
                raise SystemExit(1)

        report = detect.run_full_detect()
        if report.lark_auth and not report.lark_auth.token_ok:
            _warn("lark-cli 登录状态可能无效或已过期")
            click.echo("  请在终端执行：")
            click.echo(click.style("    lark-cli auth login --recommend", fg="bright_white"))
            if not assume_yes:
                click.pause("  完成后按 Enter 继续…")

    workspaces = detect.resolve_workspace(workspace, all_workspaces=all_workspaces)
    if not workspaces:
        _err("未找到 CoPaw 工作区。请确认已运行 copaw init，且存在 ~/.copaw/workspaces/default")
        raise SystemExit(1)

    for ws in workspaces:
        click.echo()
        click.secho(f"  部署到工作区: {ws}", fg="magenta")
        try:
            copaw_rt.deploy_to_workspace(ws, force=force)
            _ok(f"已写入 {ws / 'skills' / SKILL_DIR_NAME} 与 skill.json")
        except OSError as e:
            _err(str(e))
            raise SystemExit(1) from e

    click.echo()
    click.secho(
        "  完成。请在 CoPaw 控制台新开对话，并在技能中启用 "
        + SKILL_DIR_NAME
        + "（若未启用）。",
        fg="green",
        bold=True,
    )
    click.echo()


@main.command("status")
@click.option("--all-workspaces", is_flag=True, help="列出所有工作区路径")
def status_cmd(all_workspaces: bool) -> None:
    """查看环境与技能状态。"""
    report = detect.run_full_detect()
    click.echo(f"Python: {report.python_version}  {'✓' if report.python_ok else '✗'}")
    click.echo(
        f"CoPaw:  {report.copaw_version or '—'}  {'✓' if report.copaw_installed else '✗'}",
    )
    click.echo(
        f"Node:   {report.node_version or '—'}  {'✓' if report.node_ok else '✗'}",
    )
    click.echo(
        f"npm:    {report.npm_version or '—'}  {'✓' if report.npm_ok else '✗'}",
    )
    if report.lark_cli_path:
        click.echo(f"lark-cli: {report.lark_cli_path} ({report.lark_cli_version}) ✓")
    else:
        click.echo("lark-cli: — ✗")
    click.echo(
        f"飞书应用配置: {'已配置' if report.lark_config_ok else '未配置'}",
    )
    if report.lark_auth:
        click.echo(
            f"登录状态: {'正常' if report.lark_auth.token_ok else '需重新登录'}",
        )
    ws_list = detect.list_copaw_workspaces()
    if all_workspaces:
        for p in ws_list:
            click.echo(f"  工作区: {p.name} -> {p}")
    default = detect.copaw_working_dir() / "workspaces" / "default"
    skill_dir = default / "skills" / SKILL_DIR_NAME
    manifest = load_manifest(default / "skill.json")
    ent = manifest.get("skills", {}).get(SKILL_DIR_NAME)
    if ent:
        click.echo(
            f"技能 {SKILL_DIR_NAME}: enabled={ent.get('enabled')} channels={ent.get('channels')}",
        )
    else:
        click.echo(f"技能 {SKILL_DIR_NAME}: 未在 skill.json 中注册")
    click.echo(f"技能目录存在: {skill_dir.exists()} ({skill_dir})")


@main.command("fix")
@click.option("--workspace", "-w", default=None)
@click.option("--all-workspaces", is_flag=True)
@click.option("-y", "--yes", "assume_yes", is_flag=True)
def fix_cmd(workspace: str | None, all_workspaces: bool, assume_yes: bool) -> None:
    """尝试修复：补全技能文件、合并 skill.json。"""
    workspaces = detect.resolve_workspace(workspace, all_workspaces=all_workspaces)
    if not workspaces:
        click.echo("未找到工作区", err=True)
        raise SystemExit(1)
    for ws in workspaces:
        skill_dir = ws / "skills" / SKILL_DIR_NAME
        if not skill_dir.is_dir() or not (skill_dir / "SKILL.md").exists():
            click.echo(f"补全技能: {ws}")
            copaw_rt.deploy_to_workspace(ws, force=True)
        else:
            click.echo(f"合并 skill.json: {ws}")
            copaw_rt.deploy_to_workspace(ws, force=False)
    report = detect.run_full_detect()
    if report.lark_auth and not report.lark_auth.token_ok:
        click.echo("请执行: lark-cli auth login --recommend")


@main.command("update")
@click.option("--workspace", "-w", default=None)
@click.option("--all-workspaces", is_flag=True)
def update_cmd(workspace: str | None, all_workspaces: bool) -> None:
    """更新技能文件（merge 时会保留 skill.json 中已有 config）。"""
    workspaces = detect.resolve_workspace(workspace, all_workspaces=all_workspaces)
    if not workspaces:
        raise SystemExit(1)
    for ws in workspaces:
        copaw_rt.deploy_to_workspace(ws, force=True)
    click.echo("已更新技能模板。")


@main.command("uninstall")
@click.option("--skill-only", is_flag=True, help="只移除 CoPaw 技能，不卸载 npm 包")
@click.option("-y", "--yes", "assume_yes", is_flag=True)
@click.option("--workspace", "-w", default=None)
@click.option("--all-workspaces", is_flag=True)
def uninstall_cmd(
    skill_only: bool,
    assume_yes: bool,
    workspace: str | None,
    all_workspaces: bool,
) -> None:
    """移除技能目录与 skill.json 条目；可选卸载 @larksuite/cli。"""
    if not assume_yes:
        click.confirm("确认卸载 Lark Agent Bridge 技能？", abort=True)
    workspaces = detect.resolve_workspace(workspace, all_workspaces=all_workspaces)
    for ws in workspaces:
        copaw_rt.undeploy_from_workspace(ws)
        click.echo(f"已移除: {ws}")
    if not skill_only:
        npm_cands = detect.npm_executable_candidates()
        npm = npm_cands[0] if npm_cands else None
        if npm and (assume_yes or click.confirm("是否卸载全局 npm 包 @larksuite/cli？", default=False)):
            import subprocess

            subprocess.run([npm, "uninstall", "-g", "@larksuite/cli"], check=False)
    click.echo("完成。卸载本工具请执行: pip uninstall lark-agent-bridge")


@main.command("doctor")
def doctor_cmd() -> None:
    """输出详细诊断信息。"""
    import platform

    report = detect.run_full_detect()
    click.echo("=== Lark Agent Bridge doctor ===")
    click.echo(f"bridge 版本: {__version__}")
    click.echo(f"OS: {platform.system()} {platform.release()} {platform.machine()}")
    click.echo(f"Python: {report.python_version} exe={sys.executable}")
    click.echo(f"CoPaw pip: {report.copaw_installed} {report.copaw_version}")
    click.echo(f"Node: {report.node_ok} {report.node_version}")
    click.echo(f"npm: {report.npm_ok} {report.npm_version}")
    click.echo(f"lark-cli: {report.lark_cli_path}")
    click.echo(f"lark-cli version string: {report.lark_cli_version}")
    click.echo(f"config ok: {report.lark_config_ok} ({report.lark_config_hint})")
    if report.lark_auth:
        click.echo(f"auth raw: {report.lark_auth.raw}")
    if report.errors:
        click.echo("issues:")
        for e in report.errors:
            click.echo(f"  - {e}")
    click.echo(f"COPAW root: {detect.copaw_working_dir()}")


@main.command("verify")
def verify_cmd() -> None:
    """对 lark-cli 做本地冒烟（version、help、config、auth、doctor）。需已安装 lark-cli。"""
    exe = detect.which_lark_cli()
    if not exe:
        click.secho("未找到 lark-cli，请先: npm install -g @larksuite/cli", fg="red", err=True)
        raise SystemExit(1)
    click.echo(f"使用: {exe}\n")
    steps = self_check.run_verify_suite(exe)
    click.echo(self_check.format_report(steps))
    soft = {"config show", "auth status"}
    failed_hard = [s for s in steps if not s.ok and s.name not in soft]
    soft_fail = [s for s in steps if not s.ok and s.name in soft]
    if failed_hard:
        click.secho(
            f"\n关键项失败 {len(failed_hard)} 个（--version / --help / doctor）。请重装或检查 PATH。",
            fg="red",
        )
        raise SystemExit(2)
    if soft_fail:
        click.secho(
            "\nconfig / auth 未就绪属正常（需 lark-cli config 与 auth login）。",
            fg="yellow",
        )
    click.secho("\nCLI 本体可用；请在完成飞书配置后于 CoPaw 中试用。", fg="green")


# README 中的 install 与 setup 对齐
main.add_command(setup_cmd, name="install")


if __name__ == "__main__":
    main()
