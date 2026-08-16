# Codex 对话与执行日志系统复盘及风格档案

> 生成基线：2026-08-14T22:14:07Z。本文件总结本机当前可访问的 Codex 对话、执行日志与记忆索引；它不是对未同步 ChatGPT、已删除记录或生产系统状态的声明。

## 一、执行经验总结

### 1. 生命周期状态必须逐层报告

| 导致问题的做法 | 正确方式 | 教训 |
| --- | --- | --- |
| 把 plan、source、tests、runtime、deployment、production enforcement、customer adoption 或 commercial validation 压成一个“完成” | 分别报告每层状态、证据时间与尚缺的 gate；上一层通过只允许进入下一层验证 | 生命周期是状态机，不是一枚绿色徽章；源码存在、测试通过或网页 HTTP 200 都不能证明 runtime 已同步、生产已执行或客户已采用 |
| 用历史绿灯、缓存摘要或没有最终 `exit_code` 的长任务输出宣布通过 | 在当前 checkout 重跑权威入口，等待进程终态并记录 `command / exit_code / key_output / timestamp` | 没有最终退出码就是没有可审计结论；历史证据只能用于定位，不是 fresh receipt |

| 层 | 回答的问题 | 可接受证据 |
| --- | --- | --- |
| Plan | 做什么、边界和验收是什么 | 经确认的计划或 handoff |
| Source | 目标代码/文档是否已写入正确 checkout | exact diff、文件哈希、当前 Git 状态 |
| Tests | 当前源码是否通过约定门禁 | fresh command 与最终 exit code |
| Runtime | 实际运行目录是否已同步并加载 | allowlist sync receipt、runtime probe、独立 readback |
| Deployment | 是否已发布到目标环境 | 部署工具回执、目标版本或 SHA |
| Production | 真实控制是否正在执行 | 生产侧 readback、监控和回滚证据 |
| Adoption | 用户是否真实使用 | 经授权的使用证据，而非技术可用性 |
| Commercial | 是否产生可验证商业价值 | 经授权的客户、收入或效果证据；没有则明确未验证 |

### 2. 授权与能力必须分离

| 导致问题的做法 | 正确方式 | 教训 |
| --- | --- | --- |
| 把 phase 切换、policy 编辑、token 可用、connector 可调用或本地 gate 通过，当成 Drive/Docs/邮件/财务等外部写授权 | 每个外部动作都核对当前、具体、可归因的 action grant；`default=deny`、grant 缺失或作用域不符时立即停在本地 | “能做”不等于“获准做”；policy/source mutation 也不会反向授权 connector execution |
| 在线写入发生部分 mutation 后，根据最终结构断言失败直接盲重试 | 保存失败 receipt，先判断远端已发生的变更，执行可恢复 rollback，再用独立读取路径核验最终结构；新一轮写入必须重新授权 | 失败可能发生在“写入之后、断言之前”；盲重试会叠加副作用，readback 与 rollback 本身是产品能力 |
| 把 AI 输出直接写入报价、财务、授权或合规结果 | AI 只做候选提取、分类、配对与编排；确定性 contract、业务规则、金额边界和 owner approval 决定最终状态 | 概率模型适合缩短人工判断，不适合替代不可逆业务约束 |

### 3. 最小范围要形成完整闭环

| 导致问题的做法 | 正确方式 | 教训 |
| --- | --- | --- |
| 为了“顺手优化”或提高 review 分数，扩大文件数、重构邻近模块、添加未来抽象 | 冻结 exact write set；只处理与验收直接相关的问题，范围外发现单独报告 | 高分不能覆盖授权；最小改动不是少做验证，而是减少无关变化 |
| 只修工单点名的症状，在每个调用者重复加 guard | 先 grep 所有调用者和消费者，找共享根因；先加入能稳定失败的回归，再在共同路径做最小修复 | 一个共享根因修复通常比多个症状补丁更小、更耐久 |
| 先改实现再找测试证明 | 先让针对缺陷的回归稳定 RED，确认失败原因，再做最小 GREEN 修复并跑完整门禁 | RED 证明测试能看见问题；GREEN 只在同一证据链中才有意义 |
| 因评审迭代得分高就把独立 blind review、浏览器验收或生产检查视为可省略 | 将各 gate 独立记录；任何一项未完成都保留为开放状态 | 评分是诊断工具，不是范围扩张理由，也不是验收替代品 |

### 4. Checkout、环境与 Git 是证据的一部分

