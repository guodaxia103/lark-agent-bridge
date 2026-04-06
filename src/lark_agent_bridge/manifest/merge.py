# -*- coding: utf-8 -*-
"""Merge lark_cli_bridge into CoPaw workspace skill.json without clobbering others."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lark_agent_bridge import SKILL_DIR_NAME

SCHEMA = "workspace-skill-manifest.v1"


def _now_iso() -> str:
    return (
        datetime.now(tz=timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


def load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "schema_version": SCHEMA,
            "version": 0,
            "skills": {},
        }
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "schema_version": SCHEMA,
            "version": 0,
            "skills": {},
        }
    if not isinstance(data, dict):
        return {
            "schema_version": SCHEMA,
            "version": 0,
            "skills": {},
        }
    data.setdefault("schema_version", SCHEMA)
    data.setdefault("version", 0)
    data.setdefault("skills", {})
    if not isinstance(data["skills"], dict):
        data["skills"] = {}
    return data


def write_manifest_atomic(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def merge_lark_bridge_entry(
    manifest: dict[str, Any],
    *,
    enabled: bool = True,
    preserve_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Insert or update only SKILL_DIR_NAME entry; bump version."""
    skills: dict[str, Any] = manifest.setdefault("skills", {})
    existing: dict[str, Any] = (
        skills.get(SKILL_DIR_NAME)
        if isinstance(skills.get(SKILL_DIR_NAME), dict)
        else {}
    )

    now = _now_iso()
    req = {"require_bins": ["lark-cli"], "require_envs": []}
    meta = {
        "name": SKILL_DIR_NAME,
        "description": "通过本机 lark-cli（飞书官方 CLI）操作飞书；与内置飞书通道并行。",
        "version_text": "0.2.0",
        "commit_text": "",
        "signature": "",
        "source": "customized",
        "protected": False,
        "requirements": req,
        "updated_at": now,
    }

    channels = existing.get("channels") if existing else None
    if not channels:
        channels = ["all"]

    cfg = preserve_config
    if cfg is None and isinstance(existing.get("config"), dict):
        cfg = existing.get("config")

    entry: dict[str, Any] = {
        "enabled": enabled,
        "channels": channels,
        "source": "customized",
        "metadata": meta,
        "requirements": req,
        "updated_at": now,
    }
    if cfg:
        entry["config"] = cfg

    skills[SKILL_DIR_NAME] = entry
    # Match CoPaw style: large ms timestamp
    manifest["version"] = int(time.time() * 1000)
    manifest["schema_version"] = SCHEMA
    return manifest


def remove_lark_bridge_entry(manifest: dict[str, Any]) -> dict[str, Any]:
    skills = manifest.setdefault("skills", {})
    skills.pop(SKILL_DIR_NAME, None)
    manifest["version"] = int(time.time() * 1000)
    return manifest
