# DHF 公开站修复计划 v2（委员会修订版）

日期：2026-08-22 · 状态：计划，未写仓库文件、未部署
`verification_receipt: verification_not_applicable`（本文件只是计划；文中数字已用只读探针核对，见附录 A）

## 0. 本版相对 v1 的改动

v1 的切片顺序和「先统一真相，再修路径与呈现，最后两阶段发布」的骨架保留。本版修的是 v1 会在实施中自己绊倒自己的地方：

1. 英文 Lifecycle 的处理从「默默推翻 08-11 决策」改为一个显式 owner 决策 D1，默认走不反转决策的路线。
2. 把夜间 22:00 `dhf-public-site-sync` 自动 commit/push 任务纳入时序，消掉它和隔离 worktree、两个 PR 的竞争。
3. RED 合同改为先探针、后定字符串；「`File: docs/...`」这条在首页/Beginner 上 grep 为 0，不能直接当缺陷。
4. metadata 批处理增加 twin 映射与单页例外，否则「缺 twin 整批失败」按定义必败（25 EN ≠ 23 CN）。
5. 明确 48 页状态日期与两阶段发布的关系：日期只在 PR A 推进一次，PR B 不碰日期。
6. 「profiles 已进入源码合同」要有指名道姓的只读证据；教学页在三种 runtime 结果下各有固定措辞。
7. 标出哪些测试是新增的；把「parity 验证日期不随状态日期推进」写成规则；社交图给出生成方式。

## 1. 架构对齐决策

| 编号 | 决策 | 依据 / 备注 |
|---|---|---|
| A1 | `light / standard / governed` 是否已是**源码合同**，由 Slice 0 的只读探针决定，不预设答案 | 证据来源见 §3 Slice 0 第 3 步；Status EN 第 163 行现仍写「do not describe … as active runtime behavior」 |
| A2 | 正式学习路径固定为 `Home → Beginner → Memory Map → Context → Lifecycle → Governance → Evidence → Status` | 取代首页现有四步 |
| A3 | 语言切换代表**语义等价**页面；但「等价」的判定以 `dhf-content-drift-accept.json` 中已归档的 owner 决策为上位规则，不得在本计划内默默推翻 | 现有 8 条 accept 条目中 4 条是 owner 决策（Lifecycle EN 轻量版 08-11；three-lenses EN 索引 08-19） |
| A4 | Status 是唯一「当前事实页」；其他页只解释概念并链接 Status，不复制运行证据 | 同 v1 |
| A5 | `data-dhf-status` 日期是 48 页 + `test_runner.py` 的硬不变量；**每次发布只推进一次**，且「Local runtime parity: verified <date>」只在真正重跑 parity 时才改 | 来自既有状态合同 |

### 决策 D1：英文 Lifecycle 怎么办 —— **owner 已于 2026-08-22 拍板：选项 A**

执行细则（取代下文选项描述中的待定项）：

- 英文 `project-lifecycle-harness-flow-en.html` 按中文页五区块补齐：Overview / Flow / Stage-skill routing / Runtime helpers / Delivery gates；lead 文案去掉「lightweight entry map」定位；mermaid 边数与中文对齐（含 security 与 browser-QA 分支）。
- `project-lifecycle-harness-flow-skills-en-status-style.html` **保留**，定位为「Skill 路由图视图」，它与 `…-skills-zh-status-style.html` 本就是自成一对、同步的页面。为避免重复内容：英文 Lifecycle 的 Stage-skill routing 区块只放阶段→skill 的摘要表并链接到 status-style 页，**不**整页复制那张路由图；status-style 页 canonical 指向自身，og:title 用「Skill Routing Diagram」与主 Lifecycle 区分。
- `dhf-content-drift-accept.json` 删除 `project-lifecycle-harness-flow-en.html:headings` 与 `:branches` 两条；完成标准 9 的 accept 条目数基线由 8 变 6，不得再新增。
- 翻译以 `docs/LIFECYCLE_SKILL_ROUTING.md` 的 Lifecycle Stage Map 为事实来源，中文页为结构权威；任何中文页有而路由文档没有的断言，先查文档再翻，查不到即触发停止条件「英文 Lifecycle 无法可靠翻译」。
- Slice 4 写集 +1 页（status-style EN 的 lead 与链接调整），Slice 3 的 twin 映射把两对 Lifecycle 页分开登记。
- `test_dhf_core_bilingual_parity_contract` 对 Lifecycle 这一对不再读 accept 豁免；`dhf_content_drift.py` 在 Slice 4 结束后必须对这一对报 0。

