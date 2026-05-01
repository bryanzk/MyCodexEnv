---
name: arbitrage-fp-by-code
description: Use when a pipeline-ts arbitrage label looks wrong or missing and you need to trace the result through transfer simplification, address grouping, cycle detection, nearest-node selection, or balance-delta rules.
---

# Arbitrage FP by Code

## Overview

用 `pipeline-ts` 源码解释某笔交易为什么被识别成 arbitrage，或为什么这是一个 arbitrage 误报。arbitrage 不是按 protocol action 判定，而是按 `Transfer -> simplify -> cycle -> post-filter` 判定。

## Required Inputs

- 最少输入：
  - `pipeline-ts` 仓库路径
  - 目标 tx hash
  - 链和区块号
  - 原始 transfer 或可生成 transfer 的 trace
- 推荐输入：
  - `Transaction` 风格 JSON，带 `stackFrameList`、`eventLogs`
  - tx metadata：`fromAddress`、`toAddress`、`blockMiner`、`gasPrice`、`gasUsed`
  - fundflow
  - 如有，`blockActions.pool_action`
- 关于 BlockSec call trace：
  - 只有 call tree，不够
  - 如果包含 `CALL/CREATE`、`LOG2/LOG3/LOG4`、`from/to/value/input/error/frameId`，足够做高质量人工分析
  - 要接近 PT 的完整复盘，仍然最好有 PT 风格 `Transaction` JSON

## Workflow

1. 读取 arbitrage 主链路。
   - `apps/recognition/src/algo/recognizer/atomic/arbitrage/arbitrageRecognizer.ts`
2. 先看 raw transfer，不先看 protocol action。
   - `apps/recognition/src/algo/common/transferRecognizer.ts`
3. 还原 simplify 前后的最小 transfer 表。
   - `replaceTransferToken`
   - `simplifySameGroupTransfer`
   - `mergeSameFromToTokenTransfer`
   - `simplifyZeroAmountDeltaMiddleNode`
4. 检查地址归并。
   - `apps/recognition/src/algo/recognizer/atomic/arbitrage/addressGroup.ts`
   - 如有 tx-local groups，再看 `apps/recognition/src/algo/action/addressGroupReader.ts`
5. 构造最小 cycle 图。
   - `apps/recognition/src/algo/recognizer/atomic/arbitrage/graphCycle.ts`
6. 继续检查 post-filter。
   - `cycleCheck.ts`
   - `graphCycleNearestNode.ts`
   - `cycleBalanceDelta.ts`
   - `cashPooling.ts`
7. 判断误报根因属于哪一类。
   - grouping 合并过强
   - simplify 误删中间节点
   - merge 造环
   - cycle 过滤过弱
   - nearest-node / balance-delta 放行

## Core Pattern

不要直接问“这是不是套利”，要问：

1. 原始 transfer 图里有没有真实闭环
2. simplify 之后图被改成了什么
3. SCC 是怎么被造出来的
4. 哪个 post-filter 把它放行了

如果 cycle 只在 simplify 后才出现，优先怀疑：

- address grouping
- middle node removal
- same from/to/token merge

## Quick Reference

- arbitrage 主入口只消费：
  - `tx.transfers`
  - `tx.addressGroups`
- 不依赖 protocol action 做主判定
- 最值得优先检查的函数：
  - `recognizeTxTransfer`
  - `simplifyTransfers`
  - `findGraphCycles`
  - `checkArbitrageCycles`
  - `findTxNearestNodes`
  - `checkIfObeyNegativeCycleNodeBalanceDeltaRule`

## Input Tiers

- 初步人工分析：
  - tx hash
  - BlockSec 完整 trace 导出
  - fundflow
- 高置信误报分析：
  - 上述输入
  - tx metadata
  - 原始 transfer 列表
- 接近 PT 行为复盘：
  - `Transaction` JSON
  - `stackFrameList`
  - `eventLogs`
  - 可选 `blockActions.pool_action`

## Output Format

输出默认包含：

- 一句结论
- raw transfer 表
- simplified transfer 表
- 最小 cycle 图
- 精确放行点
- 根因分类
- 哪些是直接证据，哪些是推断

如果用户只给了 BlockSec trace，明确说明：

- 当前结论是否能覆盖 PT 的 `transferRecognizer`
- 哪些字段无法完全复盘
- 因缺失输入导致的不确定性

## Common Mistakes

- 用 protocol action 解释 arbitrage 结果
- 只看最终 cycle，不看 simplify 前后差异
- 忽略 address group 对 Curve / Maker / Aave 的强归并
- 忽略 `nearestNodes` 和 negative-balance rule
- 把“有 call trace”误当成“能完整复现 PT transfer 图”

## Verification

在结论里始终附带 fresh evidence：

- `command`
- `exit_code`
- `key_output`
- `timestamp`

如果没有 PT 风格 `Transaction` JSON，必须明确说明当前分析是“高质量人工复盘”，不是“1:1 运行时复盘”。
