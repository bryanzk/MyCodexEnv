# Codex model tiers and custom agents

核验日期：2026-08-22
本机 Codex：`codex-cli 0.147.0`

## 配置键核验

### Custom-agent 文件：verified

本机原始证据：

```text
$ codex --version
WARNING: proceeding, even though we could not create PATH aliases: Operation not permitted (os error 1)
codex-cli 0.147.0

$ codex --help
-c, --config <key=value>
    Override a configuration value that would otherwise be loaded from `~/.codex/config.toml`.
    Use a dotted path (`foo.bar.baz`) to override nested values.
```

官方文档：[Subagents](https://developers.openai.com/codex/multi-agent/)

> To define your own custom agents, add standalone TOML files under `~/.codex/agents/` for personal agents or `.codex/agents/` for project-scoped agents.

文档要求的不是 frontmatter，而是 standalone TOML 顶层字段：`name`、`description`、`developer_instructions`。`model`、`model_reasoning_effort` 和 `sandbox_mode` 是支持的普通 `config.toml` 键。仓库因此以 `codex/agents/*.toml` 为源码，由同步脚本落到 `~/.codex/agents/`。

### `[agents]`：verified

本机原始证据：

```text
$ codex app-server --help
generate-json-schema  [experimental] Generate JSON Schema for the app server protocol

$ codex app-server generate-json-schema --experimental --out /tmp/mce-p0-2-schema.Wo9zAy
exit_code=0
```

官方文档：[Configuration Reference](https://developers.openai.com/codex/config-reference/)

> Multi-agent settings and custom role declarations. Scalar setting names are reserved and can't be used as custom role names.

当前文档列出的字段是：`agents.<name>.config_file`、`agents.<name>.description`、`agents.default_subagent_model`、`agents.default_subagent_reasoning_effort`、`agents.enabled`、`agents.interrupt_message`、`agents.max_concurrent_threads_per_session`。旧的 `agents.max_threads` 仅为 legacy alias。本切片只安装 standalone custom-agent 文件，不新增全局 `[agents]` 默认值。

### `fork_turns`：unverified / open question

本机原始证据：

```text
$ rg -n 'fork_turns|forkTurns|spawn_agent|spawnAgent' /tmp/mce-p0-2-schema.Wo9zAy
exit_code=1
key_output=(empty)

$ rg -n 'fork_turns|forkTurns|spawn_agent|spawnAgent' ~/.npm-global/lib/node_modules/@openai/codex
exit_code=1
key_output=(empty)
```

官方文档：[Subagents](https://developers.openai.com/codex/multi-agent/)

> Explicit spawn values override.

当前宿主的 `spawn_agent` 工具 schema 暴露 `fork_turns`，并描述 `none`、`all` 或正整数字符串，但 Codex CLI 0.147.0 的生成 schema、已安装包和官方 Subagents 页面均未给出该参数或取值合同。因此不能把宿主工具的字段推断成可持久化 Codex 配置；P0-2 不写 `fork_turns`，后续须由公开 Codex schema 或官方文档单独核实。

## P0-1 基线事实与 A/B 臂

P0-1 governed run 1 观测到：压缩约在 67.5 万 token 触发，之后 9 轮重新增长到约 58.8 万；每次 `exec` 都重发整个上下文；每个会话固定起步约 36.5K uncached input。它们说明压缩阈值本身值得实验，但不构成本切片的节省结论。

`model_auto_compact_token_limit` 因此列为 A/B 的第三臂，候选值为 `300000` 与 `500000`。P0-2 仍按 owner D1 把模板基准设为 `900000`；本切片不运行第三臂、不生成 after 基线，也不把候选值写进 runtime。

## follow-ups

- `observations[5]` 的 `key_output` 含运行派生值，等价性比较时忽略。
- AC-16 是 `source_stage_unsynced` 状态下的一次性快照，首次提升后不可重新捕获；validator 自本 commit 起按 `captured_in_commit` 的 author date 绑定，不再绑 artifact 最近 commit。动 `tests/fixtures/dhf_simplification_*` 的 commit 之后必须再跑一次门禁。
- `dhf_simplification_evidence.py` 的 `BASE_COMMIT` 固定为 `00818ae`，首次提升后 `source_stage_unsynced` 不可达；任何 skill 源改动必须同交付提升；P1 处理。
- sync guard 要求 `HEAD == origin/main`，因此 skill/hook 源改动的交付顺序固定为 commit → push → sync → 门禁；P0-2 的两次 push 即由此触发。
- sync 会把 `model_reasoning_effort` 重置为模板值，owner 手动值每次 sync 后需重设或改模板。
- skill 源改动需同时刷新 paired gate 的 transition/candidate manifest；先跑 `python3 scripts/harness_refresh_identity.py status`，改动后用 `python3 scripts/harness_refresh_identity.py refresh --message "<备注>" [--approve]`。
