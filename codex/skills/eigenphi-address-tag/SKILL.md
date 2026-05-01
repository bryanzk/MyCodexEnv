---
name: eigenphi-address-tag
description: Use when a Codex session needs to query an EVM address tag or label from the local eigenphi-analyse-transaction repository, including static tags from internal tables or protocol LP lists and optional tx-context tags via a tx hash.
---

# Eigenphi Address Tag

## Overview

用于查询 `eigenphi-analyse-transaction` 仓库里的地址 tag。

固定入口：
- 优先运行 `bash scripts/query_address_tag.sh`
- 不要先手写 `rg` 到处搜，除非 wrapper 失败后需要补充排查
- 当本地静态表和 tx-context 都没有命中时，继续运行 `bash scripts/query_scan_address_tag.sh`
- 需要 `from` / `to` / `miner` / `leaf` 这类交易上下文标签时，必须同时提供 `--tx`
- 带 `--tx` 查询时，wrapper 会自动选择服务，优先级固定：
  - 已运行且健康的本地分析 API
  - 线上公开分析接口 `https://eigenphi.io/api/v1/analyseTransaction`
  - 冷启动本地依赖
    - 先 ensure 本地 Ethereum JSON-RPC
    - 再 ensure 本地分析 API
  - 若冷启动仍失败，再回退线上公开分析接口
- 上述路径仍未命中 tag 时，再回退到对应链的 scan 地址页：
  - `ethereum -> https://etherscan.io`
  - `bsc -> https://bscscan.com`
  - `fantom -> https://ftmscan.com`
  - `avalanche -> https://snowtrace.io`
  - `polygon -> https://polygonscan.com`
  - `optimism -> https://optimistic.etherscan.io`
  - `arbitrum -> https://arbiscan.io`
  - `cronos -> https://cronoscan.com`

默认仓库路径：
- `/Users/kezheng/Codes/CursorDeveloper/eigenphi-analyse-transaction`

本地自动启动前提：
- 本机可执行 `sbcl`
- skill 会检查两层本地服务：
  - `127.0.0.1:8545` 的 Ethereum JSON-RPC
  - `127.0.0.1:8889` 的 tx-context API
- 若 `8545` 不存在，skill 会先尝试自动拉起本地 RPC proxy，再启动分析 API

可选环境变量：
- `EIGENPHI_ANALYSE_TX_REPO`
  - 覆盖默认仓库路径
- `EIGENPHI_SBCL_BIN`
  - 显式指定 `sbcl` 可执行文件路径
- `EIGENPHI_TX_API_BASE`
  - 覆盖本地 tx-context 查询使用的 API 地址
- `EIGENPHI_TX_API_BASE_ONLINE`
  - 覆盖线上公开分析接口地址，默认 `https://eigenphi.io`
- `EIGENPHI_TX_API_TTL_SECONDS`
  - 覆盖 API 租约时长，默认 `43200`
- `EIGENPHI_ETH_RPC_UPSTREAM`
  - 当本地 `127.0.0.1:8545` 不存在时，用它作为上游自动拉起本地 RPC proxy
  - 默认 `http://123.118.108.250:9999`
- `EIGENPHI_ETH_RPC_TTL_SECONDS`
  - 覆盖本地 RPC proxy 租约时长，默认 `43200`
- `EIGENPHI_LIBFIXPOSIX_PREFIX`
  - 覆盖 `libfixposix` 安装前缀；默认自动探测 `$HOME/.local`、`$HOME/.local/libfixposix`、`/opt/homebrew`、`/usr/local`
- `EIGENPHI_SCAN_USER_AGENT`
  - 覆盖 scan 页面抓取时使用的 User-Agent

## Workflow

### 1. 先判断查询类型

- 只查地址固有 tag：
  - 传 `--chain` 和 `--address`
- 还要查交易上下文 tag：
  - 额外传 `--tx`
- 若本地结果为空：
  - 回退 scan 地址页公开 tag / label

### 2. 统一入口执行

冷启动本地服务时自动 ensure：

```bash
bash scripts/ensure_local_eth_rpc.sh
bash scripts/ensure_local_api.sh
```

若本次查询带 `--tx`，wrapper 会先直连检查本地 RPC：

```bash
curl -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
  http://127.0.0.1:8545
```

