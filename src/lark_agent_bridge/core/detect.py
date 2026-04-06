# -*- coding: utf-8 -*-
"""Detect Python, CoPaw, Node, lark-cli, config, and auth state."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class LarkCliAuthInfo:
    raw: dict[str, Any] = field(default_factory=dict)
    token_ok: bool = False
    note: str = ""


@dataclass
class DetectReport:
    python_ok: bool = False
    python_version: str = ""
    copaw_installed: bool = False
    copaw_version: str = ""
    node_ok: bool = False
    node_version: str = ""
    npm_ok: bool = False
    npm_version: str = ""
    lark_cli_path: str | None = None
    lark_cli_version: str = ""
    lark_config_ok: bool = False
    lark_config_hint: str = ""
    lark_auth: LarkCliAuthInfo | None = None
    errors: list[str] = field(default_factory=list)

    def all_ready_for_skill(self) -> bool:
        return bool(
            self.python_ok
            and self.copaw_installed
            and self.node_ok
            and self.npm_ok
            and self.lark_cli_path
            and self.lark_config_ok
            and self.lark_auth
            and self.lark_auth.token_ok,
        )


def _run_capture(
    args: list[str],
    *,
    timeout: float = 60.0,
) -> tuple[int, str, str]:
    try:
        p = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
            shell=False,
        )
        return p.returncode, p.stdout or "", p.stderr or ""
    except FileNotFoundError:
        return 127, "", "command not found"
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"


def python_info() -> tuple[bool, str]:
    v = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    ok = sys.version_info >= (3, 10)
    return ok, v


def pip_show_copaw() -> tuple[bool, str]:
    code, out, _ = _run_capture(
        [sys.executable, "-m", "pip", "show", "copaw"],
        timeout=30.0,
    )
    if code != 0:
        return False, ""
    m = re.search(r"^Version:\s*(\S+)", out, re.MULTILINE)
    ver = m.group(1) if m else ""
    return True, ver


def which_node() -> tuple[bool, str]:
    path = shutil.which("node")
    if not path:
        return False, ""
    code, out, _ = _run_capture(["node", "--version"], timeout=10.0)
    if code != 0:
        return False, path
    return True, out.strip().lstrip("v")


def npm_executable_candidates() -> list[str]:
    """Paths to npm (Windows often needs npm.cmd)."""
    out: list[str] = []
    if sys.platform == "win32":
        for name in ("npm.cmd", "npm"):
            p = shutil.which(name)
            if p and p not in out:
                out.append(p)
    else:
        p = shutil.which("npm")
        if p:
            out.append(p)
    return out


def which_npm() -> tuple[bool, str]:
    cands = npm_executable_candidates()
    if not cands:
        return False, ""
    last = cands[-1]
    for npm_path in cands:
        code, out, _ = _run_capture([npm_path, "--version"], timeout=10.0)
        if code == 0:
            return True, out.strip()
    return False, last


def which_lark_cli() -> str | None:
    return shutil.which("lark-cli")


def lark_cli_version(exe: str) -> str:
    code, out, err = _run_capture([exe, "--version"], timeout=15.0)
    if code != 0:
        return (err or out or "").strip()[:200]
    return out.strip()[:200]


def parse_config_show(stdout: str, stderr: str) -> tuple[bool, str]:
    s = (stdout or "").strip()
    if not s:
        return False, "stdout empty (not configured?)"
    try:
        data = json.loads(s)
    except json.JSONDecodeError:
        if "Not configured" in (stderr or "") or "not configured" in (stderr or "").lower():
            return False, "not configured (stderr)"
        return False, "stdout is not valid JSON"
    if isinstance(data, dict) and data.get("appId"):
        return True, "ok"
    return False, "unexpected config JSON"


def parse_auth_status(stdout: str) -> LarkCliAuthInfo:
    info = LarkCliAuthInfo()
    s = (stdout or "").strip()
    if not s:
        return info
    try:
        data = json.loads(s)
    except json.JSONDecodeError:
        return info
    info.raw = data if isinstance(data, dict) else {}
    ts = str(info.raw.get("tokenStatus", "")).lower()
    identity = info.raw.get("identity")
    note = str(info.raw.get("note", "") or "")
    info.note = note
    # Heuristic: valid / active states
    if ts in ("valid", "ok", "active"):
        info.token_ok = True
    elif identity and ts not in ("expired", "invalid", "missing", "none", ""):
        info.token_ok = True
    elif "valid" in ts:
        info.token_ok = True
    return info


def run_full_detect() -> DetectReport:
    r = DetectReport()
    r.python_ok, r.python_version = python_info()
    if not r.python_ok:
        r.errors.append("需要 Python 3.10 或更高版本")

    r.copaw_installed, r.copaw_version = pip_show_copaw()
    if not r.copaw_installed:
        r.errors.append("未检测到 copaw 包（pip install copaw）")

    r.node_ok, r.node_version = which_node()
    if not r.node_ok:
        r.errors.append("未找到 Node.js（lark-cli 依赖）")

    r.npm_ok, r.npm_version = which_npm()
    if not r.npm_ok:
        r.errors.append("未找到 npm")

    r.lark_cli_path = which_lark_cli()
    if r.lark_cli_path:
        r.lark_cli_version = lark_cli_version(r.lark_cli_path)
        code, out, err = _run_capture(
            [r.lark_cli_path, "config", "show"],
            timeout=30.0,
        )
        r.lark_config_ok, r.lark_config_hint = parse_config_show(out, err)
        if not r.lark_config_ok:
            r.errors.append(f"lark-cli 未配置应用: {r.lark_config_hint}")

        a_code, a_out, a_err = _run_capture(
            [r.lark_cli_path, "auth", "status"],
            timeout=30.0,
        )
        r.lark_auth = parse_auth_status(a_out)
        if a_code != 0 and not r.lark_auth.raw:
            r.errors.append(f"lark-cli auth status 失败: {a_err[:200]}")
        elif not r.lark_auth.token_ok:
            r.errors.append("lark-cli 登录状态异常或已过期，请运行 lark-cli auth login --recommend")
    else:
        r.errors.append("未找到 lark-cli（npm install -g @larksuite/cli）")

    return r


def copaw_working_dir() -> Path:
    import os

    raw = os.environ.get("COPAW_WORKING_DIR", "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return Path.home() / ".copaw"


def list_copaw_workspaces(copaw_root: Path | None = None) -> list[Path]:
    root = copaw_root or copaw_working_dir()
    ws = root / "workspaces"
    if not ws.is_dir():
        return []
    return sorted(
        [p for p in ws.iterdir() if p.is_dir()],
        key=lambda p: p.name,
    )


def resolve_workspace(
    name: str | None,
    *,
    all_workspaces: bool,
) -> list[Path]:
    workspaces = list_copaw_workspaces()
    if not workspaces:
        return []
    if all_workspaces:
        return workspaces
    if name:
        target = copaw_working_dir() / "workspaces" / name
        return [target.resolve()] if target.is_dir() else []
    default = copaw_working_dir() / "workspaces" / "default"
    if default.is_dir():
        return [default.resolve()]
    return workspaces[:1]
