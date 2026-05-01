# FP TX Review Board Page Contract

## Purpose

这份 contract 用来约束未来所有 FP tx categorizing data page 的共同外观与共同交互。

## Non-Negotiable Features

- 单文件 HTML
- 数据内嵌
- 可离线打开
- 搜索 / 筛选 / 排序
- 选中 tx
- 导出选中 CSV / JSON
- 导出 processed state JSON
- `localStorage` 记住 processed
- 每行带 `EigenTx` / `Etherscan`
- 每行带 `判定逻辑与证据`
- 导出字段含 `determinationLogic` / `evidenceSummary`
- sticky 表头
- sticky 左侧关键列
- grid 内部可横向和纵向滚动

## Non-Negotiable Visual Direction

- 温暖、纸感、编辑部式 dashboard
- 不是通用企业后台
- 不是深色炫光
- 不是纯数据长表

## Grid Priorities

优先级从高到低：
1. 可以看到并滚动所有行
2. sticky 列保住上下文
3. `tx / note / actions` 拿到足够宽度
4. 其余列再压缩

## Reuse Rule

如果未来任务要求做新的 FP tx review page：
- 默认先复制模板
- 不要先从零设计
- 只有用户明确要求改版，才允许偏离
