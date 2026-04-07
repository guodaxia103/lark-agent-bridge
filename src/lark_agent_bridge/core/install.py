# -*- coding: utf-8 -*-
"""Install @larksuite/cli and optional skills add."""

from __future__ import annotations

import shutil
import subprocess
import sys
from typing import Callable

from lark_agent_bridge.core.detect import npm_executable_candidates


def run_stream(
    args: list[str],
    on_line: Callable[[str], None] | None = None,
    timeout: float = 600.0,
) -> int:
    """Run command; optionally print each line of stdout/stderr."""
    try:
        p = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=False,
            bufsize=1,
        )
        assert p.stdout is not None
        for line in p.stdout:
            if on_line:
                on_line(line.rstrip("\n"))
        p.wait(timeout=timeout)
        return int(p.returncode or 0)
    except FileNotFoundError:
        return 127
    except subprocess.TimeoutExpired:
        try:
            p.kill()
        except Exception:
            pass
        return 124


def _npx_executable() -> str | None:
    if sys.platform == "win32":
        for name in ("npx.cmd", "npx"):
            p = shutil.which(name)
            if p:
                return p
    else:
        return shutil.which("npx")
    return None


def npm_install_lark_cli_global(*, cn_mirror: bool = False) -> tuple[bool, str]:
    cands = npm_executable_candidates()
    if not cands:
        return False, "npm 未找到"
    npm = cands[0]
    install_cmd = [npm, "install", "-g", "@larksuite/cli"]
    if cn_mirror:
        install_cmd += ["--registry", "https://registry.npmmirror.com"]
    code = run_stream(install_cmd)
    if code != 0:
        return False, f"npm install -g @larksuite/cli 失败 (exit {code})"
    npx = _npx_executable()
    if not npx:
        return True, "已安装 lark-cli，但未找到 npx（可跳过 skills add）"
    code2 = run_stream([npx, "skills", "add", "larksuite/cli", "-y", "-g"])
    if code2 != 0:
        return True, f"lark-cli 已安装，但 npx skills add 失败 (exit {code2})，可稍后手动执行"
    return True, "ok"


def pip_install_copaw_upgrade() -> tuple[bool, str]:
    code = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-U", "copaw"],
        timeout=600,
    ).returncode
    if code != 0:
        return False, f"pip install -U copaw 失败 (exit {code})"
    return True, "ok"
