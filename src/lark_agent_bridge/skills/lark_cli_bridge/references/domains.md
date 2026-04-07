# 官方 lark-cli Agent Skills（领域索引）

以下对应 `larksuite/cli` 仓库中 `skills/` 下各包，可通过：

```bash
npx skills add larksuite/cli -y -g
npx skills add larksuite/cli -s <name> -y
```

按需安装单域。在 CoPaw 中完成任务时，优先用本机 `lark-cli` + 下表「典型场景」选择领域；细节以官方 SKILL 与 `lark-cli --help` 为准。

| Skill 包名 | CLI 顶层命令 | 典型场景 |
|------------|-------------|----------|
| lark-calendar | `calendar` | 日历、日程、忙闲 |
| lark-im | `im` | 即时消息、群聊 |
| lark-contact | `contact` | 联系人搜索 |
| lark-doc | `docs` | 云文档 |
| lark-drive | `drive` | 云空间、文件 |
| lark-sheets | `sheets` | 电子表格 |
| lark-base | `base` | 多维表格 |
| lark-wiki | `wiki` | 知识库 |
| lark-task | `task` | 任务 |
| lark-mail | `mail` | 邮件 |
| lark-vc | `vc` | 视频会议 |
| lark-minutes | `minutes` | 纪要 |
| lark-event | `event` | 事件订阅 |
| lark-approval | `approval` | 审批 |
| lark-whiteboard | `whiteboard` | 白板 |
| lark-workflow-meeting-summary | — | 会议摘要工作流（组合命令） |
| lark-workflow-standup-report | — | 站会报告工作流（组合命令） |
| lark-openapi-explorer | — | 从官方文档挖掘未封装 API |
| lark-skill-maker | — | 自定义 skill 辅助 |
| lark-shared | `config`, `auth` | 配置、登录、身份、权限通用规则 |

**说明**："CLI 顶层命令"列为 `lark-cli <命令> --help` 的入口名称，以本机安装版本为准（`lark-cli --help` 查看完整列表）。标"—"的是工作流或辅助包，不直接对应单一 CLI 命令。