| 导致问题的做法 | 正确方式 | 教训 |
| --- | --- | --- |
| 在错误 checkout/worktree 工作，或把 feature worktree 结果当成 main checkout 结果 | 开始先运行 `git rev-parse --show-toplevel`，核对 branch、HEAD、worktree 与任务锚点；所有 receipt 绑定该身份 | 路径相似不代表证据可互换 |
| 把 dirty 文件视为可清理噪声，或让自己的 staged/unstaged 改动吞并用户改动 | 开始和结束核对 `git status`；记录 ownership；不 reset、clean、覆盖或隐式暂存范围外文件；确需保护时使用可复核的固定哈希与 `git stash apply` | Dirty state 首先是所有权信号，不是卫生问题 |
| 使用错误 venv、缺少固定依赖路径，随后把环境错误归类为代码回归 | 先确认仓库指定入口、解释器与依赖来源；将 environment/auth/policy blocker 与 deterministic code regression 分栏 | 修代码不能解决认证、政策、网络、依赖或执行环境阻断 |
| 仅凭 `git branch -d` 失败/成功判断分支是否可删除，或在未证明 ancestry 时强制删除/推送 | 用 `main...branch` 分类 ahead/diverged，证明本地和远端 tip ancestry；rebase 冲突按语义合并；远端改写只用明确授权的 `--force-with-lease` | Git 操作的安全依据是 ancestry、lease 与 ownership，不是命令是否碰巧接受 |

### 5. UI/UX 必须在真实交互中验收

| 导致问题的做法 | 正确方式 | 教训 |
| --- | --- | --- |
| 只看静态截图、DOM 状态或桌面宽度，就宣布交互完成 | 使用真实浏览器覆盖 desktop 与 `390x844`；验证主路径、滚动/溢出、Tab 顺序、Escape、焦点返回、可见 focus 与 live region | jsdom 能验证 contract，但不能替代浏览器 ownership、布局与键盘体验 |
| 为追求“高级感”套用紫色霓虹、强 glow、无节制渐变、对称卡片墙或低信息密度 | 使用主色加单一强调色、清晰字体层级、非对称 grid、参与构图的背景；保留信息密度并强化来源和状态 | 风格必须服务信任与任务，不应成为跨产品复制的模板 |
| 改 UI 时破坏既有业务接口、storage/wire shape 或可访问性语义 | 保持业务 contract，优先调整内部 read model 与 presentation；对外部文本做安全渲染，对高风险动作提供清晰阻断与回退 | 视觉升级不能以接口兼容性、安全或可访问性为代价 |

### 6. Handoff 必须把下一步变成可执行动作

| 导致问题的做法 | 正确方式 | 教训 |
| --- | --- | --- |
| 只说“后续继续”“基本完成”或复制长篇历史，让接手者重新猜边界 | 写清结果、剩余 blocker、exact checkout、ownership、当前 phase、授权状态、freshness、rollback 状态与一个 exact next step | Handoff 的价值是减少恢复成本，不是保存所有过程文本 |
| 把父任务 handoff 当成业务链已闭环，或根据 title/active/idle 判断结项 | 追踪到 terminal successor，读取最后用户请求、最终答复、验证、外部 readback 与明确 blocker | 会话结束、任务结束与业务闭环是三个不同判断 |

## 二、用户偏好与理念档案

### 核心理念

- **证据优先**：结果必须能由当前命令、输出、readback 或来源复核；不接受历史绿灯替代 fresh evidence。
- **授权与能力分离**：工具、凭据、token、phase 或 policy 只表示能力或条件，不自动授予动作权限。
- **生命周期分层**：plan、source、tests、runtime、deployment、production、adoption、commercial validation 分别成立、分别失败。
- **最小范围完整闭环**：只改明确授权范围，但范围内必须从根因、回归、修复到验证闭环。
- **保护用户所有权**：dirty 文件、stash、分支、客户资料和外部记录都先识别 owner；不因方便而覆盖或吸收。
- **可恢复**：高风险动作必须有 rollback、幂等/去重考虑和独立 readback；失败要保留可追溯 receipt。
- **当前事实优先**：Chronicle、memory、旧报告和网页快照用于路由；当前 checkout/runtime/source system 的重新验证决定结论。

### 产品理念

