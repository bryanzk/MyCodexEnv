---
name: verification-loop
description: 交付前的全量验证流程，覆盖构建 (Build)、静态检查 (Static Check)、测试 (Test)、覆盖率 (Coverage) 与安全扫描 (Security Scan)。
---

# Verification Loop

## 概述

在功能完成或交付前执行系统化验证，确保质量门禁可追溯。

## 验证阶段

### Phase 1: Build
```bash
# 构建 (Build) 校验（Go）
go build ./...
```

构建失败立即停止并修复。

### Phase 2: Static Check
```bash
# Go 静态检查 (Static Check)
go vet ./...
```

如有 golangci-lint：
```bash
golangci-lint run
```

### Phase 3: Test + Coverage
```bash
# 运行全量测试 (Test) 并生成覆盖率 (Coverage)
go test ./... -coverprofile=coverage.out

go tool cover -func=coverage.out | tail -1
```

目标覆盖率 (Coverage)：>= 80%，关键逻辑优先 100%。

### Phase 4: Security Scan
```bash
# 粗粒度密钥扫描 (Security Scan)（按需扩展规则）
rg -n "(AKIA|sk-|api_key|secret|password)" -S .
```

### Phase 5: Diff Review
```bash
# 变更审阅 (Diff Review)
git diff --stat
```

## 输出格式

完成后输出验证报告：

```
VERIFICATION REPORT
===================

Build:     [PASS/FAIL]
Static:    [PASS/FAIL]
Tests:     [PASS/FAIL] (X/Y passed)
Coverage:  [PASS/FAIL] (Z%)
Security:  [PASS/FAIL] (X issues)
Diff:      [N files changed]

Overall:   [READY/NOT READY]

Issues to Fix:
1. ...
2. ...
```

## 记录要求

- 运行结果需同步到 `TEST_VERIFICATION.md`，作为交付证据。
