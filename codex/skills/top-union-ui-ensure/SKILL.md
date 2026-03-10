---
name: top-union-ui-ensure
description: Ensure the local Top Union UI for fp-detector is running through the single supported entrypoint at scripts/run_top_union_ui_server.sh ensure. Use when a Codex session needs to open, verify, restart, or troubleshoot the local Top Union review UI against the remote DB without hand-writing python server commands or ad-hoc SSH tunnels.
---

# Top Union Ui Ensure

## Overview

用于 `fp-detector` 仓库里的本地 Top Union UI 守护场景。

固定原则：
- 只允许使用 `scripts/run_top_union_ui_server.sh ensure` 作为启动入口。
- 不要直接运行 `fp-detector-server`、`python -m fp_detector.server` 或手写 `ssh -L`。
- 验证顺序固定为 `ensure -> status -> health`，必要时再看 `logs`。

默认仓库路径：
- `/Users/kezheng/Codes/CursorDeveloper/fp-detector`

默认访问地址：
- UI: `http://127.0.0.1:18001/v1/fp/top-union/ui`
- Health: `http://127.0.0.1:18001/healthz`

## Workflow

### 1. 切到仓库根目录

```bash
cd /Users/kezheng/Codes/CursorDeveloper/fp-detector
```

### 2. 统一入口确保服务可用

```bash
scripts/run_top_union_ui_server.sh ensure
```

### 3. 立即验证

```bash
scripts/run_top_union_ui_server.sh status
scripts/run_top_union_ui_server.sh health
```

### 4. 如仍异常，再看日志

```bash
scripts/run_top_union_ui_server.sh logs
```

## Output Requirements

执行这个 skill 后，回答里至少包含：
- 是否执行了 `ensure`
- `status` 结果
- `health` 结果
- 本地 UI URL

## Common Mistakes

- 直接手写 `python -m fp_detector.server`
- 直接手写 `ssh -L ...`
- 跳过 `status` / `health` 就声称“已经好了”
- 在别的工作目录执行这个 skill
