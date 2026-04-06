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

- User：按提示执行 `lark-cli auth login --scope "..."` 或 `--recommend`。
- Bot：引导用户打开 `console_url` 在后台开通权限。

## 配置应用

首次使用：

```bash
lark-cli config init --new
```

在终端中按提示在浏览器完成（需用户本人操作）。

## 安全

- 不要在日志中输出 appSecret、accessToken。
- 删除/批量操作前确认用户意图。
