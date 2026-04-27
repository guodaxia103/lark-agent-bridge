# -*- coding: utf-8 -*-
"""Unit tests for pure functions in core/detect.py."""

from __future__ import annotations

from lark_agent_bridge.core.detect import (
    lark_cli_meets_recommended,
    parse_auth_status,
    parse_config_show,
)


class TestParseConfigShow:
    def test_valid_json_with_app_id(self):
        ok, hint = parse_config_show('{"appId":"cli_abc","appSecret":"***"}', "")
        assert ok is True
        assert hint == "ok"

    def test_empty_stdout(self):
        ok, hint = parse_config_show("", "")
        assert ok is False
        assert "empty" in hint.lower()

    def test_not_configured_stderr(self):
        ok, hint = parse_config_show("", "Not configured yet")
        assert ok is False
        assert "not configured" in hint.lower()

    def test_invalid_json(self):
        ok, hint = parse_config_show("not-json{", "")
        assert ok is False
        assert "json" in hint.lower()

    def test_json_without_app_id(self):
        ok, hint = parse_config_show('{"someOther":"val"}', "")
        assert ok is False
        assert "unexpected" in hint.lower()

    def test_json_with_empty_app_id(self):
        ok, hint = parse_config_show('{"appId":""}', "")
        assert ok is False

    def test_non_dict_json(self):
        ok, hint = parse_config_show("[1,2,3]", "")
        assert ok is False


class TestParseAuthStatus:
    def test_valid_token(self):
        info = parse_auth_status('{"tokenStatus":"valid","identity":"user@test"}')
        assert info.token_ok is True

    def test_active_token(self):
        info = parse_auth_status('{"tokenStatus":"active","identity":"u"}')
        assert info.token_ok is True

    def test_expired_token(self):
        info = parse_auth_status('{"tokenStatus":"expired"}')
        assert info.token_ok is False

    def test_missing_token(self):
        info = parse_auth_status('{"tokenStatus":"missing"}')
        assert info.token_ok is False

    def test_empty_stdout(self):
        info = parse_auth_status("")
        assert info.token_ok is False
        assert info.raw == {}

    def test_invalid_json(self):
        info = parse_auth_status("not json")
        assert info.token_ok is False

    def test_identity_with_unknown_status(self):
        info = parse_auth_status('{"tokenStatus":"something","identity":"user@t"}')
        assert info.token_ok is True

    def test_note_preserved(self):
        info = parse_auth_status('{"tokenStatus":"valid","note":"some note"}')
        assert info.note == "some note"

    def test_none_status(self):
        info = parse_auth_status('{"tokenStatus":"none"}')
        assert info.token_ok is False


class TestLarkCliVersion:
    def test_recommended_version_matches_plain_semver(self):
        assert lark_cli_meets_recommended("1.0.19") is True

    def test_newer_version_matches_prefixed_output(self):
        assert lark_cli_meets_recommended("lark-cli 1.0.20") is True

    def test_older_version_warns(self):
        assert lark_cli_meets_recommended("1.0.18") is False

    def test_unparseable_version_is_unknown(self):
        assert lark_cli_meets_recommended("dev-build") is None
