# P1-2 计划：一条命令刷新 managed-source 身份 v9（完成标准 3 允许清单补时间戳）

日期：2026-08-23 · 状态：计划，未改仓库
`verification_receipt: verification_not_applicable`（仓库事实见附录 A，只读核对）

## 1. 要解决的事

P0-2、P0-3 每次改 `codex/` 下的 skill 或 hook 源，都要手工过三层冻结哈希，每层单独撞一次、单独一轮往返：

| 层 | 文件 | 现在怎么刷 |
|---|---|---|
| A | `runtime-approvals/approved-source-digests.txt` | 手算 `codex/` 整目录 digest，手工追加一行带备注 |
| B | `tests/fixtures/dhf_simplification_transition_identity.json`（488 B） | 没有正规命令；要先调内部函数 `identity_bundle()` + `_canonical_sha256()` 重算，否则 `capture` 被旧 identity 循环阻断 |
| C | `tests/fixtures/dhf_simplification_observations.json`（666 KB） | `run_dhf_simplification_pair.py capture`，但只有 B 刷完才跑得通 |
| D | 同文件内 AC-16 live runtime evidence | AC-16 要求 `changed_paths==[]` 且 `promotion_difference_paths` 非空，即 `source_stage_unsynced` 状态——首次提升后永远不可达，所以它是 2026-07-14 的一次性历史快照，**不可重新捕获**。validator 却把 `captured_at` 绑到文件最近 commit 的 author date，`25490b8` 重新 commit 后 main 永久红灯。止血 = validator 改绑不可变出处 `captured_in_commit` |

目标：一条命令把 A、B、C、D 按正确顺序刷完，并有一条只读命令先告诉你哪层过期。

## 2. 不做的事

- 不动 `dhf_simplification_evidence.py` 的 `BASE_COMMIT`（那是 P1-5）。
- 不改三层的判定规则、不放宽任何测试，只改「怎么生成」。
- 不改 `sync_codex_home.sh` 的 guard 逻辑；只在它的 preflight 失败信息里加一句提示。

## 3. 交付物

一个脚本 `scripts/harness_refresh_identity.py`，两个子命令：

`status`（只读）：对 A、B、C 各输出 `current` / `expected` / `fresh|stale`，退出码：全 fresh 为 0，任一 stale 为 1。expected 的算法直接 import 现有函数：A 用 `sync_codex_home.sh` 第 199 行同款 digest（抽成可 import 的函数，测试断言两者相等）；B 用 `run_dhf_simplification_pair.identity_bundle()` 重算并与 transition_identity.json 逐字段比；C 读 observations.json 里存的 `promotion_skill_sha256` 与各 manifest 哈希，与 `identity_bundle()` 重算值比，不跑 `capture`；D 读 AC-16 的 `captured_in_commit`：字段存在、哈希在 git 历史中、`captured_at` 与该 commit 的 author date（`%aI`）≤15 分钟为 fresh。

`refresh --message "<备注>" [--approve]`（写）：按 B → C → D → A 顺序执行。B 用 `identity_bundle()` 重写 transition identity；C 跑官方 `capture`；D **不写任何东西**：C 层 capture 时保留 AC-16 记录原样，stdout 打 `AC-16 preserved (historical, provenance <hash>)`；A 是 owner 审批记录，**默认只把要追加的那一行打印到 stdout，不写文件**；只有带 `--approve` 才追加。每层完成后立刻重跑该层的 `status`，不 fresh 就停、退出码非 0、前面已写的不回滚（都是幂等可重跑）。不 commit。

`sync_codex_home.sh` 的 `source_digest_unapproved` 报错信息末尾加一句：`run: python3 scripts/harness_refresh_identity.py status`。

## 4. 完成标准

1. 在当前 HEAD（全部 fresh）上 `status` 退出 0，三层均 `fresh`。
2. 在临时 `git worktree` 里给 `codex/skills/delivery-harness-framework/SKILL.md` 追加一行空注释：`status` 退出 1 且 A/B/C 均 `stale`（D 按时间独立判定）；`refresh --message test` 退出 0 且 A 未被写入、stdout 含待追加行；`refresh --message test --approve` 后 `status` 退出 0；该 worktree 内 `python3 test_runner.py` 全绿。worktree 用完删除，主工作树零改动。
3. `refresh` 产生的 A 行、B 文件、C 文件与 P0-3 手工流程（commit `25490b8`）的产物逐字段等价：C 的 diff 只含 digest、manifest path、assertion count、`verification_receipt.timestamp`（重新 capture 的固有产物）；`key_output` 中的运行派生值（时间、路径、耗时）经逐条核对后可放行。
4. `test_runner.py` 新增测试覆盖：`status` 四层各自的 fresh/stale、`refresh` 顺序 B→C→D→A、B 失败时 C 不执行、无 `--approve` 时 A 不写、D 的出处字段缺失/哈希不存在两种 stale。测试用 fixture 小样本，不在 test_runner 里跑完整 666 KB 的 capture。
5. `docs/harness/model-tiers.md#follow-ups` 里「skill 源改动需刷新 paired gate」那行改为指向本脚本。

