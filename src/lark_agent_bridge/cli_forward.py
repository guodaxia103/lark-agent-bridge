# -*- coding: utf-8 -*-
"""Forward `lark-bridge cli …` to the local `lark-cli` binary (passthrough)."""

from __future__ import annotations

import subprocess
import sys
from typing import Sequence


def argv_after_cli(argv: Sequence[str]) -> list[str]:
    """Return arguments after ``cli`` or ``lark`` (passthrough subcommand name)."""
    for i, seg in enumerate(argv):
        if seg in ("cli", "lark"):
            return list(argv[i + 1 :])
    return []


def run_lark_cli_forward(exe: str, argv: Sequence[str]) -> int:
    """Run ``exe`` with args taken from ``argv`` after the ``cli`` token."""
    rest = argv_after_cli(argv)
    if not rest:
        rest = ["--help"]
    try:
        p = subprocess.run([exe] + rest, shell=False)
        return int(p.returncode)
    except OSError:
        return 1
