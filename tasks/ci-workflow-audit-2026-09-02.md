# MyCodexEnv CI 流程审计（2026-09-02）

状态：Owner 于 2026-09-02 确认并按第 3 节顺序落地，分四个 commit（分支 `ci-optimization-2026-09-02`）：
`6267ebc` cancel-in-progress 只对 PR + 锁 Python 3.12 + 廉价检查前置；`c2fbc6d` Pages 改为 CI 成功后 `workflow_run` 发布并 checkout 通过门禁的 head_sha；`5448b14` `test_runner.py --lane docs --changed PATH...`（ast 反向引用选测，含经 scripts/hooks 的二阶引用；eligible 路径 `docs/**`、`tasks/**`、顶层 README/AGENTS/CONTEXT）、ci.yml lane 判定与每日定时全量、README/README.zh-CN/verification guide 说明、README 作为 normative mirror 触发的 `harness_refresh_identity.py refresh`；`d4e4d11` corpus 验证器 `ast.parse` 按内容摘要缓存（golden corpus 39s→12s、paired gate 120s→67s）、hook 性能预算改绑 p99。最终全量 152 tests 148 pass / 4 skip，容器实测 4 分 0 秒（原 5 分 32 秒）。同一方法已在 ShipQ 落地（`docs/plans/2026-09-02-ci-workflow-optimization-proposal.md` @ ShipQ），本文只记录 MyCodexEnv 的差异与结论。

未做（有意保留）：sync 类测试仍每次 rsync 57 MB vendored gstack（runtime 行为变更，需单独评审）；paired gate 剩余 67s 来自每个 unittest 各跑一次 `run_comparison` 的子进程部分，可再缓存 base 侧测量但收益已不大。

## 1. 现状

`ci.yml`：push main / PR / 手动触发；`concurrency` 按 ref 分组且 **cancel-in-progress 对 main 也生效**；`fetch-depth: 0`；`python-version: "3.x"`（不锁小版本）；把 `codex/hooks/dhf_preprompt.py` 与 DHF skill 种进 `/tmp/ci-dhf-home`，`HOME` 指过去，`CI_DHF_RUNTIME_RESET=1` 跑 `python3 test_runner.py`；最后才跑 `git diff --check` 与 `scripts/check_surfaces.py --check-public-nav`。没有 pip 安装（纯标准库），没有缓存需求。

`pages.yml`：`docs/**` 变化即发布 GitHub Pages，**与 CI 是否通过无关**。

`test_runner.py`：单文件 12,789 行、150 个测试函数、串行进程内执行、注册表制（`TESTS` 列表 + `test_runner_registry_complete` 强制登记）。唯一的子集选择是 `--host-only`（两个宿主集成门）。另有 `tests/test_dhf_simplification*.py`（54 + 32 个 unittest）由 runner 以子进程整文件调用。

本地策略 `docs/agents/verification-and-change-safety.md` 已经是分层的：docs/visuals 变更只做定向内容/链接检查，"the existing CI owns the full gate"；源码/测试/契约变更才在最后跑一次全量。**也就是说本地已经不跑全量，CI 是唯一每次都跑全量的地方。**

### 1.1 实测（2026-09-02，main e76b08c，py3.12.3，2 vCPU 容器，按 CI 步骤种子 DHF home，`CI=true`）

| 项目 | 数值 |
|---|---|
| 测试数 | 150（146 pass，4 skip：codex CLI 相关） |
| 全量耗时 | 332 s（5.5 分钟），串行 |
| 前 5 个测试 | 242 s（73%） |
| 前 13 个测试 | 90% |
| 131 个 <1 s 的测试合计 | 20 s |
| 仓库 | 2930 个跟踪文件，pack 29 MB，530 commits |

注意环境依赖：容器初次运行 12 个失败，全部因缺 `rsync`（sync 脚本第 1306 行）和未设 `CI=true`（`_reset_ci_dhf_runtime_promotion` 的隔离检查）。ubuntu-latest 自带 rsync 且 Actions 自动设 `CI=true`，所以 GitHub 上是绿的；但这说明"可复现绿"对本地/其他 runner 有两个隐含前提，值得写进 README 的 CI 说明。

