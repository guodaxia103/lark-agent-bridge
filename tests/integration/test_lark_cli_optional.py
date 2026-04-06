# -*- coding: utf-8 -*-
"""If lark-cli is on PATH, run smoke steps (no Feishu tenant required for --version)."""

import shutil

import pytest

from lark_agent_bridge.core import detect
from lark_agent_bridge.self_check import run_verify_suite


pytestmark = pytest.mark.integration


def test_lark_cli_smoke_if_installed():
    exe = shutil.which("lark-cli") or detect.which_lark_cli()
    if not exe:
        pytest.skip("lark-cli not on PATH")
    steps = run_verify_suite(exe)
    names = {s.name: s for s in steps}
    assert names["--version"].ok, names["--version"].detail
    assert names["--help"].ok, names["--help"].detail
