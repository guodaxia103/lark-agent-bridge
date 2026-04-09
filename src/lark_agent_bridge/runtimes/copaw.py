# -*- coding: utf-8 -*-
"""Deploy bundled skill into CoPaw workspace."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from lark_agent_bridge import SKILL_DIR_NAME
from lark_agent_bridge.manifest.merge import (
    load_manifest,
    merge_lark_bridge_entry,
    remove_lark_bridge_entry,
    write_manifest_atomic,
)

BACKUP_DIR_NAME = ".lark-bridge-backups"
DEFAULT_BACKUP_KEEP = 10


def bundled_skill_source() -> Path:
    """Directory containing packaged lark_cli_bridge skill files."""
    return Path(__file__).resolve().parent.parent / "skills" / SKILL_DIR_NAME


def _backup_stamp() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def backups_root(workspace_dir: Path) -> Path:
    return workspace_dir / BACKUP_DIR_NAME


def list_workspace_backups(workspace_dir: Path) -> list[Path]:
    root = backups_root(workspace_dir)
    if not root.is_dir():
        return []
    return sorted(
        [p for p in root.iterdir() if p.is_dir()],
        key=lambda p: p.name,
        reverse=True,
    )


def prune_workspace_backups(workspace_dir: Path, *, keep_last: int = DEFAULT_BACKUP_KEEP) -> list[Path]:
    backups = list_workspace_backups(workspace_dir)
    if keep_last < 1:
        keep_last = 1
    removed: list[Path] = []
    for p in backups[keep_last:]:
        shutil.rmtree(p, ignore_errors=True)
        removed.append(p)
    return removed


def create_workspace_backup(
    workspace_dir: Path,
    *,
    reason: str,
    keep_last: int = DEFAULT_BACKUP_KEEP,
) -> Path:
    root = backups_root(workspace_dir)
    root.mkdir(parents=True, exist_ok=True)

    stamp = _backup_stamp()
    slug = "".join(ch for ch in reason.strip().lower().replace(" ", "-") if ch.isalnum() or ch in ("-", "_"))
    if not slug:
        slug = "manual"
    base_name = f"{stamp}-{slug}"
    backup_dir = root / base_name
    idx = 1
    while backup_dir.exists():
        backup_dir = root / f"{base_name}-{idx}"
        idx += 1
    backup_dir.mkdir(parents=True, exist_ok=False)

    skill_src = workspace_dir / "skills" / SKILL_DIR_NAME
    if skill_src.is_dir():
        shutil.copytree(skill_src, backup_dir / "skill")

    manifest_src = workspace_dir / "skill.json"
    if manifest_src.is_file():
        shutil.copy2(manifest_src, backup_dir / "skill.json")

    metadata = {
        "created_at": datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z"),
        "reason": reason,
        "workspace": str(workspace_dir),
        "skill_present": skill_src.is_dir(),
        "manifest_present": manifest_src.is_file(),
    }
    (backup_dir / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    prune_workspace_backups(workspace_dir, keep_last=keep_last)
    return backup_dir


def restore_workspace_backup(workspace_dir: Path, backup_dir: Path) -> None:
    if not backup_dir.is_dir():
        raise FileNotFoundError(f"备份目录不存在: {backup_dir}")

    skill_dest = workspace_dir / "skills" / SKILL_DIR_NAME
    if skill_dest.exists():
        shutil.rmtree(skill_dest)
    skill_backup = backup_dir / "skill"
    if skill_backup.is_dir():
        skill_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(skill_backup, skill_dest)

    manifest_dest = workspace_dir / "skill.json"
    manifest_backup = backup_dir / "skill.json"
    if manifest_backup.is_file():
        manifest_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(manifest_backup, manifest_dest)
    elif manifest_dest.exists():
        manifest_dest.unlink()


def deploy_to_workspace(
    workspace_dir: Path,
    *,
    force: bool = False,
) -> Path:
    """Copy skill tree and merge skill.json. Returns path to skill dir."""
    src = bundled_skill_source()
    if not (src / "SKILL.md").exists():
        raise FileNotFoundError(f"找不到打包技能: {src}")

    skills_root = workspace_dir / "skills"
    skills_root.mkdir(parents=True, exist_ok=True)
    dest = skills_root / SKILL_DIR_NAME

    if dest.exists() and not force:
        pass  # keep existing skill files; only refresh manifest below
    elif dest.exists():
        shutil.rmtree(dest)
        shutil.copytree(src, dest)
    else:
        shutil.copytree(src, dest)

    manifest_path = workspace_dir / "skill.json"
    data = load_manifest(manifest_path)
    merge_lark_bridge_entry(data, enabled=True)
    write_manifest_atomic(manifest_path, data)
    return dest


def undeploy_from_workspace(workspace_dir: Path) -> None:
    """Remove skill directory and manifest entry."""
    dest = workspace_dir / "skills" / SKILL_DIR_NAME
    if dest.exists():
        shutil.rmtree(dest)

    manifest_path = workspace_dir / "skill.json"
    data = load_manifest(manifest_path)
    remove_lark_bridge_entry(data)
    write_manifest_atomic(manifest_path, data)
