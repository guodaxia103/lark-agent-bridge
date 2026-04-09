# -*- coding: utf-8 -*-
"""Shared exit codes for lark-agent-bridge CLI."""

from __future__ import annotations

from dataclasses import dataclass


# Keep numeric codes stable for backward compatibility.
E_FAILED = 1
E_ACTION_REQUIRED = 2
E_EXEC_NOT_FOUND = 127


@dataclass(frozen=True)
class ErrorDef:
    code: str
    exit_code: int
    summary: str


ERROR_DEFS = {
    "LAB-CLI-001": ErrorDef("LAB-CLI-001", E_FAILED, "参数冲突或命令使用错误"),
    "LAB-CLI-002": ErrorDef("LAB-CLI-002", E_FAILED, "未找到 CoPaw 工作区"),
    "LAB-SETUP-001": ErrorDef("LAB-SETUP-001", E_FAILED, "Python 版本不满足要求"),
    "LAB-SETUP-002": ErrorDef("LAB-SETUP-002", E_FAILED, "Node/npm/lark-cli 依赖缺失"),
    "LAB-SETUP-003": ErrorDef("LAB-SETUP-003", E_ACTION_REQUIRED, "需要先完成应用配置"),
    "LAB-SETUP-004": ErrorDef("LAB-SETUP-004", E_ACTION_REQUIRED, "需要先完成登录授权"),
    "LAB-DEPLOY-001": ErrorDef("LAB-DEPLOY-001", E_FAILED, "部署或写入工作区失败"),
    "LAB-BACKUP-001": ErrorDef("LAB-BACKUP-001", E_FAILED, "备份创建或恢复失败"),
    "LAB-BACKUP-002": ErrorDef("LAB-BACKUP-002", E_FAILED, "未找到可用备份"),
    "LAB-PERMS-001": ErrorDef("LAB-PERMS-001", E_FAILED, "权限快照依赖缺失"),
    "LAB-PERMS-002": ErrorDef("LAB-PERMS-002", E_ACTION_REQUIRED, "scope 不满足，需要补授权"),
    "LAB-VERIFY-001": ErrorDef("LAB-VERIFY-001", E_FAILED, "lark-cli 冒烟校验失败"),
    "LAB-FORWARD-001": ErrorDef("LAB-FORWARD-001", E_EXEC_NOT_FOUND, "透传时未找到 lark-cli"),
}

