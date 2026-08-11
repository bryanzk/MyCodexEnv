# Canonical Harness Forward-Fix 计划 v2

计划编号：MCE-20260810-canonical-harness-forward-fix-v2（取代 v1）
目标分支：codex/mce-20260810-canonical-harness-forward-fix
日期：2026-08-10
状态：draft — 待 Codex 侧独立盲审；外部评审（Claude 委员会循环）结论附于文末

v2 相对 v1 的改动，对应外部评审的四个 findings：

- RV-01（major）：v1 把 out-of-scope 豁免收窄到"结构化 target 的文件操作"，exec shell 一律不豁免——这会让最初的动机场景（非 Git 文档目录里 mkdir、heredoc、脚本生成 PDF）重新被拦，且 apply_patch 的归类未定义。v2 用"威胁模型一致性原则 + 完整性监视"替代"从 shell 文本证明目标安全"，恢复零摩擦。
- RV-02（minor）：WAL 补 journal 记录文件的父目录 fsync 与 pre-PREPARED 清理规则。
- RV-03（minor）：CODEX_HARNESS_PHASE 环境门收窄到 governed roots 内，并列入 residual risks。
- RV-04（minor）：明确所有新旋钮只进 harness-scope.json 与 targets manifest，tool-policy.json 本周期零改动并以测试强制。

一至三节（背景、canonical/runtime 冲突、混合 runtime 事故）与 v1 相同，不重复。核心决策不变：不改写已发布历史、不拆 71af4a4、单一 deployment-closed forward commit、runtime promotion 单独授权、七目标整体 promotion。

---

## 四、威胁模型一致性原则（v2 新增，替代 v1 §4 的收窄结论）

v1 的推理链是：shell 文本无法可靠解析出目标路径（env 变量、相对路径、变量拼接均可绕过文本检查）→ 因此凡不能证明目标安全的写入一律不豁免。前半句成立（probe 已实证 `tee "$CODEX_HOME/hooks.json"` 与 `tee ../kezheng/.codex/hooks.json` 可穿过文本筛），后半句是过度推论：

**本系统接受的威胁模型是同 UID 协作环境。** journal 不做密码学认证（same-UID tampering 是 v1 自己声明的 residual risk），self-declare 可被 prompt-injected agent 执行（v1 的 ACCEPTED_RISK）。在这个模型下，要求"数学上证明一条 shell 命令不会碰 protected roots"是对单一通道施加了高于整体模型的标准——攻击者若已能构造恶意 shell，同样能走其他已被接受为 residual 的通道。

因此 v2 的原则是：**enforcement 的强度与威胁模型对齐——防不住的不假装防，改为可靠检测 + 可靠恢复。**

1. **文本筛降级为 screening，不再是 guarantee。** 保留（便宜、拦截朴素形态），文档与测试中明确它可被绕过。v1 发现的空断言（`assert blocked(result) or result == {}`）在 canonical 测试中替换为显式预期 verdict。
2. **protected roots 的真实防线改为完整性监视（integrity watch）。** sync_codex_home.sh 在每次同步（无论是否 promotion 事务；非事务路径用 temp + os.replace + fsync 原子写）生成 `~/.codex/harness/deployed-manifest.json`：覆盖它部署的全部文件（七目标 + 其余 canonical hooks，含 dhf_preprompt.py）的 SHA256/type/mode。guard 在每次 PreToolUse 决策前校验 manifest 内所有文件的当前 digest：
   - 全部一致 → 正常决策；
   - 任何不一致 → fail-closed 拒绝一切非 read 调用，block 消息内嵌恢复命令原文（在终端运行 `scripts/verify_codex_env.sh` 核对差异、`scripts/sync_codex_home.sh` 恢复；人工终端不经过 guard，无锁死风险）；
   - manifest 不存在（首次 promotion 前，或 operator 在终端删除它以停用 watch——这是文档化的终端逃生门）→ watch 未激活，行为等同现状，bearing 注入一行提示。

   **watch 的诚实属性：tamper-evidence，不是 tamper-proof。** manifest 无法包含自身的 digest（自指哈希不存在）；能绕过文本筛写 protected root 的攻击者原则上也能重写 manifest 使 watch 致盲。watch 的价值边界：单步篡改、无意覆盖（如今天的混合 runtime 事故）、以及未同时修复 manifest 的注入攻击，会在下一个工具调用被冻结；"篡改 + 同步伪造 manifest"的两步攻击属于同 UID residual（§十二-7）。
   成本模型：manifest 文件数 ≤ 32、单文件 ≤ 1 MiB、**总量 ≤ 4 MiB**，超限 fail-closed；guard 维护 digest 缓存（键：path + size + mtime_ns + inode），仅对元数据变化的文件重新哈希——mtime 可被同 UID 伪造，并入 §十二-7 的同一 residual。实测预算并入 §十 的性能门。

## 五、Scope 与豁免模型（v2 改写）

Policy truth：

