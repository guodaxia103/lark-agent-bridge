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


def test_copaw_workspace_resolve_respects_env(tmp_path, monkeypatch):
    from lark_agent_bridge.core.detect import copaw_working_dir, resolve_workspace

    root = tmp_path / "fakehome"
    (root / "workspaces" / "default").mkdir(parents=True)
    monkeypatch.setenv("COPAW_WORKING_DIR", str(root))
    assert copaw_working_dir() == root.resolve()
    wss = resolve_workspace(None, all_workspaces=False)
    assert len(wss) == 1
    assert wss[0].name == "default"
