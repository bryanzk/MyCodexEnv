# 提案：把 Grilling 和 CONTEXT.md 融入 DHF

Date: 2026-07-06
Repo: `MyCodexEnv`
Status: draft, 待评审
来源: 与 mattpocock/skills 的对比分析（grill-with-docs、CONTEXT.md 术语表机制）

## 一句话

DHF 会校验需求 artifact 合不合格，但没教 agent 怎么把模糊需求问清楚；DHF 有文件地图（repo-index），但没有语言地图（领域术语表）。这两个洞，grilling 和 CONTEXT.md 正好能补上。

## 问题

### 问题 1：requirements gate 只管收，不管问

现在的流程是：需求模糊 → 停在 `requirements` 阶段 → 产出 requirements artifact → `harness_requirements.py validate` 校验。

校验器能挡住格式不合格的 artifact，但挡不住"格式合格、内容却是 agent 自己脑补"的 artifact。agent 最常见的做法是：猜一个合理解释，写成漂亮的验收标准，然后通过校验。misalignment 被合法化了。

缺的是一个交互技术：agent 该怎么问、问到什么程度算问完。

### 问题 2：repo-index 告诉 agent 去哪读，没告诉 agent 这里的话怎么说

`docs/repo-index.md` 是 source-of-truth 文件地图。但项目黑话不在任何地图上。agent 每次会话都要重新猜"harness"、"surface"、"lane"、"promotion" 在这个 repo 里的确切含义，猜错就产生错误命名和啰嗦解释。多 agent 并行时更糟：每个 worker 各猜各的，integrator 收到三套词汇。

缺的是一份术语合同：一个词只有一个意思，所有 agent 用同一套词。

## 复用策略：直接采用 mattpocock/skills 的三个文件

### 上游版本 pin

- Repo: `https://github.com/mattpocock/skills`
- Commit: `694fa30311e02c2639942308513555e61ee84a6f`（main，2026-06-10）
- 获取方式（无需 clone）：

```bash
BASE="https://raw.githubusercontent.com/mattpocock/skills/694fa30311e02c2639942308513555e61ee84a6f"
curl -fsSL "$BASE/skills/productivity/grilling/SKILL.md"            -o codex/skills/grilling/SKILL.md
# SKILL.md 以上游原文为主体，在文末追加 DHF 适配节（见下），不留临时文件
curl -fsSL "$BASE/skills/engineering/grill-with-docs/CONTEXT-FORMAT.md" -o codex/skills/grilling/CONTEXT-FORMAT.md
curl -fsSL "$BASE/skills/engineering/grill-with-docs/ADR-FORMAT.md"     -o codex/skills/grilling/ADR-FORMAT.md
curl -fsSL "$BASE/LICENSE"                                           -o codex/skills/grilling/LICENSE
```

上游 repo 是 MIT 协议。合规要求：vendor 目录内保留上游 `LICENSE` 全文副本（上面第 4 条 curl），每个搬入文件头部另加一行来源声明。以下三个文件可以近乎原样搬入：

| 上游文件 | 搬入位置 | 改动量 |
| --- | --- | --- |
| `skills/productivity/grilling/SKILL.md` | `codex/skills/grilling/SKILL.md` | 原文仅 3 条规则（一次一问、附推荐答案、能查 repo 不问人），全部保留；追加一节 DHF 适配 |
| `skills/engineering/grill-with-docs/CONTEXT-FORMAT.md` | `codex/skills/grilling/CONTEXT-FORMAT.md` | 原样。格式规则（定义紧凑、禁收通用编程概念、Avoid 别名、CONTEXT-MAP 多上下文）都直接适用 |
| `skills/engineering/grill-with-docs/ADR-FORMAT.md` | `codex/skills/grilling/ADR-FORMAT.md` | 原样。ADR 三条件、极简模板、qualifies 清单直接适用 |

每个搬入文件头部加一行来源声明：`Adapted from mattpocock/skills (MIT), commit 694fa30`。不 fork 整个 repo，不引入 skills.sh 安装器，只 vendor 这三个文件——上游更新靠人工 diff，频率低，成本可接受（与 `scripts/sync_gstack_vendor.py` 的 vendor 先例做法一致）。

`skills-lock.json` 不需要登记：它属于 skills.sh 安装器的 lock 机制，`codex/skills/*` 的运行时激活走 `scripts/sync_codex_home.sh`（复制到 `~/.codex/skills/`），两条链路互不相干。

**自己写的部分只有 DHF 适配层**（追加在 grilling SKILL.md 内）：

- 触发条件：`requirements` / `planning` 阶段判定模糊时由 router 调用。
- 结束条件：能写出通过 `harness_requirements.py` 校验、且没有一条验收标准是 agent 脑补的 artifact。
- 术语敲定即时写入 CONTEXT.md（沿用 grill-with-docs 的 inline 更新规则）。
- 问答记录进 requirements artifact 的 `open_questions_resolved` 字段。

