# DHF 简化版产品使用指南

## 这次修改解决了什么问题

DHF（Delivery Harness Framework）原本为复杂交付提供完整的状态恢复、权限、证据、checkpoint 和多人协作治理。它能降低高风险任务的交付风险，但如果所有任务都走同一套完整流程，简单问答、小范围修改和普通本地开发也会承担不必要的流程成本。

本次修改把 DHF 改为按任务风险自动分层：简单任务直接完成，常规开发保留必要的完成标准和 fresh verification，高风险任务才启用完整治理。业务目标是让流程成本与任务风险匹配，同时不降低安全、授权和验证标准。

## 用户会看到哪些变化

| 使用场景 | 新行为 | 用户价值 |
| --- | --- | --- |
| 简单解释、整理、格式转换 | 使用 `light`，直接产出结果，不启动生命周期 helper | 响应更短，等待更少 |
| 本地功能、调试、重构、UI 行为修改 | 使用 `standard`，先明确完成标准，再运行针对性反馈和 fresh verification | 保留工程质量，不附加无关流程 |
| 恢复或交接任务、远程发布、私密数据、破坏性操作、多人写入、架构来源冲突 | 使用 `governed`，只加载与实际风险匹配的恢复、权限、证据和 checkpoint | 高风险工作仍有完整保护和可追溯性 |
| 普通 prompt 没有要求 DHF，也没有兼容性风险信号 | 不注入 DHF | 日常对话不受影响 |
| ShipQ 项目任务 | 继续延迟加载 ShipQ 专属 adapter | 项目规则不泄漏到其他仓库 |

无论使用哪一层，完成结果都保留四项业务保证：交付结果、范围与约束、验证凭证、剩余风险或下一步。涉及实现、修复、文档或配置变更时，验证凭证仍必须是本次执行产生的 `command`、`exit_code`、`key_output` 和 `timestamp`。

## 源码与运行态如何生效

仓库源码已包含简化规则，但仓库文档不声明当前机器的受管 Codex runtime
已经推广。当前机器是否生效必须由本机 fresh evidence 判定，涉及以下运行态文件：

- `~/.codex/hooks/dhf_preprompt.py`
- `~/.codex/skills/delivery-harness-framework/SKILL.md`
- `~/.codex/skills/delivery-harness-framework/evals/evals.json`
- `~/.codex/skills/delivery-harness-framework/evals/validate_completion_output.py`

`source_stage_unsynced` 表示源码验收通过，但不代表当前机器已激活；
`runtime_promoted` 表示受管路径与当前源码完全一致，才可以在 fresh evidence
支持下声明运行态已推广。前一种状态如需启用，必须另行授权定向推广或执行环境复现流程；
不要对现有 Codex home 做盲目的全量同步。

当 fresh evidence 为 `runtime_promoted` 时，要让新任务使用新规则：

1. 结束当前任务后，新建一个 Codex 任务；如果希望同时刷新应用加载的 hooks 和 skills，重启 Codex Desktop 后再新建任务。
2. 在新任务中正常描述需求。需要明确启用 DHF 时，在 prompt 中写 `使用 DHF` 或 `Use DHF`。
3. 查看最终交付中的验证凭证；有文件或运行态变更时，应包含四字段 fresh evidence。

已经进入当前任务上下文的旧规则不会被运行态文件反向改写，因此“新建任务”是最清晰的生效边界。

## 日常如何使用

### 1. 让系统自动选择

大多数情况下只需正常描述任务。普通 prompt 不会自动注入 DHF；明确的复杂任务、恢复、接手、交接或状态冲突信号会激活 DHF，并根据风险选择合适层级。

示例：

```text
使用 DHF，修复本地 CLI 的导出选项，先明确 Definition of Done，再运行 fresh verification。
```

这类常规本地实现通常进入 `standard`：它会保护现有用户改动、建立可运行的反馈回路，并用新鲜结果验证，但不会默认执行恢复、环境探测或 checkpoint helper。

### 2. 简单任务显式使用 DHF

