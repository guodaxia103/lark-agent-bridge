# V1 Delivery Backlog (2 Weeks)

目标：让 `lark-agent-bridge` 达到“小白可交付”标准，优先保障首次成功率与可恢复性。

## Sprint Scope

- 周期：2 周
- 角色：产品/开发/测试
- 验收基线：`python -m pytest tests -q` 全绿 + CI 全绿 + Nightly E2E 最近一次成功

## P0 (Must)

### 1. 错误码与提示文案标准化

- Owner: 开发
- 说明: 为常见失败场景定义稳定错误码和统一模板（原因、建议命令、检查项）
- 交付:
  - `docs/error-codes.md`
  - `cli.py` 中关键命令统一使用
- 验收:
  - 至少覆盖 `setup/resume/update/upgrade/perms/uninstall`
  - 测试覆盖文案关键片段

### 2. 备份清理策略

- Owner: 开发
- 说明: 当前备份会持续累积，需要可配置保留策略（例如每工作区保留最近 N 个）
- 交付:
  - `rollback` 新增 `--keep` 或 `cleanup` 子命令
  - 自动清理机制（默认保留 10 个）
- 验收:
  - 超出阈值自动删除最旧备份
  - 测试覆盖排序与清理边界

### 3. 安装链路首次成功率埋点（本地）

- Owner: 产品 + 开发
- 说明: 不上报隐私，仅本地结构化日志，便于支持排障
- 交付:
  - `~/.qwenpaw/...`（兼容 `~/.copaw/...`）下生成最近一次 setup/resume 结果摘要
  - `doctor` 展示最近失败阶段
- 验收:
  - 失败阶段可定位到 Python/Node/lark-cli/config/auth/deploy 任一阶段

## P1 (Should)

### 4. README 场景化重构

- Owner: 产品 + 文档
- 说明: 以“首次安装、续跑、回滚、重装”四条路径重排文档
- 交付:
  - 新增“3 分钟快速成功路径”
  - 常见错误改为“复制即用命令”
- 验收:
  - 新用户无需阅读全文即可完成 setup

### 5. Detect 解析契约测试

- Owner: 测试
- 说明: 构造多版本 `lark-cli` 输出 fixtures，锁定 parser 行为
- 交付:
  - `tests/fixtures/lark_cli_outputs/*.json|txt`
  - 对 `parse_config_show/parse_auth_status` 的参数化测试
- 验收:
  - 新增测试覆盖异常输出、空输出、字段变体

### 6. 回滚演练脚本

- Owner: 测试
- 说明: 提供一键演练 update -> rollback 流程
- 交付:
  - `scripts/e2e_rollback_smoke.*`
- 验收:
  - 在 CI 或本地可一键执行并输出 PASS/FAIL

## P2 (Could)

### 7. `status` 机器可读输出

- Owner: 开发
- 说明: 新增 `--json` 方便外部工具集成
- 交付:
  - `status --json`
- 验收:
  - 字段稳定，文档明确

### 8. 发布自动门禁脚本化

- Owner: 开发
- 说明: 将 release gate checklist 部分自动化
- 交付:
  - `scripts/release_gate.py` 或 make target
- 验收:
  - 一条命令输出“可发布/阻断项”

## Suggested Issue Titles

1. `feat: add structured error codes and unified failure template`
2. `feat: implement backup retention policy for workspace backups`
3. `feat: persist setup/resume stage summary for doctor diagnostics`
4. `docs: rewrite README into scenario-first onboarding`
5. `test: add parser contract fixtures for lark-cli output variants`
6. `test: add e2e rollback smoke script`
7. `feat: support status --json output`
8. `chore: automate release gate checks`