以下为拍板前的两个选项，留作决策记录：

- **选项 B（推荐，默认）**：尊重 08-11 决策。英文页改名为 “Project Lifecycle — Summary Flow”，lead 文案明说这是轻量入口；页首加一条醒目链接指向完整英文对等页 `project-lifecycle-harness-flow-skills-en-status-style.html`；语言按钮**保持标准组件样式**（`test_dhf_language_switch_border_contract` 钉住的是 `.dhf-nav a.dhf-nav-lang` 的 1px 边框规则，Slice 5 改 44px 时不得拆掉这条规则），仍指向中文完整页；这对「摘要 ↔ 完整」是全站唯一被 accept 文件登记的非等价切换，A3 对它豁免。accept 两条条目**保留**，理由字段追加「2026-08-22 复核，维持」。
- **选项 A**：反转 08-11 决策，按中文五区块（Overview / Flow / Stage-skill routing / Runtime helpers / Delivery gates）补齐英文，并删除两条 accept 条目。必须同时决定 `…-skills-en-status-style.html` 的去留（否则两张完整英文流程图互为重复内容，canonical 也说不清）。
- 不允许的做法：补齐英文的同时留着 status-style 页，两边都不说谁是主。

D1 选 A 时，Slice 4 的写集多 1 页（status-style 页的定位/链接调整），accept 文件删 2 条。

### 「8 组核心双语页」明确清单

Home（index / index-zh，`index-en` 为兼容副本）、Beginner、Memory Map、Context、Lifecycle（按 D1）、Governance、Evidence（`dhf-value-evidence`）、Status。three-lenses、best-care、case-safe 等 Evidence 子页**不在**「语义结构一致」标准内，它们已有各自的 wave 测试和 accept 决策。

## 2. 完成标准

1. Status EN/CN 不再含「working-tree change」「Not performed in this task」「尚未提交」等文案（现位于 EN 132/135 行、CN 88 行）。
2. Status 以五行分别陈述：Source / Runtime / Publication / Production / Customer outcome，每行都有日期或「未验证」。
3. 首页五步路径、Beginner Continue、Memory Map Prev/Next、Context Previous 全部经过 Memory Map。
4. 48 页（25 `lang=en` / 23 `lang=zh-CN`）全部具备唯一 title、description、canonical、hreflang（en / zh-CN / x-default）、`og:*`、`twitter:card`；单页例外按 §3 Slice 3 的 twin 映射处理。
5. 上述 8 组核心页语义 section 一致（Lifecycle 按 D1 的定义）。
6. `.dhf-nav-lang`（现 `min-height: 30px !important`，css 第 258 行）与 Memory Map 章节按钮 ≥ 44px。
7. 首页、Beginner 正文与 footer 不出现源码路径与命令清单；Memory Map 折叠卡片内的 `docs/repo-index.md` 等保留。
8. 16 个核心页在 1440 / 900 / 390 无溢出、无 console/network 错误、无断链。
9. `dhf_content_drift.py --json` count=0、stale=0；accept 条目由 8 减到 6，不新增。
10. 夜间同步任务在整个实施窗口内没有产生与本分支冲突的提交（§3 Slice 0 第 6 步）。

## 3. 实施切片

### Slice 0：隔离、事实探针与 RED（AFK · high）

1. 本机先确认并清除残留 `.git/index.lock`（2026-08-22 一次只读 `git status` 在 VM mount 上留下了 0 字节锁文件，VM 内不可删）。
2. 从最新 `origin/main` 建隔离 worktree；基线断言：48 页含 `dhf-nav-links`，25 `lang=en` / 23 `lang=zh-CN`，48 页 `data-dhf-status="2026-08-11"`；不符即停。
3. 只读探针，**每条都把输出存进 `tasks/` 下的实施记录**：
   - Source 侧：`grep -rn 'light\|standard\|governed' codex/policy codex/hooks scripts/harness_*.py` + `git log -1 --format=%H -- <命中文件>`；命中并且 router/policy 有分支逻辑 → 「源码合同已含 profiles」；只命中文档/注释 → 「仅文档」。
   - Runtime 侧：`python3 scripts/harness_status.py status --runtime`，结果归入 `runtime_promoted / source_stage_unsynced / drifted / unavailable` 四类。
   - Evidence：`python3 scripts/dhf_simplification_evidence.py`。
   - Publication：对 16 个核心页做公开回读（HTTP 200 + `data-dhf-status` 值 + 页面 commit 标记）。
