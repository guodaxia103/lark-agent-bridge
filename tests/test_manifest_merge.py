# -*- coding: utf-8 -*-
from lark_agent_bridge.manifest.merge import (
    load_manifest,
    merge_lark_bridge_entry,
    remove_lark_bridge_entry,
)
from lark_agent_bridge import SKILL_DIR_NAME


def test_merge_preserves_other_skills(tmp_path):
    p = tmp_path / "skill.json"
    p.write_text(
        '{"schema_version":"workspace-skill-manifest.v1","version":1,"skills":{"Other":{"enabled":true,"channels":["all"],"source":"customized"}}}\n',
        encoding="utf-8",
    )
    data = load_manifest(p)
    merge_lark_bridge_entry(data, enabled=True)
    assert "Other" in data["skills"]
    assert SKILL_DIR_NAME in data["skills"]
    assert data["skills"][SKILL_DIR_NAME]["enabled"] is True


def test_remove(tmp_path):
    data = {
        "schema_version": "workspace-skill-manifest.v1",
        "version": 1,
        "skills": {SKILL_DIR_NAME: {"enabled": True}, "X": {}},
    }
    remove_lark_bridge_entry(data)
    assert SKILL_DIR_NAME not in data["skills"]
    assert "X" in data["skills"]
