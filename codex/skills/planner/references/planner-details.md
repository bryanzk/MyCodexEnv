# Planner 参考模板与清单

## 计划模板

```markdown
# Implementation Plan: [Feature Name]

## Overview
[2-3 句摘要]

## Requirements
- [Requirement 1]
- [Requirement 2]

## Architecture Changes
- [Change 1: file path + description]
- [Change 2: file path + description]

## Implementation Steps

### Phase 1: [Phase Name]
1. **[Step Name]** (File: path/to/file)
   - Action: 明确动作
   - Why: 这么做的原因
   - Dependencies: 无 / 依赖某步
   - Risk: Low/Medium/High

### Phase 2: [Phase Name]
...

## Testing Strategy
- Unit tests: [files]
- Integration tests: [flows]
- E2E tests: [journeys]

## Risks & Mitigations
- **Risk**: 描述
  - Mitigation: 应对方式

## Success Criteria
- [ ] Criterion 1
- [ ] Criterion 2
```

## 需求分析要点

- 目标、范围、输入/输出、非功能约束
- 验收标准（正向、可测试）
- 约束与假设（依赖、性能、兼容性）

## 架构梳理要点

- 影响模块与文件路径
- 复用现有模式与接口
- 潜在回归点

## 红旗清单

- 超大函数（>50 行）
- 深层嵌套（>4 层）
- 复制粘贴代码
- 缺失错误处理
- 硬编码常量
- 缺失测试或覆盖不足
- 明显性能瓶颈
