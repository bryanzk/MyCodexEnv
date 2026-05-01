# Top Union Daily Report Terms

Use these terms exactly when generating, verifying, or explaining Top Union daily reports.

## Required Terms

- `Top 1% Union`: the candidate set after applying the Top 1% Profit and Top 1% Revenue union logic.
- `Top 1% Profit & Revenue 候选集合`: the report-facing Chinese wording for the Top 1% Union candidate set.
- `latest preview UI`: the local Top Union UI HTTP source for current values.
- `/v1/fp/top-union/latest-preview`: the authoritative HTTP endpoint for current preview values.
- `UI default_selected filters`: filters derived from `available_high_confidence_filters[].default_selected`.
- `高置信误报规则`: the report-facing Chinese wording for high-confidence false-positive filters.
- `误报率`: report value mapped from `preview_fp_rate`.
- `FP 笔数`: report value mapped from `preview_fp_tx`.
- `Union 笔数`: report value mapped from `union_count`.
- `24h 候选池笔数`: report value mapped from `candidate_total_24h`.
- `上一日日报`: the previous daily report used for yesterday values.
- `sidecar JSON`: the persisted `top_union_daily_YYYYMMDD.json` file beside the Markdown report.
- `Markdown report`: the persisted daily report file named by the script output.
- `验证证据四元组`: `command`, `exit_code`, `key_output`, and `timestamp`.

## Do Not Use As Substitutes

- Do not say `open session 口径` when the value came from latest preview UI.
- Do not say `service 直算口径` when the value came from `/v1/fp/top-union/latest-preview`.
- Do not call `mom_baseline` "昨天"; yesterday must come from `上一日日报`.
- Do not replace `FP 笔数` with generic wording like `问题数`, `命中数`, or `错误数`.
- Do not replace `Union 笔数` with generic wording like `总数` or `集合大小` unless explicitly explaining the mapping.
- Do not say `已通过验证` without the `验证证据四元组`.

## Preferred Output Phrases

- `当前值来自 latest preview UI，并按 UI default_selected filters 刷新。`
- `昨天值来自上一日日报 sidecar JSON；缺失时保持空白，不回填其他基线。`
- `统计口径为：去掉高置信误报规则后的 Top 1% Profit & Revenue 候选集合。`
- `验证证据：command / exit_code / key_output / timestamp。`
