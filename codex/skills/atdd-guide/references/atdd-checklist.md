# ATDD Checklist

## 1) Acceptance Test 质量门槛

- 从外部用户视角描述行为，不绑定具体 UI 控件。
- 每个场景只覆盖一个业务意图，保持原子化。
- 每个场景独立准备数据，不依赖其他场景执行顺序。
- 通过公共接口访问系统，禁止后门注入状态。
- 明确正向路径、边界条件、错误路径。

## 2) DSL 设计清单

- DSL 词汇全部使用领域语言（Domain Language）。
- 提供默认值和可选参数（optional parameters）以降低样板代码。
- 复用常见启动步骤，例如 `register_user`、`seed_account`。
- 避免在 DSL 中暴露 HTTP 字段、CSS 选择器、数据库细节。

## 3) Protocol Driver 设计清单

- 每类协议/通道至少一个 Driver（UI/API/RPC/CLI）。
- Driver 与 DSL 方法保持语义一一对应。
- Driver 负责参数展开、协议转换、重试与超时策略。
- 将系统交互细节集中在 Driver 层，测试用例不直接接触。

## 4) Production-like 验证清单

- 使用与生产一致的部署工具链与配置方式。
- 验证配置变更、依赖版本、启动流程是否影响验收结果。
- 保证测试环境从 SUT 视角无法区分于生产环境。
- 记录环境版本、执行命令与测试结果作为证据链。

## 5) Outside-in 执行模板

1. 写一个失败的 Acceptance Test。
2. 在 DSL 增加领域动作表达。
3. 在 Driver 实现对应协议调用。
4. 用 TDD 完成最小实现并让测试转绿。
5. 重构 DSL/Driver/实现代码，保持测试全绿。
