# Refactor Cleaner 参考细则

## 工具命令

```bash
# 未使用的导出/文件/依赖
npx knip

# 未使用的 npm 依赖
npx depcheck

# 未使用的 TypeScript 导出
npx ts-prune

# 未使用的 eslint disable 指令
npx eslint . --report-unused-disable-directives
```

## 删除日志模板

默认写入 `docs/DELETION_LOG.md`，若项目约定不同路径请遵循项目规范。

```markdown
# Code Deletion Log

## [YYYY-MM-DD] Refactor Session

### Unused Dependencies Removed
- package-name@version - Last used: never, Size: XX KB

### Unused Files Deleted
- src/old-component.tsx - Replaced by: src/new-component.tsx

### Duplicate Code Consolidated
- src/A.tsx + src/B.tsx -> src/A.tsx
- Reason: identical behavior

### Unused Exports Removed
- src/utils/helpers.ts - Functions: foo(), bar()
- Reason: no references found

### Impact
- Files deleted: 0
- Dependencies removed: 0
- Lines of code removed: 0

### Testing
- Build: pass/fail
- Tests: pass/fail
```

## 安全清单

- 先删 SAFE 再考虑 CAREFUL/RISKY
- 全文搜索引用与动态 import
- 核对公开 API 与文档承诺
- 每一批删除后运行测试或构建
- 记录删除日志

## 重复合并准则

- 优先保留功能最完整且测试覆盖更高的实现
- 更新所有引用后再删除重复代码
- 保持对外接口不变，必要时提供兼容层

## 不建议使用场景

- 临近发布或线上不稳定
- 项目测试缺失且无法运行