## 提案 1：Grilling 作为 requirements 阶段的标准技术

### 做什么

Vendor 上游 `grilling` skill（见复用策略），在需求或计划模糊时对用户逐题追问，直到决策树的每个分支都有答案。核心规则来自上游原文：一次只问一个问题并等回答；每题附推荐答案；能靠读 repo 回答的不许问人。DHF 适配层补充触发与结束条件。

### 挂进哪里

三处改动：

1. **Skill routing 表**（`delivery-harness-framework` SKILL.md + 手册第 8 章）：
   "需求不清"一行的首选 route 从 `planner / req-to-dev / requirements gate` 改为 `grilling → planner → requirements gate`。grilling 负责问清楚，planner 负责结构化，gate 负责校验。
2. **阶段进入条件**（手册第 4 章 / 第 7 章）：`requirements` 阶段的默认动作从"产出需求 artifact"改为"先 grilling 后产出"。跳过 grilling 需要显式理由（例如用户已给出完整验收标准）。
3. **planning 阶段可复用**：架构决策模糊时同样可以调 grilling，对应 mattpocock 的 grill-with-docs 用法。

### 与现有组件的关系

| 组件 | 关系 |
| --- | --- |
| `harness_requirements.py` | 不变。grilling 的产出喂给它校验，两者是上下游 |
| `planner` skill | 不变。grilling 之后接 planner 做任务拆解 |
| requirements artifact 模板 | 增加一个字段 `open_questions_resolved`：记录 grilling 问了哪些问题、答案是什么，作为需求来源的审计线索 |
| evidence | grilling 结果属于 `decision` 类证据：谁在什么时候确认了哪个分支 |

## 提案 2：CONTEXT.md 作为 Runtime layer 的语言地图

### 做什么

新增一个 runtime surface：repo 根目录的 `CONTEXT.md`，纯术语表，格式直接用 vendor 进来的 `CONTEXT-FORMAT.md`：每条术语一两句定义 + `Avoid` 别名清单，禁止写实现细节、禁止当 spec 或草稿本用。将来若 repo 出现多个领域上下文，按上游规则升级为 `CONTEXT-MAP.md`。ADR 沿用 vendor 的 `ADR-FORMAT.md`（极简模板 + 三条件门槛），落在 `docs/adr/`，目录按需懒创建。

读取顺序调整为：`AGENTS.md` → `docs/repo-index.md` → `CONTEXT.md` → `docs/harness-state.md`。

### 硬性边界

- CONTEXT.md 只是术语表。实现决策去 ADR，文件位置去 repo-index，状态去 harness-state。四个文件各管一摊，不许互相越界。
- 更新时机：术语在 grilling 或开发中被敲定的那一刻就写入，不许攒到最后批量补。
- ADR 门槛沿用三条件：难以逆转、缺上下文会让未来读者困惑、真实取舍的结果。三条不全就不写 ADR。

### 与 repo-index 的分工

| | repo-index | CONTEXT.md |
| --- | --- | --- |
| 回答的问题 | 事实在哪个文件 | 这个词是什么意思 |
| 内容 | 路径、验证命令、高风险区 | 术语、定义、别名禁用 |
| 更新者 | 结构变化时更新 | 术语敲定时更新 |

### 对多 agent 的直接收益

agent team contract 增加一条：所有 worker 在开工前必须读 CONTEXT.md，report 中的术语必须与之一致。integrator 收到不一致术语时按 blocker 处理，不做静默翻译。这条写进 `harness_agent_team.py` 的校验说明（先文档约定，脚本校验放后续 slice）。

## 改动面清单

| Surface | 改动 |
| --- | --- |
| `codex/skills/grilling/SKILL.md` | vendor 上游原文 + DHF 适配节 |
| `codex/skills/grilling/CONTEXT-FORMAT.md` | vendor 原样 + 来源声明 |
| `codex/skills/grilling/ADR-FORMAT.md` | vendor 原样 + 来源声明 |
| `codex/skills/grilling/LICENSE` | 上游 MIT LICENSE 全文副本 |
| `codex/skills/delivery-harness-framework/SKILL.md` | 两处：routing 表加 grilling 一行；Runtime Surfaces 与 Startup Sequence 加 CONTEXT.md 及新读取顺序 |
| `docs/surfaces.json` | 登记 `CONTEXT.md` surface（canonical manifest，不登记会与 repo-index 产生 drift） |
| `docs/delivery-harness-framework-manual-cn.md` | 第 4、7、8 章更新阶段动作和 routing 表；14.1 术语表改为指向 CONTEXT.md 的引用 |
| `docs/repo-index.md` | 登记 CONTEXT.md 和 `codex/skills/grilling/` |
| `CONTEXT.md` | 新增，首批收录 DHF 现有术语（phase、lane、evidence、checkpoint、write set、integrator 等，从手册 14.1 迁移） |
| `docs/templates/harness-requirements.md` | 增加 `open_questions_resolved` 字段 |