静态查询：

```bash
bash scripts/query_address_tag.sh --chain ethereum --address 0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2
```

带 tx 的上下文查询：

```bash
bash scripts/query_address_tag.sh --chain ethereum --address 0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2 --tx 0x...
```

线上回退接口：

```bash
https://eigenphi.io/api/v1/analyseTransaction?enableCallStack=on&enableCallStackAddressTag=on&chain=ethereum&tx=0x...
```

scan 页面回退：

```bash
bash scripts/query_scan_address_tag.sh --chain ethereum --address 0x63242a4ea82847b20e506b63b0e2e2eff0cc6cb0
```

### 3. 结果解释

- `== static ==`
  - 来自静态地址表、builder 表或协议 LP 地址列表
- `== tx-context ==`
  - 来自 `/api/v1/analyseTransaction` 返回的 `addressTags`
- `== explorer ==`
  - 来自 scan 地址页公开展示的 `Public Name Tag` 或页面 label
- `source: ...`
  - 表示命中的文件或 API 来源
- `api status: ...`
  - 表示这次是复用已有 API、刷新 12 小时租约，还是后台新启动了本地 API
- `rpc status: ...`
  - 表示本地 `8545` 是复用已有 RPC、刷新租约，还是后台新启动了本地 proxy
- `service selection: ...`
  - 表示这次命中了哪条查询路径：
    - `local-fast`
    - `online-fallback`
    - `local-cold-start`
    - `online-last-resort`
    - `explorer-fallback`
- `detail: public name tag`
  - 表示命中的是 scan 页面主标签
- `detail: explorer label`
  - 表示命中的是 scan 页面上方公开 label，例如 `KyberSwap`、`DEX`
- 若显示 `readiness unavailable`
  - 说明 Web/API 进程已启动，但链节点 `127.0.0.1:8545` 不可用，tx-context 查询仍可能失败
- 若显示 `sbcl not found`
  - 说明 skill 无法自动拉起本地 API，需要先安装或暴露 `sbcl`
- 若显示 `missing dependency: sbcl is not installed`
  - 说明 Homebrew 公式存在，但当前机器没有装好 `sbcl`
- 若显示 `missing dependency: Ethereum JSON-RPC at http://127.0.0.1:8545 is unavailable`
  - 说明不是“地址没 tag”，而是 tx-context 所需链依赖没起来
  - skill 会先尝试自动拉起本地 RPC proxy；若仍失败，再回退线上接口
- 若显示 `suggestion: ...`
  - 直接把这行里的命令或环境变量建议带给用户

## Output Requirements

执行这个 skill 后，回答里至少包含：
- 实际执行的命令
- 查询模式
  - `static` 或 `static + tx-context`
- API 状态
  - 若走了 tx-context，写 `reused`、`lease refreshed` 或 `started`
  - 若只走静态表 / explorer 回退，明确写 `n/a`
- RPC 状态
  - 若走了 tx-context，写 `reused`、`lease refreshed`、`proxy started` 或 `n/a`
- 服务来源
  - `local-fast`、`online-fallback`、`local-cold-start`、`online-last-resort` 或 `explorer-fallback`
- 命中的 tag
- 命中来源
- 如果本地没命中、但 scan 页面命中，明确说这是 explorer fallback，不要误写成 EigenPhi 静态表结果
- 如果 `--tx` 查询失败，明确说是 API 未连通，还是 readiness 失败导致链依赖不可用
- 如果自动启动失败，明确说是 `sbcl` 未安装、`EIGENPHI_SBCL_BIN` 配错、repo 路径错误，还是启动后 `/liveness` 仍未起来
- 如果有 `suggestion:` 行，优先把这些建议原样转述给用户

## Common Mistakes

- 用户要的是交易里的角色标签，却没传 `--tx`
- 看到 `address` 是合约就默认它一定有静态 tag
- 本地没命中时，直接回答“没有 tag”，却没有继续查 scan 地址页公开 tag
- 本地 API 已启动，但 `127.0.0.1:8545` 不可用时，直接声称“没有 tx-context tag”
- 本机没有 `sbcl` 时，还声称 skill 已经自动启动了本地 API
- 手写一堆 grep，绕过 `bash scripts/query_address_tag.sh`
