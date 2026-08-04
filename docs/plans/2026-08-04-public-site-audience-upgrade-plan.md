# 公开站受众升级计划(evaluation → 修改)

日期:2026-08-04 · 状态:executable plan · 来源:2026-08-04 全站评审(三受众:AI 提效产品人 / FDE / Agentic Engineering 爱好者)

## 原则(全程适用)

- 对外语言规则:公开页零内部代号(不出现 W6a、commit 号、内部脚本命令清单、receipt 字段名);事故叙事用脱敏复盘口径。
- 内容一致性:所有被 test_runner 契约锁定的字面(必需词条、`data-dhf-status="2026-08-03"`、状态页标题)在 B7 之前一律原样保留。
- 每个新 HTML 页:复用 index-en 的 CSS 体系与状态横幅;登记 `docs/surfaces.json`(含 public_nav)与 `docs/repo-index.md` 三处清单;`check_surfaces.py --check-public-nav` 必须过。
- **B7 前置门**:任何触碰 `test_runner.py` 的工作项被冻结,直到操作员处理完其中 78 行未提交的用户改动;到达 B7 时停下来问操作员。

## 批次(每项一个 commit,顺序固定)

### B1 中文侧补齐(🔴,受众 A 主入口)
- B1a 新建 `docs/dhf-for-product-and-field-cn.html`:翻译 EN 版全部内容含 5 张 SVG(图内文字一并中文化);互链:EN/CN 页脚互指。
- B1b `docs/index.html`:新增 governance 区块(对齐 index-en 的三卡结构,中文文案);导航条加"产品与交付团队"tag;Start Here 区加对应卡片。

### B2 Agentic Engineering 深度页(🔴,受众 C 招牌)
- B2a 新建 `docs/dhf-engineering-notes-en.html`"Engineering Notes: Governing Compaction & Deployment"。内容源(全部现成,只做脱敏转写):
  - 压缩治理的第一性推导(四公理→强制切换的条件性→五前提),源:2026-08-02 gate plan 与本站会话结论;
  - transition matrix 图解(可复用 PM/FDE 页 Guarantee 5 风格,展开六种裁定);
  - 脱敏事故复盘:"一个过时的定时任务如何覆盖了新运行时,以及 24 小时内的根治"——时间线、根因(未推送 + 无条件同步)、三层修复(守卫/备份/report-only),源:v0 plan 与 harness-state 相关条目,不出现内部代号与 commit 号;
  - "政策文本用契约测试锁字面"一节(文档即代码实践)。
- B2b `docs/dhf-engineering-notes-cn.html` 中文版。
- B2c index-en 与 index.html:governance 三卡由 `<div>` 改为 `<a>`,落地到对应语言的 Engineering Notes 页。

### B3 Written Spec 出 HTML(🔴,修复路径断点)
- 新建 `docs/lifecycle-skill-routing-en.html`:静态渲染 `LIFECYCLE_SKILL_ROUTING.md` 全文(构建时一次性转换,站点样式包裹;表格保留)。页头注明"源文件:docs/LIFECYCLE_SKILL_ROUTING.md(维护者入口)"。
- 全站 8 处 `href="./LIFECYCLE_SKILL_ROUTING.md"` 改指 HTML 版;`HARNESS_RUNTIME.md` 的 1 处链接保留(维护者卡片,可接受裸 md)。
- 同步义务:在 `LIFECYCLE_SKILL_ROUTING.md` 头部加注释行"修改本文件后需重新生成 HTML 版";B7 时把"md 与 html 标题集合一致"加入契约测试。

### B4 首页受众分流条(🟡)
- index-en 与 index.html hero 之下加三入口分流条:产品视角→PM/FDE 页;FDE→PM/FDE 页 + status 页;工程深度→Engineering Notes。文案各一句,不新增页面。

### B5 FDE 证物(🟡)
- PM/FDE 页(EN+CN)Guarantee 2 之后加折叠/次级区块"看一份真的":一张脱敏 verification receipt 示例(概念字段名:what ran/how it exited/what it showed/when)与一段 report-only 刷新报告的输出形态示意。全部手工脱敏样例,不引用真实路径与命令。

### B6 降噪与核对(🟡)
- B6a 三个 archive 页(`project-lifecycle-harness-flow-skills-en.html`、`project-lifecycle-harness-flow-skills.html`、`project-lifecycle-harness-flow-skills-zh-status-style.html` 如属旧版)页顶加"Archived / 已归档"横幅,指回现行版。注意:仅加横幅,不动被契约测试引用的内容。
- B6b EN/CN beginner 内容差异审计:输出差异清单到 commit message 或 plan 附注;EN 缺实质内容才补写,否则记录"差异为合理精简"结论。
- B6c 孤儿页 `eigenphi-project-architecture.html`:**操作员决策项**——删除 / 移出 docs / 保留并加"项目案例"入口,三选一;到达时停下来问,默认不动。

### B7 契约测试协调批(🔴 前置门:test_runner.py 脏改动已由操作员处理)
- 状态页字面更新:EN/CN"已发现漂移"改为当前事实(恢复于 2026-08-04,持续按部署验证),同步改 alignment 测试词条与全站 `data-dhf-status` 日期。
- 新页面纳入 alignment 测试的 english_pages/chinese_pages 清单。
- B3 的 md↔html 一致性断言加入测试。

## 验证门(每 commit)

1. `python3 scripts/check_surfaces.py --check-public-nav`
2. `PYTHONDONTWRITEBYTECODE=1 python3 test_runner.py`(B7 前:对基线零新增失败;B7 后:全绿)
3. `git diff --check`
4. 新/改页面本地打开抽查:深色模式、移动端断点(860px)、SVG 文字不溢出。

## Residual

- B7 之前新页面暂不受 alignment 契约保护——窗口期短,可接受。
- Pages 发布延迟数分钟,push 后线上核验由操作员完成。
- 站点无构建管线,md→html 为一次性转换,长期同步依赖 B7 的一致性断言。
