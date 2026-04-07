# -*- coding: utf-8 -*-
"""Deploy bundled skill into CoPaw workspace."""

from __future__ import annotations

import shutil
from pathlib import Path

from lark_agent_bridge import SKILL_DIR_NAME
from lark_agent_bridge.manifest.merge import (
    load_manifest,
    merge_lark_bridge_entry,
    remove_lark_bridge_entry,
    write_manifest_atomic,
)


def bundled_skill_source() -> Path:
    """Directory containing packaged lark_cli_bridge skill files."""
    return Path(__file__).resolve().parent.parent / "skills" / SKILL_DIR_NAME


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