4. 探针字符串核对后再写 RED 合同（新增 4 个测试；现有测试名见附录 B）：
   - `test_dhf_public_truth_contract`（新增）：Status 不含 stale 文案列表。
   - `test_public_dhf_information_architecture`（现有，改常量）：五步路径含 Memory Map。
   - `test_dhf_public_metadata_contract`（新增）：48 页 metadata 完整 + twin 映射一致。
   - `test_dhf_core_bilingual_parity_contract`（新增）：8 组核心页 section ID 一致，读取 accept 文件做豁免。
   - `test_dhf_touch_target_contract`（新增）：CSS 合同，`.dhf-nav-lang` 与 Memory Map 章节按钮 min-height ≥ 44px。
   - 「公共页不暴露源码路径」：**先 grep 确定实际模式**（首页/Beginner 的 `File: docs/` 为 0；要找的是 footer/正文里的 `docs/…`、`scripts/…`、`~/.codex` 字面量），范围限定为首页与 Beginner 的 footer 和非折叠正文，再写进 `test_dhf_public_truth_contract`。
5. 运行一次，确认每个 RED 都指向探针里看到的真实缺陷；RED 来自字符串猜错的，修测试而非修站。
6. **夜间任务时序**：实施窗口要么整体落在 22:00 之前并在 22:00 前合并 PR A，要么在 22:00 后重新 `git rebase origin/main`；合并前必须再跑一次 `dhf_content_drift.py`。不修改、不停用该任务（它属于 policy 范围）。
7. 向 owner 提交 D1 决策请求，附探针结果。

### Slice 1：P0 当前真相修复（AFK · runtime 只读，禁止 promotion）

- Status EN/CN 五行真相表按 Slice 0 的四类结果填写固定措辞：

| Runtime 探针 | Status 写法 | Beginner / Lifecycle 教学页写法 |
|---|---|---|
| `runtime_promoted` | 「已激活，验证于 <fresh timestamp>」+ 摘要 | 现在时态（「governed 工作会触发…」） |
| `source_stage_unsynced` | 「源码已实现，本机 runtime 尚未激活」 | 「按设计（by design）…」+ 链接 Status |
| `drifted / unavailable` | 「未验证」 | 同上，且不得出现「runs / 会运行」 |

- Publication 行在 PR A 中写「更新已合并，等待公开回读」。
- 删除 EN 132/135、CN 88 行的 stale 文案。EN 163 行「do not describe … as active」**改写而非删除**：`runtime_promoted` 时改为「profiles 已于 <date> 激活」；`source_stage_unsynced` 时它仍然为真，改成与上表同义的一句并保留；`drifted / unavailable` 时保留原句。
- Production 与 Customer outcome 两行本计划**没有新证据**，只做日期与措辞一致性整理，沿用现有事实；不得借本次刷新顺手升级这两行的状态。
- `data-dhf-status` 48 页一次性推进到 PR A 的日期；`test_runner.py` 期望值同步；parity 日期不动。
- 同步 `repo-index.md`、`LIFECYCLE_SKILL_ROUTING.md`、`HARNESS_RUNTIME.md` 中的 profile 陈述，措辞取同一张表。

### Slice 2：重建学习路径（AFK）

同 v1：首页三份（index / index-zh / index-en）四步改五步，Hero CTA 加 Memory Map；Beginner Continue 第一项 → Memory Map；Memory Map 加 Prev Beginner / Next Context / Current Status；Context Previous → Memory Map。Memory Map 的 Prev/Next 组件复用其他页的局部导航类名，便于 Slice 5 统一。

### Slice 3：全站 metadata 与社交分享（AFK）

