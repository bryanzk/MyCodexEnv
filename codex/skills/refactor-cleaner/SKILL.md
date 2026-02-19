---
name: refactor-cleaner
description: 清理死代码、重复实现与无用依赖的重构流程；用于主动清理、合并重复代码、删除无用导出/文件/依赖并记录删除日志。
---

# Refactor Cleaner

## 概述

执行保守的死代码清理（dead code）与重复实现合并，确保删除安全可验证，并记录删除日志。

## 工作流

1. 运行静态检测工具（能跑就跑）
   - knip / depcheck / ts-prune / eslint（unused-disable-directives）
   - 若工具不存在，跳过并在结论中说明
2. 汇总并分级风险
   - SAFE：未引用的依赖、未引用导出
   - CAREFUL：可能动态引用
   - RISKY：公共 API、共享基础库
3. 逐项验证
   - 全文搜索引用
   - 检查动态 import/字符串引用
   - 核对是否公开 API 或文档承诺
   - 必要时查看 git 历史
4. 按批次删除
   - 依赖 -> 导出 -> 文件 -> 重复实现
   - 每批后运行测试/构建
5. 记录删除日志
   - 默认写入 `docs/DELETION_LOG.md`
   - 若项目有其他路径约定，以项目规则为准

## 关键原则

- 保守删除，不确定就不删
- 先删 SAFE，再考虑 CAREFUL/RISKY
- 每次修改都要能被测试或构建验证

## 参考资料

需要详细检查清单、删除日志模板或示例命令时，读取 `references/refactor-cleaner-details.md`。
