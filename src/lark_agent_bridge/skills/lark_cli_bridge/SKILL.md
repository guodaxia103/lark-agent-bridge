---
name: lark_cli_bridge
description: "Use the official Feishu/Lark CLI (lark-cli) on this machine to read calendars, search contacts, send IM, and more. Prefer whitelist commands only; parse JSON output. This is separate from the built-in Feishu bot channel."
metadata:
  copaw:
    emoji: "🪶"
    requires: {}
---

# Lark CLI Bridge

When the user asks to operate Feishu/Lark in ways that need the **official command-line tool** (`lark-cli`), use this skill.

## Relationship to the built-in Feishu channel

- **Built-in Feishu channel**: bot receives/sends messages inside Feishu apps.
- **This skill**: the assistant runs **`lark-cli`** on the **same computer** as CoPaw, usually under the **user OAuth** identity configured for `lark-cli`.

They can coexist. Do not assume they use the same app credentials.

## Prerequisites

1. `lark-cli` is installed and on `PATH`.
2. The user has completed `lark-cli config` and `lark-cli auth login` (or equivalent).

If commands fail with auth errors, tell the user to run in a terminal:

```bash
lark-cli auth login --recommend
```

## How to run commands

Use the **`execute_shell_command`** tool with a **single** command line. **Do not** chain shell operators (`&&`, `;`, `|`) with unrelated dangerous operations.

Default output is JSON. Example:

```bash
lark-cli --format json calendar +agenda
```

```bash
lark-cli --format json auth status
```

## Allowed areas (examples only)

Adjust to the user request; stay within safe, read-only or normal business operations:

- Calendar: shortcuts like `calendar +agenda` (see `lark-cli --help` and official docs).
- IM / Messenger: follow official shortcut names under the `im` service.
- Contacts: search users as documented by `lark-cli contact`.
- Docs / Drive: use documented shortcuts; avoid destructive bulk deletes.

**Do not** run: `config remove`, destructive `rm`-style shell, or piping remote scripts.

## Parsing output

- Successful JSON may include `_notice` hints; still treat the payload as authoritative when `ok` is true.
- On failure, stderr often contains a JSON envelope with `error.type`, `error.message`, and sometimes `hint`.

## Exit codes (lark-cli)

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | API / general error |
| 2 | Bad arguments |
| 3 | Auth failure |
| 4 | Network error |
| 5 | Internal error |

If exit code is **3**, ask the user to re-authenticate with `lark-cli auth login --recommend`.

## Safety

- **Do not** interpolate raw user text directly into shell commands (injection risk).
- Prefer fixed subcommands from this whitelist style; if user gives a free-form query, pass it only through `lark-cli` flags documented to accept queries safely.