Out of scope：不改 hooks、不改 tool-policy、不动 `harness_requirements.py` 和 `harness_agent_team.py` 的代码（本提案只改文档合同，脚本校验是后续 slice）、不迁移 gstack skill、不登记 `skills-lock.json`（理由见复用策略）。

## 分阶段落地

1. **Slice 1（2 小时）**：按"上游版本 pin"的 curl 命令 vendor 四个文件（含 LICENSE）+ 每个文件加来源声明 + 写 DHF 适配节 + routing 表更新。CONTEXT.md 此时尚不存在——沿用上游懒创建规则（首个术语敲定时创建），grilling 可先行使用。**runtime 激活**：`./scripts/sync_codex_home.sh` 同步到 `~/.codex/skills/`，再跑 `./scripts/verify_codex_env.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex" --claude-home "$HOME/.claude"` 确认 sync 无 drift。验证：`python3 scripts/check_surfaces.py --repo-root "$(pwd)"`、`git diff --check`、verify_codex_env 退出码 0。
2. **Slice 2（半天）**：建 CONTEXT.md（首批 DHF 术语，从手册 14.1 迁移）+ `docs/surfaces.json` 登记 + repo-index 登记 + SKILL.md 的 Runtime Surfaces 与 Startup Sequence 更新。验证：`python3 scripts/check_surfaces.py --repo-root "$(pwd)"`（覆盖 surfaces.json ↔ repo-index 一致性）、`python3 test_runner.py`、`git diff --check`。
3. **Slice 3（一天）**：手册第 4、7、8 章更新 + 14.1 改为指向 CONTEXT.md 的引用 + requirements 模板加 `open_questions_resolved` 字段（模板新增小节，`harness_requirements.py` 现有校验不认识该字段但不会拒绝，已用 `validate` 实测通过后再合入）。验证：`python3 scripts/check_surfaces.py --repo-root "$(pwd)" --check-public-nav`、`python3 test_runner.py`、`python3 scripts/harness_requirements.py validate docs/templates/harness-requirements.md`。
4. **Slice 4（后续，可选）**：`harness_requirements.py` 校验 `open_questions_resolved` 字段；`harness_agent_team.py` 提示 worker 读 CONTEXT.md。

每个 slice 独立可验证，做完一个用 `scripts/harness_checkpoint.py append` 写一条 checkpoint（带 command / exit_code / key_output / timestamp）。

## 风险

- **上游漂移**：vendor 的文件与上游脱节。缓解：文件头记录来源 commit hash;上游本身极稳定(纯 prompt 文档,无代码依赖),漂移影响小,按需人工 diff 即可。
- **grilling 拖慢简单任务**：小改动被迫走问答。缓解：routing 表明确豁免条件——用户已给验收标准、或改动属于 low demand（单文件文档/config），直接跳过。
- **CONTEXT.md 变成垃圾场**：有人往里塞实现细节和 TODO。缓解：文件头写死"只收术语"，review 阶段把越界内容当 finding 处理。
- **术语表和手册 14.1 术语表重复**：两处维护会漂移。缓解：CONTEXT.md 为准，手册 14.1 改为指向 CONTEXT.md 的引用。

## 验收标准

每条标注检查方式（executable = 命令可判定；manual = 人工评审判定）：

1. [executable] `python3 scripts/check_surfaces.py --repo-root "$(pwd)" --check-public-nav`、`python3 test_runner.py`、`git diff --check` 全部 exit_code=0。
2. [executable] `./scripts/verify_codex_env.sh` exit_code=0，且 `~/.codex/skills/grilling/SKILL.md` 存在。
3. [executable] `python3 scripts/harness_requirements.py validate docs/templates/harness-requirements.md` exit_code=0。
4. [executable] `codex/skills/grilling/` 下四个文件齐全，SKILL.md、CONTEXT-FORMAT.md、ADR-FORMAT.md 头部含 `mattpocock/skills` 与 `694fa30` 字样（`grep -l "694fa30" codex/skills/grilling/*.md` 返回 3 个文件）。
5. [manual] 用一个真实模糊需求走 `grilling → planner → requirements gate`，检查 artifact 的 `open_questions_resolved` 里每条验收标准都能追溯到一个被确认的问答。
6. [manual] 新会话 agent 读完启动序列后术语使用与 CONTEXT.md 一致（抽查 3 个术语）。
