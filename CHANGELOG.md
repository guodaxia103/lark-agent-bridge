# Changelog

本文档记录面向用户的版本说明；完整提交历史见 Git。

## [0.3.8] — 2026-04-14

### 改进

- 全面切换为 QwenPaw 优先命名：`setup/status/doctor` 与关键提示改为 QwenPaw 语义
- 运行时保持 CoPaw 兼容：仍可识别 `copaw` 包与历史工作区
- `setup` 的 Python 包检测/安装改为“优先 `qwenpaw`，失败回退 `copaw`”
- 工作区根目录解析改为优先 `QWENPAW_WORKING_DIR`，兼容 `COPAW_WORKING_DIR`
- 默认工作区目录改为 `~/.qwenpaw`，若存在旧目录 `~/.copaw` 会自动兼容
- README 与错误码/发布门禁文档同步更新到 QwenPaw 口径

## [0.3.7] — 2026-04-09

### 新增

- 新增 `lark-bridge resume`：在 `setup` 因配置/登录未完成而中断后，完成浏览器步骤即可继续部署
- 新增 `lark-bridge rollback`：支持恢复工作区技能目录与 `skill.json` 到最近或指定备份
- 新增 `lark-bridge backups list/cleanup`：查看并清理工作区备份
- `update` / `upgrade` / `uninstall` 执行前自动创建工作区备份
- `update` / `upgrade` / `uninstall` 新增 `--backup-keep`（默认保留最近 10 份备份）

### 改进

- `status` 支持 `--workspace` 并按工作区输出技能与权限快照状态
- 关键失败路径统一为“原因 + 建议命令 + 检查项”的可执行提示，降低小白排障成本
- 引入统一错误码体系（见 `docs/error-codes.md`）

## [0.3.6] — 2026-04-07

### 修订

- `SKILL.md` 补充 `lark-bridge perms sync/show/check` 用法提示，明确可结合权限快照加速执行前判权

## [0.3.5] — 2026-04-07

### 新增

- 新增 `lark-bridge upgrade`：面向小白的一键升级入口（更新技能模板并给出下一步建议）
- 新增 `lark-bridge perms` 命令组：
  - `perms sync`：生成权限快照
  - `perms show`：展示权限快照（可选 `--refresh`）
  - `perms check`：按 scope 检查当前 token 权限并给授权建议
- `setup` 成功部署后会尝试写入权限快照（失败不阻断）
- `status` 新增 `--refresh-perms`，并显示权限快照摘要

### 修复

- 统一补齐“升级后下一步”的小白提示，避免只升级包不更新技能/权限认知
- 补充 `permissions` 与 CLI 新命令测试，降低回归风险

## [0.3.4] — 2026-04-07

### 技能文档优化

- `SKILL.md` 增加“最短成功路径”与“执行前权限判断（强制）”，降低误用率
- `SKILL.md` 将 `auth login` 指引统一为中文表达，减少中英混杂
- `references/auth_and_identity.md` 增加“常见任务与 scope 速查”表
- `references/discovery.md` 增加“命令发现回退策略”（domain -> schema -> api）
- `references/output_and_errors.md` 增加“标准失败回复模板”，便于快速给用户可执行反馈

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

[0.3.8]: https://github.com/guodaxia103/lark-agent-bridge/tree/v0.3.8
[0.3.7]: https://github.com/guodaxia103/lark-agent-bridge/tree/v0.3.7
[0.3.6]: https://github.com/guodaxia103/lark-agent-bridge/tree/v0.3.6
[0.3.5]: https://github.com/guodaxia103/lark-agent-bridge/tree/v0.3.5
[0.3.4]: https://github.com/guodaxia103/lark-agent-bridge/tree/v0.3.4
[0.3.3]: https://github.com/guodaxia103/lark-agent-bridge/tree/v0.3.3
[0.3.2]: https://github.com/guodaxia103/lark-agent-bridge/tree/v0.3.2
[0.3.1]: https://github.com/guodaxia103/lark-agent-bridge/tree/v0.3.1
[0.3.0]: https://github.com/guodaxia103/lark-agent-bridge/tree/v0.3.0