- 战略收敛到 **exactly one ICP、one productized service、one value proposition**，并把事实、推断和未验证假设分开。
- 客户数据收集先做三案例轻量 pilot：客户上传原始材料，agent 组织证据、候选配对和草稿；人工只确认例外与业务判断，不要求客户搭目录或填写复杂表格。
- AI 负责 candidate extraction、编排与降本；确定性业务核心由 contract、规则、权限和 owner approval 控制，尤其不能跨越财务和授权边界。
- 信任不是文案层：source attribution、状态可见、独立 readback、rollback 与 fresh receipt 都是产品能力。
- 优先加强已有 proof center，再考虑新建 portfolio 或第二套展示面；只有已有入口确实无法服务不同受众或已有 2–3 个获准复用案例时才扩张。
- 技术完成与采用分开：可运行、已部署、被客户采用、产生商业价值分别需要证据。

### UI 视觉偏好

共同基线是“高级、可信、克制”：避免紫色霓虹、强 glow、无节制渐变和卡片墙；采用主色加单一强调色、清晰字体层级、非对称 grid，让背景参与构图；保留必要信息密度，同时提高信息来源、更新时间和状态的可见性。

场景不能过度泛化：

- **ShipAI**：品牌入口与服务证明优先，视觉可更精炼、编辑化；必须让能力、证据与行动入口比装饰更醒目。
- **RetirementCalculator**：金融信任、解释性和渐进披露优先；体验可参考成熟财富产品的平静与清晰，但不能把 WarRoom 的告警密度搬入个人决策流程。
- **WarRoom**：允许高密度、非对称和更强态势感；消息来源、社交信息、地图/背景、时间线和更新时间必须成为构图主体，而非缩在同质卡片中。
- **SimonSays**：学习主路径、反馈与键盘/焦点连续性优先；视觉变化不能破坏 storage/wire contract 或 onboarding/recall 流程。

这些差异来自特定项目的直接请求与重复验收模式；不能将某一项目的具体配色、密度或动效强度升级为全局偏好。

### 交互偏好

- 核心路径短，主操作可预测；次要信息渐进披露。
- 状态持续可见，阻断说明原因、影响与恢复动作。
- 高风险动作可控：确认边界明确，失败不盲重试，支持 rollback/readback。
- 同时覆盖 desktop 与 390px 级移动视口。
- Tab 顺序、Escape 关闭、关闭后的焦点返回、可见 focus、live region 是完成条件，不是 polish。
- 保留业务接口、schema、storage/wire shape；UI 内部可重组，外部 contract 不被视觉改版顺带改变。

### 文档与沟通偏好

- 默认使用简体中文，代码标识符、命令、路径与 commit message 保持英文。
- 结果优先；review 使用 findings-first、严重度排序、绝对路径和紧凑行号。
- 完成/修复/通过必须提供 `command / exit_code / key_output / timestamp` 四字段。
- 事实、推断、假设和未验证状态明确分栏；不把计划、建议或能力描述成已实施结果。
- 每次交付给出一个明确下一步；handoff 必须可直接执行，不要求接手者重建上下文。

## 三、可复用规则清单

### 开始任务

- [ ] 确认 task mode：plan、review、diagnose、report-only 或 implementation。
- [ ] 核对 repo 根、checkout/worktree、branch、HEAD、cwd 与适用 `AGENTS.md`。
- [ ] 记录起始 `git status`，区分用户已有改动、agent-owned 改动和保护文件。
- [ ] 写明 exact write set、禁止动作、完成条件与需要暂停的授权点。
- [ ] 检查指定 skill、README、repo index、相关 tests/scripts；不从记忆直接猜当前状态。

### 设计与实现

- [ ] 先追踪端到端真实路径与所有共享调用者，再决定最小修改点。
- [ ] 复用仓库现有模式、标准库、平台能力或已安装依赖；不为未来场景加抽象。
- [ ] 非平凡缺陷先补一个能稳定 RED 的回归，再做共享根因的最小修复。
- [ ] 不顺手重构、优化、改格式或提高评分；范围外问题只记录。
- [ ] 保持外部 contract、schema、wire/storage shape，除非用户明确授权变更。

### UI/UX

- [ ] 先定义场景、用户任务和信息层级，不复用通用“AI 紫色 dashboard”模板。
- [ ] 主色加单一强调色；限制 glow/gradient；避免同质卡片墙。
- [ ] 保持业务所需信息密度，突出来源、时间、状态和主行动。
- [ ] 背景、地图、图形或纹理参与构图，但不牺牲可读性与性能。
- [ ] 用真实浏览器验收 desktop 与 `390x844`，覆盖溢出、点击、Tab、Escape、焦点返回和 live region。

