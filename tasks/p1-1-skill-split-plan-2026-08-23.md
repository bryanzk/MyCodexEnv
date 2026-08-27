# P1-1 计划：DHF SKILL.md 拆 L2/L3 v2（委员会修订）

日期：2026-08-23 · 状态：计划，未改仓库
`verification_receipt: verification_not_applicable`（仓库事实见附录 A，只读核对）

## 1. 要解决的事

DHF 一旦被激活，Codex 就加载完整 `SKILL.md`：582 行、37,712 字符（约 9K token），24 个小节。但任何一次任务实际用到的只是其中一条路径——light 任务用不上 Agent Team Gate，读文档任务用不上 Deployment Readiness。这是 PDF「渐进式披露」原则在本仓库最大的一块未落地。

前提说清楚：这**不降低进门费**。31.9K 起步 uncached 里的 68K 字符是全部 277 个 skill 的 L1 目录，不是 DHF 正文；正文只在激活时计费。所以本计划的靶子是「每次 governed/standard 任务激活 DHF 的 9K token × 激活次数」，量法见 §5。目录瘦身是另一件事（§7）。

## 2. 骨架留什么、搬走什么

留在 `SKILL.md`（目标 ≤180 行 / ≤12KB）：

- Overview、Lifecycle Ownership（裁剪）
- profile 与 stage 路由：Standard Runtime Stages、Stage Classifier 的**判定表**（详例搬走）
- Source Of Truth Order（全留，四处测试断言引用它）
- Helper Router 的选择表
- 全部 Gate 的**名字 + 一句话触发条件 + 指向 references 的 read_file 路径**——名字一个都不能丢，85 个 corpus 场景按 gate 名做路由断言
- 安全硬边界与 Output Contract 的必填字段清单

references 按任务类型分组设计：目标是典型 governed 任务全程按需 `read_file` ≤2 个文件，light/standard 任务 0–1 个；做不到就重新分组，不加骨架行数。

搬到 `references/`（按需 read_file）：

| 新文件 | 来源小节 | 字符 |
|---|---|---:|
| `stage-classifier-details.md` | Stage Classifier 的示例与边界案例 | ~6,000 |
| `output-contract-details.md` | Output Contract 的完整格式与示例 | ~4,000 |
| `architecture-alignment.md` | Architecture Alignment Checkpoint Gate 全文 | 2,684 |
| `agent-team-gate.md` | Agent Team Gate 全文（与既有 `agent-team-context-policy.md` 相邻互链） | 2,230 |
| `evidence-and-report.md` | Evidence And Report Gate 全文 | 2,081 |
| `startup-and-recovery.md` | Startup Sequence、Dirty Worktree、State Snapshot 详情 | ~3,500 |
| `deployment-and-capture.md` | Deployment Readiness、External Capture 全文 | ~1,700 |
| `exceptions-and-checkpoint.md` | Exception Handling 详情、Checkpoint 示例 | ~2,500 |

预期骨架约 12–13KB（-65%）。数字以实施为准，不承诺百分比。

## 3. 不变量（改坏任何一条就是失败）

1. **Gate 名字与路由语义不变**：`run_dhf_simplification_pair.py compare` 的 routing parity 与 actual outcome parity 保持 85/85。
2. **`dhf_preprompt.py` 的解析合同不变**：它读运行时 SKILL.md（第 350 行）提取 governed 注入内容；骨架必须保留它解析的全部锚点。实施第 0 步先读 `dhf_preprompt.py` 全文，列出它依赖的标题/行模式清单，骨架逐条保。
3. **Source Of Truth Order 小节标题与条目不变**（`test_runner.py` 四处引用）。
4. 每个搬走的小节在骨架留一行：`详见 references/<file>（read_file 按需加载）`。
5. runtime 与源逐字节一致（既有测试 `test_runner.py:1625`）。

## 4. 交付流程（P1-2 的成果第一次实战）

每一步：`python3 scripts/harness_refresh_identity.py status` → 改 → `refresh --message "P1-1 <step>"` → commit → 门禁 → **commit 后再跑一次门禁**。A 层审批只需一次：收尾 sync 前对最终 digest 跑 `refresh --approve`（sync guard 只在 sync 时查 digest，中间步骤打印的待批行不用逐个批）。commit → push → sync → verify 在收尾执行一次。

Commit 拆分：
1. `P1-1: extract references (no skeleton change)`——先原样复制八个小节到 references/，SKILL.md 未动，门禁必绿。
2. `P1-1: skeleton`——SKILL.md 裁剪为骨架。refresh 身份。跑 `compare` 出 parity。
3. `P1-1: before-baseline`（在第 1 步**之前**跑并 commit，见 §5）与 `P1-1: after-baseline`（骨架落地并 sync 后跑）。
4. `P1-1: checkpoint + next action`。

## 5. 量效果

**改前必须重跑**：after-p0-3 基线（8-22 21 时）跑在 P0-3 SKILL.md 提升（8-23 00:38）之前，量的是旧 runtime，不能当 P1-1 的 before；standard 在 after-p0-3 里也没跑。所以骨架动工前，在当前 HEAD、当前 runtime 上先跑 `before-p1-1-*`：governed 3 次（brief 派工，方法同 after-p0-3）、standard 3 次、light-b 3 次。这组同时充当 P1-2 之后的健康快照。

改后同样九次，出 `after-p1-1-*`。身份用 `codex_config_keys_sha256`。比较口径：中位数、requests、input、cached、uncached、首请求 uncached、wall。预期效应在 governed/standard 的总 input 与激活后轮次的 uncached；light-b 是阴性对照（不激活 DHF，应 1.00×±2%）。

判定规则预登记：governed 与 standard 的 input 中位数任一下降且 light-b 三项 1.00×±2% → 有效；都在方差内 → 记录「拆分无可辨效应」，不回滚（骨架本身是可维护性收益），但 P1 后续优先级重排。

## 6. 停止条件

- 第 0 步发现 `dhf_preprompt.py` 解析依赖的锚点无法在 ≤180 行骨架内全部保留 → 停，贴锚点清单，等 owner 定骨架上限。
- routing parity 或 outcome parity ≠ 85/85 → 停，贴 diff，不改 corpus 来迁就骨架。
- `refresh` 或门禁在任一步红 → 停。

## 7. 不做的事

- 不动 skill 目录（277 个 skill 的 L1 catalog、113 个无使用信号 skill 的去重）——那是 P1-1b，等本计划的 after 数据出来再立项。
- 不改 corpus、不改 validator、不改 `dhf_preprompt.py` 的逻辑（只允许在第 0 步结论要求时对其锚点做**等价**适配，且需单独说明）。
- 不承诺任何百分比。

## 附录 A：2026-08-23 只读核对

- `SKILL.md`：582 行 / 37,712 字符 / 24 小节；最大小节 Stage Classifier 7,427 字符、Output Contract 5,154。
- corpus 场景按 gate 名引用：Checkpoint Gate ×6、其余 8 个 gate 各 ×1。
- `run_dhf_simplification_pair.py` 第 185/260/1214/1526 行以 `BASELINE_BASE_SHA` 的 SKILL.md 为 baseline 输入——拆分只影响 candidate 侧，baseline 侧读历史 commit，不受影响。
- `dhf_preprompt.py` 第 20–23、350 行读取运行时 SKILL.md。
- `test_runner.py` 第 1619–1630 行断言 runtime 与源逐字节一致；四处引用「Source Of Truth」。
- 既有 `references/agent-team-context-policy.md` 是 P0-3 建立的先例。
