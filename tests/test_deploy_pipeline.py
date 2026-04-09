# -*- coding: utf-8 -*-
"""E2E-style test: deploy bundled skill into a fake CoPaw workspace layout (no real CoPaw process)."""

import json

from lark_agent_bridge import SKILL_DIR_NAME
from lark_agent_bridge.manifest.merge import load_manifest
from lark_agent_bridge.runtimes.copaw import (
    create_workspace_backup,
    deploy_to_workspace,
    list_workspace_backups,
    prune_workspace_backups,
    restore_workspace_backup,
)


def test_deploy_creates_skill_tree_and_manifest(tmp_path, monkeypatch):
    """Guarantees: files on disk + skill.json entry — what we deliver to users' CoPaw."""
    ws = tmp_path / "workspaces" / "default"
    ws.mkdir(parents=True)
    manifest = ws / "skill.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": "workspace-skill-manifest.v1",
                "version": 1,
                "skills": {
                    "other": {
                        "enabled": True,
                        "channels": ["all"],
                        "source": "customized",
                    },
                },
            },
        ),
        encoding="utf-8",
    )

    deploy_to_workspace(ws, force=True)

    skill_root = ws / "skills" / SKILL_DIR_NAME
    assert (skill_root / "SKILL.md").is_file()
    assert (skill_root / "references" / "discovery.md").is_file()

    data = load_manifest(manifest)
    assert SKILL_DIR_NAME in data.get("skills", {})
    assert data["skills"][SKILL_DIR_NAME].get("enabled") is True
    assert "other" in data["skills"]


def test_deploy_force_false_preserves_existing_files(tmp_path):
    """force=False should keep existing skill files and only refresh manifest."""
    ws = tmp_path / "workspaces" / "default"
    ws.mkdir(parents=True)

    skills_dir = ws / "skills" / SKILL_DIR_NAME
    skills_dir.mkdir(parents=True)
    marker = skills_dir / "CUSTOM_FILE.txt"
    marker.write_text("user customization", encoding="utf-8")
    (skills_dir / "SKILL.md").write_text("old content", encoding="utf-8")

    deploy_to_workspace(ws, force=False)

    assert marker.exists(), "force=False should not delete existing files"
    assert marker.read_text(encoding="utf-8") == "user customization"

    data = load_manifest(ws / "skill.json")
    assert SKILL_DIR_NAME in data["skills"]
    assert data["skills"][SKILL_DIR_NAME]["enabled"] is True


def test_deploy_force_true_replaces_skill_dir(tmp_path):
    """force=True should replace the entire skill directory with bundled content."""
    ws = tmp_path / "workspaces" / "default"
    ws.mkdir(parents=True)

    skills_dir = ws / "skills" / SKILL_DIR_NAME
    skills_dir.mkdir(parents=True)
    marker = skills_dir / "CUSTOM_FILE.txt"
    marker.write_text("should be removed", encoding="utf-8")
    (skills_dir / "SKILL.md").write_text("old", encoding="utf-8")

    deploy_to_workspace(ws, force=True)

    assert not marker.exists(), "force=True should remove old custom files"
    assert (skills_dir / "SKILL.md").is_file()
    content = (skills_dir / "SKILL.md").read_text(encoding="utf-8")
    assert "old" not in content or "lark_cli_bridge" in content

    data = load_manifest(ws / "skill.json")
    assert SKILL_DIR_NAME in data["skills"]


def test_copaw_workspace_resolve_respects_env(tmp_path, monkeypatch):
    from lark_agent_bridge.core.detect import copaw_working_dir, resolve_workspace

    root = tmp_path / "fakehome"
    (root / "workspaces" / "default").mkdir(parents=True)
    monkeypatch.setenv("COPAW_WORKING_DIR", str(root))
    assert copaw_working_dir() == root.resolve()
    wss = resolve_workspace(None, all_workspaces=False)
    assert len(wss) == 1
    assert wss[0].name == "default"


def test_backup_and_restore_workspace_state(tmp_path):
    ws = tmp_path / "workspaces" / "default"
    skill_dir = ws / "skills" / SKILL_DIR_NAME
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("old skill", encoding="utf-8")
    (ws / "skill.json").write_text('{"skills":{"x":{}}}\n', encoding="utf-8")

    backup = create_workspace_backup(ws, reason="update")
    assert backup.is_dir()
    assert (backup / "skill" / "SKILL.md").is_file()
    assert (backup / "skill.json").is_file()

    (skill_dir / "SKILL.md").write_text("new skill", encoding="utf-8")
    (ws / "skill.json").write_text('{"skills":{"y":{}}}\n', encoding="utf-8")

    restore_workspace_backup(ws, backup)
    assert (skill_dir / "SKILL.md").read_text(encoding="utf-8") == "old skill"
    assert '"x"' in (ws / "skill.json").read_text(encoding="utf-8")


def test_list_workspace_backups_descending(tmp_path):
    ws = tmp_path / "workspaces" / "default"
    ws.mkdir(parents=True)
    b1 = create_workspace_backup(ws, reason="first")
    b2 = create_workspace_backup(ws, reason="second")
    backups = list_workspace_backups(ws)
    assert backups
    assert backups[0].name == b2.name
    assert backups[1].name == b1.name


def test_prune_workspace_backups_keep_n(tmp_path):
    ws = tmp_path / "workspaces" / "default"
    ws.mkdir(parents=True)
    create_workspace_backup(ws, reason="one")
    create_workspace_backup(ws, reason="two")
    create_workspace_backup(ws, reason="three")
    removed = prune_workspace_backups(ws, keep_last=2)
    assert len(removed) >= 1
    remained = list_workspace_backups(ws)
    assert len(remained) == 2