- 先生成 **twin 映射表**（由 `dhf-nav-links` 里的语言切换目标反推），并显式登记单页例外：
  - `index-en.html`：canonical → `/`，hreflang 与 `index.html` 相同，不视为缺 twin。
  - `lifecycle-skill-routing-en.html`：无中文 twin，hreflang 只写 en + x-default。
  - 其余 EN 多出的页逐一登记；映射表本身进 `test_dhf_public_metadata_contract`。
- 预检：现 0 页有 `og:*`、17 页有 canonical；已有 canonical 的页若与映射表冲突 → 整批失败；无冲突则覆盖。
- 每页写：唯一 title / description（按页面 h1 与 lead 生成初稿，人工核对中英文各一遍）、canonical、hreflang 三件套、`og:title/description/url/image/image:alt/locale`、`twitter:card=summary_large_image`。
- 批处理合同：只允许 `<head>` 内变化，`<body>` 字节级不变，否则整批失败。
- 社交图：新增 `docs/dhf-social-card.html` 模板（语言中性：站名 + 一句 tagline + 域名），用仓库已有的 Playwright 截 1200×630 成 `docs/dhf-social-card.png`；模板留在仓库以便重生成。

### Slice 4：核心双语等价与受众降噪（AFK）

- Lifecycle 按 D1 执行（已定选项 A：补齐英文五区块、status-style 页降为路由图视图并被链接、删 2 条 accept）。
- Beginner 两页统一语义 section ID；其他核心页只修 parity 审计里的真实缺口。
- 首页、Beginner：行为语言优先，脚本名、`~/.codex`、命令放进 `<details>` “Implementation details”；Memory Map 的技术细节保留在折叠卡片中。
- 不新增 accept 条目。

### Slice 5：共享视觉与无障碍（AFK）

- Memory Map 加与其他页一致的可见 Status 条。
- css 第 258 行 `min-height: 30px !important` → 44px；Memory Map 章节按钮 ≥ 44px。
- Status 四卡：≥ 900px 为 2×2，< 900px 单列（900 是 QA 的中间断点，不能落在 3+1）。
- `.reveal` 强制可见的三条路径分别实现：`@media print`、`@media (prefers-reduced-motion: reduce)`、以及 `html[data-capture]` 属性（Browser QA 全页截图前由脚本设置），避免截图靠等待动画。
- 触控高度的最终裁判是 Browser QA 里 Playwright `boundingBox().height ≥ 44` 的实测（390px 视口），`test_dhf_touch_target_contract` 只是 CSS 层守卫，防止再次出现 `!important` 覆盖。
- 保留 Memory Map 字体与 Hero；统一 global nav、status 条、footer、语言按钮组件。

### Slice 6：状态与文档收口（AFK）

- `repo-index.md` 日期、阅读顺序、profile 真相；`LIFECYCLE_SKILL_ROUTING.md` 及其 HTML 渲染页；`HARNESS_RUNTIME.md` runtime 边界。
- `harness-state.md` 顶部 Current Snapshot 从旧 Wave 4 更新，并追加一条实施 checkpoint；不重写历史 State Log。

### Slice 7：验证与两阶段发布（本地 AFK；远程发布 HITL）

Focused gate（含 4 个新增测试）：

```
PYTHONDONTWRITEBYTECODE=1 python3 -c '
import test_runner as t
t.test_public_dhf_information_architecture()
t.test_public_dhf_architecture_status_alignment()
t.test_dhf_memory_map_bilingual_information_architecture()
t.test_dhf_public_truth_contract()          # new
t.test_dhf_public_metadata_contract()       # new
t.test_dhf_core_bilingual_parity_contract() # new
t.test_dhf_touch_target_contract()          # new
'
```

最终门禁：

```
python3 scripts/check_surfaces.py --repo-root "$(pwd)" --check-public-nav
python3 scripts/dhf_content_drift.py --json     # count=0, stale=0
git diff --check
python3 test_runner.py
```

Browser QA 同 v1（16 页 × 1440/900/390、light/dark、reduced-motion、print、导航/语言/Prev-Next/卡片展开、44px、metadata 与社交图回读、全站 crawl、零 console/network 错误）。

发布：

