# DHF Value & Evidence 模块审查与调整计划

日期：2026-08-19 · 审查范围：`docs/` 下 Evidence 模块全部 22 个子页面（中英）+ 两个 hub 页 + 漂移检测器
审查方式：`dhf-public-site-sync` skill 的检测约定 + 全站链接图谱扫描 + 六关键词逐页词频统计 + `scripts/dhf_content_drift.py` 实跑（read-only）

---

## 一、审查结论（先说最重要的）

你的三个直觉全部被数据证实，而且根源是同一个：**这个站有两套"网络机制"，一套能用，一套是摆设。**

- 能用的：`dhf-value-evidence-cn/en` 上的 memory spine（CAP → BRIDGE × SAFE → TRUST + RECOVER 失败分支），五个节点都是可点击的链接，各自指向理念的"归属页"。
- 摆设的：其余 20 个子页面顶部的 memory cue（`data-dhf-memory-cue`），只是纯文本徽章——**一个链接都没有**，而且每页只列 2–3 个词条。它长得像导航，实际什么也连不了。

网络感稀薄，不是因为缺内容，而是因为唯一的全站互链组件不可点击。

### 发现 1：PROTECT 不是记忆词汇体系的一等成员

- value-evidence 两页的 spine 里没有 PROTECT（只有 CAP/BRIDGE/SAFE/TRUST/RECOVER + BEST/CARE 两个 lens）。
- 更扎眼的：`dhf-protect-seven-components-cn/en` **自己页面的 memory cue 里都没有 PROTECT 词条**——只标了 SAFE、TRUST 和 BEST lens。
- 全站词频：PROTECT 除自己页（4 次）和 best-care-recover（1–2 次）外，在整个证据族几乎为 0。

### 发现 2：protect 页确实是孤岛（你点名的那页）

出链：protect-cn 的 "Connected reading" 只指 5 个 hub 页（新手指南、生命周期、治理、状态、evidence），**没有任何一条指向证据族兄弟页面**。
入链：中文侧只有 value-evidence-cn、best-care-recover、data-business-value-explainer 三页指向它；英文侧只有 value-evidence-en 和 architecture-status-en。而 case-safe-mapping、safe-controlled-recovery、incident-memory-map 这些最该引用"是哪个受保护组件挡住了失控"的页面，一条链接都没有。

### 发现 3：EN 侧整体不如 CN 完整，且这是系统性的，不止你点名那一页

| 页面 | CN | EN | 差距 |
|---|---|---|---|
| shipq-dhf-safe-controlled-recovery | 32.6KB · 3 张表 · 有关联阅读区 | 11.5KB · 0 表 · **无关联阅读区** | H2 骨架相同（9 个），但每节内容瘦身，表格全丢 |
| shipq-dhf-incident-recovery-memory-map | 22.1KB · 1 张表 | 9.6KB · 0 表 | SAFE 停点矩阵表丢失 |
| dhf-shipq-development-history | 42.8KB · RECOVER 出现 2 次 | 16.9KB · **RECOVER 0 次** | EN 版演进史完全不提失败分支 |
| dhf-data-business-value-explainer | 30.7KB | 8.8KB | EN 是摘要级 |
| dhf-examples-three-lenses | 53.4KB（十案例全文） | 8.5KB（索引级） | 可能是刻意轻量，需要决策 |
| dhf-best-care-recover | 28.4KB | 13.2KB | EN 有互链但内容减半 |

互链网络同样不对称：CN 证据子页之间有密集的"相关页面"互链条（safe-controlled-recovery ↔ incident-map ↔ case-mapping ↔ development-history ↔ explainer ↔ three-lenses 全连通）；EN 侧除 best-care-recover-en 和 case-safe-mapping-en 有少量互链外，其余子页只有全局导航 + 中文对照链接。

### 发现 4：为什么夜间漂移任务从来没报过这些？——检测器有个命名盲区

`dhf_content_drift.py` 的 `check_bilingual` 只匹配 `*-en.html ↔ *-cn.html` 命名对。而整个证据族的中文页用的是**无后缀命名**（`shipq-dhf-safe-controlled-recovery.html` 即中文），所以这一族 11 对页面全部逃过双语结构比对。今天实跑检测器：`ok: true, count: 0`——站在检测器视角一切干净，站在读者视角 EN 少了一半。这不是检测器坏了，是它压根没看这些页。

### 发现 5：value-evidence-cn 的结构图确实简陋，但方向没错