### 1.2 时间花在哪

| 测试 | 耗时 | 原因 |
|---|---|---|
| `test_dhf_simplification_paired_gate` | 120 s | 子进程跑 `tests/test_dhf_simplification_pair.py` 32 个 unittest，**每个**都调一次 `run_comparison`；单次 2.3 s 里 1.6 s 是 `validate_dhf_simplification_corpus.validate_corpus` 用 `ast.parse` 反复解析同一批 Python 文件（55 次 parse / 70 次 compile，主要是 12.8k 行的 `test_runner.py`） |
| `test_dhf_simplification_golden_corpus` | 39 s | 同上，54 个 unittest |
| `test_canonical_harness_hook_performance_budgets` | 38 s | 3 种 payload × 1000 次进程内采样 + 交错子进程采样，断言绝对时长（median ≤10 ms、p95 ≤20 ms、进程内 p95 ≤1 ms） |
| `test_harness_seven_target_promotion_wal_and_deployed_manifest` | 28 s | 完整 promotion/WAL 链路，多次 rsync 整个 `codex/`（含 57 MB 的 vendored gstack） |
| `test_verify_requires_superpowers_plugin_install…` / `…missing_codex…` / `test_sync_renders_template_and_copies_skills` | 17 / 14 / 13 s | 每个都先做一次完整 sync（rsync `codex/` 到临时 HOME） |

### 1.3 变更类型（最近 60 天，299 个非 merge 提交）

| 类型 | 数量 | 占比 |
|---|---|---|
| 只改 `docs/**` 或顶层 `*.md` | 75 | 25% |
| 只改 docs / 顶层 md / `tasks/**` | 130 | 43% |
| 触及 `test_runner.py` 或 `tests/` | 131 | 44% |
| 触及 `codex/`、`claude/`、`scripts/` | 102 | 34% |

main 上 282 个 first-parent 提交对 26 个 merge：直推为主。按每次 ≈6 分钟估算，两个月 ≈28 小时 runner 时间。仓库是公开的（`github.com/bryanzk/MyCodexEnv`），Actions 分钟不计费，所以成本主要是等待时间和 `cancel-in-progress` 造成的记录缺口，不是额度。

## 2. 全量是否必要

代码/runtime/测试变更：是。理由和 ShipQ 相同——契约测试遍布，runner 又是单文件注册表制，没有可靠的模块级映射。

文档变更：否。这里的 `docs/` 是公开 Pages 站点 + harness 状态文件，被 41 个测试函数读取（信息架构、双语 parity、surfaces manifest、harness-state 格式等），但这 41 个合计只要 **7.8 s**；剩下 109 个测试（324 s）全是 sync/verify/hook/WAL/simplification，与 docs 无关。25%–43% 的提交属于这一类，每次却在等 5.5 分钟的 runtime 测试。

## 3. 建议（按收益/风险排序）

