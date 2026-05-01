---
name: sandwich-fp-by-code
description: Use when a pipeline-ts sandwich label looks wrong or missing and you need to explain the result from recognizer code, action abstraction, pool-key matching, or nested-pool semantics.
---

# Sandwich FP by Code

## Overview

用 `pipeline-ts` 源码解释某笔交易为什么被识别成 sandwich，或为什么没有被识别成 `FrontRun`、`Victim`、`BackRun`。先读 recognizer 的真实谓词，再把交易压成最小 `Action` 表，最后把失败点回溯到上游字段。

## Required Inputs

- 最少输入：
  - `pipeline-ts` 仓库路径
  - 目标 tx hash
  - 链和区块号
- 推荐输入：
  - 同一 bundle 的 front / middle / back 三笔 hash
  - `blockActions.pool_action` 或等价 action dump
  - raw call trace
  - fundflow
  - 地址标签和 token 标签
- 如果缺少 runtime dump：
  - 允许基于源码和本地 trace 做推断
  - 明确标注“推断”与“直接证据”的边界

## Workflow

1. 读取 sandwich 识别入口与匹配条件。
   - `apps/recognition/src/algo/recognizer/affiliated/sandwich/attackerPairRecognizer.ts`
   - `apps/recognition/src/algo/recognizer/affiliated/sandwich/sandwichedActionRecognizer.ts`
   - `apps/recognition/src/algo/recognizer/affiliated/sandwich/sandwichUnitMerger.ts`
2. 手工还原最小 `Action` 表。
   - 拆出 front / middle / back 的最少 `Trade`、`AddLiquidity`、`RemoveLiquidity`
   - 不直接按整笔 tx 净效果下结论
3. 明确 recognizer 真正使用的 pool key。
   - `Trade.pool = transfers[0].to`
   - `AddLiquidity.pool = transfers[1].to`
   - `RemoveLiquidity.pool = transfers[1].from`
4. 回溯 pool key 的上游产生链条。
   - `Action` 的 pool 字段来自哪里
   - `transfer[1].from` 或 `transfers[0].to` 是如何被构造的
5. 对照 trace 和 fundflow，判断失败点属于哪一类。
   - attacker pair 没配成
   - victim action 没落在同一 pool key
   - token 集合不重叠
   - bundle merge 被丢弃
   - 模型边界问题，例如 metapool / nested pool
6. 横向检查同类 recognizer。
   - 默认检查 `JIT`
   - 如果也是精确 pool 匹配，指出同类漏报风险

## Core Pattern

把问题压成三层：

1. 识别条件层：
   - 代码里到底要求什么
2. 中间抽象层：
   - 这笔交易被抽成了什么 `Action`
3. 原始链路层：
   - raw trace / fundflow 实际发生了什么

只有三层都对齐，才能判断“是识别器错了”还是“模型边界到了”。

## Quick Reference

- 先看这几个字段：
  - `commonTrader`
  - `actionPool`
  - attacker token set
  - victim token set
- 先读这几个函数：
  - `findAttackerPair`
  - `checkActionPool`
  - `checkActionToken`
  - `getTradePool`
  - `getRemoveLiquidityPool`
- 标准产出：
  - 最小 `Action` 表
  - 失败谓词
  - 字段回溯链
  - 根因分类

## Output Format

输出默认包含：

- 一句结论
- 最小 `Action` 表或等价列表
- 精确失败点，指到函数或条件
- 对 trace / fundflow 的业务解释
- 哪些部分是直接证据，哪些是推断

如果用户问“为什么不是 back piece / victim / frontrun”，必须明确写出：

- recognizer 希望匹配哪个 `commonTrader`
- 实际 `actionPool` 是什么
- 两者在哪一步分叉

## Common Mistakes

- 把“经济上经过某个池”当成 recognizer 实际使用的 pool key
- 只看整笔 tx，不拆 `Action`
- 不区分 raw pool、semantic pool、recognizer pool
- 不检查 `sandwichUnitMerger`，直接把 pair 成功当成 bundle 成功
- 不检查 `JIT` 是否也受同一问题影响

## Verification

在结论里始终附带 fresh evidence：

- `command`
- `exit_code`
- `key_output`
- `timestamp`

如果 runtime `pool_action` 不可得，明确说明当前结论依赖本地 trace / fundflow 和源码推断。
