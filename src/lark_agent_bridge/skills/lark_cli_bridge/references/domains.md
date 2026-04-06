# 官方 lark-cli Agent Skills（领域索引）

以下对应 `larksuite/cli` 仓库中 `skills/` 下各包，可通过：

```bash
npx skills add larksuite/cli -y -g
npx skills add larksuite/cli -s <name> -y
```

按需安装单域。在 CoPaw 中完成任务时，优先用本机 `lark-cli` + 下表「典型场景」选择领域；细节以官方 SKILL 与 `lark-cli --help` 为准。

| Skill 包名 | 典型场景 |
|------------|----------|
| lark-calendar | 日历、日程、忙闲 |
| lark-im | 即时消息、群聊 |
| lark-contact | 联系人搜索 |
| lark-doc | 云文档 |
| lark-drive | 云空间、文件 |
| lark-sheets | 电子表格 |
| lark-base | 多维表格 |
| lark-wiki | 知识库 |
| lark-task | 任务 |
| lark-mail | 邮件 |
| lark-vc | 视频会议 |
| lark-minutes | 纪要 |
| lark-event | 活动/日程相关扩展 |
| lark-approval | 审批 |
| lark-whiteboard | 白板 |
| lark-workflow-meeting-summary | 会议摘要工作流 |
| lark-workflow-standup-report | 站会报告工作流 |
| lark-openapi-explorer | 从官方文档挖掘未封装 API |
| lark-skill-maker | 自定义 skill 辅助 |
| lark-shared | 配置、登录、身份、权限通用规则 |

**说明**：上表用于「找对领域」；**实际执行的命令**以当前安装的 `lark-cli` 版本 `help` 为准。
