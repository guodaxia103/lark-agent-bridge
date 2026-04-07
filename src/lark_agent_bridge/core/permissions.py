# -*- coding: utf-8 -*-
"""Permission snapshot and scope checking helpers for lark-cli."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lark_agent_bridge import SKILL_DIR_NAME

DEFAULT_SCOPES_TO_CHECK = [
    "wiki:wiki:readonly",
    "space:document:readonly",
    "calendar:calendar:readonly",
    "im:message",
]


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _run_capture(args: list[str], timeout: float = 30.0) -> tuple[int, str, str]:
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
        return int(p.returncode or 0), p.stdout or "", p.stderr or ""
    except FileNotFoundError:
        return 127, "", "command not found"
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"


def _json_or_empty(raw: str) -> dict[str, Any]:
    s = (raw or "").strip()
    if not s:
        return {}
    try:
        data = json.loads(s)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _extract_scope_names(payload: Any) -> list[str]:
    out: list[str] = []
    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, str):
                out.append(item)
            elif isinstance(item, dict):
                for key in ("scope", "name", "id", "value"):
                    v = item.get(key)
                    if isinstance(v, str) and v.strip():
                        out.append(v.strip())
                        break
    elif isinstance(payload, dict):
        for key in ("scopes", "scope_list", "data"):
            if key in payload:
                out.extend(_extract_scope_names(payload.get(key)))
    return sorted({x for x in out if x})


def auth_scopes(lark_cli: str) -> tuple[list[str], str]:
    code, out, err = _run_capture([lark_cli, "auth", "scopes"], timeout=30.0)
    if code != 0:
        return [], (err or out or "").strip()[:200]
    data = _json_or_empty(out)
    return _extract_scope_names(data), "ok"


def auth_status(lark_cli: str) -> dict[str, Any]:
    code, out, _ = _run_capture([lark_cli, "auth", "status"], timeout=30.0)
    if code != 0:
        return {}
    return _json_or_empty(out)


def config_show(lark_cli: str) -> dict[str, Any]:
    code, out, _ = _run_capture([lark_cli, "config", "show"], timeout=30.0)
    if code != 0:
        return {}
    return _json_or_empty(out)


def check_scopes(lark_cli: str, scopes: list[str]) -> dict[str, bool]:
    result: dict[str, bool] = {}
    for scope in scopes:
        code, out, _ = _run_capture(
            [lark_cli, "auth", "check", "--scope", scope],
            timeout=30.0,
        )
        if code == 0:
            result[scope] = True
            continue
        data = _json_or_empty(out)
        ok = bool(data.get("ok")) if data else False
        result[scope] = ok
    return result


def runtime_dir(workspace_dir: Path) -> Path:
    return workspace_dir / "skills" / SKILL_DIR_NAME / ".runtime"


def snapshot_path(workspace_dir: Path) -> Path:
    return runtime_dir(workspace_dir) / "permissions.json"


def build_snapshot(
    lark_cli: str,
    *,
    scopes_to_check: list[str] | None = None,
    actor: str = "user",
) -> dict[str, Any]:
    check_list = scopes_to_check or list(DEFAULT_SCOPES_TO_CHECK)
    app_scopes, scopes_hint = auth_scopes(lark_cli)
    checked = check_scopes(lark_cli, check_list)
    checked_ok = [k for k, v in checked.items() if v]
    snap = {
        "generated_at": _now_iso(),
        "lark_cli_path": lark_cli,
        "actor": actor,
        "config": config_show(lark_cli),
        "auth_status": auth_status(lark_cli),
        "app_scopes": app_scopes,
        "checked_scopes": checked,
        "scope_hint": scopes_hint,
        "summary": {
            "app_scope_count": len(app_scopes),
            "checked_total": len(check_list),
            "checked_ok_count": len(checked_ok),
            "checked_missing": [s for s in check_list if s not in checked_ok],
        },
    }
    return snap


def write_snapshot(workspace_dir: Path, snapshot: dict[str, Any]) -> Path:
    p = snapshot_path(workspace_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return p


def read_snapshot(workspace_dir: Path) -> dict[str, Any]:
    p = snapshot_path(workspace_dir)
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}