- **governed Git repo**：完整 policy，与现行为一致。
- **out-of-scope（governed_roots 之外，含非 Git 文档目录）**：low/medium 类别（repo_write、network）**直接豁免，包括 exec shell，不要求结构化 target**——这是原始目标"文档工作零摩擦"的实现，v1 曾错误收回。secret/destructive/dynamic_exec/remote/agent_dispatch 照旧不豁免。protected roots 由 §四 的 screening + integrity watch 防护。
- **out-of-scope 新增 persistence screening**：对 shell 文本与结构化 target 做第二组 best-effort 筛，命中 `~/Library/LaunchAgents`、`~/.zshrc`、`~/.zshenv`、`~/.zprofile`、`~/.bashrc`、`~/.profile`、crontab 写入形态 → 拒绝。清单为默认值，可在 harness-scope.json 的 `persistence_path_patterns` 扩展；同为 screening 定位。governed repo 内不启用此筛，dotfiles 类仓库按正常 phase 规则走。
- **governed 非 Git 同 canonical cwd**：可解析 task-mode marker（S1 语义）；unknown phase 下 low/medium 被拒时给 self-declare 指引。
- **不同非 Git cwd** → ROOT_WORKSPACE_MISMATCH；**Git/非 Git 或不同 Git roots** → ROOT_REPO_MISMATCH。均 fail-closed，与已实现语义一致。

Per-tool target 表（RV-01 闭合条件，测试逐条覆盖）：

| 工具 | 结构化 target | 归类依据 |
|---|---|---|
| write / edit / multi_edit | `file_path` 等顶层字段 | 字段即 host 将写入的路径 |
| apply_patch | 从 patch 头（`*** Add/Update/Delete File:` 行）解析全部目标路径 | host 执行的就是这份 patch，头部路径即真实目标；解析失败 → 视为无结构化 target。**混合规则：任一解析出的 target 命中 protected/persistence → 整个调用按命中处理**，不做部分放行 |
| exec shell | 无 | 按 cwd 的 scope 规则走（out-of-scope 即豁免 low/medium） |

原始场景预期 verdict（作为验收测试固化）：Downloads 非 Git 目录内 `mkdir`、heredoc 写 md、`pandoc`/python 生成 PDF、apply_patch 建文件 → 全部 allow；同目录 `rm -rf`、`curl|sh`、写 LaunchAgents、`tee ~/.codex/hooks.json`（文本筛命中）→ 拒。**如实标注**：`tee "$CODEX_HOME/hooks.json"` 这类绕过文本筛的形态，该次调用会**放行**，冻结发生在下一个工具调用（integrity watch），恢复靠 operator 终端 re-sync——验收测试按此真实语义断言，不粉饰为"拒"。

## 六、环境门收窄（RV-03）

`CODEX_HARNESS_PHASE` / payload phase 注入仅在 cwd 位于 governed_roots 内时被采纳；out-of-scope 与 governed 非 Git cwd 一律忽略，走后续解析链。gate trace 恒记录 env 存在性与是否被采纳。residual risks 明确列入：governed repo 内的 env 注入仍是最宽通道，接受理由是上游 harness 的合法用途，收窄到 governed 内已把暴露面对齐到"本就允许写入的区域"。

## 七、self-declare 合同（v2 修订）

定义不变：agent-operable、TTL-bound、workspace-bound、audited phase override；不是 human approval / authentication / prompt-injection resistance。

verdict delta（v2）：同一 workspace、原本仅因 unknown phase 被拒、low/medium 类别——**含 exec shell 与结构化文件操作**（v1 仅限结构化 target 的限制随 §四 原则移除；protected roots 由 integrity watch 兜底，high 类别不可降级）。

CLI 语法（严格，双子命令均入 task_admin 白名单，shlex 全解析 + 元字符黑名单）：

```
<resolved CODEX_HOME>/bin/codex-task declare <phase> --reason <reason-code> [--ttl <duration>] [--session-id <uuid>]
<resolved CODEX_HOME>/bin/codex-task revoke --reason <reason-code>
```

reason-code：`[A-Za-z0-9._:-]{1,64}`；默认 TTL 8h，上限 24h；precedence：env(governed 内) > transcript > self-declared > snapshot。bare 名或 resolved 绝对路径之外的调用形态（PATH 花样、`./`、变量路径、多余 argv、重复 flag、redirect、pipe、newline、backtick、`$()`）不得入白名单，落回正常分类。prompt-injected declare 仍为 ACCEPTED_RISK（owner：本机 operator；窗口：TTL；audit + revoke 提供可见性与撤销）。

## 八、七个 runtime targets 与 manifest（v1 §八 保留，两处补充）

七目标清单、整体 promotion、`harness-guard-targets.json` 为 source-side manifest、sync/verify 读同一 committed manifest——均不变。补充：

