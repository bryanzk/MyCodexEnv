---
name: mevscan-recognizer-debug-local
description: Use when debugging MEVScan recognizer decisions without committing temporary instrumentation, especially when you need local-only build-tagged logs, reversible git patches, and a fixed check order across simplify, cycle, nearest-node, and balance-rule branches.
---

# MEVScan Recognizer Debug Local

## Overview

用 `1 + 3` 方案做 `MEVScan` recognizer 本地调试：

- `1`：用 patch 保存和开关全部临时调试改动，不进提交历史
- `3`：用 `build tag` 隔离 debug 输出，默认构建零影响

这个 skill 只解决“如何本地安全加 recognizer debug 并快速定位根因”。具体解释某笔 tx 为什么误报/漏报时，配合 [`$mevscan-arbitrage-fp-by-code`](/Users/kezheng/.codex/skills/mevscan-arbitrage-fp-by-code/SKILL.md) 一起用。

## When to Use

用在这些场景：

- 你要看 `FindGraphCycles`、`FindNearestNodes`、`CheckNodeBalanceDelta` 的中间决策
- 你不想 commit `fmt.Printf` / `log.Printf` 之类的临时代码
- 你需要反复打开/关闭同一套 recognizer debug 输出
- 你要把误报排查固定成统一顺序，而不是每次临场乱翻 JSON

不要用在这些场景：

- 你准备把调试能力产品化并长期保留在仓库里
- 你只是想解释单笔 tx 的已有运行产物，没有必要加本地 instrumentation

## Workflow

### 1. 只在本地建 debug hook

建议把 hook 放在 `pkg/recognizer/arbitrage/`，并且同时准备两份本地文件：

- `debug_local.go`
- `debug_stub_local.go`

`debug_local.go`

```go
//go:build recognizerdebug

package arbitrage

import "log"

func debugRecognizef(format string, args ...any) {
	log.Printf("[recognizerdebug] "+format, args...)
}
```

`debug_stub_local.go`

```go
//go:build !recognizerdebug

package arbitrage

func debugRecognizef(string, ...any) {}
```

然后只在你关心的节点插一层很薄的 hook，例如：

```go
debugRecognizef("nearest_nodes=%v", nearestNodes)
debugRecognizef("balance_obey=%v negative=%v positive=%v", result.IsObeyRule, result.NegativeNodeBalanceDelta, result.PositiveNodeBalanceDelta)
```

不要把业务判断写进 debug hook。hook 只负责吐证据，不负责改变逻辑。

### 2. 防止本地文件误提交

把本地 debug 文件加到 repo 的 `.git/info/exclude`，不要改 `.gitignore`：

```bash
printf '%s\n' \
  'pkg/recognizer/arbitrage/debug_local.go' \
  'pkg/recognizer/arbitrage/debug_stub_local.go' \
  >> .git/info/exclude
```

### 3. 让 untracked 文件也能进 patch

新文件默认不会出现在 `git diff` 里。要先用 `intent-to-add`：

```bash
git add -N \
  pkg/recognizer/arbitrage/debug_local.go \
  pkg/recognizer/arbitrage/debug_stub_local.go
```

如果你改了其他文件里的 hook 调用，也一并纳入 patch 范围。

### 4. 保存 patch

建议把 patch 放到 repo 外，例如：

```bash
mkdir -p ~/.codex/patches
git diff -- \
  pkg/recognizer/arbitrage/arbitrageur.go \
  pkg/recognizer/arbitrage/cycle.go \
  pkg/domain/transforms/analyze_mevs.go \
  pkg/recognizer/arbitrage/debug_local.go \
  pkg/recognizer/arbitrage/debug_stub_local.go \
  > ~/.codex/patches/mevscan-recognizer-debug-local.patch
```

如果这次只改了部分文件，就缩小 `git diff -- <paths...>` 范围，不要把无关脏改动一起收进去。

### 5. 打开/关闭本地 debug

应用：

```bash
git apply ~/.codex/patches/mevscan-recognizer-debug-local.patch
```

撤销：

