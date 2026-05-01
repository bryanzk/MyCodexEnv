---
name: top-union-daily-report
description: Use when generating or verifying an fp-detector Top Union daily report for a specific local cutoff time, especially when the agent needs to remember the report script, environment loading, timezone/report-time parameters, output file path, and required verification evidence.
---

# Top Union Daily Report

## Overview

用于 `fp-detector` 仓库里生成 Top Union 每日报告。

输出日报、解释统计口径或总结阻塞时，先读取并遵守 [TERMS.md](TERMS.md)。不要用泛化词替代其中定义的业务字段、口径和验证术语。

核心原则：
- 统一走 `scripts/daily_top_union_fp_report.py`，不要手写一段新的统计脚本。
- 当前值必须优先取自本地 Top Union UI HTTP 接口 `/v1/fp/top-union/latest-preview`，不要混用 open session 口径，也不要直接假设本地 service 直算就一定等于 UI。
- 默认过滤项必须跟随 UI 的 `available_high_confidence_filters[].default_selected`，不要手写另一套默认 token。
- “昨天”的值优先取输出目录里上一日的日报结果；优先读 `top_union_daily_YYYYMMDD.json`，没有再读同名 Markdown；仍取不到就留空。
- 默认先 `--skip-feishu`，除非用户明确要求发送。
- 结果必须同时检查 JSON stdout 和落盘的 Markdown 报告。
- 回答用户时必须带验证证据：`command`、`exit_code`、`key_output`、`timestamp`。

## When to Use

适用于这些场景：
- 用户要求“生成日报”“跑一下 18:30 / 19:30 的日报”
- 用户要查看某个本地时点的 Top Union preview 日报
- 用户要确认日报文件路径、关键指标、昨天对比信息
- 用户要求按当前日报 API 口径复现一份 Markdown 报告

不适用于这些场景：
- 用户要修改日报统计口径或 API 契约
- 用户要自定义 `safe_default_filter_tokens`；当前脚本不暴露该参数，应改走 service/API
- 用户要跑 Top Union UI，会话应改用 `top-union-ui-ensure`

## Workflow

### 1. 进入当前会话 worktree 或仓库

优先在当前 `fp-detector` worktree 内执行，不要切回共享主 checkout。

```bash
cd /Users/kezheng/Codes/CursorDeveloper/fp-detector-sessions/<session-id>
```

如果当前就在正确目录，可跳过。

### 2. 加载服务环境变量

日报脚本依赖仓库根 `.env`。

```bash
set -a
source /Users/kezheng/Codes/CursorDeveloper/fp-detector/.env
set +a
```

如果要确保和当前 UI 完全同源，先确保本地 UI 服务可用：

```bash
scripts/run_top_union_ui_server.sh ensure
scripts/run_top_union_ui_server.sh status
scripts/run_top_union_ui_server.sh health
```

### 3. 运行日报脚本

默认时区是 `America/Toronto`。如果用户只说“6:30 pm”，把它转成 `18:30`。

```bash
uv run python scripts/daily_top_union_fp_report.py \
  --report-time HH:MM \
  --timezone America/Toronto \
  --skip-feishu
```

例如生成 `18:30` 的日报：

```bash
uv run python scripts/daily_top_union_fp_report.py \
  --report-time 18:30 \
  --timezone America/Toronto \
  --skip-feishu
```

### 4. 读取脚本输出

脚本 stdout 会返回一段 JSON，至少要检查：
- `output`
- `output_json`
- `report_date`
- `preview_fp_rate`
- `preview_fp_tx`
- `union_count`
- `candidate_total_24h`
- `yesterday_report_found`
- `mom_baseline_found`

### 5. 打开 Markdown 报告

用 stdout 里的 `output` 路径读取实际报告内容，确认：
- 标题里的 `report_time` 正确
- 报告主体是以下结构，而不是旧版 delta/baseline 模板：

```markdown
# Top 1% Union 每日报告（report time）

核心指标（19:30 口径）
误报率: 9.4%（昨天10.2%）
FP 笔数: 20（昨天35）
Union 笔数: 216（昨天252）
24h 候选池笔数: 15014（昨天16840）

统计口径为：去掉高置信误报规则后的Top 1% Profit & Revenue 候选集合
```

- 当前值来自 latest preview UI：
  - 脚本会优先调用本地 UI HTTP 接口，再按 UI 的 `default_selected` 过滤项二次刷新。
  - `误报率` -> `preview_fp_rate`
  - `FP 笔数` -> `preview_fp_tx`
  - `Union 笔数` -> `union_count`
  - `24h 候选池笔数` -> `candidate_total_24h`
- “昨天”值来自上一日日报；如果缺失，应保持空白样式 `（昨天）`，不要擅自改成别的基线

## Quick Reference

| 用户意图 | 命令 |
| --- | --- |
| 跑 19:30 日报 | `uv run python scripts/daily_top_union_fp_report.py --report-time 19:30 --timezone America/Toronto --skip-feishu` |
| 跑 18:30 日报 | `uv run python scripts/daily_top_union_fp_report.py --report-time 18:30 --timezone America/Toronto --skip-feishu` |
| 需要发 Feishu | 去掉 `--skip-feishu`，并确认 `.env` 里有 webhook |

## Output Requirements

执行这个 skill 后，回答里至少包含：
- 实际统计时点和时区
- 报告文件路径
- JSON 侧车路径
- `preview_fp_rate`
- `preview_fp_tx`
- `union_count`
- `candidate_total_24h`
- 是否成功读取上一日日报
- 验证证据四元组：`command`、`exit_code`、`key_output`、`timestamp`

## Common Mistakes

- 忘记 `source /Users/kezheng/Codes/CursorDeveloper/fp-detector/.env`
- 只看 stdout JSON，不打开 Markdown 报告
- 用户说的是本地时间，却直接按 UTC 理解
- 把 `6:30 pm` 写成 `6:30`
- 用户没要求发送，却去掉了 `--skip-feishu`
- 看到旧文案缓存，没有确认报告标题里的实际 `report_time`
- 把“昨天”值错误地用成 `mom_baseline` 或别的实时基线，而不是上一日日报
- 没有检查 `FP 笔数` 是否已映射到 `preview_fp_tx`
- UI 默认过滤项已经变化，但脚本/人工复现还在手写旧 token

## Red Flags

出现这些情况时，先停下再核对：
- 还没跑脚本就直接报数字
- 没有 `output` 路径却声称“日报已生成”
- 只说“成功生成”，但没有验证证据
- 用户要的是日报，你却改去调用别的统计脚本
- “昨天”值明明缺失，却被你用别的数字补上了
