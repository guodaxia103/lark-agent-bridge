---
name: lark_cli_bridge
description: "Full access to the official Feishu/Lark CLI (lark-cli) on this machine: any service, shortcut, or raw OpenAPI via lark-cli api. Use discovery commands first (--help, schema), then execute. Separate from the built-in Feishu bot channel; often uses user OAuth. See references/ for domain map and auth rules."
metadata:
  copaw:
    emoji: "🪶"
    requires: {}
---

# Lark CLI Bridge（飞书官方 CLI 全能力）

当用户需要通过 **本机安装的 `lark-cli`** 操作飞书（任意开放 API 能力）时，启用本技能。目标：**不遗漏 CLI 已暴露的能力**——包括快捷命令、动态注册的 API 命令、以及裸 `api` 调用。

## 与 CoPaw 内置「飞书通道」的关系

| 方式 | 说明 |
|------|------|
| 内置飞书通道 | 机器人在飞书 App 内收发信息 |
| 本技能 | 在 **CoPaw 所在电脑** 上执行 `lark-cli`，多为 **用户 OAuth** 身份，可访问用户日历、邮箱等资源（取决于授权） |

两者可并存，凭证与权限模型不同，不要混为一谈。

## 能力范围（如何做到「全功能」）

`lark-cli` 的能力分三层，**按顺序尝试**：

1. **快捷命令（Shortcuts）**  
   `lark-cli calendar +agenda` 这类。用 `lark-cli <可能的服务名> --help` 查看当前安装版本下有哪些命令。

2. **已注册的 OpenAPI 命令树**  
   `lark-cli <service> <resource> <method> --params '...'`。用 `lark-cli <service> --help` 逐级查看。

3. **任意原生 OpenAPI（未被封装时）**  
   ```bash
   lark-cli api GET /open-apis/...
   lark-cli api POST /open-apis/... --data '{...}'
   ```
   路径与参数需与飞书开放平台文档一致。可先查 `lark-cli schema <service.resource.method>`（若可用）。

**发现命令（必会）**：

```bash
lark-cli --help
lark-cli doctor
```

详细说明见同目录 **`references/discovery.md`**。

## 必读参考（用 read_file 打开）

| 文件 | 内容 |
|------|------|
| `references/discovery.md` | 如何发现任意子命令、schema、api |
| `references/domains.md` | 官方 Agent Skills 领域与 `npx skills add` 对应关系 |
| `references/auth_and_identity.md` | 用户/bot 身份、`--as`、权限与登录；**`auth login` 在 Agent 中请加 `--json`**（stdout 出授权信息） |
| `references/output_and_errors.md` | JSON、`--jq`、退出码、`_notice` |

若用户已用 `npx skills add larksuite/cli` 安装官方 Skills，那些 Markdown 在**本机 skills 目录**；本包内的 `references` 是精简版，保证在 CoPaw 内可读。

## 执行方式

使用 **`execute_shell_command`**，**一条命令一行**（避免无关的 `&&` / `|`）。默认加 `--format json` 便于解析：

```bash
lark-cli --format json doctor
```

```bash
lark-cli --format json --as user calendar +agenda
```

需要 **用户身份** 访问个人日历时，加 `--as user`；仅应用后台资源可用 `--as bot`（见 `references/auth_and_identity.md`）。

### `auth login` only (agents / IDE shell)

When running **`lark-cli auth login`** from an agent or IDE tool, **append `--json`** so the verification URL is on **stdout** as JSON (`verification_uri_complete`, etc.). Default mode prints the link on **stderr**, which many UIs hide from the main “Output”. This applies **only** to `auth login`; do **not** add `--json` to other commands for this reason—other commands keep using `--format json` as usual. Optional two-step: `--no-wait` then `auth login --device-code …`. See `references/auth_and_identity.md`.

## 写入 / 删除类操作

对**删除资源、批量修改、发大量消息**等，先向用户确认意图；可用 `--dry-run`（若该子命令支持）。

## 安全

- 勿将用户**原始长文本**直接拼进 shell 字符串；使用 `lark-cli` 提供的 `--query`、`--params` 等参数传递。
- 勿在命令中输出或记录 `appSecret`、token 明文。
