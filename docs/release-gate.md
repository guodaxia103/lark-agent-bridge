# Release Gate Checklist

本文档用于发布前门禁。所有条目通过后，才能打 tag 推送 PyPI。

## 1. 代码与版本

- [ ] `pyproject.toml` 与 `src/lark_agent_bridge/__init__.py` 版本一致
- [ ] `CHANGELOG.md` 已包含当前版本发布说明
- [ ] `README.md` 的命令示例与当前 CLI 保持一致（重点检查 `setup/resume/status/update/rollback`）
- [ ] `docs/error-codes.md` 已覆盖本次新增/变更的错误码

## 2. 自动化验证

- [ ] 本地执行：`python -m pytest tests -q` 通过
- [ ] CI 工作流 `CI` 全绿（Windows + Ubuntu，3.11/3.12）
- [ ] `Nightly E2E` 最近一次成功（已安装 `lark-cli` 的 smoke）

## 3. 功能回归（人工）

在一个干净环境（推荐新用户目录）至少验证一次：

- [ ] `lark-bridge setup` 初次安装路径正常
- [ ] 未完成配置时提示 `lark-cli config init --new` 与 `lark-bridge resume`
- [ ] 未完成登录时提示 `lark-cli auth login --recommend` 与 `lark-bridge resume`
- [ ] `lark-bridge resume` 能完成部署并更新权限快照
- [ ] `lark-bridge status --workspace <name>` 输出工作区技能状态
- [ ] `lark-bridge update` 会先创建备份再覆盖
- [ ] `lark-bridge rollback --workspace <name>` 能恢复最近备份
- [ ] `lark-bridge uninstall --skill-only` 会创建备份并删除技能条目

## 4. 兼容与边界

- [ ] Windows PowerShell 路径与编码输出正常
- [ ] Linux/macOS 路径默认值正常（`~/.qwenpaw`，兼容 `~/.copaw` / `~/.lark-cli`）
- [ ] 多工作区（`--workspace` / `--all-workspaces`）行为符合预期

## 5. 发布动作

- [ ] 创建并推送 tag（示例：`v0.3.8`）
- [ ] 确认 `publish-pypi.yml` 执行成功并上传 wheel/sdist
- [ ] GitHub Release 已发布并附更新说明

## 6. 发布后观察（24h）

- [ ] 监控 issue 中安装失败/回滚失败/权限检查相关反馈
- [ ] 若出现高频失败，优先补文档与错误提示，再考虑热修复