1. PR A：全部内容、路径、metadata、视觉、Status 候选文案（publication=「已合并待回读」）。合并前 rebase 到 `origin/main` 并重跑 drift。
2. CI（`.github/workflows/ci.yml`：跑 `test_runner.py` 与 `check_surfaces.py`，**不跑** drift）green → 合并 → 等 Pages（`pages.yml`）`status=built`。drift count=0 因此只能靠本地门禁和夜间任务兜底，PR 描述里要贴本地 drift 输出。
3. 公开回读 16 页 + 社交 metadata + 站内链接。
4. PR B：**只改** Status EN/CN 的 Publication 行（「已公开并回读，<时间> <commit>」）。**不改** `data-dhf-status` 日期、不改 parity 日期、不动其他 46 页。Slice 0 写 `test_dhf_public_truth_contract` 时要确认 `test_public_dhf_architecture_status_alignment` 没有钉住 Publication 行文本，否则 PR B 会红。
5. 再等 Pages 并回读。

回滚：`git revert` 两个 merge commit；不 force-push、不改 DNS；若夜间任务在其间推送过，先 rebase 再 revert。

## 4. 停止条件

- runtime 探针 `drifted / unavailable`：继续修站，但 Status 与教学页一律按表中「未验证」行措辞。
- 48 页 / 25 / 23 基线不符；`data-dhf-status` 值不统一。
- 发现**非本任务、非夜间同步任务**产生的 dirty 文件（夜间任务的提交按 Slice 0 第 6 步 rebase 处理，不算停止）。
- metadata 批处理无法保持 `<body>` 不变。
- D1 已拍板（A）；若翻译过程中发现中文 Lifecycle 的断言在 `LIFECYCLE_SKILL_ROUTING.md` 中无据可查，停止并回报，不自行补写。
- CI、drift（含 stale accept）、浏览器或 Pages 回读失败。
- 发布没有单独授权。

## 5. 不修改

`codex/` runtime、hooks、skills、policy（含夜间同步任务本身）；`scripts/dhf_content_drift.py`；Pages workflow、CNAME、DNS；DHF taxonomy、Evidence ladder、案例事实；客户采用或商业价值声明。

## 附录 A：2026-08-22 只读探针结果（本计划依据）

- `grep -l dhf-nav-links docs/*.html | wc -l` = 48；`lang="en"` 25，`lang="zh-CN"` 23。
- `data-dhf-status` 48 页，全部 `2026-08-11`。
- `og:title` 0 页；`rel="canonical"` 17 页。
- Status EN 第 132 行「remains a working-tree change」、135 行「Not performed in this task」、163 行「do not describe light/standard/governed profiles as active」；CN 第 88 行「仍是 working-tree 变更」。
- `File: docs/` 在 index.html 与 beginner-guide-en 为 0 处；`docs/repo-index.md` 出现在 memory-map-en 折叠卡片内。
- `docs/dhf-site-status.css` 第 258 行 `min-height: 30px !important`；第 230/410/417 行已有 44px 规则。
- accept 文件 8 条，其中 Lifecycle EN 两条（08-11）、three-lenses EN 两条（08-19）为 owner 决策。
- 本地 `main` 与 `origin/main` 同步；HEAD `b3ad06a`。
- `scripts/harness_status.py status --runtime|--evidence` 存在且只读。
- `test_runner.py` 第 10425 行附近钉住 `Local runtime parity: verified 2026-08-10`（注意：是 08-10，不是状态日期 08-11），印证 A5「parity 日期与状态日期是两个量」。
- `ci.yml` 第 54/60 行只跑 `test_runner.py` 与 `check_surfaces.py`。
- 仓库已有 Playwright 用法：`scripts/export_mermaid_flowchart_png.py`，社交图可复用同一套依赖。

## 附录 B：现有相关测试名

`test_public_dhf_information_architecture`、`test_public_dhf_architecture_status_alignment`、`test_dhf_language_switch_border_contract`、`test_dhf_memory_map_bilingual_information_architecture`、`test_dhf_value_evidence_information_architecture`、`test_dhf_evidence_wave1…wave4_*`。`test_dhf_public_truth_contract`、`test_dhf_public_metadata_contract`、`test_dhf_core_bilingual_parity_contract`、`test_dhf_touch_target_contract` 均为本计划新增。
