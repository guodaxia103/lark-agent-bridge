# 发现 lark-cli 的全部命令

## 1. 根帮助

```bash
lark-cli --help
```

查看顶层命令：`config`、`auth`、`api`、`schema`、`doctor` 以及各业务域入口（如 `calendar`、`im`、`contact` 等，随版本与 meta 数据可能增减）。

## 2. 逐级 help

```bash
lark-cli calendar --help
lark-cli im --help
```

对不确定的服务名，先 `lark-cli --help` 列出再下钻。

## 3. doctor

```bash
lark-cli doctor
```

检查 CLI、缓存、登录等环境（输出为 JSON 时可加 `--format json`）。

## 4. schema（若构建中包含 meta）

```bash
lark-cli schema --help
lark-cli schema some.service.method --format pretty
```

用于查看某 API 方法的参数结构（具体可用名称以本机 `--help` 为准）。不是所有版本都包含 schema，执行前先 `lark-cli schema --help` 确认可用。

## 5. 裸 HTTP：覆盖「CLI 未封装」的任意 OpenAPI

```bash
lark-cli api GET /open-apis/calendar/v4/calendars
lark-cli api POST /open-apis/... --data '{"field":"value"}'
```

路径、方法与 body 以飞书开放平台文档为准：飞书 `https://open.feishu.cn/llms.txt`、Lark `https://open.larksuite.com/llms.txt`。

## 6. 官方 Agent Skills（扩展阅读）

安装后可在本机阅读各域最佳实践（与 QwenPaw 的 `read_file` 独立，需用户已执行）：

```bash
npx skills add larksuite/cli -y -g
```

领域列表见同目录 `domains.md`。

## 7. 推荐回退策略（减少版本差异导致的失败）

按下面顺序执行，成功率最高：

1. 先试领域命令：`lark-cli <domain> --help`
2. 再查 schema（若可用）：`lark-cli schema ...`
3. 最后用裸 API：`lark-cli api GET/POST /open-apis/...`

示例：

```bash
lark-cli wiki --help
# 若没有目标子命令，再退到：
lark-cli api GET /open-apis/wiki/v2/spaces
```
