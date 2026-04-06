# -*- coding: utf-8 -*-
"""Smoke checks for lark-cli when present on PATH (used by lark-bridge verify)."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from typing import Any


@dataclass
class StepResult:
    name: str
    ok: bool
    detail: str = ""
    data: dict[str, Any] = field(default_factory=dict)


def _run(argv: list[str], timeout: float = 60.0) -> tuple[int, str, str]:
    try:
        p = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
            shell=False,
        )
        return p.returncode, p.stdout or "", p.stderr or ""
    except FileNotFoundError:
        return 127, "", "not found"
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"


def run_verify_suite(lark_cli: str) -> list[StepResult]:
    """Ordered smoke steps; do not require Feishu network for --version/help."""
    out: list[StepResult] = []

    code, so, se = _run([lark_cli, "--version"], timeout=20.0)
    out.append(
        StepResult(
            name="--version",
            ok=code == 0,
            detail=(so or se).strip()[:500],
        ),
    )

    code, so, se = _run([lark_cli, "--help"], timeout=20.0)
    out.append(
        StepResult(
            name="--help",
            ok=code == 0 and ("api" in (so + se).lower() or "Usage" in (so + se)),
            detail=f"exit={code}, len={len(so)+len(se)}",
        ),
    )

    code, so, se = _run([lark_cli, "config", "show"], timeout=30.0)
    cfg_ok = False
    if code == 0 and so.strip():
        try:
            j = json.loads(so.strip())
            cfg_ok = isinstance(j, dict) and bool(j.get("appId"))
        except json.JSONDecodeError:
            cfg_ok = False
    out.append(
        StepResult(
            name="config show",
            ok=cfg_ok,
            detail="parsed appId" if cfg_ok else (se[:200] or so[:200] or "no json"),
        ),
    )

    code, so, se = _run([lark_cli, "auth", "status"], timeout=45.0)
    auth_ok = code == 0 and bool(so.strip())
    out.append(
        StepResult(
            name="auth status",
            ok=auth_ok,
            detail=(so or se)[:400],
        ),
    )

    code, so, se = _run([lark_cli, "doctor"], timeout=60.0)
    out.append(
        StepResult(
            name="doctor",
            ok=code == 0,
            detail=(so or se)[:400],
        ),
    )

    return out


def format_report(steps: list[StepResult]) -> str:
    lines = []
    for s in steps:
        mark = "OK" if s.ok else "FAIL"
        lines.append(f"[{mark}] {s.name}: {s.detail}")
    return "\n".join(lines)
