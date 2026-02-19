# Code Reviewer 参考细则

## 审查步骤

1. `git diff` 获取改动
2. 聚焦改动文件与相邻上下文
3. 安全与稳定性优先
4. 输出分级问题与修复建议

## 安全检查清单（Critical）

- 硬编码密钥/Token
- SQL 注入或拼接查询
- XSS（未转义的用户输入）
- 输入验证缺失
- 路径遍历
- 认证/鉴权绕过
- 不安全依赖或已知漏洞

## 质量检查清单（High）

- 超长函数（>50 行）
- 超大文件（>800 行）
- 深层嵌套（>4 层）
- 错误处理缺失
- 重复代码
- 新增代码缺少测试

## 性能检查清单（Medium）

- 低效算法（O(n^2) 等）
- 不必要的重复计算
- N+1 查询
- 缺少缓存

## 输出格式示例

```
[CRITICAL] Hardcoded API key
File: src/api/client.ts:42
Issue: API key exposed in source code
Fix: Move to environment variable
```

## 审批结论

- Approve: 无 Critical/High
- Warning: 只有 Medium
- Block: 有 Critical 或 High
