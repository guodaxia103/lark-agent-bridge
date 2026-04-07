# 输出格式与错误

## 推荐格式

```bash
lark-cli --format json ...
```

可选：`ndjson`、`table`、`csv`、`pretty`。需要过滤时用：

```bash
lark-cli --format json ... --jq '.some.path'
```

## 成功响应

- 可能含 `_notice`（如版本更新提示）；若有 `_notice.update`，可在完成用户任务后建议用户升级 CLI。

## 失败响应

stderr 常为 JSON envelope：`ok: false`、`error.type`、`error.message`、`hint`。

## `auth login` 的输出（例外）

- **默认**：提示语与 **授权链接** 写在 **stderr**；进程会长时间阻塞直到用户完成浏览器授权，此期间 **stdout 可能几乎为空**。若你的环境只显示 stdout，会误以为「没有链接」。
- **Agent / IDE**：对 **`auth login` 子命令** 追加 **`--json`**，则设备授权信息在 **stdout** 输出 JSON（与「其它命令的 `--format json`」无关，不要混用）。详见 `auth_and_identity.md`。

## 退出码（常见约定）

| 码 | 含义 |
|----|------|
| 0 | 成功 |
| 1 | API / 业务错误 |
| 2 | 参数错误 |
| 3 | 认证失败 |
| 4 | 网络错误 |
| 5 | 内部错误 |

3 时优先检查 `lark-cli auth status` 并引导重新登录或补 scope。
