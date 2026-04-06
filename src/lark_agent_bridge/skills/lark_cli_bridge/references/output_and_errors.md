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
