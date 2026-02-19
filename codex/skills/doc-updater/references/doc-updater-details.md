# Doc Updater 参考细则

## 分析命令示例

```bash
# TypeScript AST 分析
npx ts-morph

# 依赖图
npx madge --image graph.svg src/

# 提取 JSDoc
npx jsdoc2md src/**/*.ts
```

## Codemap 目录结构

```text
docs/CODEMAPS/
├── INDEX.md
├── frontend.md
├── backend.md
├── database.md
├── integrations.md
└── workers.md
```

## Codemap 模板

```markdown
# [Area] Codemap

**Last Updated:** YYYY-MM-DD
**Entry Points:** list of main files

## Architecture
[ASCII diagram]

## Key Modules
| Module | Purpose | Exports | Dependencies |
|--------|---------|---------|--------------|
| ... | ... | ... | ... |

## Data Flow
[Data flow description]

## External Dependencies
- package-name - Purpose, Version

## Related Areas
Links to other codemaps
```

## README 更新模板

```markdown
# Project Name

Brief description

## Setup

```bash
npm install
cp .env.example .env.local
npm run dev
```

## Architecture
See docs/CODEMAPS/INDEX.md

## Documentation
- docs/GUIDES/setup.md
- docs/GUIDES/api.md
```

## 质量检查清单

- 文件路径存在
- 示例可运行
- 内部链接可用
- 说明与代码一致
- 更新时间已刷新