### 外部写入

- [ ] 为每个动作确认当前 action grant、目标、作用域、owner 和幂等键；phase/policy/token 不算授权。
- [ ] 写前读取当前状态并绑定 revision/version；写后使用独立路径 readback。
- [ ] 预先定义 rollback；失败时先判断是否已部分 mutation，保留 receipt，不盲重试。
- [ ] 客户数据最小化、脱敏并按授权使用；不把仓库可见性当成公开复用许可。
- [ ] AI 结果保持 candidate 状态，确定性规则与 owner approval 决定落账、报价、发布或授权。

### 高风险动作

- [ ] 明确 authorization state、phase、ownership、freshness state、rollback 和 blast radius。
- [ ] 远程、财务、生产、删除、强制覆盖等动作前做只读 target resolution。
- [ ] 权限、认证、政策、网络或依赖阻断与代码回归分开；不通过改代码绕过 gate。
- [ ] 使用最小 allowlist，不用宽泛 glob、整目录同步或隐式默认目标。
- [ ] 动作后独立 readback；无法确认最终状态时报告 unknown/partial，而不是 success。

### Git

- [ ] 开始与结束都运行 `git status`，不覆盖、reset、clean 或吸收用户改动。
- [ ] 用 `main...branch`、worktree list 与 ancestry 证明合并/删除条件。
- [ ] rebase 冲突按语义保留双方有效能力，不机械选 ours/theirs。
- [ ] 仅暂存授权路径；“commit and push”不自动授权 PR、deploy 或 runtime sync。
- [ ] 改写远端必须单独授权，并使用已验证 lease 的 `--force-with-lease`。

### 验证与交付

- [ ] 先跑最小针对性回归，再跑仓库权威完整门禁和 `git diff --check`。
- [ ] 等待命令终态；没有最终 `exit_code` 不得判绿。
- [ ] 对 UI 增加真实浏览器证据；对外部写增加独立 readback；对 runtime 增加实际 runtime probe。
- [ ] 四字段 receipt 完整：`command / exit_code / key_output / timestamp`。
- [ ] 分层报告 plan/source/tests/runtime/deployment/production/adoption/commercial 状态。
- [ ] 结束核对 exact diff、ownership、未提交/未推送状态、remaining risk 与一个 exact next step。

### 9 步快速决策协议

1. **定模式**：这是检查、诊断、计划还是获准实施？未获准 mutation 就保持只读。
2. **定锚点**：确认 repo、checkout、branch、HEAD、cwd 与适用规则。
3. **冻边界**：记录 dirty ownership、exact write set、外部动作和禁止项。
4. **读真相**：优先当前源码、tests、scripts、runtime/source-system readback；memory/Chronicle 只路由。
5. **分状态**：逐层标记 plan/source/tests/runtime/deployment/production/adoption/commercial，不跨层推断。
6. **找根因**：遍历共享调用者；非平凡缺陷先建立 RED 证据。
7. **做最小闭环**：复用既有能力，只改必要位置；外部/高风险动作先核授权与 rollback。
8. **fresh 验证**：跑针对性、完整、浏览器或 readback gate，收齐四字段终态。
9. **精确交付**：报告结果、边界、remaining risk 和唯一 next step；不得把 handoff 当成后续动作授权。

## 四、方法、证据边界与语料快照

### 覆盖范围

- 本复盘只覆盖本机 **current accessible Codex**：`<codex-home>/state_5.sqlite` 中的线程元数据、其指向且当前存在的 rollout JSONL、`codex-chat-search` 可检索的 user/assistant 消息，以及 `<codex-home>/memories/MEMORY.md` 中的归纳索引。
- 不声称覆盖未同步的 ChatGPT 会话、其他设备/账号、已删除记录、不可访问 connector 历史或未落盘的临时上下文。
- 生成时 fresh 查询结果：SQLite 中有 **2,396** 个 thread 和 **2,396** 个唯一 rollout path；磁盘上 `sessions` 与 `archived_sessions` 合计 **2,396** 个 rollout JSONL，SQLite 所指路径 **2,396 存在、0 缺失**；`MEMORY.md` 有 **103** 组 `## User preferences` 与 **405** 条 `- symptom:` 记录。
- 上述数字是 2026-08-14T22:14:07Z 的本机快照，不应在未来报告中沿用；应重新查询。

### 归因规则