```text
使用 DHF，把这段发布说明改写成三条面向客户的要点。
```

没有常规开发或高风险信号时，系统使用 `light`。它仍交付清晰结果和边界，但不增加生命周期仪式。

### 3. 高风险任务

```text
使用 DHF，恢复上次交接的发布任务；先核对当前状态和授权，不要直接部署。
```

恢复、交接、远程或生产发布、敏感数据、破坏性操作、多人写入冲突等场景进入 `governed`。系统只组合命中风险所需要的 helper 和输出字段；用户授权边界不会因为启用 DHF 而扩大。

### 4. 单次跳过 DHF

在 prompt 中写明以下任一表达即可优先跳过：

```text
不用 DHF，只解释这段配置的含义。
```

也支持 `skip dhf`、`no dhf`、`不要 DHF`、`跳过 DHF`。单次跳过不会修改全局配置。

## 管理员开关与回退

简化版默认开启，等价于：

```bash
export DHF_PREPROMPT_SIMPLIFIED_PROFILES=1
```

如需临时回退到旧版统一流程，请在启动 Codex Desktop 或 Codex 进程前设置：

```bash
export DHF_PREPROMPT_SIMPLIFIED_PROFILES=off
```

`0`、`false`、`off`、`legacy` 都表示回退。恢复简化版时执行 `unset DHF_PREPROMPT_SIMPLIFIED_PROFILES`，或把值设回 `1`，然后新建任务。其他显式值不会被猜测解释，而是安全回退到旧版并输出诊断信息。

该环境变量是进程级开关，不是单个 prompt 的开关。只想跳过一次时，应使用上一节的 prompt 表达。

## 如何确认运行态正常

在 MyCodexEnv 仓库根目录运行统一的只读状态入口：

```bash
python3 scripts/harness_status.py status --runtime --codex-home "$HOME/.codex" --json
```

检查源码候选版本与受管 runtime 的关系：

```bash
python3 scripts/dhf_simplification_evidence.py --repo-root "$(pwd)"
```

合法结果有两种：

- `runtime_state=source_stage_unsynced`：`source_stage_gate_pass=true`，且
  `promotion_difference_paths` 非空；源码验收通过，但运行态尚未激活。
- `runtime_state=runtime_promoted`：`promotion_gate_pass=true`，且
  `promotion_difference_paths=[]`；此时才可声明当前受管 runtime 已推广。

以上两种受支持状态命令退出码都为 `0`；`runtime_state=drifted` 会失败，不能用来
声明源码验收或运行态推广完成。

检查 Codex 是否能加载全部受管 skills：

```bash
python3 scripts/check_codex_skill_loader.py \
  --repo-root "$(pwd)" \
  --codex-home "$HOME/.codex" \
  --json
```

预期 missing、disabled 和 loader errors 都为 `0`。

## 在其他机器上启用

“Git 仓库已经包含修改”不等于“目标机器 runtime 已经启用修改”。在新机器或另一台开发机上，应先通过 MyCodexEnv 的环境复现流程安装 runtime，再执行上面的运行态一致性检查。

仅为了启用本功能时，不建议对已有个人 Codex home 盲目执行 broad mirror 或带 `--delete` 的全量同步。应使用经过授权的定向推广或完整的环境复现流程，并先确认目标机器中的个人配置、凭据和非托管 skills 不会被覆盖。完整环境复现入口见 `docs/CODEX_ENV_REPRODUCTION.md`。

## 兼容性与不变项

- 旧的 helper 命令仍可调用；新的统一状态入口只是减少记忆成本。
- 普通非项目 prompt 仍保持 continue-only，不会因为安装了 DHF 就自动增加上下文。
- opt-out 始终早于通用路由和项目 adapter。
- 安全、权限、私密数据、远程操作和破坏性操作门禁没有被简化。
- fresh verification 仍是完成声明的必要条件，旧结果不能替代本次验证。

底层运行时合同和故障排查细节见 `docs/HARNESS_RUNTIME.md`；仓库受管 surface 和脚本索引见 `docs/repo-index.md`。
