# Error Codes

`lark-agent-bridge` 关键失败路径使用统一错误码，格式为 `LAB-模块-序号`。

## Exit Code Convention

- `1`: 通用失败（依赖缺失、文件写入失败、参数错误）
- `2`: 需要用户行动后重试（配置/登录/scope 授权）
- `127`: 外部可执行文件不存在（主要用于透传 `lark-cli`）

## Error Catalog

| 错误码 | Exit | 说明 |
|------|------|------|
| `LAB-CLI-001` | 1 | 参数冲突或命令使用错误（如 `--workspace` 与 `--all-workspaces` 同时传） |
| `LAB-CLI-002` | 1 | 未找到 CoPaw 工作区 |
| `LAB-SETUP-001` | 1 | Python 版本不满足要求 |
| `LAB-SETUP-002` | 1 | Node/npm/lark-cli 依赖缺失 |
| `LAB-SETUP-003` | 2 | 需要先完成 `lark-cli config init` |
| `LAB-SETUP-004` | 2 | 需要先完成 `lark-cli auth login` |
| `LAB-DEPLOY-001` | 1 | 部署或写入工作区失败 |
| `LAB-BACKUP-001` | 1 | 备份创建或恢复失败 |
| `LAB-BACKUP-002` | 1 | 未找到可用备份 |
| `LAB-PERMS-001` | 1 | 权限快照依赖缺失 |
| `LAB-PERMS-002` | 2 | scope 不满足，需要补授权 |
| `LAB-VERIFY-001` | 1 | `verify` 的硬失败（CLI 本体不可用） |
| `LAB-FORWARD-001` | 127 | 透传模式未找到 `lark-cli` |

## Output Format

所有统一失败输出包含以下结构：

1. 错误码与原因（`[×][LAB-XXXX] ...`）
2. 建议执行命令（可复制）
3. 建议检查项（可选）

