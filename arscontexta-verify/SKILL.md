---
name: arscontexta-verify
description: Use when validating note quality, schema completeness, link health, and operational integrity before declaring an Ars Contexta processing cycle complete.
---

# Ars Contexta Verify

## 概述

用于执行 6R 中的 Verify：在交付前进行结构化校验，避免“看似完成但不可维护”。

## 校验清单

1. 新笔记是否包含 `description` 与 `source`。
2. 新笔记是否存在至少一条有效关系（入链或出链）。
3. MOC 是否已覆盖新主题。
4. `ops/queue` 状态是否一致。
5. `ops/sessions` 是否记录本轮摘要。

## 常用命令

```bash
rg -n "^description:" <notes_dir>
rg -n "\[\[" <notes_dir>
```

## 输出契约

- 通过项 / 失败项
- 失败项对应文件路径
- 修复优先级建议

## 常见错误

- 只做口头校验不提供证据。
- 通过标准不一致，导致后续 health 波动。
