# 身份与权限（user / bot）

## 两种身份

| 身份 | CLI 标志 | 典型用途 |
|------|----------|----------|
| 用户 | `--as user` | 用户日历、邮箱、个人云文档等 |
| 应用 / 机器人 | `--as bot` | 仅应用可用资源；**不能**当作用户个人资源 |

默认多为 `auto`，需根据报错与文档切换。

## 何时需要登录

- **User 能力**：需要用户在飞书开发者侧开通 scope，且本机执行过 `lark-cli auth login`（可按 scope 增量授权）。
- **Bot 能力**：通常只需 appId/appSecret；**不要**对 bot 误用 `auth login` 解决权限问题，应去开放平台开通 scope。

## 权限不足时

错误 JSON 中常有 `permission_violations`、`console_url`、`hint`。

- User：按提示执行 `lark-cli auth login --scope "..."` 或 `--recommend`（见下节 **Agent / IDE** 建议加 `--json`）。
- Bot：引导用户打开 `console_url` 在后台开通权限。

## 常见任务与 scope 速查（建议先核对）

| 场景 | 常见 scope 示例 | 建议命令 |
|------|------------------|----------|
| 读取知识库 / 文档 | `wiki:wiki:readonly` / `space:document:readonly` | `lark-cli auth check --scope "wiki:wiki:readonly"` |
| 读取日历 | `calendar:calendar:readonly` | `lark-cli auth check --scope "calendar:calendar:readonly"` |
| 发 IM 消息 | `im:message`（以实际后台命名为准） | `lark-cli auth check --scope "im:message"` |
| 读取通讯录 | `contact:user.base:readonly` | `lark-cli auth check --scope "contact:user.base:readonly"` |

说明：scope 命名以你租户后台与 `lark-cli auth scopes` 返回为准；上表用于快速定位思路。

## Agent / IDE 中执行 `auth login`（推荐 `--json`）

**现象**：默认（不加 `--json`）时，授权链接印在 **stderr**，成功后的业务 JSON 也在 **stdout** 很少；许多 IDE / Agent 面板只展示 **stdout**，或等进程结束才合并流，看起来像「很久没有任何输出」。

**做法（仅影响本条命令，不改变其它子命令行为）**：

1. **优先**：在原有 `scope` / `domain` / `recommend` 参数基础上 **追加 `--json`**。授权 URL 与 `user_code` 会在 **stdout** 打出一行 JSON（字段含 `verification_uri_complete`、`verification_uri` 等），便于 Agent 解析并展示给用户。OAuth 流程与默认模式相同，命令仍会 **阻塞轮询** 直到用户在浏览器完成授权或超时。
2. **可选**：`--no-wait` —— 仅发起设备授权并 **立即** 在 stdout 输出 JSON（含 `verification_url`、`device_code`），再让用户执行第二条：`lark-cli auth login --device-code <DEVICE_CODE>` 完成轮询（适合要先把链接交给用户、再后台等待的场景）。

**示例**（与仅缺 scope 时一致，多一个 `--json`）：

```bash
lark-cli auth login --scope "space:document:retrieve" --json
```

```bash
lark-cli auth login --recommend --json
```

**说明**：`--json` / `--no-wait` **只作用于 `auth login` 子命令**；`drive`、`wiki`、`calendar` 等其它命令仍按各自文档使用 `--format json` 等，**无需**因本节而改动。

## 配置应用

首次使用：

```bash
lark-cli config init --new
```

在终端中按提示在浏览器完成（需用户本人操作）。

## 清除本机授权与重新登录

以下为 **`lark-cli auth`** 子命令（非 `lark-bridge`）。

| 目的 | 命令 |
|------|------|
| 退出登录、清掉本机保存的用户 token | `lark-cli auth logout` |
| 重新授权（推荐/按需 scope） | `lark-cli auth login --recommend` 或 `lark-cli auth login --scope "..."` |
| 查看当前登录与 token 状态 | `lark-cli auth status`（可选 `--verify` 联网校验） |
| 列出已登录用户 | `lark-cli auth list` |
| 查询应用已开通的用户权限（开放平台侧） | `lark-cli auth scopes` |
| 检查当前 token 是否包含指定 scope | `lark-cli auth check --scope "scope1 scope2"` |

**说明**：`logout` 只清除**本机**凭证；若要在飞书账号侧撤销对某应用的授权，需在飞书客户端或开放平台按官方入口操作。子命令列表以 `lark-cli auth --help` 为准。

## 安全

- 不要在日志中输出 appSecret、accessToken。
- 删除/批量操作前确认用户意图。