## 5. 实施顺序

0. 止血（写集临时扩到 validator + 测试 + AC-16 记录）：用 `git log -S` 找到原始 `captured_at` 的引入 commit，AC-16 记录加 `captured_in_commit`；validator 有该字段时按它绑定，无则沿用旧逻辑；15 分钟窗口和两个状态条件不变。commit `P0-3: bind AC-16 to immutable capture provenance`，**commit 后再跑一次门禁**。
1. 先写 `status`（只读），在当前 HEAD 跑通，commit：`P1-2: identity status (read-only)`。
2. 抽 A 的 digest 函数，加「与 sync 脚本结果相等」的测试，commit：`P1-2: shared source digest`。
3. 写 `refresh`（含 `--approve` 门），用完成标准 2 的方法在临时 worktree 验证，commit：`P1-2: identity refresh`。
4. sync 报错提示 + 文档，commit：`P1-2: docs + sync hint`。
5. **config 键哈希**（原 P1-2b，独立 commit：`P1-2: config identity = cost-relevant keys`）。`harness_cost_report.py` 新增字段 `codex_config_keys_sha256`。算法写死：`tomllib` 解析 → 取 `model`、所有 `model_*`、`personality`、`[features]`、`[mcp_servers.*]` → `json.dumps(obj, sort_keys=True, separators=(",",":"))` → sha256。只排除 `notify`、`service_tier`（`personality` 会改系统提示文本，属成本相关，必须包含）。**旧字段 `codex_config_sha256` 保留照算**，既有基线 JSON 一个字节不改。drift 护栏改为：两份基线都有 `codex_config_keys_sha256` 时比新字段，否则回退比旧字段。测试：两份 config 样本作为字符串放进 `tests/fixtures/config-identity/`（一份为 after-p0-2 的内容，一份在其上只加 `service_tier = "default"`），不读活的 `~/.codex`；断言旧字段不等、新字段相等、护栏不报 drift；再加一份只改 `personality` 的样本，断言新字段不等。

写集：`scripts/harness_refresh_identity.py`（新）、`scripts/sync_codex_home.sh`（仅报错文案 + 可选抽函数）、`test_runner.py`、`docs/harness/model-tiers.md`、`scripts/harness_cost_report.py`（仅第 5 步）。不碰 `tests/fixtures/`（只由脚本生成，不手改），不碰 `docs/harness/cost-baseline/*.json`。

## 6. 停止条件

- `identity_bundle()` 或 `_canonical_sha256()` 不是稳定接口（签名依赖 CLI 内部状态）→ 停，报告，不复制逻辑。
- 完成标准 3 的等价性不成立 → 停，贴 diff。
- A 的 digest 抽函数后与 sync 脚本算出的值不等 → 停。
- 第 0 步：原始 `captured_at` 与其引入 commit 的 author date 差 >15 分钟 → 停。已核：`8cfb8cf` author date 差 5 分 27 秒，通过。
- 第 5 步：after-p0-2 的 config 与 **after-p0-3 基线记录的 config（哈希 `344f434a…`）** 在成本相关键上确有差异（不只是 `service_tier`）→ 停，贴 diff。活的 `~/.codex/config.toml` 与此无关，owner 基线后手改 reasoning 不触发本条。

## 附录 A：2026-08-23 只读核对

- `runtime-approvals/approved-source-digests.txt`：最近两行为 P0-2、P0-3 手工追加；`sync_codex_home.sh` 第 102、199、209 行读取并校验。
- `dhf_simplification_evidence.py` 第 16 行 `BASE_COMMIT = "00818ae…"`。
- `run_dhf_simplification_pair.py`：第 120 行 `_canonical_sha256`、第 179 行 `identity_bundle`、第 525 行「cannot finalize … failing comparison」、第 1482/1486 行 `compare` / `capture` 子命令。
- fixtures：transition_identity 488 B、observations 666 KB、scenarios 69 KB。
- `harness_cost_report.py` 第 169–186 行：按 `(baseline_dir, git_head, codex_config_sha256)` 做 drift 护栏。
