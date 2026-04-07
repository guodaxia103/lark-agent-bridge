# -*- coding: utf-8 -*-
"""E2E-style test: deploy bundled skill into a fake CoPaw workspace layout (no real CoPaw process)."""

import json

from lark_agent_bridge import SKILL_DIR_NAME
from lark_agent_bridge.manifest.merge import load_manifest
from lark_agent_bridge.runtimes.copaw import deploy_to_workspace


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