1. **`cancel-in-progress` 只对 PR 生效。** 现在 main 上连续 push 会取消前一次运行，中间提交没有 CI 记录；直推为主的仓库尤其明显。改为 `cancel-in-progress: ${{ github.event_name == 'pull_request' }}`。零风险。
2. **廉价检查前置。** `git diff --check` 与 `check_surfaces.py` 各 <1 s，放到 test_runner 之前，格式/导航错误 20 秒内可见，而不是 6 分钟后。零风险。
3. **Pages 发布挂在 CI 之后。** 目前 docs 一推就发布，即使同一提交的 `check_surfaces --check-public-nav` 或 IA 契约红了也照发。改 `pages.yml` 为 `on: workflow_run: workflows: [CI], types: [completed], branches: [main]` + `if: conclusion == 'success'`（代价是每次绿的 main push 都会重发一次，幂等，约 30 s），或者把 deploy 并入 `ci.yml` 作 `needs: gate` 的 job。中收益、低风险。
4. **docs lane。** 在 `test_runner.py` 增加 `--lane docs`：用 `ast` 扫自身源码，选出（含经模块级常量与辅助函数传递引用）引用了 `docs`、`tasks`、顶层 md 的测试函数，加 `test_runner_registry_complete`。CI 里用与 ShipQ 相同的 `git diff --name-only base...HEAD` 判定：变更集 ⊆ `docs/**` ∪ 顶层 `*.md` ∪ `tasks/**` → `--lane docs`（约 8 s）+ `check_surfaces` + `git diff --check`；否则全量。配一个每日 schedule 串行全量做安全网。预计 25%–43% 的运行从 ≈6 分钟降到 ≈40 秒。需要改 runner 与 workflow，中等工作量；选测逻辑已在容器里用同样的 ast 方法验证（`docs/harness-state.md` → 6 个测试，`docs/index.html` → 6 个，`docs/repo-index.md`+`surfaces.json` → 10 个，全部 docs 引用集 41 个 / 7.8 s）。
5. **锁定 Python 小版本。** `"3.x"` 会随 runner 镜像升级悄悄换解释器（现在会拿到 3.13/3.14），与"红=真回归"的设计目标矛盾；建议锁到本机 bootstrap 使用的版本并显式升级。
6. **测试工程（独立于 CI，收益最大但要改测试）：**
   - `validate_dhf_simplification_corpus._callable_exists/_test_callable_exists`：按文件路径+内容摘要缓存 `ast.parse` 结果。单次 `run_comparison` 2.3 s → ≈0.7 s，两个 simplification 门合计 159 s → 估计 40–50 s。
   - `test_dhf_simplification_pair.py` 的 `compare()` 默认已复用 class 级 candidate 测量，但 base 侧每次重算；同样缓存到 `setUpClass`。
   - `test_canonical_harness_hook_performance_budgets`：1000 次进程内迭代可降到 300 且统计意义不变；绝对阈值在共享 runner 上有 flaky 风险，已通过"与 empty guard 的相对 overhead"部分缓解，建议再把绝对断言改成相对。
   - sync 类测试每次 rsync 57 MB 的 vendored gstack；若 sync 排除 `codex/skills/gstack/browse/test/fixtures/`（28 MB 的 haiku 响应 fixture）或在测试里用精简 fixture 仓，5 个 sync/verify 测试合计 ≈75 s 可减半。这是 runtime 行为变更，需单独评审。

不建议：pytest-xdist 式并行——runner 是进程内串行、共享 `HOME`/临时 runtime，并行需要先做隔离改造，收益不如第 6 条。

## 4. 与 ShipQ 的差异

| | ShipQ | MyCodexEnv |
|---|---|---|
| 测试框架 | pytest，141 文件 | 自研 runner，单文件 150 函数 + 2 个 unittest 文件 |
| 全量耗时 | 3 min 串行 / 87 s xdist | 5.5 min 串行，不可并行 |
| 热点 | 分散（前 30 文件 94%） | 极集中（前 5 个 73%），可单点修 |
| docs 性质 | 计划/设计笔记 + 策略 JSON | 公开 Pages 站点 + harness 状态 |
| 本地门禁 | 原为全量，已改 lane | 本地早已分层，CI 是唯一全量 |
| docs lane 可省 | 3 min → 12 s | 5.5 min → 8 s |
| 主要风险 | 无 | main 上 cancel-in-progress；Pages 发布不等 CI |

## 5. 方法与证据等级

- 耗时来自把 `git bundle --all` 克隆到 Python 3.12 容器、按 `ci.yml` 步骤种子 DHF home 后对 `TESTS` 逐函数计时（不是 GitHub runner 的真实数据，runner 4 vCPU 但这些测试多为子进程/IO 绑定，差异有限）。
- 变更分布来自 `git log --since="60 days ago" --name-only`。
- docs lane 的选测结果来自对 `test_runner.py` 的 `ast` 静态分析原型，未落入 runner。
