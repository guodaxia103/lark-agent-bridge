# GitHub Issue Drafts

以下条目可直接复制到 GitHub Issues。每条都包含背景、范围、验收标准。

## 1. `feat: add structured error codes and unified failure template`

**背景**  
CLI 失败提示已较友好，但缺少统一错误码，不利于支持与统计。

**范围**
- 统一错误码规范（`LAB-xxx`）
- 失败输出统一模板（错误码 + 建议命令 + 检查项）
- 文档化错误码目录

**验收标准**
- 关键命令失败路径均带错误码
- `docs/error-codes.md` 完整列出可见错误码
- 测试覆盖关键错误提示断言

## 2. `feat: implement backup retention policy for workspace backups`

**背景**  
自动备份已上线，但长期会积累大量目录，需要保留策略。

**范围**
- 默认每工作区仅保留最近 10 份备份
- `update/upgrade/uninstall` 支持 `--backup-keep`
- 新增 `backups cleanup --keep` 手动清理

**验收标准**
- 备份数量超过阈值后自动删除最旧备份
- `backups cleanup` 输出清理数量
- 单测覆盖保留边界与排序

## 3. `feat: persist setup/resume stage summary for doctor diagnostics`

**背景**  
用户常反馈“为什么失败”，但缺少最近一次流程阶段信息。

**范围**
- 记录最近一次 `setup/resume` 阶段（detect/install/config/auth/deploy）
- `doctor` 展示最近失败阶段与时间

**验收标准**
- 任一阶段失败后可在 `doctor` 中定位
- 不记录敏感凭证信息

## 4. `docs: rewrite README into scenario-first onboarding`

**背景**  
README 目前偏命令手册，新手可能仍需上下跳读。

**范围**
- 首屏聚焦 3 分钟路径
- 将“中断续跑、回滚恢复、彻底重装”做成独立场景

**验收标准**
- 新用户可按顺序完成 setup，无需全文搜索
- 关键场景至少各 1 个可复制命令块

## 5. `test: add parser contract fixtures for lark-cli output variants`

**背景**  
`detect` 依赖 CLI 输出形态，未来版本变动可能导致误判。

**范围**
- 增加 fixtures（空输出、非 JSON、字段变体）
- 参数化测试 `parse_config_show/parse_auth_status`

**验收标准**
- 多种输出变体下行为稳定
- 回归测试可快速定位 parser 破坏

## 6. `test: add e2e rollback smoke script`

**背景**  
回滚能力关键，但当前主要由单测保障。

**范围**
- 增加脚本演练 `update -> rollback`
- 输出 PASS/FAIL 摘要

**验收标准**
- 本地和 CI 可执行
- 演练后技能目录与 manifest 状态恢复成功

## 7. `feat: support status --json output`

**背景**  
运维/自动化集成需要机器可读状态。

**范围**
- `lark-bridge status --json`
- 字段覆盖环境、工作区、技能、权限快照摘要

**验收标准**
- JSON 输出可解析且字段稳定
- 文档给出字段说明

## 8. `chore: automate release gate checks`

**背景**  
发布门禁目前主要依赖人工 checklist。

**范围**
- 脚本化检查版本一致性、测试状态、关键文档更新
- 输出阻断项与建议修复

**验收标准**
- 一条命令输出“可发布/不可发布”
- 与 `docs/release-gate.md` 对齐