现在的 spine 是"一行五格 + 两个 lens 链接"：有主链、有失败分支、可点击——骨架是对的。缺的是：(a) PROTECT 层缺席；(b) 没有表达"PROTECT 在运行时支撑 SAFE"这层关系；(c) 没有把 BEST/CARE/RECOVER 和七级证据阶梯的关系画出来；(d) 视觉上就是一排卡片，不像一张"地图"。

---

## 二、关键决策：Evidence 页和 best-care-recover 页怎么分工

建议**不合并，重新分工**，理由：两页回答的是不同问题，合并会把 28KB 的助记内容塞进 hub 页，hub 就不再是 hub。

| | dhf-value-evidence（hub） | dhf-best-care-recover（助记页） |
|---|---|---|
| 回答的问题 | 六个理念**是什么、证据在哪一页、彼此什么关系** | 这套体系**怎么记、怎么复述** |
| 持有物 | 全站唯一的**概念地图**（升级版 spine，含 PROTECT 层） | BEST/CARE 展开、RECOVER 七步、词汇详解 |
| 词汇定义 | 每词一句话 + 链接归属页 | 保留完整 vocabulary 区（唯一详解处） |
| 互相引用 | 地图下方一行："怎么把这张图记住 → BEST/CARE" | 保留现有 model taxonomy 六格，但改为与新地图同构，并回链 Evidence 页 |

best-care-recover 页的 "04 · MODEL TAXONOMY" 六格其实已经是一张不错的分工表（Control & Value / Runtime Architecture=PROTECT / Evolution / Operating Memory / Incident Response / Cases）——新概念地图直接以它为蓝本画，两页天然对齐，不产生第二套说法。

---

## 三、分阶段调整计划

### Phase 0 · 定合同（半小时，纯决策，不改文件）

1. 确认词汇合同：六个一等理念 = CAP、BRIDGE、SAFE、TRUST、RECOVER、**PROTECT**；BEST/CARE 是 lens 不是理念。所有页面的 cue/spine/图都遵守这一套，不再出现"PROTECT 页不认识 PROTECT"。
2. 确认每个理念的唯一归属页（现 spine 已隐含，明确化）：
   CAP/BRIDGE → development-history · SAFE → case-safe-mapping · TRUST → data-business-value-explainer · RECOVER → safe-controlled-recovery · PROTECT → protect-seven-components
3. 决策：examples-three-lenses-en 是"待补全"还是"刻意轻量索引"？若是后者，Phase 5 里写 accept 条目（参照 lifecycle-flow-en 先例）。

### Phase 1 · 把 memory cue 从徽章变成导航（这是投入产出比最高的一步）

改 `docs/dhf-evidence-memory.css` + 22 个子页面的 cue 块：

1. cue 词条全部变成 `<a>`，链到各理念归属页——CSS 已有 `.dhf-memory-key` 的 hover 样式可复用，成本低。
2. 每页 cue 展示**全部六个词条**，用新增的 `data-dhf-memory-emphasis` 属性高亮本页主角、灰化其余（CSS 加两条规则即可）。读者在任何一页都能看到完整词汇表 + 自己在地图中的位置 + 一步跳到任何理念。
3. protect 两页的 cue 加入 PROTECT 词条并高亮。

这一步完成后，22 页 × 6 词条 = 全站网络自动成形，protect 孤岛问题解决一半。

### Phase 2 · 重做 value-evidence 概念地图（CN 先行，EN 同步）

把现有单行 spine 升级为两层地图（仍是 HTML/CSS 栅格，不引入 mermaid，保持可点击）：

```
CAP ──→ BRIDGE ──×── SAFE ──→ TRUST        ← 主链（价值层）
                      │  ↘ 失败分支 → RECOVER
                      ▲
                   PROTECT                  ← 运行时层：七个受保护组件在运行时落实 SAFE
────────────────────────────────────────
BEST · 系统视角 ｜ CARE · 行动视角          ← 记忆层（lens，链 best-care-recover）
```

要点：PROTECT 放在 SAFE 正下方、用向上箭头表达"支撑"关系（这是现在整个站都没说清的一层）；RECOVER 保持虚线失败分支；每个节点仍链归属页；图下加一行小字"证据层级见下方阶梯"衔接 02 · Evidence Ladder。
**按 [[css-changes-require-live-measurement]] 的教训：布局改动必须在真实浏览器里量过再落文件**，桌面 + 960px + 720px 三档都要看。

### Phase 3 · 把 protect 页织进网络（双向）