```bash
git apply -R ~/.codex/patches/mevscan-recognizer-debug-local.patch
```

如果 patch 因上下文漂移失败，先读失败 hunk，再重新生成 patch；不要硬改旧 patch 继续赌。

### 6. 用 build tag 跑验证

默认构建：

```bash
go test ./pkg/recognizer/arbitrage ./pkg/domain/transforms
```

打开 debug：

```bash
go test -tags recognizerdebug ./pkg/recognizer/arbitrage ./pkg/domain/transforms
```

如果你有定向 case，优先跑最小范围：

```bash
go test -tags recognizerdebug -run TestCheckNodeBalanceDelta ./pkg/recognizer/arbitrage
```

## Fixed Check Order

排查 recognizer 时，按这个顺序，不要跳步：

1. `parser completeness`
   - `swap` / `borrow` / `withdraw` / `flashloan` 是否齐全
   - 缺失时优先怀疑 parser，不先怪 recognizer
2. `raw transfer`
   - 原始 token / ETH value transfer 是否存在
3. `simplify delta`
   - 哪条边在 `replaceTransferToken`
   - 哪条边在 `mergeSameFromToTokenTransfer`
   - 哪个节点在 `simplifyZeroAmountDeltaMiddleNode`
4. `cycle / SCC`
   - cycle 是 raw 就有，还是 simplify 后才出现
5. `nearest node`
   - 为什么是这个节点，不是别的节点
6. `balance rule branch`
   - 是 `all positive`
   - 还是 `external inflow exists only`
   - 还是 `any negative token in+out short-circuit`
7. `suppress / pnl`
   - 只在 recognizer 已定位清楚后再看

## Suggested Reason Codes

本地 debug 输出建议优先固定成这些 reason code：

- `parser.swap_unparsed`
- `simplify.zero_delta_middle_node`
- `simplify.same_from_to_token_merged`
- `cycle.none`
- `cycle.valid`
- `nearest.none`
- `nearest.selected`
- `balance.all_positive`
- `balance.external_inflow_exists_only`
- `balance.any_negative_token_inout_short_circuit`
- `balance.reject_unexplained_negative`
- `analyze.duplicate_swap_action`

同一轮调试里，reason code 要稳定复用，不要一会儿写中文、一会儿写 free text。

## Quick Reference

- 主入口：
  - `pkg/domain/transforms/analyze_mevs.go`
- cycle：
  - `pkg/recognizer/arbitrage/cycle.go`
- nearest node / balance：
  - `pkg/recognizer/arbitrage/arbitrageur.go`
- 解释单笔误报：
  - [`$mevscan-arbitrage-fp-by-code`](/Users/kezheng/.codex/skills/mevscan-arbitrage-fp-by-code/SKILL.md)

常用搜索：

```bash
rg -n "FindGraphCycles|FindNearestNodes|CheckNodeBalanceDelta" pkg/domain/transforms pkg/recognizer/arbitrage -S
rg -n "debugRecognizef\\(" pkg/recognizer/arbitrage pkg/domain/transforms -S
```

## Common Mistakes

- 只建 `debug_local.go`，没建默认 `stub`，导致不带 tag 的构建直接失败
- 直接 `git diff > patch`，结果漏掉 untracked debug 文件
- 把 patch 存在 repo 里，后面误加到提交
- 一边看 suppress，一边看 recognizer，没有先锁定根因层级
- 把 `arb_path` 重复 hop 当成 recognizer 根因，而不是先检查 analyzer 重复收集
- 用 debug 输出改业务逻辑，导致这套 patch 既是观测又是修复，后面很难复盘

## Verification

交付结论时，至少附：

- `command`
- `exit_code`
- `key_output`
- `timestamp`

推荐最少验证 3 项：

1. 默认构建不带 tag 仍然通过
2. 带 `recognizerdebug` tag 的目标包能运行并吐出 reason code
3. `git apply -R` 后工作区回到预期状态

如果这次没有真正修改 repo，只是在设计调试方案，要明确说明这是“本地调试工作流设计”，不是“已落地到仓库的永久能力”。