1. **tool-policy.json 零改动为硬约束（RV-04）**：本周期所有新旋钮（scope、watch 上限、persistence 模式、env 门开关）只进 harness-scope.json 与 targets manifest。测试断言 promotion 前后 tool-policy 的 SHA 逐字不变；实现中若发现必须改它 → 停止，回到 operator 重新授权，不得静默扩围。
2. **deployed-manifest.json**（§四）由 sync 生成（promotion 走事务、日常 sync 走原子写），是 integrity watch 的唯一基线。它无法覆盖自身（自指哈希不存在）：单独篡改它 → 与真实文件 digest 不符 → 冻结；连同目标文件一起伪造 → watch 致盲，即 §十二-7 的 residual。

## 九、journal/WAL（v1 §九 保留，两处补充，RV-02）

v1 的 journal trust、binding（schema/txn-id/repo/source-SHA/manifest-digest/target-set）、durable order、digest 三态恢复、并发 flock 全部保留。补充：

1. **每个 journal 记录文件（PREPARED / TARGET_INTENT / TARGET_APPLIED / COMMITTED）创建后，fsync 其父目录**——否则 crash 可丢 dirent，形成"target 已改而 journal 看似缺失"的假象。backup 与 target parent 的 fsync v1 已有。
2. **pre-PREPARED 清理规则**：持锁发现存在 backup/manifest 而无 PREPARED → 该事务从未修改任何 target（PREPARED fsync 是修改的先决），直接清理残留并允许新事务；此规则写入测试。

crash 矩阵不变；失败注入测试从 N=1..7 全矩阵缩减为 N∈{1,4,7} 加全部边界态——七文件复制的恢复逻辑对 N 无分支，全矩阵只增加运行时间不增加覆盖（如实现出现按 N 分支的代码，恢复全矩阵）。

## 十、测试与门禁（v1 §十 保留，增补）

新增/修订的关键测试：

- 原始场景验收组（§五的 verdict 表逐条）；
- per-tool target 表逐条（含 apply_patch 头解析成功/失败两态）；
- integrity watch：篡改七目标之一 → 下一调用冻结；篡改非七目标的 deployed hook（dhf_preprompt.py）→ 同样冻结；manifest 缺失 → 现状行为 + bearing 提示；文件数/单文件/总量三上限分别超限 → fail-closed；digest 缓存命中时不重哈希、元数据变化时重哈希；冻结消息含恢复命令原文；非 promotion 的日常 sync 后 manifest 更新且不误冻结；
- apply_patch 混合 target（良性 + protected 同 patch）→ 整体按 protected 处理；
- persistence screening 命中/漏过（漏过用例明确标注 screening 定位，不做 guarantee 断言）；
- env 门：governed 内采纳、out-of-scope 忽略、trace 记录两态；
- revoke 语法、revoke 后 verdict 回退；
- 替换 v1 发现的空断言为显式 verdict 断言；
- 性能：SessionStart fixture 10 次 worst ≤ 0.18s，PreToolUse（含 watch）10 次 worst ≤ 0.10s；允许单次重跑一次并记录环境负载，防 CI 抖动误报；
- 其余 v1 清单（roots 矩阵、wrapper、TTL、workspace 隔离、precedence、old-guard 兼容、WAL 边界、并发、collection 证明、fresh receipts）全部保留。

## 十一、commit 策略（不变）

内部 RED/GREEN 顺序：task_state → scope/watch → declare/revoke → bearing/trace → manifest/sync/verify/docs；最终单一 deployment-closed commit：`feat(codex-hooks): canonicalize scoped harness governance`。真实 ~/.codex promotion 单独授权，七目标整体执行。

## 十二、residual risks（v2 汇总）

1. 同 UID tampering（journal 与 runtime 均不做密码学认证）；
2. guard verdict 后的 TOCTOU（单次调用窗口内）；
3. prompt-injected 合法 declare（ACCEPTED_RISK，TTL + audit + revoke 兜底）；
4. governed roots 内的 env phase 注入（§六收窄后余量）；
5. 文本 screening（protected + persistence）可被构造绕过——由 integrity watch 检测兜底，watch 自身有单调用 TOCTOU 窗口；
6. out-of-scope 区域对 governed/protected/persistence 之外任意路径的写入不受限（与"零摩擦"目标同源，接受）;
7. integrity watch 是 tamper-evidence 而非 tamper-proof："篡改目标文件 + 同步伪造 deployed-manifest"的两步同 UID 攻击可使 watch 致盲；digest 缓存的 mtime/inode 键同样可被同 UID 伪造。与 residual-1 同源，接受理由相同。

operator 不接受 1-7 中任何一条时，promotion 停止。

## 十三、评审状态

- v1 未闭合 findings：BF-01/BF-02 由 §九补充闭合（待盲审确认）；BF-03 由 §十性能与兼容条款闭合。
- 外部评审 RV-01..RV-04：本 v2 逐条闭合（§四/五、§九、§六、§八）。
- calibrated status：incomplete，直至 Codex 侧独立盲审通过。本文件不宣称 10/10 终态。