- 直接用户表达：仅包括用户在任务中明确写出的目标、约束、审美或验收要求。
- 归纳偏好：必须由多个可核对任务反复支持，并保留适用场景；不能把一次项目选择泛化为全局人格。
- 系统注入、developer/AGENTS 文本、ambient UI、工具政策，以及复制到 prompt 中的 agent transcript，不当作直接用户表达。
- Chronicle 只用于时间线与检索入口交叉核对；可见窗口、任务卡、网页或旧命令输出不证明动作已执行。
- Memory 与 rollout summary 是压缩索引；关键当前事实必须回到 SQLite、原始 rollout、当前 checkout/runtime 或 source system 重新验证。
- 不收集或复述凭据、token、账号值、客户隐私、私人通信内容或具体财务细节；必要时只保留中性的流程边界。

### Fresh 统计复核入口

```bash
CODEX_HOME_PATH=/path/to/codex-home
sqlite3 "${CODEX_HOME_PATH}/state_5.sqlite" \
  'SELECT COUNT(*), COUNT(DISTINCT rollout_path) FROM threads;'
find "${CODEX_HOME_PATH}/sessions" "${CODEX_HOME_PATH}/archived_sessions" \
  -type f -name 'rollout-*.jsonl' | wc -l
rg -n '^## User preferences$' "${CODEX_HOME_PATH}/memories/MEMORY.md" | wc -l
rg -n '^- symptom:' "${CODEX_HOME_PATH}/memories/MEMORY.md" | wc -l
```

### 代表性 thread ID 证据索引

| Thread ID | 代表性证据 | 使用边界 |
| --- | --- | --- |
| `019fa641-ba42-7971-aab3-691892eac50e` | Codex 会话结项审计：按最终请求、receipt、blocker、handoff 与 successor 判断；本地 Codex 可审计但 ChatGPT 覆盖不足 | 支持 current accessible Codex only、handoff 去重和 exact next step，不支持全平台覆盖声明 |
| `019fe9bd-54b8-7ca0-b5de-da99b69bf6f9` | MyCodexEnv 分支治理：ancestry/rebase/lease、dirty ownership 与 source green/runtime drift 分离 | 支持 Git 与生命周期分层；历史 SHA/测试数字不是当前状态 |
| `019fe957-92e4-7621-b17d-e7117fd96daa` | 只读商业定位：exactly one ICP/service/value proposition，优先增强既有 proof center | 支持产品理念；市场与仓库事实需要按当前日期复核 |
| `019fc4f9-5cd8-7633-a28a-78570988e897` | RED-first 的 DHF review 修复：先四个失败回归、再最小修复、完整门禁和最终退出码 | 支持根因修复、exact write set 与四字段证据；不把该次 green 复用于当前代码 |
| `019fc38a-48f7-7e52-be7d-5c365d0a3f29` | SimonSays split-profile 修复：共享 read model、wire shape 保持、desktop/390x844 与焦点验收仍需独立闭环 | 支持共享根因、contract、真实浏览器/可访问性；push 不等于 browser/runtime acceptance |
| `019c8d4f-443c-7810-af17-36a2a27ed4d7` | ShipAI 的外部 design skill 安装与 index 优化链 | 仅作 ShipAI 视觉工作与第三方 skill 安全/复用的入口，不把 skill 文本当用户直接偏好 |
| `019caec6-d556-7dd3-8b71-90d697899f09` | WarRoom 高密度 UX：保持信息密度、强化消息来源/社交信息、更新时间与来源链接 | 支持 WarRoom 场景化偏好，不泛化为所有产品都应高密度 |
| `019dad5d-a726-7241-af6d-49481862bfb3` | 加拿大退休计算器：面向真实用户的金融信任、解释性与成熟财富产品式体验 | 支持 RetirementCalculator 场景化偏好；不复述个人财务数据或把产品设计当财务建议 |
| `019ff166-e57a-7dd1-b515-60542aff1797` | ShipQ Phase 2：三案例轻量 pilot、客户负担最小化、`default=deny` 下外部 Drive 写入阻断 | 支持授权/能力分离与轻量客户流程；计划、policy 或 token 不构成连接器写授权 |

## 五、结论

这套工作方式的核心不是增加流程，而是让每个结论停在它真正有证据支持的生命周期层：在正确 checkout 内，以最小授权范围修共享根因，用 fresh gate 和独立 readback 闭环，并把仍未完成的下一步写到足够精确、但绝不自动越权。
