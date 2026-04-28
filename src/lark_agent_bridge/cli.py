# -*- coding: utf-8 -*-
"""CLI entry: lark-bridge."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import click

from lark_agent_bridge import SKILL_DIR_NAME, __version__
from lark_agent_bridge.core import exit_codes
from lark_agent_bridge.core import detect, install, permissions
from lark_agent_bridge.manifest.merge import load_manifest
from lark_agent_bridge.runtimes import copaw as copaw_rt
from lark_agent_bridge import self_check
from lark_agent_bridge import cli_forward


def _print_header(title: str) -> None:
    click.echo()
    click.secho(f"  {title}", fg="cyan", bold=True)
    click.echo()


def _fail_with_guidance(
    reason: str,
    *,
    commands: list[str] | None = None,
    checks: list[str] | None = None,
    exit_code: int = exit_codes.E_FAILED,
    error_code: str | None = None,
) -> None:
    click.echo()
    prefix = "  [×]"
    if error_code:
        prefix += f"[{error_code}]"
    click.secho(f"{prefix} {reason}", fg="red", err=True)
    if commands:
        click.secho("  建议执行：", fg="yellow")
        for cmd in commands:
            click.echo(click.style(f"    {cmd}", fg="bright_white"))
    if checks:
        click.secho("  建议检查：", fg="yellow")
        for item in checks:
            click.echo(f"    - {item}")
    raise SystemExit(exit_code)


def _resolve_workspaces_or_exit(
    workspace: str | None,
    all_workspaces: bool,
    *,
    action: str = "执行操作",
) -> list[Path]:
    if workspace and all_workspaces:
        _fail_with_guidance(
            f"{action}失败：不能同时使用 --workspace 和 --all-workspaces。",
            commands=[
                "lark-bridge status --workspace <工作区名>",
                "lark-bridge status --all-workspaces",
            ],
            error_code="LAB-CLI-001",
        )
    workspaces = detect.resolve_workspace(workspace, all_workspaces=all_workspaces)
    if not workspaces:
        _fail_with_guidance(
            f"{action}失败：未找到 QwenPaw 工作区。",
            commands=[
                "qwenpaw init --defaults",
                "qwenpaw init",
                "copaw init",
                "lark-bridge status --all-workspaces",
            ],
            checks=[
                "确认 ~/.qwenpaw/workspaces 或 ~/.copaw/workspaces 下存在至少一个工作区目录",
                "若使用了自定义路径，请检查 QWENPAW_WORKING_DIR / COPAW_WORKING_DIR 环境变量",
            ],
            error_code="LAB-CLI-002",
        )
    return workspaces


def _sync_permissions_for_workspace(ws, lark_cli: str) -> Path | None:
    try:
        snap = permissions.build_snapshot(lark_cli)
        return permissions.write_snapshot(ws, snap)
    except OSError:
        return None


def _resume_command(workspace: str | None, all_workspaces: bool, *, force: bool) -> str:
    parts = ["lark-bridge", "resume"]
    if workspace:
        parts += ["--workspace", workspace]
    if all_workspaces:
        parts.append("--all-workspaces")
    if force:
        parts.append("--force")
    return " ".join(parts)


def _create_backup_or_fail(ws: Path, *, reason: str, keep_last: int) -> Path:
    try:
        return copaw_rt.create_workspace_backup(ws, reason=reason, keep_last=keep_last)
    except OSError as e:
        _fail_with_guidance(
            f"创建备份失败: {e}",
            commands=[
                f"lark-bridge backups list --workspace {ws.name}",
                f"lark-bridge backups cleanup --workspace {ws.name} --keep {keep_last}",
            ],
            error_code="LAB-BACKUP-001",
        )


@click.group(invoke_without_command=True)
@click.version_option(__version__, prog_name="lark-bridge")
@click.pass_context
def main(ctx: click.Context) -> None:
    """Lark Agent Bridge — 将 lark-cli 能力接入 QwenPaw（兼容 CoPaw）。"""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@main.command("setup")
@click.option("--workspace", "-w", default=None, help="QwenPaw 工作区目录名，默认 default")
@click.option(
    "--all-workspaces",
    is_flag=True,
    help="为 QwenPaw 工作区安装技能（自动兼容 ~/.qwenpaw 与 ~/.copaw）",
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
@click.option(
    "--no-install-lark-cli",
    is_flag=True,
    help="检测到缺少 lark-cli 时不自动安装（默认会自动安装）",
)
def setup_cmd(
    workspace: str | None,
    all_workspaces: bool,
    cn: bool,
    assume_yes: bool,
    force: bool,
    skip_lark_check: bool,
    no_install_lark_cli: bool,
) -> None:
    """一键检查环境、安装 lark-cli（可选）、并把技能写入 QwenPaw 工作区。"""
    _print_header("lark-bridge setup")

    report = detect.run_full_detect()

    def _ok(msg: str) -> None:
        click.secho(f"  [✓] {msg}", fg="green")

    def _warn(msg: str) -> None:
        click.secho(f"  [!] {msg}", fg="yellow")

    py_ok, py_ver = detect.python_info()
    if py_ok:
        _ok(f"Python {py_ver}")
    else:
        _fail_with_guidance(
            f"Python 版本过低: {py_ver}，需要 >= 3.10。",
            checks=["运行 `python --version` 确认当前终端使用的 Python", "升级到 Python 3.10+ 后重新执行 setup"],
            error_code="LAB-SETUP-001",
        )

    paw_ok, paw_ver, paw_pkg = detect.detect_paw_package()
    if paw_ok:
        pkg_hint = paw_pkg or "qwenpaw/copaw"
        _ok(f"QwenPaw 包已安装 ({pkg_hint} {paw_ver or '?'})")
    else:
        _warn("未检测到 qwenpaw/copaw（pip show qwenpaw 或 pip show copaw）")
        if assume_yes or click.confirm("是否现在执行 pip install -U qwenpaw？", default=True):
            ok, msg = install.pip_install_paw_upgrade()
            if ok:
                if "copaw" in msg:
                    _ok("已安装兼容包 copaw（建议后续迁移到 qwenpaw）")
                else:
                    _ok("pip install -U qwenpaw 完成")
            else:
                _fail_with_guidance(
                    msg,
                    commands=[
                        "python -m pip install -U qwenpaw",
                        "python -m pip install -U copaw",
                        "lark-bridge setup",
                    ],
                    error_code="LAB-SETUP-002",
                )
        else:
            _fail_with_guidance(
                "用户取消了 qwenpaw 安装，setup 已停止。",
                commands=[
                    "python -m pip install -U qwenpaw",
                    "python -m pip install -U copaw",
                    "lark-bridge setup",
                ],
                error_code="LAB-SETUP-002",
            )

    if not skip_lark_check:
        node_ok, node_ver = detect.which_node()
        npm_ok, npm_ver = detect.which_npm()
        if node_ok:
            _ok(f"Node.js v{node_ver}")
        else:
            _fail_with_guidance(
                "未找到 Node.js。",
                commands=[
                    "winget install OpenJS.NodeJS.LTS",
                    "lark-bridge setup",
                ],
                checks=["安装完成后请重新打开终端再执行命令"],
                error_code="LAB-SETUP-002",
            )
        if npm_ok:
            _ok(f"npm {npm_ver}")
        else:
            _fail_with_guidance(
                "未找到 npm。",
                commands=["node --version", "npm --version", "lark-bridge setup"],
                checks=["确认 Node.js 安装完整且 npm 在 PATH 中"],
                error_code="LAB-SETUP-002",
            )
    else:
        _warn("已跳过 Node/npm 与 lark-cli 检测（--skip-lark-check），仅部署技能文件")

    path: str | None = None
    if not skip_lark_check:
        path = detect.which_lark_cli()
        if not path:
            _warn("未找到 lark-cli")
            if no_install_lark_cli:
                _fail_with_guidance(
                    "已设置 --no-install-lark-cli，且当前缺少 lark-cli，无法继续。",
                    commands=[
                        "npm install -g @larksuite/cli",
                        "lark-bridge setup",
                    ],
                    error_code="LAB-SETUP-002",
                )
            click.echo("  正在自动安装 lark-cli（npm install -g @larksuite/cli）…")
            ok, msg = install.npm_install_lark_cli_global(cn_mirror=cn)
            if ok:
                _ok("lark-cli 安装流程完成")
            else:
                _fail_with_guidance(
                    msg,
                    commands=[
                        "npm install -g @larksuite/cli",
                        "lark-bridge setup --cn",
                    ],
                    checks=["确认 npm 全局安装权限和网络连通性"],
                    error_code="LAB-SETUP-002",
                )
            report = detect.run_full_detect()

        path = detect.which_lark_cli()
        if not path:
            _fail_with_guidance(
                "安装后仍未找到 lark-cli，请确认 npm 全局 bin 在 PATH 中。",
                commands=["npm bin -g", "lark-cli --version", "lark-bridge setup"],
                error_code="LAB-SETUP-002",
            )
        _ok(f"lark-cli: {path}")
        cli_ver = detect.lark_cli_version(path)
        if detect.lark_cli_meets_recommended(cli_ver) is False:
            _warn(
                "当前 lark-cli 版本低于建议版本 "
                + detect.RECOMMENDED_LARK_CLI_VERSION
                + "，部分 slides/attendance/新版 auth 能力可能不可用",
            )

        report = detect.run_full_detect()
        if not report.lark_config_ok:
            _warn("未检测到有效的 lark-cli 应用配置")
            click.echo("  请先在终端执行（将打开浏览器完成配置）：")
            click.echo(click.style("    lark-cli config init --new", fg="bright_white"))
            click.echo("  完成后再运行：")
            click.echo(click.style(f"    {_resume_command(workspace, all_workspaces, force=force)}", fg="bright_white"))
            _fail_with_guidance(
                "当前未完成配置，已停止本次 setup。",
                commands=[
                    "lark-cli config init --new",
                    _resume_command(workspace, all_workspaces, force=force),
                ],
                exit_code=exit_codes.E_ACTION_REQUIRED,
                error_code="LAB-SETUP-003",
            )

        report = detect.run_full_detect()
        if report.lark_auth and not report.lark_auth.token_ok:
            _warn("lark-cli 登录状态可能无效或已过期")
            click.echo("  请先在终端执行：")
            click.echo(click.style("    lark-cli auth login --recommend", fg="bright_white"))
            click.echo("  完成后再运行：")
            click.echo(click.style(f"    {_resume_command(workspace, all_workspaces, force=force)}", fg="bright_white"))
            _fail_with_guidance(
                "当前未完成登录，已停止本次 setup。",
                commands=[
                    "lark-cli auth login --recommend",
                    _resume_command(workspace, all_workspaces, force=force),
                ],
                exit_code=exit_codes.E_ACTION_REQUIRED,
                error_code="LAB-SETUP-004",
            )

    workspaces = _resolve_workspaces_or_exit(workspace, all_workspaces, action="setup")

    for ws in workspaces:
        click.echo()
        click.secho(f"  部署到工作区: {ws}", fg="magenta")
        try:
            copaw_rt.deploy_to_workspace(ws, force=force)
            _ok(f"已写入 {ws / 'skills' / SKILL_DIR_NAME} 与 skill.json")
            if path and not skip_lark_check:
                snap_path = _sync_permissions_for_workspace(ws, path)
                if snap_path:
                    click.echo(f"  已写入权限快照: {snap_path}")
                else:
                    _warn("权限快照写入失败（不影响安装）")
        except OSError as e:
            _fail_with_guidance(
                f"写入工作区失败: {e}",
                commands=["lark-bridge doctor", "lark-bridge fix"],
                error_code="LAB-DEPLOY-001",
            )

    click.echo()
    click.secho(
        "  完成。请在 QwenPaw 控制台新开对话，并在技能中启用 "
        + SKILL_DIR_NAME
        + "（若未启用）。",
        fg="green",
        bold=True,
    )
    click.echo()


@main.command("resume")
@click.option("--workspace", "-w", default=None, help="QwenPaw 工作区目录名，默认 default")
@click.option("--all-workspaces", is_flag=True, help="对所有工作区继续部署")
@click.option("--force", is_flag=True, help="覆盖已存在的技能目录并重新写入")
def resume_cmd(workspace: str | None, all_workspaces: bool, force: bool) -> None:
    """在浏览器完成 config/auth 后继续部署技能。"""
    _print_header("lark-bridge resume")
    report = detect.run_full_detect()
    if not report.lark_cli_path:
        _fail_with_guidance(
            "未找到 lark-cli，无法继续。",
            commands=["npm install -g @larksuite/cli", "lark-bridge setup"],
            error_code="LAB-SETUP-002",
        )
    if not report.lark_config_ok:
        _fail_with_guidance(
            "尚未完成 lark-cli 应用配置。",
            commands=["lark-cli config init --new", _resume_command(workspace, all_workspaces, force=force)],
            exit_code=exit_codes.E_ACTION_REQUIRED,
            error_code="LAB-SETUP-003",
        )
    if not report.lark_auth or not report.lark_auth.token_ok:
        _fail_with_guidance(
            "尚未完成 lark-cli 登录或登录已过期。",
            commands=["lark-cli auth login --recommend", _resume_command(workspace, all_workspaces, force=force)],
            exit_code=exit_codes.E_ACTION_REQUIRED,
            error_code="LAB-SETUP-004",
        )

    workspaces = _resolve_workspaces_or_exit(workspace, all_workspaces, action="resume")
    for ws in workspaces:
        click.secho(f"  继续部署工作区: {ws}", fg="magenta")
        try:
            copaw_rt.deploy_to_workspace(ws, force=force)
            snap_path = _sync_permissions_for_workspace(ws, report.lark_cli_path)
            click.secho(f"  [✓] 已更新技能: {ws / 'skills' / SKILL_DIR_NAME}", fg="green")
            if snap_path:
                click.echo(f"  已刷新权限快照: {snap_path}")
        except OSError as e:
            _fail_with_guidance(
                f"继续部署失败: {e}",
                commands=["lark-bridge doctor", "lark-bridge fix"],
                error_code="LAB-DEPLOY-001",
            )

    click.echo()
    click.secho("  完成。下一步建议：lark-bridge status", fg="green", bold=True)
    click.echo()


@main.command("status")
@click.option("--workspace", "-w", default=None, help="只查看指定工作区")
@click.option("--all-workspaces", is_flag=True, help="列出并检查所有工作区")
@click.option("--refresh-perms", is_flag=True, help="实时刷新权限快照（会调用 lark-cli auth）")
def status_cmd(workspace: str | None, all_workspaces: bool, refresh_perms: bool) -> None:
    """查看环境与技能状态。"""
    report = detect.run_full_detect()
    click.echo(f"Python: {report.python_version}  {'✓' if report.python_ok else '✗'}")
    click.echo(
        f"QwenPaw: {report.copaw_version or '—'}"
        + (f" ({report.paw_package})" if report.paw_package else "")
        + f"  {'✓' if report.copaw_installed else '✗'}",
    )
    click.echo(
        f"Node:   {report.node_version or '—'}  {'✓' if report.node_ok else '✗'}",
    )
    click.echo(
        f"npm:    {report.npm_version or '—'}  {'✓' if report.npm_ok else '✗'}",
    )
    if report.lark_cli_path:
        click.echo(f"lark-cli: {report.lark_cli_path} ({report.lark_cli_version}) ✓")
        if report.lark_cli_recommended is False:
            click.secho(
                f"  建议升级 lark-cli >= {detect.RECOMMENDED_LARK_CLI_VERSION}: npm install -g @larksuite/cli",
                fg="yellow",
            )
    else:
        click.echo("lark-cli: — ✗")
    click.echo(
        f"飞书应用配置: {'已配置' if report.lark_config_ok else '未配置'}",
    )
    if report.lark_auth:
        click.echo(
            f"登录状态: {'正常' if report.lark_auth.token_ok else '需重新登录'}",
        )
    workspaces = _resolve_workspaces_or_exit(workspace, all_workspaces, action="status")
    click.echo()
    for ws in workspaces:
        click.secho(f"[workspace] {ws.name}", fg="cyan")
        click.echo(f"  path: {ws}")
        skill_dir = ws / "skills" / SKILL_DIR_NAME
        manifest = load_manifest(ws / "skill.json")
        ent = manifest.get("skills", {}).get(SKILL_DIR_NAME)
        if ent:
            click.echo(
                f"  技能注册: enabled={ent.get('enabled')} channels={ent.get('channels')}",
            )
        else:
            click.echo(f"  技能注册: 未在 skill.json 中注册 {SKILL_DIR_NAME}")
        click.echo(f"  技能目录: {'存在' if skill_dir.exists() else '缺失'} ({skill_dir})")
        if report.lark_cli_path and refresh_perms:
            p = _sync_permissions_for_workspace(ws, report.lark_cli_path)
            if p:
                click.echo(f"  权限快照: 已刷新 ({p})")
            else:
                click.echo("  权限快照: 刷新失败")
        snap = permissions.read_snapshot(ws)
        if snap:
            summary = snap.get("summary", {})
            click.echo(
                "  权限快照: "
                + f"app_scopes={summary.get('app_scope_count', 0)}, "
                + f"checked_ok={summary.get('checked_ok_count', 0)}/{summary.get('checked_total', 0)}",
            )
        else:
            click.echo("  权限快照: 未生成（可运行 `lark-bridge perms sync`）")
        click.echo()


@main.command("fix")
@click.option("--workspace", "-w", default=None)
@click.option("--all-workspaces", is_flag=True)
@click.option("-y", "--yes", "assume_yes", is_flag=True)
def fix_cmd(workspace: str | None, all_workspaces: bool, assume_yes: bool) -> None:
    """尝试修复：补全技能文件、合并 skill.json。"""
    _ = assume_yes
    workspaces = _resolve_workspaces_or_exit(workspace, all_workspaces, action="fix")
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
@click.option(
    "--backup-keep",
    type=click.IntRange(1, 200),
    default=copaw_rt.DEFAULT_BACKUP_KEEP,
    show_default=True,
    help="每个工作区最多保留多少份最近备份",
)
def update_cmd(workspace: str | None, all_workspaces: bool, backup_keep: int) -> None:
    """更新技能文件（merge 时会保留 skill.json 中已有 config）。"""
    workspaces = _resolve_workspaces_or_exit(workspace, all_workspaces, action="update")
    for ws in workspaces:
        backup = _create_backup_or_fail(ws, reason="update", keep_last=backup_keep)
        click.echo(f"已创建备份: {backup.name}")
        try:
            copaw_rt.deploy_to_workspace(ws, force=True)
            click.echo(f"已更新技能模板: {ws}")
        except OSError as e:
            _fail_with_guidance(
                f"更新失败: {e}",
                commands=[f"lark-bridge rollback --workspace {ws.name} --backup-id {backup.name}"],
                error_code="LAB-DEPLOY-001",
            )


@main.command("rollback")
@click.option("--workspace", "-w", default=None, help="回滚指定工作区")
@click.option("--all-workspaces", is_flag=True, help="回滚所有工作区")
@click.option(
    "--backup-id",
    default="latest",
    help="备份目录名，默认 latest 表示最近一次备份",
)
def rollback_cmd(workspace: str | None, all_workspaces: bool, backup_id: str) -> None:
    """将工作区恢复到最近一次（或指定）备份。"""
    workspaces = _resolve_workspaces_or_exit(workspace, all_workspaces, action="rollback")
    for ws in workspaces:
        if backup_id == "latest":
            backups = copaw_rt.list_workspace_backups(ws)
            if not backups:
                _fail_with_guidance(
                    f"工作区 {ws.name} 没有可用备份。",
                    commands=[f"lark-bridge update --workspace {ws.name}"],
                    error_code="LAB-BACKUP-002",
                )
            chosen = backups[0]
        else:
            chosen = copaw_rt.backups_root(ws) / backup_id
            if not chosen.is_dir():
                _fail_with_guidance(
                    f"未找到备份: {chosen}",
                    commands=[f"lark-bridge rollback --workspace {ws.name} --backup-id latest"],
                    error_code="LAB-BACKUP-002",
                )
        try:
            copaw_rt.restore_workspace_backup(ws, chosen)
        except OSError as e:
            _fail_with_guidance(
                f"恢复备份失败: {e}",
                commands=[f"lark-bridge backups list --workspace {ws.name}"],
                error_code="LAB-BACKUP-001",
            )
        click.secho(f"[✓] 已回滚 {ws.name} <- {chosen.name}", fg="green")


@main.group("backups")
def backups_group() -> None:
    """备份管理（列表、清理）。"""


@backups_group.command("list")
@click.option("--workspace", "-w", default=None, help="查看指定工作区")
@click.option("--all-workspaces", is_flag=True, help="查看所有工作区")
def backups_list_cmd(workspace: str | None, all_workspaces: bool) -> None:
    """列出工作区备份。"""
    workspaces = _resolve_workspaces_or_exit(workspace, all_workspaces, action="backups list")
    for ws in workspaces:
        click.secho(f"[workspace] {ws.name}", fg="cyan")
        backups = copaw_rt.list_workspace_backups(ws)
        if not backups:
            click.echo("  (无备份)")
            continue
        for p in backups:
            click.echo(f"  - {p.name}")
        click.echo()


@backups_group.command("cleanup")
@click.option("--workspace", "-w", default=None, help="清理指定工作区")
@click.option("--all-workspaces", is_flag=True, help="清理所有工作区")
@click.option(
    "--keep",
    type=click.IntRange(1, 200),
    default=copaw_rt.DEFAULT_BACKUP_KEEP,
    show_default=True,
    help="保留最近多少份备份",
)
def backups_cleanup_cmd(workspace: str | None, all_workspaces: bool, keep: int) -> None:
    """清理旧备份，仅保留最近 N 份。"""
    workspaces = _resolve_workspaces_or_exit(workspace, all_workspaces, action="backups cleanup")
    for ws in workspaces:
        removed = copaw_rt.prune_workspace_backups(ws, keep_last=keep)
        click.echo(f"{ws.name}: 已删除 {len(removed)} 份旧备份，保留最近 {keep} 份")


def _print_qwenpaw_upgrade_guidance(report: detect.DetectReport) -> None:
    commands = detect.qwenpaw_upgrade_guidance(
        install_method=report.paw_install_method,
        package=report.paw_package,
        launcher_path=report.paw_launcher_path,
    )
    if report.paw_install_method == "script":
        click.echo("如需升级 QwenPaw（官方脚本安装）：")
    elif report.paw_install_method == "legacy-pip":
        click.echo("检测到旧 copaw 包，建议迁移到 QwenPaw：")
    else:
        click.echo("如需升级 QwenPaw（pip 安装）：")
    for cmd in commands:
        click.echo(f"  {cmd}")


@main.command("upgrade")
@click.option("--workspace", "-w", default=None)
@click.option("--all-workspaces", is_flag=True)
@click.option("--with-lark-cli", is_flag=True, help="同时尝试升级全局 lark-cli")
@click.option("--with-qwenpaw", is_flag=True, help="同时尝试升级 pip 安装的 QwenPaw")
@click.option("--cn", is_flag=True, help="升级 lark-cli 时使用国内 npm 镜像")
@click.option(
    "--backup-keep",
    type=click.IntRange(1, 200),
    default=copaw_rt.DEFAULT_BACKUP_KEEP,
    show_default=True,
    help="每个工作区最多保留多少份最近备份",
)
def upgrade_cmd(
    workspace: str | None,
    all_workspaces: bool,
    with_lark_cli: bool,
    with_qwenpaw: bool,
    cn: bool,
    backup_keep: int,
) -> None:
    """小白一键升级：更新技能模板并给出下一步。"""
    _print_header("lark-bridge upgrade")
    click.echo("建议先执行：pip install -U lark-agent-bridge")
    report = detect.run_full_detect()
    if with_qwenpaw:
        if report.paw_install_method == "script":
            click.secho("  [!] 检测到 QwenPaw 可能由官方脚本安装，本工具不自动执行远程脚本。", fg="yellow")
            _print_qwenpaw_upgrade_guidance(report)
        else:
            click.echo("正在尝试升级 QwenPaw（python -m pip install -U qwenpaw）…")
            ok, msg = install.pip_install_qwenpaw_upgrade()
            if ok:
                click.secho("  [✓] QwenPaw pip 升级完成", fg="green")
            else:
                _fail_with_guidance(
                    msg,
                    commands=detect.qwenpaw_upgrade_guidance(
                        install_method=report.paw_install_method,
                        package=report.paw_package,
                        launcher_path=report.paw_launcher_path,
                    ),
                    checks=["确认当前 Python 环境与 QwenPaw 安装环境一致"],
                    error_code="LAB-SETUP-002",
                )
    else:
        _print_qwenpaw_upgrade_guidance(report)

    if with_lark_cli:
        click.echo("正在尝试升级全局 lark-cli …")
        ok, msg = install.npm_install_lark_cli_global(cn_mirror=cn)
        if ok:
            click.secho("  [✓] lark-cli 升级流程完成", fg="green")
        else:
            _fail_with_guidance(
                msg,
                commands=["npm install -g @larksuite/cli", "lark-bridge upgrade"],
                checks=["确认网络与 npm 全局安装权限"],
                error_code="LAB-SETUP-002",
            )
    else:
        click.echo("如需升级 lark-cli，请执行：npm install -g @larksuite/cli")

    workspaces = _resolve_workspaces_or_exit(workspace, all_workspaces, action="upgrade")
    for ws in workspaces:
        backup = _create_backup_or_fail(ws, reason="upgrade", keep_last=backup_keep)
        click.echo(f"  已创建备份: {backup.name}")
        try:
            copaw_rt.deploy_to_workspace(ws, force=True)
            click.secho(f"  [✓] 已更新工作区技能: {ws}", fg="green")
        except OSError as e:
            _fail_with_guidance(
                f"升级失败: {e}",
                commands=[f"lark-bridge rollback --workspace {ws.name} --backup-id {backup.name}"],
                error_code="LAB-DEPLOY-001",
            )

    report = detect.run_full_detect()
    if not report.lark_config_ok:
        click.secho("  [!] 尚未完成飞书应用配置", fg="yellow")
        click.echo("      请执行：lark-cli config init --new")
    elif report.lark_auth and not report.lark_auth.token_ok:
        click.secho("  [!] 尚未完成飞书登录或登录已过期", fg="yellow")
        click.echo("      请执行：lark-cli auth login --recommend")
    click.echo("下一步建议：lark-bridge status")


@main.group("perms")
def perms_group() -> None:
    """权限快照与 scope 检查。"""


@perms_group.command("sync")
@click.option("--workspace", "-w", default=None)
@click.option("--all-workspaces", is_flag=True)
@click.option("--as", "actor", type=click.Choice(["user", "bot"]), default="user")
def perms_sync_cmd(workspace: str | None, all_workspaces: bool, actor: str) -> None:
    """实时拉取权限并写入工作区快照。"""
    exe = detect.which_lark_cli()
    if not exe:
        _fail_with_guidance(
            "未找到 lark-cli，请先安装并完成配置登录。",
            commands=["npm install -g @larksuite/cli", "lark-cli auth login --recommend"],
            error_code="LAB-PERMS-001",
        )
    workspaces = _resolve_workspaces_or_exit(workspace, all_workspaces, action="perms sync")
    for ws in workspaces:
        snap = permissions.build_snapshot(exe, actor=actor)
        p = permissions.write_snapshot(ws, snap)
        click.echo(f"已写入权限快照: {p}")
        summary = snap.get("summary", {})
        click.echo(
            f"  app_scopes={summary.get('app_scope_count', 0)}, "
            f"checked_ok={summary.get('checked_ok_count', 0)}/{summary.get('checked_total', 0)}",
        )


@perms_group.command("show")
@click.option("--workspace", "-w", default=None)
@click.option("--all-workspaces", is_flag=True)
@click.option("--refresh", is_flag=True, help="读取前先刷新一次快照")
def perms_show_cmd(workspace: str | None, all_workspaces: bool, refresh: bool) -> None:
    """展示权限快照。"""
    workspaces = _resolve_workspaces_or_exit(workspace, all_workspaces, action="perms show")
    exe = detect.which_lark_cli()
    for ws in workspaces:
        if refresh and exe:
            _sync_permissions_for_workspace(ws, exe)
        snap = permissions.read_snapshot(ws)
        if not snap:
            click.echo(f"{ws}: 未找到权限快照，请先运行 `lark-bridge perms sync`")
            continue
        summary = snap.get("summary", {})
        click.echo(f"{ws}:")
        click.echo(f"  generated_at: {snap.get('generated_at', '-')}")
        click.echo(f"  app_scope_count: {summary.get('app_scope_count', 0)}")
        click.echo(
            f"  checked_ok: {summary.get('checked_ok_count', 0)}/{summary.get('checked_total', 0)}",
        )
        missing = summary.get("checked_missing", [])
        if missing:
            click.echo(f"  checked_missing: {missing}")


@perms_group.command("check")
@click.option("--scope", "scopes", multiple=True, required=True, help="要检查的 scope，可重复传")
@click.option("--as", "actor", type=click.Choice(["user", "bot"]), default="user")
def perms_check_cmd(scopes: tuple[str, ...], actor: str) -> None:
    """检查当前 token 是否具备指定 scope。"""
    exe = detect.which_lark_cli()
    if not exe:
        _fail_with_guidance(
            "未找到 lark-cli，请先安装并完成配置登录。",
            commands=["npm install -g @larksuite/cli", "lark-cli auth login --recommend"],
            error_code="LAB-PERMS-001",
        )
    check_result = permissions.check_scopes(exe, list(scopes))
    missing = [k for k, v in check_result.items() if not v]
    for s in scopes:
        ok = check_result.get(s, False)
        mark = "✓" if ok else "✗"
        click.echo(f"[{mark}] {s}")
    if missing and actor == "user":
        scope_join = " ".join(missing)
        click.secho("\n缺少用户授权 scope。可执行：", fg="yellow")
        click.echo(f"  lark-cli auth login --scope \"{scope_join}\" --json")
    elif missing and actor == "bot":
        click.secho("\n缺少应用权限，请在开放平台开通相应 scope。", fg="yellow")
    if missing:
        _fail_with_guidance(
            "scope 校验未通过，请补齐权限后重试。",
            commands=["lark-bridge perms sync", "lark-bridge perms show"],
            exit_code=exit_codes.E_ACTION_REQUIRED,
            error_code="LAB-PERMS-002",
        )


@main.command("uninstall")
@click.option("--skill-only", is_flag=True, help="只移除 QwenPaw 技能，不卸载 npm 包")
@click.option("-y", "--yes", "assume_yes", is_flag=True)
@click.option("--workspace", "-w", default=None)
@click.option("--all-workspaces", is_flag=True)
@click.option(
    "--backup-keep",
    type=click.IntRange(1, 200),
    default=copaw_rt.DEFAULT_BACKUP_KEEP,
    show_default=True,
    help="每个工作区最多保留多少份最近备份",
)
@click.option(
    "--purge-lark-cli-config",
    is_flag=True,
    help="同时清理 ~/.lark-cli 配置与登录凭证（危险操作，默认不清理）",
)
def uninstall_cmd(
    skill_only: bool,
    assume_yes: bool,
    workspace: str | None,
    all_workspaces: bool,
    backup_keep: int,
    purge_lark_cli_config: bool,
) -> None:
    """移除技能目录与 skill.json 条目；可选卸载 @larksuite/cli。"""
    if not assume_yes:
        click.confirm("确认卸载 Lark Agent Bridge 技能？", abort=True)
    workspaces = _resolve_workspaces_or_exit(workspace, all_workspaces, action="uninstall")
    for ws in workspaces:
        backup = _create_backup_or_fail(ws, reason="uninstall", keep_last=backup_keep)
        click.echo(f"已创建备份: {backup.name}")
        copaw_rt.undeploy_from_workspace(ws)
        click.echo(f"已移除: {ws}")
    if not skill_only:
        npm_cands = detect.npm_executable_candidates()
        npm = npm_cands[0] if npm_cands else None
        if npm and (assume_yes or click.confirm("是否卸载全局 npm 包 @larksuite/cli？", default=False)):
            import subprocess

            subprocess.run([npm, "uninstall", "-g", "@larksuite/cli"], check=False)

    purge = purge_lark_cli_config
    if not purge and not assume_yes:
        purge = click.confirm(
            "是否同时清理 ~/.lark-cli 配置与登录凭证？（将删除本机保存的 app 配置与 token）",
            default=False,
        )
    if purge:
        cfg = detect.lark_cli_config_dir()
        if cfg.exists():
            try:
                shutil.rmtree(cfg)
                click.echo(f"已清理 lark-cli 本机配置: {cfg}")
            except OSError as e:
                click.secho(f"清理 lark-cli 配置失败: {e}", fg="yellow")
        else:
            click.echo(f"未发现 lark-cli 配置目录，无需清理: {cfg}")
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
    click.echo(
        "QwenPaw pip: "
        + f"{report.copaw_installed} {report.copaw_version}"
        + (f" ({report.paw_package})" if report.paw_package else ""),
    )
    click.echo(f"Node: {report.node_ok} {report.node_version}")
    click.echo(f"npm: {report.npm_ok} {report.npm_version}")
    click.echo(f"lark-cli: {report.lark_cli_path}")
    click.echo(f"lark-cli version string: {report.lark_cli_version}")
    if report.lark_cli_recommended is False:
        click.echo(f"lark-cli recommended: false (建议 >= {detect.RECOMMENDED_LARK_CLI_VERSION})")
    elif report.lark_cli_recommended is True:
        click.echo("lark-cli recommended: true")
    else:
        click.echo("lark-cli recommended: unknown")
    click.echo(f"config ok: {report.lark_config_ok} ({report.lark_config_hint})")
    if report.lark_auth:
        click.echo(f"auth raw: {report.lark_auth.raw}")
    if report.errors:
        click.echo("issues:")
        for e in report.errors:
            click.echo(f"  - {e}")
    click.echo(f"QWENPAW/COPAW root: {detect.copaw_working_dir()}")


@main.command("verify")
def verify_cmd() -> None:
    """对 lark-cli 做本地冒烟（version、help、config、auth、doctor）。需已安装 lark-cli。"""
    exe = detect.which_lark_cli()
    if not exe:
        _fail_with_guidance(
            "未找到 lark-cli，请先安装后再执行 verify。",
            commands=["npm install -g @larksuite/cli", "lark-bridge setup"],
            error_code="LAB-VERIFY-001",
        )
    click.echo(f"使用: {exe}\n")
    steps = self_check.run_verify_suite(exe)
    click.echo(self_check.format_report(steps))
    # 未做 config 时 doctor 也会报配置项失败，与「CLI 损坏」不同，按软失败处理
    soft = {"config show", "auth status", "doctor"}
    failed_hard = [s for s in steps if not s.ok and s.name not in soft]
    soft_fail = [s for s in steps if not s.ok and s.name in soft]
    if failed_hard:
        click.secho(
            f"\n关键项失败 {len(failed_hard)} 个（仅 --version / --help 为硬失败）。请检查 PATH 与 lark-cli 安装。",
            fg="red",
        )
        raise SystemExit(exit_codes.E_ACTION_REQUIRED)
    if soft_fail:
        click.secho(
            "\nconfig / auth / doctor 部分未通过：若尚未执行 lark-cli config init，属正常；完成后可再运行 verify。",
            fg="yellow",
        )
    click.secho("\nCLI 本体可用；请在完成飞书配置后于 QwenPaw 中试用。", fg="green")


def _cli_passthrough_run() -> None:
    """Shared body for `cli` / `lark` passthrough subcommands."""
    exe = detect.which_lark_cli()
    if not exe:
        _fail_with_guidance(
            "未找到 lark-cli，无法透传命令。",
            commands=["npm install -g @larksuite/cli", "lark-bridge setup"],
            exit_code=exit_codes.E_EXEC_NOT_FOUND,
            error_code="LAB-FORWARD-001",
        )
    code = cli_forward.run_lark_cli_forward(exe, sys.argv)
    raise SystemExit(code)


@main.command(
    "cli",
    add_help_option=False,
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
        help_option_names=[],
    ),
)
@click.pass_context
def cli_passthrough_cmd(ctx: click.Context) -> None:
    """原样转发给本机 lark-cli：后面接的内容与直接运行 lark-cli 相同。

    例：lark-bridge cli auth login --recommend
        lark-bridge cli wiki spaces list --page-all

    等价于：lark-cli …（仅多写一层前缀，便于只记 lark-bridge 一个入口）。
    """
    _ = ctx  # 保留 pass_context 以便 Click 把未知参数放进 ctx.args
    _cli_passthrough_run()


# 与 `cli` 相同，便于记忆「lark」前缀
main.add_command(cli_passthrough_cmd, name="lark")


# README 中的 install 与 setup 对齐
main.add_command(setup_cmd, name="install")


if __name__ == "__main__":
    main()
