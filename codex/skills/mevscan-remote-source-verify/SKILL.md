---
name: mevscan-remote-source-verify
description: Use when you need to verify MEVScan block JSON or transaction MEV status on the remote source machine (mevscan-source), especially when the only input is a tx hash and the block number must be resolved from public RPC before checking runtime-data/analyzeMEVs and runtime-data/reviewMEVs.
---

# MEVScan Remote Source Verify

用于远程源头机 `mevscan-source` 的 MEV 验证：给一个 `tx hash`，先用公共 RPC 自动取 `blockNumber`，再去远端 JSON 里确认这笔交易是否被写进 `mev_reports`。

## 触发

- 用户只给 `tx hash`
- 要核对某块的 `analyzeMEVs` / `reviewMEVs`
- 要确认某笔交易是否被标成 `ARBITRAGE`、`LIQUIDATION`、`SANDWICH` 或 `JIT`

## 固定流程

1. 读 `~/.codex/remote-hosts.md`，确认 `mevscan-source`
2. 用公共 RPC 调 `eth_getTransactionByHash`
3. 取 `blockNumber`，在 `mevscan-source` 的 `/mnt/data/mevscan/runtime-data/{analyzeMEVs,reviewMEVs}` 里找对应 block JSON
4. grep 目标 `tx hash`，检查 `mev_reports`

## 推荐入口

- `scripts/verify_tx_on_remote_source.sh <tx_hash> [rpc_url] [remote_alias]`

这个脚本应直接输出：

- 一行 `verdict`，用于快速判断
- `block_number`
- `pipeline_state`
- `mev_summary`
- 目标交易的 `mev_reports`

## 判定规则

- 命中 `mev_reports` 就说“已被标成 MEV”
- 只有 `mev_summary.arbitrage_count` 但目标交易不在 `mev_reports`，就说“该块有 MEV，但这笔交易不是其中之一”
- 只找到 `traceBlock` / `parseActions`，不要声称完成 MEV 验证

## 必带证据

- `command`
- `exit_code`
- `key_output`
- `timestamp`

## 常见错误

- 不要要求用户先给 block number
- 不要用裸 IP 代替 alias
- 不要把 `parseActions` 误当成 `analyzeMEVs`
- 不要只看 `mev_summary`，必须落到具体交易的 `mev_reports`
