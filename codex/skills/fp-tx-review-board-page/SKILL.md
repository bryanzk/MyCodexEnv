---
name: fp-tx-review-board-page
description: Use when generating or updating a MEVScan false-positive transaction categorization page, especially when the output must preserve the established single-file dashboard style, sticky review grid, local processed-state persistence, and exportable tx evidence fields instead of inventing a new layout.
---

# FP TX Review Board Page

## Overview

这个 skill 用来保证未来的 FP tx categorizing data page 继续沿用当前已经定下来的评审面板风格，而不是每次重新发明一套 UI。

核心原则：
- **先复用模板，再改数据**
- **保留交互 contract，不只保留视觉**
- **保留“判定逻辑 + 证据”字段，不允许退化成纯标签表**

## When to Use

在这些场景使用：
- 要生成新的 FP tx review page
- 要更新某一批新日期的 FP tx categorizing page
- 要把新的 CSV / JSON 数据嵌入已有 review dashboard
- 用户要求“以后都按这页的样式来”
- 用户要的是可离线打开、可导出、可持久化处理状态与处理意见的 HTML 数据页

不要在这些场景使用：
- 只是修单个 CSS 小问题
- 只是解释当前页面的某个字段
- 要做完全不同的信息架构或完全不同视觉语言

## Source Of Truth

当前视觉与交互基线：
- 页面成品：
  - `/Users/kezheng/Codes/CursorDeveloper/MEVScan/generated/fp-tx-review-board-2026-03-22.html`
- 可复用模板：
  - `/Users/kezheng/.codex/skills/fp-tx-review-board-page/template/fp-tx-review-board.template.html`
- 页面 contract：
  - `/Users/kezheng/.codex/skills/fp-tx-review-board-page/reference/page-contract.md`

默认做法：
1. 从模板文件复制出新的 HTML
2. 把新数据嵌入 `const DATA = ...`
3. 只做最小必要改动
4. 用 contract 检查是否丢了关键能力

## Required Workflow

### 1. 先准备数据

最终嵌入页内的数据对象至少应包含：
- `txHash`
- `blockNumber`
- `from`
- `to`
- `selector`
- `profit`
- `revenue`
- `gap`
- `bucket`
- `analysisSource`
- `fallbackReason`
- `categoryCode`
- `category`
- `categoryNote`
- `confidence`
- `etherscanUrl`
- `eigentxUrl`

如果已有判定结果，还应补上：
- `determinationLogic`
- `evidenceSummary`

如果原始数据没有后两项，也必须在生成页面前推导出来，不允许留空。

### 2. 必须从模板开始

不要从空白 HTML 重新写。

先复制：

```bash
cp ~/.codex/skills/fp-tx-review-board-page/template/fp-tx-review-board.template.html \
  /target/path/generated/<new-page>.html
```

然后把：

```js
const DATA = __DATA_PLACEHOLDER__
```

替换成新的 JSON 数组。

### 3. 必须保留的交互 contract

以下能力不能丢：
- 单文件 HTML，可直接 `file://` 打开
- 数据内嵌，不依赖本地 `fetch`
- 搜索、分类、置信度、bucket、排序筛选
- 勾选 tx
- 导出选中 tx 为 CSV / JSON
- 导出 processed state JSON
- 每行都有“已处理”状态与“处理意见”输入区
- `localStorage` 持久化已处理状态与处理意见
- 页面重新打开时，已处理状态与处理意见都能自动恢复
- 导出的 processed state JSON 必须包含处理状态与处理意见，不能只导出勾选结果
- 每行都有 `EigenTx` 和 `Etherscan` 链接
- 每行都有“判定逻辑与证据”展开块
- 导出字段包含 `determinationLogic` 与 `evidenceSummary`
- 表头 sticky
- 左侧关键列 sticky
- grid 区域内部可滚动
- 宽屏下尽量 fit 浏览器视口

### 4. 允许修改的范围

可以改：
- 数据内容
- 分类与证据文案
- 标题中的日期
- 轻微布局比例
- 列宽
- 适配不同浏览器视口的 CSS

不要改：
- 整体信息架构
- 主视觉方向
- 字体组合，除非明确要求
- 从 dashboard 退化成普通长表
- 去掉 sticky / export / persistence / evidence 中任一核心能力

## Page Contract

生成的新页面应继续维持这套结构：

1. `hero`
   - 页面标题
   - 页面用途说明
   - 总览统计卡
   - 右侧说明卡

2. `controls`
   - 搜索
   - 分类筛选
   - 置信度筛选
   - bucket 筛选
   - 排序
   - toggle
   - 右侧导出与状态按钮

3. `summary`
   - 当前可见数量
   - 当前选中数量
   - 可见 profit 汇总
   - 最大分类

4. `Transaction Grid`
   - sticky header
   - sticky left columns
   - table internal scroll
   - row-level links
   - row-level processed checkbox
   - row-level opinion textarea
   - row-level note + evidence

## Visual Rules

保留这些视觉特征：
- 温暖米色背景 + 轻微网格噪声
- 浮层卡片感面板
- `Fraunces` 标题 + `Plus Jakarta Sans` 正文 + `IBM Plex Mono` 技术字段
- 左主右辅的 dashboard 布局
- 大屏下全视口压缩布局
- 表格仍然是页面主角，不被 hero 压住

不要把它改成：
- 通用 SaaS 蓝白表格
- 暗色 neon 面板
- 纯卡片流
- 无层次的平面数据墙

## Quick Reference

### 新建页面最短路径

1. 复制模板
2. 嵌入新 `DATA`
3. 更新标题日期
4. 检查逻辑/证据字段
5. 检查 processed checkbox + opinion textarea 的持久化
6. 跑校验

### 最低校验

```bash
python3 - <<'PY'
from pathlib import Path
import re
html = Path('/path/to/page.html').read_text()
script = '\n'.join(re.findall(r'<script>([\s\S]*?)</script>', html))
Path('/tmp/page-check.js').write_text(script)
PY
node --check /tmp/page-check.js
```

再补一轮静态检查：
- `const DATA = [` 已内嵌
- `localStorage.setItem` 存在
- `exportRowsAsCsv` 存在
- `determinationLogic` 存在
- `evidenceSummary` 存在
- `opinion-input` 或等价 textarea class / selector 存在
- processed state 导出逻辑直接导出 `state.processed`，且包含 opinion 字段
- `overflow-y: auto` 存在
- sticky 列样式存在

## Common Mistakes

- 只复制视觉，不复制导出和持久化逻辑
- 只保存“已处理”勾选，不保存处理意见
- 导出 processed state JSON 时丢掉处理意见，只剩布尔状态
- 只保留分类，不保留判定逻辑和证据
- 用 `fetch('./data.json')` 导致 `file://` 打不开
- 把表格做成整页滚动，导致 grid 失去内部滚动
- 把页面重新设计成另一种风格，破坏跨批次一致性
- 导出时漏掉 `determinationLogic` 和 `evidenceSummary`

## Completion Standard

只有同时满足下面条件，才算符合这个 skill：
- 新页面直接打开可用
- 视觉语言与基线页明显同源
- 交互能力完整保留
- 判定逻辑与证据可见
- 选中导出可用
- processed 状态与处理意见都可保存、恢复、导出
- grid 能滚动并看完所有 tx
- 语法检查通过