出向：protect-cn/en 的 "Connected reading" 增加四张证据族卡片——
- safe-controlled-recovery（"WAL、回滚、readback 这些组件在真实事故里怎么工作"）
- case-safe-mapping（"组件 → SAFE 控制的映射索引"）
- incident-recovery-memory-map（"事故中每个停点由哪个组件强制"）
- best-care-recover（"PROTECT 在整个模型分类里的位置"）

入向：case-safe-mapping、safe-controlled-recovery、incident-memory-map 三页（CN+EN 共 6 个文件）在讲到 WAL/回滚/授权边界处各加一条去 protect 的链接。加上 Phase 1 的 cue 链接，protect 的入链从 3 变成 10+。

### Phase 4 · EN 补全（工作量最大的一步，写英文 prose，不做机器翻译）

优先级排序：
1. **shipq-dhf-safe-controlled-recovery-en**（你点名的）：补三张表（四个状态世界对照、SAFE 控制明细、TRUST 价值转化），补 CN 版有的关联阅读区。骨架已同构，是填肉不是重写。
2. **shipq-dhf-incident-recovery-memory-map-en**：补 SAFE 停点矩阵表。
3. **dhf-shipq-development-history-en**：至少补 RECOVER 的出现——EN 版演进史现在完全不提失败分支，六理念在 EN 侧断了一环。
4. **所有 EN 证据子页**：统一补"related reading"互链条（与 CN 对等的站内网络）。
5. data-business-value-explainer-en、best-care-recover-en：视精力补深度；examples-three-lenses-en 按 Phase 0 的决策处理。

### Phase 5 · 让检测器看得见这一族（防止改完再烂回去）

1. 扩展 `dhf_content_drift.py` 的配对逻辑：`X.html ↔ X-en.html`（无后缀=中文）也纳入 `check_bilingual`。
2. 新增一个轻量检查：证据族页面的 memory cue 必须包含全部六词条且词条可点击（数 `<a data-dhf-memory-term>` 即可，与 class 命名无关，符合现有检测哲学）。
3. 跑出来的存量发现逐条 fix 或写 accept（例如 three-lenses-en 若定为轻量索引）。
   ⚠️ 注意：`dhf-public-site-sync` skill 明确禁止在 docs 同步流程里改 `scripts/`。所以这一步**不走夜间任务，作为独立的、经你批准的 harness 变更单独提交**，改完后夜间任务自动受益。

### Phase 6 · 状态合同与门禁（收尾，一次性）

- 本次是实质内容更新，符合 bump `data-dhf-status` 的条件：按 [[dhf-public-site-status-contract]]，**19 个公开页 + test_runner.py 期望值一次性同改**；不动 "Local runtime parity: verified" 日期。
- 三道门禁全过再推：`dhf_content_drift.py` exit 0 → `check_surfaces.py --check-public-nav` ok → `test_runner.py` 无新增失败（对基线比）。
- 浏览器实测：概念地图三档宽度截图、cue 链接抽点、EN 新表格渲染。
- push 走 skill 既定流程：fast-forward only、仅 docs 白名单 + 单独批准的 scripts 变更。

---

## 四、工作量与顺序建议

| Phase | 涉及文件数 | 预估强度 | 依赖 |
|---|---|---|---|
| 0 决策 | 0 | 低（需要你拍板 2 个问题） | — |
| 1 cue 导航化 | CSS ×1 + HTML ×22 | 中（机械但量大） | P0 |
| 2 概念地图 | HTML ×2 + CSS | 中（需浏览器实测） | P0 |
| 3 protect 织网 | HTML ×8 | 低 | P1 |
| 4 EN 补全 | HTML ×6–10 | **高**（真正写内容） | P0（决策 three-lenses） |
| 5 检测器 | scripts ×1 + accept.json | 中（需单独批准） | P4 后跑存量 |
| 6 状态合同+发布 | HTML ×19 + test_runner | 低（机械） | 全部 |

建议节奏：P0+P1+P3 一批（一次提交就能让"网络感"质变）；P2 一批（有视觉验证环节）；P4 按优先级拆 2–3 批；P5、P6 收尾。

## 五、两个待你拍板的问题

1. examples-three-lenses-en（8.5KB vs CN 53KB）：补全成十案例全文，还是定性为"轻量索引"写 accept？我倾向后者——EN 侧已有 three-lenses-safe-en 承担控制视角，全文翻译十个案例性价比低。
2. Phase 5 改 `scripts/dhf_content_drift.py` 超出 docs 同步的授权边界，需要你明确批准后单独做。
