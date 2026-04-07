# Changelog

本文档记录面向用户的版本说明；完整提交历史见 Git。

## [0.3.3] — 2026-04-07

### 新增

- `uninstall` 新增 `--purge-lark-cli-config`：可选清理本机 `~/.lark-cli` 配置与登录凭证
- `uninstall` 交互模式新增“是否清理 lark-cli 配置”的确认步骤

### 修复

- `uninstall` 在配置目录不存在时不报错，提示“无需清理”
- 补充测试：不误删其它技能、可选清理配置目录、缺失时容错
- README 补充完整重装场景下的清理命令示例

## [0.3.2] — 2026-04-07

### 新增

- `setup` 新增 `--no-install-lark-cli` 参数；默认情况下缺少 `lark-cli` 会自动安装

### 修复

- `setup` 在未完成 `config init` / `auth login` 时，改为输出明确下一步并停止，避免小白误按 Enter 后误以为已完成部署
- README 的 `setup` 参数表与示例更新，补充自动安装行为说明
- 测试补充：`setup` 缺少 `lark-cli` 时自动安装的行为断言

## [0.3.1] — 2026-04-07

### 修复

- GitHub Actions 的 PyPI 发布流程改为 `twine + API Token`，避免 OIDC 权限导致的失败
- 文档中的安装示例与标签版本更新为 `v0.3.1`

## [0.3.0] — 2026-04-07

### 新增

- `lark-bridge cli` / `lark-bridge lark`：原样透传至本机 `lark-cli`
- 文档：`README` 用户向瘦身；`DEVELOPMENT.md` 开发者文档
- 测试：`detect` 解析、`cli` CliRunner、`cli_forward`、部署 `force` 行为等

### 修复

- `deploy_to_workspace(force=False)`：保留已有技能目录，仅合并 `skill.json`
- `merge`：`version_text` 与包版本同步
- `setup --cn`：使用 `npm install --registry`，不再永久改写全局 npm 源

### 分发

- PyPI 包名：`lark-agent-bridge`
- GitHub Release：标签 `v0.3.0` 对应本版本；亦可 `pip install` GitHub 源码 zip（无需 Git）

[0.3.3]: https://github.com/guodaxia103/lark-agent-bridge/tree/v0.3.3
[0.3.2]: https://github.com/guodaxia103/lark-agent-bridge/tree/v0.3.2
[0.3.1]: https://github.com/guodaxia103/lark-agent-bridge/tree/v0.3.1
[0.3.0]: https://github.com/guodaxia103/lark-agent-bridge/tree/v0.3.0
