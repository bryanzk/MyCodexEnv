> **状态注记（2026-08-03）：design-archive。** 本文已由 [`2026-08-03-runtime-rollback-prevention-v0-plan.md`](./2026-08-03-runtime-rollback-prevention-v0-plan.md) 取代执行地位；本文的密码学层仅保留为威胁模型升级时的预研档案，不是当前实施合同。

# Gstack & DHF Daily Refresh Runtime 回退彻底修复计划

- 日期：2026-08-03
- 状态：Draft，candidate for independent review
- 生命周期：plan
- 执行车道：governed runtime repair
- 目标：恢复 W6a runtime parity，并从 immutable source、唯一 shared engine、journaled transaction、外部 owner confinement 和确定性证据五层消灭旧源覆盖新 runtime 的路径。

## 1. 冻结范围与完成口径

### 支持场景

- canonical repo：`/Users/kezheng/Codes/CursorDeveloper/MyCodexEnv`
- managed live home：`/Users/kezheng/.codex`
- automation：`Gstack & DHF daily refresh`
- 已知事故：automation 使用落后本地 `main` 19 个提交的 standalone clone，以 `rsync -a --delete` 覆盖或删除 W6a 已部署文件。
- 恢复范围：第 3.4 节冻结的 15 个 runtime targets，不能临时增加第 16 项。

### 非目标

- 不重写 Thread Discipline 或其他无关政策，不清理、覆盖、暂存或吸收既有用户改动。
- 不把 daily refresh 继续作为 live promotion 工具，不以 broad sync、mirror 或 `--delete` 恢复。
- 本计划本身不实施 runtime、automation、Git history、push、plugin/MCP 或 live-home 写入。
- 不新增第二个 sync wrapper；外层 launcher 只提供身份与协调，文件语义全部委托 shared engine。

### Definition of Done

以下条件必须同时成立：

1. baseline 选择、每个 candidate commit 与 publish 前均通过 Publication Contract v1、isolated named-ref fetch、`ls-remote` 和 local/remote ancestry matrix gate；发布后再次冻结 immutable `SOURCE_SHA`。
2. canonical dirty `main` 全程只读；publish 前后 `HEAD`、index bytes、tracked dirty bytes、untracked path/bytes、local-only full inventory 与相关 object reachability 完全一致，且 post-publish ancestry 等于预先冻结的期望图。
3. strict 15-path recovery 与 schema-v2 manifest bootstrap 在同一 journaled transaction 完成；WAL/backup/staging/target/manifest/parent fsync 顺序与每个 crash verdict 确定，最终只能得到完整 before-state 或 committed after-state。
4. 旧 clone/agent/child 永久无 live/control-plane 写权限；只有 external-owner one-shot launcher 可打开最小、一次性 maintenance corridor。
5. backup、lock/replay、path-race、fault/crash/restart、normal/force/direct-write negatives 与 temp/report positives 全部通过。
6. scheduler Entry receipt 必须分别为 `definition_enabled=false`、`scheduler_suspended=false`并完成revocation+drain；Phase 0只读复核，C5仅 disposable实现，Phase 6再复核两个 false 后才首次 update-disabled CAS。任何 suspend终止本 rollout并回独立 normalization，旧危险 definition永不重新启用。
7. C1-C6 parent/tree/review/tests、所有 phase gates、repo verify、atomic evidence root、W3 和下一次真实 `09:00` observation 均有 fresh 四字段 receipt。

## 2. 根因时间线与事故锚点

时间线不以本文文字自证。实施前必须生成 immutable `incident-timeline-v1.jcs`；每项只能引用 `incident_artifact_id`、artifact SHA-256、原始时间戳与只读提取 receipt。以下是待锚定的输入假设，在 artifact ID/digest 存在且 independent verifier 通过前不得标为确认事实：

1. `[INPUT-ASSUMPTION]` `09:00:59` 自动刷新开始，`09:03:36` 旧 standalone clone 误判新 runtime 为 drift。
2. `[INPUT-ASSUMPTION]` `09:04:22–09:04:24` runtime 被批量覆盖或删除；`09:04:26` automation 记录执行 `./scripts/sync_codex_home.sh --repo-root "$(pwd)" --codex-home "$HOME/.codex"`。
3. `[INPUT-ASSUMPTION]` canonical repo 当时为 `010e894`；automation clone 为 `4def1ed`；本地 `main` 相对 tracking ref ahead 19。
4. `[INPUT-ASSUMPTION]` 15 个 W6a targets 中，11 个现存文件匹配旧 clone，四个新 hook 被 `--delete` 删除；并行只读巡检没有 runtime 写入。

## 3. v1 架构决策与不变量

### 3.1 唯一 shared engine 与唯一外层 owner

v1 只有两道防线：

1. **进程内：一个 shared sync guard/transaction engine。** `sync_codex_home.sh`、人工 promotion/recovery 与 temp-home reproduction 调用同一入口；调用方不得复制 lineage、approval、bootstrap 或 transaction 逻辑。
2. **进程外：一个旧 clone/agent 无法修改的 confinement 与 one-shot privileged launcher。** 它阻止 direct `cp`、`rsync`、`rm` 及任何绕过 engine 的 live write，并持有 trust、lock、replay、receipt 与 backup authority。

Prompt、普通文件、环境变量和 runner wrapper 都不是安全边界。`MCE_AUTOMATION_NO_LIVE_RUNTIME_WRITES=1` 必须被 guard 检查，但不能替代外层 owner。

### 3.2 发布前置 lineage gate 与 immutable source

#### Publication Contract v1（literal frozen values）

- normalized repo identity 唯一字面量为 `github.com/bryanzk/MyCodexEnv`；server=`github.com`、account/namespace=`bryanzk`、repository=`MyCodexEnv`、destination ref=`refs/heads/main`。解析规则是第 3.3 节 `repo_identity_v1`，比较对象是规范化后的 UTF-8 bytes，不是 display URL。本计划的只读冻结 receipt 为 `command=[git remote get-url --all origin; git remote get-url --push --all origin; git ls-remote --get-url origin]`、`exit_code=0`、`key_output=fetch_url==push_url==https://github.com/bryanzk/MyCodexEnv.git; normalized_identity=github.com/bryanzk/MyCodexEnv`、`timestamp=2026-08-03T21:46:31Z`。该 receipt 只冻结 identity/URL，不是 publish 授权。
- exact single fetch endpoint 与 exact single push/receive endpoint 都是 `https://github.com/bryanzk/MyCodexEnv.git`；source refspec=`+refs/heads/main:refs/mce-release/<transaction_id>/remote-main`（fetch 只允许该单一 refspec），destination refspec=`<candidate_sha>:refs/heads/main`（push 只允许该单一 refspec）。`<transaction_id>` 在首次 baseline fetch 前由 external release authority 生成为 canonical UUID，并以 no-replace `release-transaction-genesis-v1` read-only receipt 冻结；baseline 与 per-commit named refs 全部使用该 ID，reuse/mismatch 即 STOP。该 receipt 只是 lineage evidence，不授权 publish。`<candidate_sha>` 必须从 candidate-freeze receipt 的 40-char SHA 解析；命令展开后不得存在占位符。
- isolated release repo 必须以 `GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_SYSTEM=/dev/null GIT_CONFIG_GLOBAL=/dev/null GIT_TERMINAL_PROMPT=0` 与 explicit `-c core.hooksPath=/dev/null -c alias.*=`等冻结配置执行。fetch/readback 使用 `-c credential.helper=`；push 的唯一 credential ingress 是 `-c credential.helper=!'/Library/Application Support/MyCodexEnv/runtime-control/publication/credential-broker-v1' --credential-fd=9 --transaction-id=<signed_transaction_id>`，其 absolute helper path/type/owner/mode/digest 必须绑定 sealed TCB，fd `9` 必须是 launcher 为该 transaction 单次继承的 sealed read-only credential fd。禁止 `pushurl`、`url.*.insteadOf`、`url.*.pushInsteadOf`、redirect、proxy rewrite、其他 credential/helper/askpass/shell/config ingress、repo/global/system config 与第二 endpoint；HTTP 3xx、resolved host/TLS peer 与 pinned endpoint 不一致或 allowlist 外 helper/config inventory 非空都 STOP。
- publication principal 必须是独立 `mycodexenv-release-publisher-v1`，远端身份必须经 GitHub authenticated-principal readback 为 literal account `bryanzk`，且对 namespace `bryanzk/MyCodexEnv` 只有该 transaction 的 branch-update 权限。credential 只能是 external publication authority 直接签发、通过上述 fd broker 消费的 memory/fd-only short-lived credential；provenance receipt 必须冻结 issuer、subject=`bryanzk`、server、repository ID、scopes、issued/expiry、non-secret fingerprint 和 revocation handle，secret 不进 repo/home/env/argv/receipt。broker 不落盘、不 cache/转发，只服务 signed transaction+endpoint；所有终态 close fd、revoke credential 并输出 redacted readback receipt。未获得该 exact receipt 时没有 publish authority，不得用 user credential store、`osxkeychain` 或其他 fallback。
- branch protection readback 必须冻结 repository ID、branch ID/name、protection/ruleset IDs+digests、required checks/reviews、force-push/deletion deny，并证明 expected-old CAS 受 server 端保护。fetch、authenticated principal readback、pre-push `ls-remote`、push receive result、post-push fetch/`ls-remote`/branch-protection readback 都必须同时绑定 server repository ID 与 namespace=`bryanzk/MyCodexEnv`；任一 namespace/repository ID 不同即 STOP/incident。

#### Candidate freeze、publication approval 与非原子发布状态

- candidate 只能在最后一个 non-empty commit 后冻结一次：`candidate_sha`、commit/tree/parents、complete diff、candidate-built engine/TCB/report-definition digests、local-only exclusion receipt 与 `candidate_gate_root`。随后在 clean detached candidate checkout 与由 candidate 构建的 empty temp homes 运行 full repo tests、`verify_codex_env`、reproduction、15-path/provenance/local-only 全门禁。在同一 isolated host image/toolchain/env 中先对 `REMOTE_BASE_SHA` 运行同一 gate manifest；`REMOTE_BASE` 失败且 candidate 同样失败的项仅标为 `pre_existing_baseline_failure`，candidate-only 或 candidate 改变失败输出/范围的项为 `candidate_associated_failure`。任一 candidate-associated failure 禁止 approval/publish；baseline/live drift 必须单独记录，不得被 candidate green 覆盖。
- signed publication approval artifact 使用第 3.10 节 cryptographic profile，exact keys 逐字为 `schema_version,server,account,namespace,repository_id,fetch_endpoint,push_endpoint,source_refspec,destination_refspec,principal_fingerprint,credential_fingerprint,expected_old,candidate_sha,candidate_tree,candidate_gate_root,branch_policy_digest,authority_key_id,issued_at,expiry,nonce,transaction_id`，其值精确绑定本节 frozen contract 且 unknown/missing keys 拒绝；`transaction_id` 必须精确等于 `release-transaction-genesis-v1` 的 genesis ID，`candidate_gate_root` 必须绑定完整 lineage evidence root，任一 mismatch 即 STOP。验签、replay claim、fresh principal/credential/branch readback 必须在 push 立即之前同一 publication lock 内重做。
- 状态机唯一为 `APPROVED_NOT_PUBLISHED -> SOURCE_PUBLISHED_UNVERIFIED -> SOURCE_VERIFIED`。publication receipt exact keys 是前述 approval 全部字段加 `state,remote_tip,receive_result,previous_receipt_digest,fetch_readback_digest,ls_remote_readback_digest,branch_policy_readback_digest`，unknown/missing keys 拒绝。push receive 成功是第一个不可撤销的跨系统边界，必须立即以 `previous_receipt_digest=<publication approval artifact digest>`、三个尚未发生的 readback digest=canonical JSON `null` no-replace seal `SOURCE_PUBLISHED_UNVERIFIED`；readback 全通过后另建 immutable `SOURCE_VERIFIED` receipt，其 `previous_receipt_digest=<sealed unverified receipt digest>`、三个 digest 都是 `sha256:<64 lowercase hex>`，不得覆盖前者。push 后任一 readback/gate 失败都保留 unverified receipt、scheduler disabled+external runtime deny，只允许 sealed evidence 和 independent forward-repair scope；不 promotion、recovery、remote rollback/rewrite/retry。
- remote 发布与 local manifest commit 不可跨系统原子。安全谓词不是“远端可在所有窗口回滚”，而是“对象保持已发布、immutable，且当前 lineage policy 允许使用”。runtime transaction 在 manifest commit 前与后都要 fresh remote readback；`SOURCE_PUBLISHED_UNVERIFIED`、remote advance 或网络不确定进入 incident reconciliation，不执行 remote 逆操作。

- canonical `origin` 必须只有一个 fetch URL 且只有一个 push URL，两者都精确等于 Publication Contract v1 endpoint；`refs/heads/main` 在 `git ls-remote` 中必须恰好一项。remote missing、多义或 identity mismatch 全部 STOP。
- 所有 lineage fetch 只在全新、clean、只服务本 transaction 的 isolated release repo 中执行；以显式 refspec 把 remote main 写入 transaction-scoped named ref `refs/mce-release/<transaction_id>/remote-main`。启动前冻结该 repo 的 exact refs/object inventory，结束后冻结 named ref/object 与 cleanup 前后 inventory；禁止依赖 `FETCH_HEAD`、canonical remote-tracking cache，禁止修改 canonical dirty repo 的 refs、index、objects、config 或其他 Git metadata。
- isolated Git 调用使用 absolute executable、空白受控 `HOME`、`GIT_CONFIG_NOSYSTEM=1`、`GIT_CONFIG_GLOBAL=/dev/null`、`GIT_CONFIG_SYSTEM=/dev/null`、`GIT_TERMINAL_PROMPT=0`、禁用 hooks/aliases/pager 与 repo/local config 影响的 clean environment；exact argv、refspec、ref/object before/after 均进入 receipt。任一不可禁用或未枚举的 config/helper/filter/hook 即 STOP。
- 选择开发 baseline 前先证明 repo 非 shallow，在 isolated release repo fresh fetch named ref，再独立执行 `git ls-remote origin refs/heads/main`，冻结 `REMOTE_BASE_SHA`；canonical repo 只作 read-only object/dirty fingerprint，不接收 fetch。
- 记录 canonical local `HEAD`、isolated fetched named ref 与 remote tip 的 ancestry matrix：`equal`、`local_ancestor_of_remote`、`remote_ancestor_of_local`、`diverged` 或 `unknown`。`diverged`、`unknown`、rewrite suspicion、shallow、object missing 全部 STOP。canonical dirty history 只用于矩阵，不得成为 baseline。
- matrix 为 `remote_ancestor_of_local` 时，在创建 checkout 前冻结 `REMOTE_BASE_SHA..LOCAL_HEAD` 的 full commit inventory、每 commit parent/tree、全量 patch-id/raw patch、aggregate tree delta，以及所有 path create/delete/rename/copy、mode、symlink、submodule/gitlink 与 semantic dependency。逐项产生 `preserved` 或 `excluded-from-candidate` receipt；机械检查必须把 candidate delta 与上述 commit/tree/patch/path/mode/symlink/submodule/content 集合交叉验证，无法机械证明的 semantic dependency 只能由独立 reviewer receipt 关闭。任一 receipt 缺失、local-only delta 与 candidate scope/依赖冲突、rename/mode/submodule 语义不清或无法证明排除即 STOP。不得 cherry-pick、复制或隐式吸收这些 local-only bytes。
- clean development checkout 必须从 `REMOTE_BASE_SHA` 建立。依赖 DAG 固定为 `REMOTE_BASE_SHA -> C1 -> C2 -> C3 -> C4 -> C5 -> C6`，无 merge、无环；每个 commit 的 parent 精确等于前一节点。
- 每个 commit 创建前后冻结 tree SHA；tree 不变时禁止 commit，保存 `no_op=true` receipt。每个 commit 还需独立 review 与 targeted-test receipt；runtime-only 操作不创建 Git commit。
- 每个 commit 创建前及 publish 前都 fresh fetch/`ls-remote`；remote tip 必须仍等于 `REMOTE_BASE_SHA`，且 `REMOTE_CANDIDATE_SHA=C6` 必须为 base 的严格后代，否则 STOP。
- publish gate 同时要求本地 fast-forward predicate、signed publication approval 和 compare-and-swap lease：只允许以 expected-old=`REMOTE_BASE_SHA` 把 frozen candidate 更新到 `refs/heads/main`。lease failure、remote change、非 fast-forward 或 rewrite suspicion 均 STOP，禁止自动 rebase/merge/force-push 重试。
- publish 前冻结 canonical `HEAD`、原始 index file bytes/hash/stat、tracked dirty path+bytes+mode、untracked path+bytes+mode、local-only inventory/object reachability，并记录 expected post-publish graph。publish 后在 isolated repo 再次 named-ref fetch + `ls-remote`，要求唯一 remote tip、isolated fetched ref、local candidate object、clean detached checkout `HEAD` 与 candidate 五者相等，随后冻结最终 `SOURCE_SHA`。
- post-publish ancestry 必须为：`REMOTE_BASE_SHA` 是 `SOURCE_SHA` 的严格祖先，remote tip=`SOURCE_SHA`；canonical `LOCAL_HEAD` 及其 local-only objects 保持可达且 bytes/inventory 不变。若 pre-matrix 为 `equal`，canonical local 是 remote base 的祖先；若为 `remote_ancestor_of_local`，且 local 未被 candidate 包含，则 remote 与 local 的 merge-base 必须仍精确为 `REMOTE_BASE_SHA`、关系预期为 `diverged-preserved-local-only`；任何其他关系、object 丢失或 canonical fingerprint 变化即 STOP。该预期 diverged 状态是保护本地历史的明确 postcondition，不可触发自动 merge/rebase。
- lineage 每一关都有 `command`、`exit_code`、`key_output`、`timestamp`。短 SHA、branch/tag、tracking cache、canonical working-tree bytes 均不是部署授权。
- recovery bytes 只能从 `SOURCE_SHA` commit objects 或经验证的 clean detached checkout 提取；recovery preflight、首个 live write前、manifest commit point 前与 commit 后都重验“对象已发布、immutable且 lineage 允许”。commit 前变化进入本地 uncommitted rollback；commit 后变化只能 incident reconciliation 并保持 scheduler disabled，不宣称可撤销 remote。

### 3.3 Canonical identity 与 manifest schema

```json
{
  "schema_version": 2,
  "repo_identity_version": 1,
  "repo_identity": "<pinned host/owner/repo identity>",
  "source_commit": "<40-char lowercase sha>",
  "managed_surface_digest_version": 1,
  "managed_surface_digest": "sha256:<64 lowercase hex>",
  "synced_at": "<RFC3339 UTC>"
}
```

- `repo_identity_v1` 解析 `https://host/owner/repo(.git)`、`ssh://git@host/owner/repo(.git)` 与 `git@host:owner/repo(.git)`；移除 scheme、userinfo、默认 port、尾 `/` 和 `.git`，DNS host 小写，repo path 保留 case。local/file remote、credential、query/fragment、非 allowlisted host、多义 remote 全拒绝。
- inventory 拒绝 duplicate target、`..`、absolute path、case-fold/Unicode collision、symlink、特殊文件及越过 approved root。
- 普通文件按原始 bytes 计算 content SHA-256；mtime/uid/gid 不进入 managed digest。

### 3.4 W6a 15-path allowlist v1

下表冻结于 baseline commit `010e894e1b2e63ac00aded2c749e68b649f0ac74`。source 相对 repo，target 相对 `/Users/kezheng/.codex`；全部为 `regular-file`、mode `0644`。最终 `SOURCE_SHA` 必须在这些 source paths 保留相同 OID 与 content hash。

| # | target | source | type | mode | Git SHA-1 blob OID | content SHA-256 |
|---:|---|---|---|---|---|---|
| 1 | `AGENTS.md` | `codex/AGENTS.md` | `regular-file` | `0644` | `656edb79cdbc3e66a9773b1a3439a9fcb1c5a189` | `fe620ec9044772208f9ace38d583babbd0652b28cffd5d22fd138fb312694f2e` |
| 2 | `hooks.json` | `codex/hooks.json` | `regular-file` | `0644` | `90779059a393c1fc7a87e3efa94342f72e7350ca` | `d9f7d167f4f5c6f554cfd56625c8391dfc75c790951184cb340bac45cde9b911` |
| 3 | `hooks/compaction_counter.py` | `codex/hooks/compaction_counter.py` | `regular-file` | `0644` | `f125bf0abf99c73966c71666d2fac24f9b701632` | `832b2d2c5c84c479fd6eb71798899c53af642942f593f60cbd3d569218d6024e` |
| 4 | `hooks/compaction_probe.py` | `codex/hooks/compaction_probe.py` | `regular-file` | `0644` | `b32f237d10928c294948f3168e46cceeddf35be5` | `06ff601544027bbad8f45ec275b79c0818ed57003c324e2c814f7f1244da8b39` |
| 5 | `hooks/context_meter.py` | `codex/hooks/context_meter.py` | `regular-file` | `0644` | `2ae38112872a9eaf3acdd91fcb88ea5aef99f871` | `1edbb0b2976aaa6e5cac8b5bfc673deb2808b1e7786c95d5f7a6a693238b9e77` |
| 6 | `hooks/dhf_preprompt.py` | `codex/hooks/dhf_preprompt.py` | `regular-file` | `0644` | `23ee9ee163b75d2515acdbe639063e45dd15f347` | `be0f0f9372cdacd5f03beb60df8269629ecdd07991814ca8dd912b97b4effbb9` |
| 7 | `hooks/harness_guard.py` | `codex/hooks/harness_guard.py` | `regular-file` | `0644` | `76f42b14bc625d070a354ab295b52cb28b6573c3` | `e4090058176ee2cf8595d7b9be3c40693b22fd4ccb4e33b83cbd5c788c88dca1` |
| 8 | `hooks/session_bearing.py` | `codex/hooks/session_bearing.py` | `regular-file` | `0644` | `511f90b4bb0aea4a1775da65e8023c9cfd9de5fd` | `2bc923ce4f31eda81489896c34c73a8c02a121a4f663c2663abd8533b2fbe7f3` |
| 9 | `runtime/evidence.schema.json` | `codex/runtime/evidence.schema.json` | `regular-file` | `0644` | `d7cc85e740b9339fd632106f7a1bb3617481373d` | `3a2db2c32a4cd5bb72f22938a221fa00980ed9c01ae200d95bf97b2b4e888474` |
| 10 | `runtime/evidence/decision-evidence.schema.json` | `codex/runtime/evidence/decision-evidence.schema.json` | `regular-file` | `0644` | `33125d53622231fc7e932209c5169fa03a9bc496` | `47d720f71bd774416cf9fa8f2e03fbec8464aac2724d9b201d4e4f601747c4dc` |
| 11 | `runtime/tool-policy.json` | `codex/runtime/tool-policy.json` | `regular-file` | `0644` | `50d0286327f459a40ade755a297412063850eba7` | `e4a6cee94e9e659d190ce01d44abf77e54666f55fe4f113d5eea5729345769b2` |
| 12 | `skills/codex-fluent/references/maintenance-checklist.md` | `codex/skills/codex-fluent/references/maintenance-checklist.md` | `regular-file` | `0644` | `27a74f97612ec7391722c9b0cb7405a54b91bc2b` | `e774d13c227fe715053cd986249415356f0c02986df5136030fd797550eb3920` |
| 13 | `skills/codex-fluent/scripts/report_active_sessions.py` | `codex/skills/codex-fluent/scripts/report_active_sessions.py` | `regular-file` | `0644` | `b5f451b3a003bc7d4de86534a349472c4ac63fa1` | `ca06a6de34173cfaa353180a455b1f1580bf1deca13cf53cf094e15858c1e571` |
| 14 | `skills/delivery-harness-framework/SKILL.md` | `codex/skills/delivery-harness-framework/SKILL.md` | `regular-file` | `0644` | `6ab8c6e918574e0b0fdc5cdd27022f766233ca3d` | `18148ab8885fd0920df72a248cef23ff3fa1b73a60b3370098542efb4cfdcd00` |
| 15 | `skills/delivery-harness-framework/evals/evals.json` | `codex/skills/delivery-harness-framework/evals/evals.json` | `regular-file` | `0644` | `e86bef72614e54890b31223ea1c81a9d21ad57e6` | `651cfe21377981dad9eadc7c6d264935512a9fcce50638ea0545fe4235348f02` |

聚合算法：表中 Git OID 与 content SHA-256 的值本体仍为裸 lowercase hex；canonical serialization 时，分别给裸值添加固定 ASCII 前缀 `sha1:` 与 `sha256:`，形成 `git_oid` 与 `content_sha` 字段。随后按 target UTF-8 byte order 排序；每行依次拼接 `target`、`source`、`object_type`、`mode`、带前缀的 `git_oid`、带前缀的 `content_sha` 六字段，每字段 UTF-8 bytes 后跟单个 NUL，无额外分隔。golden digest 为 `sha256:254e37a4dd40991b93954caf9dea8baddb4c3525a44078f005c607232d441c19`。discovery 的 count/path/type/mode/OID/content/digest 任一不一致即 STOP、修订计划并重新评审，不得临时决定第 16 项。

### 3.5 Trusted approval、lock 与 maintenance corridor

#### Approval profile v1

- 唯一 envelope schema 为 version `1`，top-level keys 精确为 `payload` 与 `signature`；`payload.approval_schema_version` 必须是 JSON number `1`，并精确包含 `issuer`、`key_id`、`action`、`repo_identity`、`old_source_sha`、`new_source_sha`、`managed_surface_digest`、`target_root`、`engine_version`、`engine_bundle_digest`、`tcb_digest`、`reason`、`issued_at`、`expiry`、`nonce`、`transaction_id`，未知或缺失 key 均拒绝。SHA 为 40-char lowercase hex，digest 使用既定 lowercase algorithm prefix，`nonce` 为 32-byte lowercase hex，`transaction_id` 为 canonical lowercase UUID，时间只接受无 fractional second 的 UTC `YYYY-MM-DDTHH:MM:SSZ`。
- payload 与 envelope 都只接受 RFC 8785 JCS 的 UTF-8 canonical JSON bytes；parser 必须拒绝 duplicate keys、UTF-8 BOM、非 I-JSON number/string、invalid Unicode、非规范 member order/escaping/number bytes与 trailing bytes，并在验签前重编码后 byte-for-byte 相等。domain bytes 精确为 `ASCII("MyCodexEnv/runtime-approval/v1") || 0x0A`；签名消息精确为 `domain_bytes || JCS_UTF8(payload)`，无额外 length、NUL、空格或换行。
- 签名算法唯一为 RFC 8032 pure Ed25519；禁止 Ed25519ph/context、算法协商或 fallback。trust policy 中 public key 是 raw 32 bytes 的 64-char lowercase hex；envelope `signature` 是 raw 64 bytes 的 128-char lowercase hex。`key_id` 唯一派生为 `ed25519-sha256:` 加 `SHA-256(raw_public_key_32_bytes)` 的 64-char lowercase hex，verifier 先重算 key ID 再按 policy 查 key。
- issuer 唯一字符串为 `mycodexenv-runtime-control-v1`。action/target/TTL policy 精确如下；`expiry - issued_at` 必须大于 0 且不超过该行秒数，target 必须 byte-for-byte 等于表值。automation、旧 clone/agent/prompt/普通用户签发的 envelope 永拒，不能通过 CLI/env/service-account override。

| action | exact target root | max TTL |
|---|---|---:|
| `immutable-source-recovery-and-bootstrap` | `/Users/kezheng/.codex` | 600 seconds |
| `immutable-source-forward-sync` | `/Users/kezheng/.codex` | 600 seconds |
| `promote-engine-bundle` | `/Library/Application Support/MyCodexEnv/runtime-control/engine` | 600 seconds |
| `approved-immutable-downgrade` | `/Users/kezheng/.codex` | 300 seconds |

- root-owned trust policy initial path 为 `/Library/Application Support/MyCodexEnv/runtime-control/trust/policies/approval-policy-v1.jcs`，parent directories 是 `root:wheel 0700`、policy file 是 `root:wheel 0400`、ACL 为空、link-count=1；canonical policy version 从 integer `1` 单调递增，绑定 exact issuer、public keys/key IDs、per-key actions、activation/revocation time 与上述 TTL/target table。authoritative active-state root `/Library/Application Support/MyCodexEnv/runtime-control/trust/policy-state/` 为 `root:wheel 0700`，内含按 version 命名、`root:wheel 0400`、ACL为空、link-count=1 的 immutable no-replace chain records，保存 highest accepted policy version/digest 与累计永久 revoked key IDs；不存在可覆盖的授权 cursor。
- initial public key/policy genesis 只能由第 4 节 Provision prerequisite 生成、激活与冻结 non-secret fingerprint receipt；Phase 0 只读验证。private key 只留 external signing authority/HSM，不进入 repo、runtime host、env 或 receipt。rotation 只接受 version=`previous+1` 的新 policy，由当前 active key与新 key双签，overlap 固定最多 24 hours；revocation 立即生效且 revoked key ID 永不复用/解除。approval claim 与 policy rotation/revocation 共用现有 external lock 与 monotonic `policy_epoch`；每个 claim 绑定 exact active policy digest+epoch。lock 内先撤销后 claim 必须拒绝，已 durable claimed 的 approval 按 claimed policy digest 只能完成该事务或进入现有 recovery-required，不能启动新事务；并发 claim/revoke 由 lock+epoch 决定单一次序并有正反 golden tests。policy-state 以第 3.5 节 replay claim 同样的 no-replace/fsync chain推进；version/digest 倒退、跳号、撤销回滚或旧 policy 重装全部 fail closed。
- manifest 存在时 `old_source_sha` 必须为 manifest 的 40-char lowercase SHA；missing-manifest recovery 时唯一编码是 canonical JSON `null`，语义仅为“锁内复核后确认 schema-v2 manifest 路径不存在”，空串、全零 SHA、字段缺失或其他 sentinel 全拒绝。unknown/tampered/not-yet-valid/expired/replayed/binding mismatch 在允许的首个 control write 前 nonzero，且 live、backup、journal、manifest bytes 零变化。

#### Trusted time 与 replay claim protocol v1

- trusted-time state 不是可覆盖 cursor，而是 replay ledger 的 immutable hash chain；每个 durable claim/no-op record 同时绑定 `previous_record_digest`、`previous_effective_unix_second`、`boot_id`、`monotonic_ns`、`wall_unix_second` 与 `new_effective_unix_second`，所以 claim 的 no-replace atomic install 同时推进 replay state和 rollback watermark。materialized index 只能是可重建 cache，不具授权语义。
- 同一 boot 下要求 current monotonic 不小于前一 record，`effective = max(wall_now, previous_effective + floor((monotonic_now - previous_monotonic)/1s))`；boot 改变时 monotonic 不比较，若 `wall_now < previous_effective - 2 seconds` 则 clock rollback fail closed，否则 `effective=max(wall_now, previous_effective)`。有效窗口唯一判定为 `effective + 2 seconds >= issued_at` 且 `effective - 2 seconds <= expiry`；2 seconds 是唯一容差，TTL 仍按未经容差扩张的 signed `expiry-issued_at` 检查。clock/boot ID 不可读取、monotonic regression、chain gap或 watermark rollback 均拒绝。
- mutating action 在获 external lock、完成 fresh approval/TCB/manifest/clock验证后，先冻结 managed/live/backup/journal/manifest before digest，再创建 transaction-id keyed canonical `CLAIMED` record。temp 必须在 replay record 同一 directory/filesystem 以 `O_CREAT|O_EXCL|O_NOFOLLOW`、`root:wheel 0600` 创建，写入+file `fsync` 后用 macOS `renameatx_np(..., RENAME_EXCL)` no-replace install final record，再 `fsync` parent directory；Phase 0 必须在真实 filesystem 实证该 exact primitive 的 no-replace与crash语义，否则 kill gate。只有 final `CLAIMED` 已安装且 parent fsync 成功后，才可创建 transaction child或 durable `PREPARED`。
- durable `CLAIMED` 本身永久消费 approval。若 crash 后存在 valid `CLAIMED` 而没有 `PREPARED`，restart 持同一锁，以 record 中 before digest 证明除该 claim 外所有 managed/live/backup/journal/manifest bytes 与 inventory zero-change，再以相同 temp+fsync+no-replace+parent-fsync protocol追加 sealed `ABORTED_BEFORE_PREPARE` transition；旧 approval 永不可重用，新 approval/new transaction 可重新开始。partial、invalid、hash-chain gap、同时存在冲突 state、不能证明 zero-change或 no-replace/parent-fsync 结果不明均进入 incident fail closed。
- mutating claim 在 temp-create 前 crash 且 final/temp 均不存在可安全重试；temp-create、file-fsync、no-replace、parent-fsync 任一边界均由 final record+temp+parent durability readback裁决：valid final 由 restart补 parent fsync并表示 approval 已消费；final 不存在但遗留 temp/partial/ambiguous state 一律 incident，不得猜测或重用。sequential/concurrent replay 必须在创建新 temp或任何其他新增 control write 前 nonzero。
- trust anchors、launcher、lock、replay store、receipt store 与 backup base 固定在 `/Library/Application Support/MyCodexEnv/runtime-control/`。ownership/mode schema 按类别冻结：control/version directories 为 `root:wheel 0700`；immutable owner-executable bundle files（launcher、engine entry、bundle helper）为 `root:wheel 0500`；immutable non-executable bundle data/config/import sources 为 `root:wheel 0400`；mutable control state files（lock、replay、receipt、journal 等）为 `root:wheel 0600`。若使用 `/usr/bin/...` 等 external system executable，只接受 TCB manifest 冻结的 absolute path、exact identity/digest 与 root-owned `0555` 或等强 non-user/group-writable mode，并单独分类，绝不经 `PATH` 解析。所有类别都要求 invoking user/group、旧 clone/agent/child 无 write；类别、ownership、mode、ACL、parent identity 或 writability 任一不符即 kill gate，不得把 user-admin group writable 视为可信。
- privileged launcher 绝不从 canonical/standalone checkout、调用时 `cwd`、用户 home、temp root 或任何 user/group-writable path 加载或执行代码、imports、helpers、plugins 或 config。同一套 reviewed shared engine 以 immutable promoted bundle 安装到 external-owner versioned root `/Library/Application Support/MyCodexEnv/runtime-control/engine/<engine_version>/`；bundle 只是同一 engine 的已发布副本，不复制或重写 transaction semantics。version root 与内容满足前述 owner/mode predicate，安装后只读使用，agent 无 promotion/write authority。
- 每个 version root 包含 signed machine-readable TCB manifest。manifest 以绝对 canonical path、object category、type、owner、group、exact mode、content SHA-256 和 provenance 列出 launcher/dispatch entry、完整 engine bundle、固定 interpreter、所有 transitively loaded imports/stdlib/native libraries、absolute helper binaries 与全部 config；同时绑定 post-publish immutable `SOURCE_SHA`、engine source paths 的 Git object OID/content hash，以及 `engine_version`、`engine_bundle_digest`。实际 category+mode 进入 canonical manifest bytes、promotion receipt 与 domain-separated `tcb_digest`，签名及 recovery approval 都绑定该值。
- external-owner service 使用冻结的 absolute executable paths、root-owned fixed `cwd`、`umask 077` 与 allowlist-only clean environment；拒绝/清除调用方 `PATH`、`PYTHONPATH`、`PYTHONHOME`、user site 与其他 loader/config override。Python 实现必须用 TCB manifest 中 absolute root-owned external-system interpreter 的 isolated/no-user-site/no-site 等效模式（例如 `-I -S`），imports 只来自 TCB manifest 中 immutable non-executable root-owned roots，禁止 dynamic imports/plugins。Git/helper 若确有必要，必须使用 manifest 中分类后的 absolute root-owned executable，并禁用 user/system/global/repo-controlled config、hooks、aliases、pagers 与 writable dependency resolution；优先让 promoted bundle 自带由 `SOURCE_SHA` 验证的 recovery payload，使 Phase 7 不执行 Git。所有实际 flags、env、category/mode 与 predicates 在 Phase 0 实证。
- external-owner launcher/service 在打开 maintenance corridor、获取会产生持久状态的 authority或执行任何 replay/control/backup/live transaction write 前，先验证 approval profile/signature，再从磁盘逐项复算 TCB manifest、bundle、interpreter/import/library/helper/config identity、category、mode 与 digest，并证明 `SOURCE_SHA`/source-object binding。完整 approval/profile/clock/watermark 与 TCB 验证至少在获锁后、atomic replay claim 前、首个 backup/control/live transaction write 前各 fresh 执行一次；任何时点 mismatch 都 nonzero，corridor 关闭且 live/control/backup/replay 零变化。
- 唯一 privileged 入口是 external-owner one-shot launcher；它只接受 profile 中逐项 allowlist 的 exact signed action，禁止 CLI/env 改写 action。recovery invocation 固定 action=`immutable-source-recovery-and-bootstrap`、`SOURCE_SHA`、第 3.4 节 digest 和 target root；downgrade 复用本节同一 approval profile/domain/issuer/authority map，promotion 仅接受 Phase 6 的独立 external-owner action/authority。验签后对预创建 lock file nonblocking 获得排他锁。
- 锁前只做不依赖 mutable state 的静态资格检查；获锁后才完整重跑 manifest、target bytes、mapping、repo identity、remote binding、recovery state、backup capacity/owner/mode/ACL/link-count 与 path identity preflight。全部通过后按 transition matrix：equal 只安装 durable `NOOP_COMMITTED`并结束，mutating action 先安装 durable `CLAIMED`，只有后者 parent fsync 后才创建 transaction child。任何失败/退出都关闭最小授权并自动恢复 deny/relock 状态。
- 双进程 probe 必须证明仅一者进入 engine，另一者 nonzero 且 live/backup/journal/manifest/replay 零写入。launcher 只做身份、锁、replay 和 confinement coordination，文件语义全部委托 shared engine。
- source、target、parent、staging、backup、manifest 均使用预打开 trusted directory fd 与 no-follow primitives；拒绝 symlink、hardlink alias、特殊文件、unexpected link count、mount/parent inode replacement。每次写前后 `fstat`/identity recheck，path replacement 或 rename race 立即回滚并 STOP。

### 3.6 One-shot recovery、backup 与唯一 commit point

- `exact-before-v1` 对 write inventory 每个对象都必须 canonical 记录：path UTF-8 bytes、existence、object type、raw file bytes+SHA-256 或 symlink bytes（symlink 本身仍按 policy 拒绝）、mode、uid/gid、ordered ACL entries、ordered xattr names+raw values、file flags、atime/mtime/birthtime/ctime 的可还原/只比较分类、resource metadata（inode/device/link-count/filesystem ID/allocation size）、以及每个 affected directory 的同等 metadata+ordered child inventory。delete backup 编码是 JCS metadata record 加单独 raw payload object，两者以 digest 绑定，不用 archive 隐式丢 metadata。restore 顺序固定为预建 owner-only parents→raw payload/symlink object→owner/group→mode→ACL→xattrs→flags→timestamps→directory metadata（deepest-first）→directory+parent fsync；created object 按 reverse apply order 删除。
- exact comparator 对 bytes/type/mode/uid/gid/ACL/xattrs/flags/timestamps/resource/directory metadata 分别输出 `equal|unsupported|changed|unknown`；只有冻结为 intentionally volatile 且不影响恢复的 inode/ctime 等字段可用稳定 identity predicate 比较，该分类必须在首写前进入 signed TCB policy。OS/filesystem 不支持枚举、backup、restore 或验证任一 required metadata 时在首写前 STOP，不降级为 bytes-only rollback。
- 非空 live home 缺 manifest 默认 fail closed。normal sync、automation、`--force-downgrade`、独立 `metadata-only` action 均不能写入。
- missing-manifest live home 唯一入口是 signed one-shot `immutable-source-recovery-and-bootstrap`：严格恢复 15 targets，并在同一 journaled transaction 创建 schema-v2 manifest。不存在恢复后不创建 manifest、或先恢复后 bootstrap 的成功路径。
- 对 `immutable-source-recovery-and-bootstrap`，dynamic delete set 必须精确为空；`--delete`、任何 discovered delete、allowlist 外 create/overwrite/delete 或第 16 项均在首写前拒绝。一般 sync inventory 对 dynamic delete 的建模不得扩大该 action 的固定 write set。
- C2 只实现 read-only guard、canonicalization、approval validation 与 lock-held preflight，不做任何 metadata/live write。C3 首次实现 transaction、live recovery+manifest bootstrap、empty-temp bootstrap 与 crash recovery。
- backup base 固定为 `/Library/Application Support/MyCodexEnv/runtime-control/backups/`，位于 live mirror/delete/automation write surface 外，由 external owner 预创建。可信 launcher 可在完整 preflight 与 replay claim 后创建全新 `<transaction_id>/` child；已存在即 STOP。child、`payload/`、`metadata/`、`journal/`、`receipts/`、`reservation/` 均冻结为 `root:wheel 0700` directory，payload/metadata/journal/receipt/reservation files 为 `root:wheel 0600`，ACL 必须为空、regular file link-count 必须为 1；类型、owner、group、mode、ACL、link-count 任一不符即首写前 STOP。
- 容量按 filesystem 分别确定，不把不同生命期的项盲目相加；对 WAL 每个 durable state 冻结当时同时存活的 backup payload、staging/temp、journal、manifest/receipt、reservation 与 filesystem allocation rounding，`peak_simultaneous_allocation_bytes` 是这些 state total 的最大值，`safety_margin = max(1 GiB, ceil(peak_simultaneous_allocation_bytes * 0.10))`，`required_free = peak_simultaneous_allocation_bytes + safety_margin`。所有项由冻结 inventory、exact-before payload、序列化上限、WAL lifetime graph 与 filesystem allocation unit 计算并写 receipt，禁止经验估值或 double-count。backup/control filesystem 与每个 target staging filesystem 都必须先以同 filesystem、owner-only reservation file 做非 sparse、预分配并 fsync 的 `required_free` reservation；不支持可验证预分配、race recheck 失败或 `ENOSPC` 均在 live 首写前 STOP。
- reservation 由 transaction 独占并纳入 WAL：每次实际分配前在持锁/confinement 下先复核 filesystem identity、available blocks 与剩余 reservation，再按该步冻结上限 durable 缩减 reservation并立即完成分配；任何短分配、外部容量竞争或 `ENOSPC` 进入 uncommitted rollback。reservation 只能在 durable `ABORTED` 或 `COMMITTED_CLEAN` 后删除并 fsync parent；crash 后由 restart 恢复所有权。失败 cleanup 不得掩盖原 verdict，保留 `recovery-required`。
- v1 禁止自动删除、覆盖、复用 pre-existing backup；retention/GC 属独立人工 scope。live 首写前验证 deterministic capacity、owner/mode/ACL/link-count、empty child、mapping、staged/backup hashes。commit 后 backup、journal 和 final receipt 设为 immutable sealed artifacts，不得覆盖、truncate、复用或就地修补。
- `write_inventory.json` 覆盖每个 create/overwrite/delete、动态 delete、parent metadata、staging、journal、backup、receipt、manifest temp/final 与 cleanup path；运行时出现未列路径即 fail closed。
- root targets、`hooks/`、`runtime/`、`skills/` 每个 surface 分别产生 created/overwritten/deleted receipt，零 count 也明确记录。
- durability 顺序固定且由同一 shared engine 实现：`PREPARED` WAL（before inventory、write set、hashes、capacity/reservation）写入并 fsync journal file+parent；所有 backup temp 写入/fsync、atomic rename、fsync backup parent 后写并 fsync `BACKED_UP`；所有 staging files 写入/fsync并 fsync staging parents 后写并 fsync `STAGED`；每个 target 前先写/fsync `APPLY_INTENT(n)`，再以同 target filesystem temp 写入/fsync、atomic rename、fsync target parent，最后写/fsync `APPLIED(n)`。全部 target 验证后写/fsync manifest temp、写/fsync `COMMIT_READY`，再 atomic rename manifest temp 为 final、fsync manifest parent，最后写/fsync `COMMITTED`。receipt/cleanup 完成后写/fsync `COMMITTED_CLEAN`；abort restore 完成后写/fsync `ABORTED`。任何 directory metadata restore 也必须 fsync 该 directory 及其 parent。
- 唯一 commit point 是把已 fsync manifest temp 在同 filesystem atomic rename 为 final manifest；parent fsync 是确认其 durable 的必要步骤。commit 后只允许 non-semantic cleanup；backup 与 external-owner receipt 成功/失败后均持久化且不可覆盖。
- commit 前任一 fault/crash 均为 uncommitted：按 journal 逆序恢复 create/overwrite/delete/dir metadata并验证 before-state。第一次 restore failure 必须从 immutable backup 重试；持续失败保留 `recovery-required`，拒绝后续 sync。
- restart verdict 确定：最后 durable state 为 `PREPARED/BACKED_UP/STAGED/APPLY_INTENT/APPLIED/COMMIT_READY` 且 final manifest 不等于完整 after-manifest时，一律逆序恢复并证明 exact before-state；manifest rename 与 parent fsync 之间 crash 时，重启以 final manifest bytes、15-path aggregate digest 和 WAL intent共同裁决，三者完整匹配则补 fsync并收敛为 committed after-state，否则恢复 before-state；`COMMITTED/COMMITTED_CLEAN` 只能验证 after-state并完成幂等 cleanup，不能重新 apply；`ABORTED` 只能验证 before-state。任何混合状态或无法证明的 verdict 为 `recovery-required`，禁止新 transaction。因此所有 crash boundary 最终只能是 byte-identical before-state 或完整 committed after-state。
- restart 必须由下一次 trusted launcher 获同一排他锁，先恢复并关闭旧 transaction，再以新 approval/new transaction 重跑完整 preflight。commit 后 restart 不能复用 approval。

### 3.7 Plugin/MCP reconciliation 分离

- file transaction commit 后返回 `file_sync_committed`；随后由人工 phase 基于冻结 expected-state snapshot 单独 reconcile，automation 永不执行。
- 前后 normalized snapshot 必须 diff。失败不回滚 file transaction、不改 manifest；返回 `file_sync_committed_plugin_reconciliation_failed` 并保持 automation paused。
- CLI 无事务/可靠 rollback 时，仅以 snapshot/diff、幂等重试和暂停控制 residual risk，不伪造原子性。

### 3.8 Source transition matrix 与显式 downgrade

- manifest 存在时，在获锁、replay state install 前和首写前分别以 expected-old CAS 读取 `source_commit`。`manifest.source_commit == requested new_source_sha` 为 `equal`：不创建 `CLAIMED`，而是把 single-use claim 与 signed no-op receipt 合并为 transaction-id keyed immutable `NOOP_COMMITTED` record。它保存 exact signed envelope bytes/signature/key ID并绑定其 digest、manifest expected-old、requested SHA、repo identity、action、transaction ID、before live/manifest digest及 previous/new watermark；signed payload 已覆盖 action/old/new/repo/transaction/time window，因此这些 receipt fields 必须与 envelope byte-for-byte重算匹配。
- `NOOP_COMMITTED` 是首次 equal 成功的 exactly-one authoritative 四字段 receipt。record schema 的 `command` 是包含 deterministic-redacted exact `argv` array、absolute `cwd` 与按 key 排序 allowlisted `env` map 的 canonical object；`exit_code` 精确为 `0`；`key_output` 是不超过 1024 UTF-8 bytes 的 deterministic `NOOP_COMMITTED` assertion，绑定 transaction/action/expected-old/requested SHA 与 live/manifest unchanged；`timestamp` 是 RFC3339 UTC second。timestamp 在全部 read-only verification 完成后、final canonical record封装前从第 3.5 节 effective time采样并 seal；它是 decision completion time，不伪称 process-return time。
- `NOOP_COMMITTED` 使用第 3.5 节同一 same-filesystem temp-create/file-fsync/`renameatx_np(..., RENAME_EXCL)` no-replace/parent-fsync protocol原子安装并推进 replay/watermark。这是唯一允许的 logical control mutation；不创建 backup、WAL、transaction child，不写 manifest/live/其他 control artifact。logical success 只在 final no-replace install+parent fsync 完成后成立；crash 后发现 valid final 时 restart只补 parent fsync并沿用 record 中 sealed completion timestamp，不生成第二份 success receipt。
- equal no-op 在持锁验证 existing transaction ID/approval digest 后、temp-create 前拒绝 sequential replay；并发调用由同一排他锁串行，后到者在任何新增 durable control write 前 nonzero，no-replace 是最终防线且不得留下 loser temp。crash 在 temp-create前、temp-create后、file-fsync后、no-replace后、parent-fsync后分别 readback：final 不存在且能证明无 temp/其他 state时可安全重试；仅有可识别 private temp时先验证未 install、删除并 fsync parent后可重试；存在 valid final 即按前款完成唯一 receipt；invalid final、无法归属的 temp、final/temp并存、directory readback失败或其他 ambiguous state 一律 incident fail closed。任何 safe-retry verdict都必须同时证明 live/manifest/backup/WAL与其他 replay records zero-change。
- rejected sequential replay 或 concurrent loser 必须保持 replay/control/live/backup/WAL zero durable write，只向调用方返回含 canonical-redacted command、nonzero exit code、bounded deterministic key output与 RFC3339 decision timestamp 的四字段 response。实施期 negative probe 由独立 out-of-band test/evidence collector 在 disposable evidence root保存该 response；collector 不属于 shared engine、transaction/control authority或 write inventory。生产拒绝若无 collector则没有 persistent reject receipt，engine 不得为了审计破坏 zero-write；gate 所需 fresh reject receipt 必须由调用 negative probe 的独立 harness保存。

| fresh `remote_tip` / manifest `old` / requested `new` | 唯一 verdict |
|---|---|
| `old == new == remote_tip` | `equal`，只走 `NOOP_COMMITTED` |
| `old == new != remote_tip` | `stale_equal`，STOP，不把落后状态当 NOOP |
| `old` 是 `new` 严格祖先且 `new == remote_tip` | `forward`，要求 manifest expected-old CAS |
| `new` 是 `old` 严格祖先，且两者均为 `remote_tip` 可达的已发布 immutable commit | 仅可走独立批准的 `downgrade` |
| fresh remote 在任一相邻 readback 间 advance，或 publish 后状态未完成验证 | publish 前 STOP；publish 后进入 `SOURCE_PUBLISHED_UNVERIFIED`/incident reconciliation |
| expected-old mismatch、rewrite/unreachable、diverged/unknown、任一 object missing | STOP；禁止 normal/force fallback |

- `forward` 必须满足上表、fresh remote binding 与 current `main` reachability；normal automation、normal sync 与任何 `--force` 不得绕过 matrix，也不得把 missing manifest 解释为 forward。
- emergency downgrade 复用第 3.5 节同一 approval envelope/profile、domain=`MyCodexEnv/runtime-approval/v1`、issuer、`authority_key_map`、external lock、policy epoch 与 watermark/no-replace replay chain；独立性仅为 exact action=`approved-immutable-downgrade`、max TTL=`300 seconds`、该 action 的 allowed key IDs，以及 action-prefixed replay key=`runtime-approval-v1/approved-immutable-downgrade/<transaction_id>/<nonce>`，不得另设 domain/issuer/replay namespace。approval 必须绑定 old/new SHA、两者 provenance、manifest expected-old CAS、reason、target root、engine/TCB/digest；target `new_source_sha` 必须是 `old_source_sha` 的严格祖先、仍为 current `remote_tip` 可达的已发布 immutable commit，并通过冻结的 known-safe、known-bad denylist 与 rollback-floor policy；不能来自 dirty checkout、local-only object、tag-only ref 或已消失历史。
- downgrade 仍由同一 shared engine 执行完整 backup、WAL、staging、15-path+manifest transaction、replay、crash/restart 和 postcondition；commit 后 manifest 必须为批准的 `new_source_sha`、15-path digest匹配、old/new receipt sealed，任何失败按第 3.6 节收敛。它不新增 wrapper 或第二套 transaction engine。
- 已发布 remote `refs/heads/main` 永不倒退、永不 force-push。代码层 rollback 首选基于当前 remote tip 创建并正常发布 forward revert commit，再走普通 `forward` promotion；只有无法及时生成安全 forward revert 且风险已书面接受时才允许 emergency downgrade。downgrade 后 runtime 落后于 remote、后续 forward 可能覆盖该状态且旧 commit 可能含已知缺陷，均作为 observation 前未关闭的 residual risk，automation 保持 disabled，直到独立 forward repair 完成。

### 3.9 Scheduler definition transaction

- scheduled execution principal 固定为 `mycodexenv-daily-report-v1`，与 scheduler mutation principal 不同 UID/GID/service subject 且无交叉 credential；provision receipt 必须冻结 UID、primary GID、空 supplementary groups、service subject、parent launcher 与 child inheritance rules、sandbox/profile bytes+digest。它只读 sealed engine/SOURCE_SHA/report definition 与 live 15-path、只写独立 temp+report destination；明确 deny live/control/backup/replay/engine/trust/scheduler credential/Git repo+refs+publication roots，network denied，subprocess 只允许 TCB manifest 中为 report 冻结的 absolute argv，无 credential API/keychain/env/fd 访问。parent/child 都不得继承 mutation credential；不能实证时 STOP且不 enable。
- rollout definition mutation 的唯一 principal 是 `mycodexenv-runtime-scheduler-adapter-v1`，唯一 backend role 是 `MyCodexEnvRuntimeSchedulerMutatorV1`；二者只能在 Phase 6 post-publish/promotion 后由 backend administrator provision。credential 只能由 backend administrator 直接签发给该 principal，provenance receipt 冻结 backend tenant/account、role、subject、issued-at、credential fingerprint和权限 diff（secret redacted）；credential 只存于 `/Library/Application Support/MyCodexEnv/runtime-control/scheduler/credentials/adapter-v1.credential`，parent `root:wheel 0700`、file `root:wheel 0400`、ACL 为空、link-count=1，禁止 env、keychain user item、repo、home、prompt或 CLI credential override。
- backend role 只允许 read stable job/state/executions、expected-revision CAS disable/update-disabled/enable 与 scheduler-level suspend；明确 backend-deny unsuspend/resume、delete、recreate、job-ID change、history restore、blind update和非 CAS mutation。旧 clone/agent/automation/prompt/普通用户/通用 API client没有该 role，对 update/enable/disable/delete/recreate/restore/suspend/unsuspend全部 backend-denied。所有 scheduler mutation 只能经 immutable external-owner CAS adapter；adapter 使用 absolute path、sealed TCB/clean env并验证 principal/role/credential fingerprint，任何其他调用路径 fail closed。
- Phase 6 provision 的 `/Library/Application Support/MyCodexEnv/runtime-control/scheduler/quarantined-definition-digests-v1.jcs` 必须在 seal 前已包含本事故 definition digest；parent `root:wheel 0700`、file `root:wheel 0400`、ACL 为空、link-count=1，并纳入 adapter TCB。adapter 在每次 update/enable前拒绝 denylist digest；backend 又只授权该 adapter principal/role mutation，所以旧危险 definition不能绕过 adapter restore/re-enable。后续更新属于独立 external-owner signed、单调 versioned `vN` policy scope，只能继承并新增 digest，不能删除或就地覆盖 v1。
- scheduler snapshot 冻结 stable job ID、backend/account/schema version、definition revision/CAS token、canonical definition digest、schedule、timezone、enabled state、absolute entrypoint、absolute `cwd`、clean env contract，以及 definition 中 sealed `engine_version`/`SOURCE_SHA` binding。job ID 漂移、schema 未知、digest 不可重算或 entrypoint/cwd 非 absolute external-owner path 全部 STOP。rollout mutator credential 必须是 job/action/allowed-revision-range/expiry-bound 的短期 capability，冻结 activation operation ID、credential rotation/revocation handle；在 success/failure/suspend/timeout 所有 terminal state 都 revoke+destroy 并 backend readback 证明无 residual update/enable authority，之后才可 handover。observation safety principal/role 字面量分别为 `mycodexenv-runtime-observation-safety-v1`/`MyCodexEnvRuntimeObservationSafetyV1`；credential 仅由 backend administrator 直接签发，provenance receipt 精确绑定 backend tenant/account、role、subject、stable job ID、`read,disable,job-scoped-suspend` actions、issued/expiry、non-secret fingerprint 与 revocation handle，唯一 storage 为 `/Library/Application Support/MyCodexEnv/runtime-control/scheduler/credentials/observation-safety-v1.credential`（parent `root:wheel 0700`、file `root:wheel 0400`、ACL 空、link-count=1），禁止 env/keychain/repo/home/prompt/CLI ingress。它复用同一 sealed scheduler adapter TCB、absolute entrypoint、clean env 与 self-check，不得建立第二 adapter；仅在 mutator 撤权销毁 readback 成功后签发/激活并 seal handover receipt，任一状态不确定则保持 disabled STOP。该 capability 不含 update/enable，只在 disable 重试耗尽后调用下述既有 job-scoped suspend contract，并在每个 observation 终态立即 revoke+destroy+readback。
- suspend contract 必须在每次授权前冻结 exact backend API method/path、resource ID、job/account scope、expected revision/CAS、idempotency/operation ID、canonical request digest、affected-job inventory 与 blast radius。adapter 只能调用已证明 job-scoped 的 suspend；非 job-scoped suspend 转独立 admin containment，不由 adapter 调用。timeout、ack loss 或 readback 不确定时禁止盲重试，只读 reconcile operation audit+resource revision；仍无法裁决则进入 `unknown-state` incident、撤权并只报告 fresh observed booleans，不声称 contained。
- nullable immutable `last-known-safe-v1` 使用 records root `/Library/Application Support/MyCodexEnv/runtime-control/scheduler/last-known-safe-v1/records/` 与 record path `<record_revision>.jcs`（revision 是 canonical base-10 integer）；单签 payload exact keys=`schema_version,job_id,record_revision,previous_record_digest,value,issued_at`，其中 `schema_version`=integer `1`、`job_id`=string、`record_revision`=positive integer、`previous_record_digest`=canonical JSON null或 `sha256:<64 lowercase hex>`、`issued_at`=RFC3339 UTC second；`value` 唯一为 canonical JSON `null`（明确表示无 safe definition，只允许 disabled+normalization）或 exact object keys=`definition_envelope_digest,definition_payload_digest,definition_revision,previous_definition_revision,source_sha,engine_version,engine_bundle_digest,tcb_digest,evidence_root_digest,created_at,expires_at,freshness_seconds`，其中 digests 都是 `sha256:<64 lowercase hex>`、revision 是 positive integer且 previous revision仅 genesis可为 null、`source_sha` 是 40-char lowercase hex、`engine_version` 是 string、times 是 RFC3339 UTC seconds、`freshness_seconds`=integer `300` 且 `expires_at-created_at` 精确 300 seconds。缺文件、空文件、缺 `value`、unsigned 或任何 sentinel 都 invalid，绝不隐式表示 null；domain=`MyCodexEnv/last-known-safe/v1`，authority=existing scheduler-definition authority并由现有 `authority_key_map` 绑定。record revision 从 `1` 单调递增，genesis `previous_record_digest=null`，之后精确绑定前 record digest；unique highest valid no-replace child 才是 head，gap/fork/replay 全 fail closed。安装复用现有 artifact/evidence lifecycle 的 same-filesystem temp+file fsync+no-replace rename+parent fsync并绑定 evidence root；锁内 CAS 前按第 3.5 节 effective time验证 `created_at <= effective < expires_at` 以及 job/revision/head、fresh backend readback、definition exact bytes/digests、`SOURCE_SHA`、engine/bundle/TCB/evidence-root，任一 mismatch 只保持 disabled。必须冻结 signed-null positive 及 missing/empty/unsigned/null-sentinel/wrong-domain/key/expired/gap/fork/replay/stale/digest/partial-write negatives。
- canonical `report-only-0900-definition-v1.jcs` payload exact keys 为 `schema_version,job_id,entrypoint,argv,cwd,env,execution_principal,schedule,timezone,dst_policy,start_timeout_seconds,run_timeout_seconds,read_roots,write_roots,deny_roots,network_policy,subprocess_policy,report_destination,report_schema_digest,expected_exit_code,verdict_map,engine_version,source_sha`。exact typed values 为 `schema_version`=integer `1`、`execution_principal`=string `mycodexenv-daily-report-v1`、`schedule`=string `09:00`、`timezone`=string `America/Toronto`、`dst_policy`=object `{"ambiguous":"first","nonexistent":"skip"}`、`start_timeout_seconds`=integer `300`、`run_timeout_seconds`=integer `1800`、`network_policy`=string `deny`、`expected_exit_code`=integer `0`、`verdict_map`=object `{"0":"safe","nonzero":"unsafe_mutation"}`；`job_id`=string且唯一取 fresh signed Entry 的 `stable_job_id`，`engine_version`=string且唯一取 promotion receipt 的同名字段，`source_sha`=40-char lowercase hex string且唯一取 `SOURCE_VERIFIED` receipt 的 `remote_tip`。其余 `entrypoint`(string)、`argv`(array of strings)、`cwd`(string)、`env`(object string-to-string)、`read_roots/write_roots/deny_roots`(arrays of absolute strings)、`subprocess_policy`(object)、`report_destination`(string)、`report_schema_digest`(`sha256:<64 lowercase hex>`) 必须逐一来自 candidate-freeze receipt 的 `report_definition_fields` 同名字段，且所得 JCS digest 精确等于其中 frozen report-definition digest；禁止 fallback、env inference 或 multi-receipt merge，这不是 operator phase manifest。JCS bytes 以 domain=`MyCodexEnv/report-only-0900-definition/v1`、existing scheduler-definition authority及现有 `authority_key_map` 签名并 hash-addressed；必须冻结 positive 及 wrong-domain/key/type/value/mapping/signature/digest/stale-binding negatives。真实 execution 前后对 live/manifest/control/backup/replay/engine/Git/scheduler 做 full bytes+metadata inventory，唯一允许 delta 是该 execution ID 的 temp/report object；任一其他 delta 结果为 nonzero `unsafe_mutation` 并进入 disable-only 路径。
- 唯一状态机是：`normalized Entry(definition_enabled=false,scheduler_suspended=false) -> Phase 0 read-only verification -> Phase 5 disposable adapter tests -> Phase 6 reverify both false -> principal/role/credential provision -> adapter TCB/self-check -> update-disabled(expected-revision CAS) -> readback/diff -> disabled scheduler-context smoke -> enable(expected-revision CAS) -> bounded real 09:00 observation`。两字段是独立 booleans，不得折叠为 `disabled|suspended` enum；每步先冻结 expected revision，成功 readback 后把新 revision 传给下一步。
- entry receipt 必须分别证明 `definition_enabled=false`、`scheduler_suspended=false`，旧 queued/running execution全部 terminal且没有新 execution。`update-disabled` 只能安装由 Phase 5 template 在 Phase 6 注入 sealed values 后得到的 report-only definition，readback canonical diff必须精确等于批准字段。
- rollback boundary 是保留 `definition_enabled=false` 且 `scheduler_suspended=false`。entry/drain、CAS/readback/smoke任一 mismatch均停止；若 update-disabled 已写入但 readback/smoke失败，只允许在未suspend、definition disabled 且 valid fresh `last-known-safe-v1` 存在时 CAS 回其 exact bytes。无法 fresh 证明两个 false 或 record 无效时只保持 external runtime deny并进入独立 containment-normalization。
- enable 只在所有 final gates 后以 readback revision CAS 执行；enable 后再次 readback/diff，状态为 `rollout observation-pending`。real `09:00` observation 有预冻结开始/结束 timeout，必须关联唯一 execution ID、sealed engine/SOURCE_SHA 与 report-only evidence。
- observation failure 时唯一自动 mutation仍是最多5次/30 seconds fresh-readback→CAS-disable；耗尽后调用已实证 scheduler-level suspend并readback `scheduler_suspended=true`。一旦 suspend，本 rollout立即终止到incident/containment-normalization，不得自动unsuspend、enable、继续09:00或从中间Phase恢复；必须由独立scope产生全新normalized Entry receipt后从计划入口重启。

### 3.10 Cryptographic artifact 与 atomic evidence contract

所有以下 artifact 均是 RFC 8785 JCS UTF-8、pure Ed25519，签名消息为 `ASCII(domain)||0x0A||JCS(payload)`。单签 artifact envelope 精确只含 `payload,signature`；trust policy 双签 envelope 精确只含 `payload,signatures`，`signatures` 恰好两个按 `key_id` UTF-8 byte order 排序的 `{key_id,role,signature}`，roles 恰好为 `current,new`，duplicate key 拒绝且两签都必须通过；positive 与 order/role/count/duplicate/one-signature-invalid negative vectors 必须冻结。所有 envelope/payload 拒绝 unknown/missing keys：approval 使用第 3.5 节 exact schema/domain/key authority；trust policy schema=`schema_version,policy_epoch,issuer,keys,actions,activation_time,revocations,previous_digest`、domain=`MyCodexEnv/trust-policy/v1`、authority=当前 key+新 key 双签；bootstrap/TCB schema=`schema_version,provision_transaction_id,artifact_provenance,authority_key_map,entries,write_set,genesis_policy_digest,activation`、domain=`MyCodexEnv/bootstrap-tcb/v1`、authority=installer authority；report definition 与 last-known-safe 分别使用第 3.9 节 exact schema/domain，authority 均为 existing scheduler-definition authority；active-version exact keys=`schema_version,provision_transaction_id,record_revision,previous_record_digest,bootstrap_tcb_digest,trust_policy_digest,authority_key_map_digest,activated_at,signer_key_id`（schema=integer `1`、transaction=canonical UUID、revision=positive integer、previous=null或 sha256、digests=sha256、time=RFC3339 UTC second、key ID=ed25519-sha256）、domain=`MyCodexEnv/active-version/v1`、authority=installer authority；provision receipt exact keys=`schema_version,provision_transaction_id,provisioning_principal,installer_authority_key_id,artifact_provenance_digest,bootstrap_tcb_digest,write_set_before_digest,write_set_after_digest,genesis_policy_digest,policy_epoch,active_version_record_digest,seal_receipt_digest,self_check_receipt_digest,credential_revocation_readback_digest,timestamp`（schema=integer `1`、transaction=canonical UUID、principal/key ID=strings、digests=sha256、epoch=positive integer、timestamp=RFC3339 UTC second）、domain=`MyCodexEnv/provision-receipt/v1`、authority=installer authority；publication approval schema=`schema_version,server,account,namespace,repository_id,fetch_endpoint,push_endpoint,source_refspec,destination_refspec,principal_fingerprint,credential_fingerprint,expected_old,candidate_sha,candidate_tree,candidate_gate_root,branch_policy_digest,authority_key_id,issued_at,expiry,nonce,transaction_id`，publication transition receipt schema=前述 approval 全部字段加 `state,remote_tip,receive_result,previous_receipt_digest,fetch_readback_digest,ls_remote_readback_digest,branch_policy_readback_digest` 并遵守第 3.2 节 state-dependent null/digest contract，domain 分别为 `MyCodexEnv/publication-approval/v1` 和 `MyCodexEnv/publication-receipt/v1`、authority 分别为 release authority 与 publisher；promotion receipt schema=`schema_version,transaction_id,source_sha,engine_version,engine_bundle_digest,tcb_digest,activation_record_digest`、domain=`MyCodexEnv/promotion-receipt/v1`、authority=external owner；atomic evidence root schema=`schema_version,transaction_id,required_entry_manifest,claims,previous_root_digest,root_digest,signer_key_id,timestamp`、domain=`MyCodexEnv/evidence-root/v1`、authority=evidence sealer，`root_digest` 唯一算法是 `sha256:` + lowercase hex `SHA-256(JCS(payload_without_root_digest))`，仅排除 `root_digest` 本字段，其他字段全部参与，并冻结 positive 与 wrong-prefix/missing-field/extra-exclusion/self-reference negative vectors。

bootstrap TCB manifest、active-version 与 provision receipt 的 genesis 是 external installer authority 及 bootstrap manifest 内冻结的 installer key/`authority_key_map`；provision receipt 验证完成后，其 digest/policy epoch 才是所有 post-provision profiles 的 genesis。每条 chain 的 head 是现有 no-replace chain 的唯一 highest valid record；同 previous digest 的多个 child 是 fork、旧 nonce/transaction/root 是 replay，两者均 fail closed。现有 `authority_key_map` 必须新增并逐一绑定 `scheduler-definition/report-definition`、`scheduler-definition/last-known-safe`、`installer/active-version`、`installer/provision-receipt` 的 allowed domain/key IDs/actions；全部 profile 复用 existing epoch/rotation/revocation/lock/replay/evidence-root，cross-domain/action substitution 拒绝，不建立第二套信任系统。每个 profile 实施时必须在任何授权前冻结 exact payload bytes、domain+payload message bytes、public key/key ID、signature、expected digest 的 positive golden vector及 wrong-domain/key/signature/schema/previous/epoch/fork/replay/state/null/type/value/mapping negatives。approval accept 与 policy rotate/revoke 按第 3.5 节共用 lock+exact policy digest/epoch，不新增控制面。

atomic evidence index 中每个 claim 必须精确含 `claim_id,predicate,before,action,after,failure,rollback,receipt_id,artifact_digest,causal_parent`；`required_entry_manifest` 预先列出 phase 必需 claim IDs/schema/digests，缺项不能 seal。index/root 以现有 same-filesystem temp+fsync+no-replace rename+parent-fsync 原子安装并签名，independent verifier 从 artifact digests 重算每个 predicate、causal DAG 和 root；第 2 节 incident artifact IDs/digests 是必需 entries，无锚点项仅保留 `input_assumption`。

## 4. 实施阶段与 phase gates

### Provision prerequisite：out-of-band bootstrap TCB genesis

Provision 是 Phase 0 之前的独立、一次性安装边界，不由 repo code、scheduler、daily refresh 或本计划 launcher 自我创建。owner 是独立 platform installer administrator；provisioning principal 是短期 `mycodexenv-bootstrap-installer-v1`，authority 只允许单个 `provision_transaction_id`、单个预冻结 revision 与下列 exact write set：`/Library/Application Support/MyCodexEnv/runtime-control/` 下的 launcher/bootstrap verifier、versioned bootstrap TCB bundle+manifest、trust policy genesis+policy-state genesis、lock/replay/receipt/backup/engine/scheduler parent roots 及一份 provision receipt；不写 live `/Users/kezheng/.codex`、Git repo/refs、scheduler job 或 credential store，也不安装 runtime payload。

inputs 必须是 external installer authority 验签的 `bootstrap-tcb-manifest-v1`：它冻结 installer package provenance（issuer/build ID/source commit/artifact URL 与 content digests）、每个 bootstrap executable/import/library/config 的 absolute path/type/owner/group/mode/content SHA-256、初始 Ed25519 public key/key ID、trust-policy canonical bytes/digest/epoch=`1`、所有 target parent identities 与 exact write set；其现有 `authority_key_map` 必须逐一绑定 runtime approval、trust current/new、installer、release approval、publisher receipt、external-owner promotion、evidence sealer，以及第 3.10 节 scheduler-definition/report-definition、scheduler-definition/last-known-safe、installer/active-version、installer/provision-receipt 的 key IDs、allowed domains/actions、epoch、rotation/revocation state，任何 cross-domain/action substitution 拒绝。private signing key 不进 host。installer 先在与 active roots 不共享 parent/mount/bind/symlink 的 disposable root 验证 golden vectors，再以 same-filesystem staging、file fsync、no-replace rename、parent fsync 逐个安装；唯一 activation point 是 no-replace 安装第 3.10 节 exact signed active-version record，随后 seal owner/mode/ACL/flags并从 sealed absolute verifier 执行 read-only self-check。

PASS output 是第 3.10 节 exact signed/hash-addressed provision receipt；其 `credential_revocation_readback_digest` 必须绑定终态 revoke+destroy 后的 backend/OS readback，并与 transaction/principal/authority、artifact provenance/TCB、write-set before/after、genesis policy digest/epoch、active-version、seal/self-check digests 一并验签。activation 前失败必须按 installer WAL 恢复 exact before-state；activation 后 self-check 失败则封锁 corridor、保留 forensic artifacts、由独立 forward installer 安装新 version，不就地覆盖。所有终态（success/failure/timeout）都必须 revoke+destroy bootstrap credential/capability 并以 backend/OS readback 证明 provisioning principal 再无 write/activate authority；无法证明 rollback 或撤权时 terminal STOP，Phase 0 不开始。

### Entry prerequisite：out-of-band emergency containment

本计划开始前，backend administrator签发的 Entry receipt 必须把两个字段分别记录为 `definition_enabled=false` 与 `scheduler_suspended=false`；同时证明所有旧 mutation principals/credentials已撤销，queued/running executions全部terminal且fresh readback无新 execution。receipt包含 backend identity/stable job ID/definition revision+digest、两个布尔字段、execution inventory、撤权结果及fresh四字段与独立backend readback。

若只有 suspend、definition仍enabled，或 `scheduler_suspended=true`，一律STOP到独立 backend-admin containment-normalization scope：保持 suspend时先把definition禁用并drain/readback；再按独立影响面与授权解除suspend，account-level suspension必须先冻结unrelated-job inventory和影响证明；最后fresh readback仍须 `definition_enabled=false`、`scheduler_suspended=false`并重新签发Entry receipt。主计划/adapter永不拥有常规unsuspend/resume权限；normalization不是第二个常规mutator，也不授权后续update/enable。

### Phase 0：只读验证 containment 与 external-owner control plane

Phase 0 只以 backend read-only API重新验证 Entry 的 `definition_enabled=false`、`scheduler_suspended=false`、stable job identity/revision/digest、旧 principals撤销、executions全terminal且无新 execution；不得接受合并enum。同时只读验证 Provision receipt、bootstrap TCB/provenance/digests、active-version seal、genesis policy digest/epoch、self-check 和 bootstrap authority revocation。任一不符即STOP回独立 containment-normalization 或 forward provisioning scope。Phase 0不调用adapter、不provision authority、不生成 key/policy、不执行任何真实scheduler/control/live mutation。验证通过后冻结 canonical dirty-main/live before inventory；其余 discovery只读记录 confinement、launcher、owner/entrypoint/process identity、trust/lock/replay/receipt/backup/engine roots与TCB schema。

同一 Phase 只读冻结 approval profile v1 的 actual initial public key/key ID、issuer/action/TTL policy与 exact JCS/signature golden receipt，只读验证 trust policy version/rotation/revocation/rollback chain、wall+monotonic/boot-ID provider及 2-second clock algorithm。no-replace/crash 语义只在 disposable、capability-equivalent same-filesystem fixture 上实证；primitive/clock/rollback protection 任一不能证明即在首个 replay/control write前 kill gate。

用 fixtures 证明 direct `cp/rsync/rm/old-normal-sync` negatives、clone/report/log/temp positives、deny precedence、child/symlink/hardlink/path replacement escape resistance，以及旧 identity 无法写 control plane/engine root。所有 create/truncate/rename/delete/chmod/write probe 只能在 capability-equivalent、never-activated disposable fixtures 上执行；fixture roots 与真实 active bundle/control/live/backup/replay roots 不共享 parent、mount、bind 或 symlink，且不能通过 hardlink/fd 指向真实对象。对真实 surfaces 只允许即使成功也不会改变 bytes/metadata 的 read-only open/stat/hash/list/capability introspection，前后 inventory 必须 zero-change；禁止任何 mutation attempt，包括“预计会被拒绝”的 attempt。冻结并验证四类 control/bundle mode、external system executable 分类、absolute launcher/interpreter/helper paths、`cwd`、`umask`、clean env、Python isolation/import roots、Git/helper config/hooks/alias/pager denial、所有 TCB category/owner/mode/digest predicates；任一依赖仍来自 user-writable path、类别不明或无法枚举即触发 kill gate并保持 automation paused。

### Phase 1：lineage gate 与 baseline

在选择 baseline 或创建 checkout 前，创建 clean isolated release repo，按第 3.2 节以 transaction-scoped named ref 执行全套 origin/fetch/`ls-remote`/matrix gate，冻结 `REMOTE_BASE_SHA` 和 canonical local-only full inventory；不得使用 `FETCH_HEAD`、tracking cache或修改 canonical Git metadata。

冻结 W6a payload provenance commit=`010e894e1b2e63ac00aded2c749e68b649f0ac74`。`payload-provenance-v1` receipt 必须分别从 provenance commit、`REMOTE_BASE_SHA`、frozen candidate 与 post-publish `SOURCE_SHA` 的 commit objects 读取第 3.4 节 15 paths，并证明四点 tree entry/type/mode/blob OID/content SHA-256/golden digest 完全相等；publish 前必须完成前三点，publish 后补第四点。任一不匹配、provenance commit 不可达或 object missing 即 STOP，转入独立 source-governance/publish scope；禁止从 canonical dirty working tree、local-only commit或 runtime 搬运 payload。全部通过后才只从 `REMOTE_BASE_SHA` 创建 clean checkout。PASS 要求 isolated ref/object、payload provenance、local-only mechanical+independent semantic exclusion 与 dirty-main fingerprint receipts 四字段完整。

### Phase 2：red regressions 与 C1

先增加 isolated named-ref fetch/local-only inventory、lineage CAS、source transition matrix/downgrade、approval profile/clock/watermark/replay、scheduler authority/revision-CAS/drain/readback/suspend、lock race、path replacement/no-follow、15-path provenance/digest、one-shot transaction、deterministic capacity/reservation/WAL/fsync、fault/restart、TCB manifest/bundle/source binding、disposable destructive fixture 与 PATH/PYTHONPATH/import/config/hooks/cwd injection、plugin split、confinement/evidence tests，并在旧实现精确 red。C1 approval golden vectors 必须内嵌 exact JCS payload bytes、fixed domain+payload signing-message bytes、public key/key ID、Ed25519 signature 与成功 verdict；负例覆盖 duplicate key、BOM、non-I-JSON/noncanonical bytes、unknown keys/version/issuer/action、wrong domain/algorithm/encoding/key ID、revoked/rotated key、TTL/window/2-second boundary、same-boot/reboot/clock rollback、watermark chain gap。另覆盖 mutating `CLAIMED -> ABORTED_BEFORE_PREPARE`、equal `NOOP_COMMITTED` exactly-one authoritative四字段 schema/decision timestamp/五个 crash boundary，以及 sequential/concurrent replay的zero engine durable write+四字段 caller response/out-of-band collector。C1 parent=base、tree 必须变化；保存 review/test receipt。

### Phase 3：read-only guard 与 C2

实现唯一 shared guard、RFC 8785 JCS byte validator、Ed25519/key-ID/trust-policy verifier、trusted-time/rollback-watermark decision、immutable replay record parser/state machine、NOOP authoritative四字段 schema与 deterministic redaction/bounds、allowlist digest、含 engine/TCB binding 的 signed validation、manifest-present transition matrix、missing-manifest `old_source_sha=null` 语义、只读 TCB verifier、external-lock 后完整 mutable preflight 与 path identity checks；获锁、claim/no-op install、首写前均重新验证。C2 只实现 canonical record/response生成与 read-only verdict，不写 live/manifest/control plane；任何 invalid/partial/ambiguous claim或 no-op state fail closed。所有拒绝在允许的首个 control/transaction write前 nonzero+zero-write；C2 parent=C1、tree 变化、review/tests 独立。

### Phase 4：C3 transaction 与 C4 plugin split

实现 mutating action 的 durable `CLAIMED` no-replace install、CLAIMED-without-PREPARED 的 sealed `ABORTED_BEFORE_PREPARE` restart，以及 equal action exactly-one authoritative `NOOP_COMMITTED`四字段 install；claim/no-op record 同时原子推进 replay/watermark。equal logical success仅在 final+parent fsync后成立，restart不得生成第二 success receipt；replay loser只返回四字段 response且engine zero durable write。只有 durable mutating claim 后才实现 one-shot 15-path recovery+manifest、forward transition与独立 `approved-immutable-downgrade`，全部复用同一 engine；实现 empty-temp bootstrap、deterministic per-filesystem capacity/reservation、冻结 owner/mode/ACL/link-count 的 fixed-root immutable backup、逐 surface receipts，以及第 3.6 节 exact WAL/fsync/crash/restart protocol。manifest rename 为唯一 file-transaction commit point，restart 只能收敛到 before-state 或 committed after-state；invalid replay state进入incident。完成 plugin/MCP split。C3 parent=C2、C4 parent=C3；各有不同 tree、review 与 targeted tests。

### Phase 5：report-only automation、C5/C6 与 pre-publish gate

Daily refresh 只保留：

```text
standalone clone -> empty temporary Codex home -> reproduction verification
live ~/.codex    -> read-only parity audit -> blocker/evidence
```

删除 live repair/promotion 与 unattended rebase/merge/push/force-push。旧 identity 下 normal/force/direct `cp/rsync/rm` 必须 nonzero+live zero-write；temp full sync/manifest 和 report/log 写成功；双进程仅一者进入。C5 接入 external-owner launcher、engine promotion manifest 与 clean-exec contract，但不复制 engine transaction semantics。

在 clean development checkout 中，C5/C6 只实现唯一 adapter、authority verifier、report-only renderer、only-disable loop与 terminal suspend/readback；明确无unsuspend/resume能力。全部 mutation tests只针对disposable backend fixture，并证明suspend后状态机终止、只能凭全新normalized Entry从入口重启；真实job zero mutation。完成后核验单链parent/tree/review/tests/no-empty与pre-publish remote=base。

publish 前必须在 clean detached frozen-candidate checkout、以 candidate-built empty temp home 运行 Phase 9 同一 full gate、15-path reproduction、前三点 payload provenance 与 local-only mechanical+independent semantic exclusion；同一 host image/toolchain/env 先对 `REMOTE_BASE_SHA` 运行同一 gate manifest以分类既有 baseline/live drift。任何 candidate-associated failure 一律阻止 signed approval 与 publish；既有 live/runtime 红灯不得充当 waiver。

### Phase 6：CAS publish 与 immutable source

Publication Contract v1 的 signed approval 验证通过后，才以 expected-old=`REMOTE_BASE_SHA` 的 lease publish唯一 candidate；先验证 fast-forward，失败即 STOP。push receive 成功立即进入 `SOURCE_PUBLISHED_UNVERIFIED`；发布后在 isolated release repo 以新的 transaction-scoped named ref fresh fetch/`ls-remote`，冻结 `SOURCE_SHA=candidate`，补齐第四点 payload provenance，并验证 remote/fetched/local/detached 五者相等以及 canonical dirty-main bytes/index/untracked、local-only full inventory/object reachability均不变。全部通过才进入 `SOURCE_VERIFIED`；失败按第 3.2 节只允许 forward repair。isolated ref/object before/after receipt 完整后才清理 isolated repo；不修改 canonical Git metadata。

随后仅由 external owner 接受独立 signed one-shot action=`promote-engine-bundle`：从 `SOURCE_SHA` 的 verified objects 构建同一 reviewed engine bundle与 recovery payload，按冻结类别设置 mode，生成包含实际 category+mode 的 TCB manifest/digests，安装到全新 versioned engine root并写 immutable promotion receipt。agent/普通 invoking user不得自行写 control plane；version 已存在、source object 不匹配、dependency provenance 不闭合或 category/owner/mode/digest 不符即 STOP。promotion action 不执行 runtime recovery，也不实现第二套 transaction semantics。

promotion 成功后、任何 maintenance corridor 打开前，external-owner service 必须从 sealed version root、以 manifest 冻结的 absolute interpreter/executable 运行 read-only `self-check`。该 probe 必须 `exit_code == 0` 并精确验证 `engine_version`、`engine_bundle_digest`、`tcb_digest`、`SOURCE_SHA`/source-object binding；before/after 证明 live/control/backup/replay 零写入，同时旧 identity 对 executable/bundle 的修改 probe 仍 nonzero+zero-write。self-check 失败则该 version 不可激活，corridor 保持关闭。

self-check 通过后，Phase 6先fresh readback再次要求 `definition_enabled=false`、`scheduler_suspended=false`且Entry lineage未漂移；任一不符STOP到normalization。随后admin才provision唯一authority/denylist，ACL明确deny unsuspend/resume并证明其他principals无mutation权；adapter TCB/self-check后才首次真实执行`update-disabled` CAS，随即readback canonical diff并运行disabled scheduler-context smoke，证明只写temp/report、live/control zero-change。失败保持definition disabled且不suspend，禁止第二mutator/bypass或旧definition回滚。

### Phase 7：one-shot live recovery + manifest bootstrap

external-owner service 先验证 recovery approval、Phase 6 promotion receipt与 fresh positive self-check receipt，逐项复算 TCB/source/category/mode bindings并建立 clean execution context；只有全部通过才允许 launcher 打开 corridor、nonblocking 获锁、完整重跑 mutable preflight。mutating `CLAIMED` record no-replace install并 parent fsync成功后，才允许创建 transaction child/PREPARED；随后从 absolute versioned root 执行 C3 shared engine，在一个 transaction 恢复 strict 15 paths + manifest。不得从 checkout/cwd/user path import/execute。commit point 前验证 15/15、四 hooks、逐 surface receipts、非目标/canonical dirty main 零变化、backup hashes、remote 与 TCB binding。成功后才人工执行 plugin/MCP reconciliation；任一失败保持 automation paused。

### Phase 8：fresh adversarial 与 fault rerun

在旧 identity 下 fresh 重跑 normal/force/cp/rsync/rm negatives、temp/report positives、lock contention、approval exact JCS/domain/Ed25519/key-ID/issuer/action/TTL/trust rotation/revocation、same-boot/reboot/clock rollback、mutating CLAIMED/no-PREPARED/partial-state、equal NOOP_COMMITTED exactly-one success receipt/sealed decision timestamp/sequential+concurrent zero-engine-write reject response与五个 crash boundary、独立 evidence collector、source transition/downgrade、scheduler principal/credential/ACL/denylist bypass、only-disable conflict/suspend、path replacement、backup pre-existence/capacity/reservation/race/ENOSPC/owner/mode/ACL/link-count，以及 copy/delete/receipt/restore/data-rename/manifest-rename/fsync/crash/restart faults。

真实 active sealed bundle/control/live 只做成功也不会改变 bytes/metadata 的 read-only open/stat/hash/list/capability introspection，并以 inode/mode/hash/inventory before/after 证明 zero-change；禁止任何可能成功的 mutation attempt。corrupted-version verifier rejection、copy/delete/crash/fsync fault injection 及任何实际篡改/替换 engine bundle、interpreter/helper、execute/write bit、category/mode 的测试，只能在全新 disposable、never-activated、独立 fixture roots 执行；fixture path 必须不与真实 active/live/control/backup/replay roots共享 parent、mount bind或 symlink。每个 probe 前后同时证明真实 active/live/control/backup/replay inode/mode/hash/inventory zero-change。另在 fixture 中逐项测试 `PATH`、`PYTHONPATH`、import roots、config、Git hooks与 `cwd` injection；每项必须在 corridor/首个 privileged write 前 nonzero。fresh positive active self-check 仍须 exit 0+zero-write。每项独立四字段 receipt，不复用 Phase 0/5 evidence。

### Phase 9：final gates、重新启用与独立观察

所有 repo/full-gate 命令的 `cwd` 必须是 clean detached `SOURCE_SHA` checkout；不得从 canonical dirty main、automation clone 或 runtime 目录运行。fresh 运行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 test_runner.py
PYTHONDONTWRITEBYTECODE=1 ./scripts/verify_codex_env.sh \
  --repo-root "$(pwd)" \
  --codex-home "$HOME/.codex" \
  --claude-home "$HOME/.claude"
codex plugin list
codex mcp list
codex doctor
python3 scripts/harness_ledger.py verify --ledger "<approved-ledger-path>"
```

repo tests/verify 必须 exit 0。plugin/MCP/doctor 与预先冻结 normalized expected state 无未批准 diff；ledger 独立 verify exit 0。

W3 checkpoint 必须使用以下 helper CLI；执行前把每个 `<...>` 替换为本次 fresh evidence 的实际值：

```bash
python3 scripts/harness_checkpoint.py append \
  --repo-root "$(pwd)" \
  --phase "<verified-phase>" \
  --summary "<verified-checkpoint-summary>" \
  --changed-surface "<comma-separated-approved-paths>" \
  --verification-command "<exact-verification-command>" \
  --verification-exit-code "<integer-exit-code>" \
  --verification-key-output "<bounded-deterministic-key-output>" \
  --next-safe-task "<one-next-safe-task>" \
  --compaction-ordinal "<integer-compaction-ordinal>" \
  --transition-key "<stable-transition-key>" \
  --gate-decision "<continue-to-boundary|immediate-successor|none>"
```

helper 成功后必须由独立 read-only parser 重新解析 `docs/harness-state.md`，精确验证 event、phase、`compaction_ordinal`、`transition_key`、`gate_decision`、helper timestamp 和关联 receipts；append 成功不能自证 W3 有效。

final gate 再核对 remote SHA、manifest、15/15、非目标runtime、canonical dirty/local-only objects、backup/control-plane/engine ownership、approval/replay chain、promotion/TCB/source binding、scheduler authority/denylist与confinement；enable前readback必须为 `definition_enabled=false`、`scheduler_suspended=false`。全绿才由唯一adapter CAS enable并进入observation。only-disable耗尽并suspend后，P9/09:00立即终止到incident/normalization；不得自动unsuspend、enable、继续观察或从当前phase恢复。只有独立scope产生全新两个false的Entry receipt后，才能从计划入口重新开始。

## 5. 统一证据契约与 gate matrix

每个 gate/probe/command/observation 单独保存：

```yaml
command: <exact argv plus cwd/env, secrets redacted>
exit_code: <integer>
key_output: <bounded deterministic assertion output>
timestamp: <RFC3339 completion time with offset>
```

四字段缺一即 `UNVERIFIED`；一个 receipt 只证明一个 gate；PASS predicate 与 expected snapshot 必须在运行前冻结。

equal 首次成功时，durable `NOOP_COMMITTED` record 本身就是唯一 authoritative receipt：其中 canonical `command={argv,cwd,env}`、`exit_code=0`、bounded deterministic `key_output` 与 sealed RFC3339 decision-completion `timestamp` 不得复制到第二个 success artifact。rejected sequential/concurrent replay 的 engine/control surfaces必须zero durable write；其四字段 caller response仅由调用 probe 的独立 harness/evidence collector持久化。生产无 collector时允许没有 persistent reject receipt，不能为了统一审计而让 engine 写 reject log；P2/P4/P8 negative gate的 fresh evidence由 out-of-band harness receipt满足。

| Gate | Deterministic PASS |
|---|---|
| Entry containment | receipt分别为`definition_enabled=false`、`scheduler_suspended=false`，旧principals撤销、executions drained；任一不符先独立normalization并重签Entry |
| P0 control plane/TCB | 只读复核两个false与Entry lineage，无 adapter/provision/mutation；其余approval/TCB/zero-change probes通过 |
| P1 lineage | isolated named ref fetch 与 refs/objects before/after 完整；origin 唯一；`ls-remote`/matrix/local-only inventory/exclusion 冻结；无 shallow/diverged/unknown/rewrite；REMOTE_BASE 含 payload provenance 且 15 OID/content/digest 匹配；checkout=base |
| P2 C1 | approval vectors、CLAIMED、NOOP exactly-one四字段/decision-time/crash/replay zero-write response+collector和 scheduler disposable reds 精确失败；parent/tree/review/test完整 |
| P3 C2 | approval/replay read-only verdict与 NOOP canonical authoritative record/caller-response schema通过；reject在允许首写前zero-write；invalid/ambiguous fail closed |
| P4 C3-C4 | mutating claim顺序正确；equal exactly-one `NOOP_COMMITTED`成功receipt，restart不重复；replay loser engine zero durable write且 harness保存四字段response；其余 transaction/plugin gates通过 |
| P5 C5-C6 | disposable tests证明adapter无unsuspend/resume，suspend后terminal且须new Entry重启；真实job zero mutation；remote=base |
| P6 publish/promotion | provision前再次readback两个false；authority deny unsuspend/others，adapter self-check后首次update-disabled CAS/readback/smoke通过 |
| P7 recovery | corridor 前 TCB/approval/promotion 全验证；versioned engine 执行 strict 15/15+manifest；backup/surface/non-target/SHA/digest/replay/plugin 正确 |
| P8 adversarial | NOOP exactly-one success、sealed decision time、reject zero-engine-write+out-of-band collector，以及 approval/replay/scheduler authority negatives fresh；真实 surfaces零变化 |
| P9 final | enable前两个false；only-disable耗尽触发suspend即本rollout终止，禁止unsuspend/enable/续跑，须独立normalization+new Entry |
| 09:00 | bounded execution只读、15/15；failure only-disable耗尽后suspend并终止，不能继续观察；fresh四字段完整 |

## 6. 独立可测、可回退 commit map

| ID / commit message | 内容边界 | 独立测试 | 回退边界 |
|---|---|---|---|
| C1 `test: pin runtime rollback safety contracts` | 只加 isolated lineage、approval exact golden/negative vectors、CLAIMED/NOOP crash+replay、scheduler authority/CAS/suspend、transaction/TCB/confinement red fixtures | exact bytes/signature greens仅对独立 vector verifier；旧实现其余精确 red；harness self-test green | 可单独 revert；不改变 runtime 行为 |
| C2 `harden sync source identity and approval preflight` | shared read-only guard、JCS/Ed25519/key-ID/trust/time/watermark/replay verdict、identity/digest、source transition/TCB、lock-held preflight；无 live/control write | approval/trust/time/replay/transition/TCB/lock/path suite + three-timing zero-write verifier | 先 revert C3-C6，再 revert C2；本 commit 无 live migration |
| C3 `make runtime file sync journaled and recoverable` | CLAIMED/ABORTED_BEFORE_PREPARE/NOOP_COMMITTED、inventory、reservation、sealed backup、exact WAL/fsync、15-path recovery/forward/downgrade+manifest、recovery | claim/no-op concurrent+crash、capacity/ENOSPC、transaction/fsync/fault/restart matrix；只产生规定 terminal states | live schema promotion 后不得直接 revert；先用同版本 recovery 收敛 active/recovery-required transaction，再按批准 runbook 回退；不得倒退 remote ref |
| C4 `separate plugin reconciliation from file sync` | expected snapshot/diff 与 distinct failure state | CLI failure/idempotency tests；不改 manifest/runtime | 仅在无 active reconciliation 时 revert；file transaction 保持有效 |
| C5 `make daily refresh report-only under confinement` | clean checkout实现adapter/authority/denylist；无真实credential/job mutation；无unsuspend/resume | disposable CAS/only-disable/suspend-terminal/new-Entry-restart + old negatives；真实job zero mutation | 仅两个false的Entry仍有效时可revert；不得恢复危险definition |
| C6 `document runtime rollback gates and receipts` | docs、scheduler expected definition/state、ledger/W3/final wiring | docs/config、scheduler digest/readback、ledger/W3 verifier、full gates | 可单独 revert 文档 wiring；不得把文档回退当作 runtime/scheduler rollback |

每 commit 必须 parent=前一节点、before/after tree 不同，并有四字段、review、targeted-test receipt；tree 相同则 no-op 不 commit。任何失败只回退 clean-checkout 当前 change，不 reset canonical dirty main，不改写已发布 history。

## 7. 验收清单

- [ ] Entry receipt分别记录`definition_enabled=false`与`scheduler_suspended=false`，并证明旧principals revoked、executions drained；未使用合并enum。
- [ ] suspended或definition enabled时已STOP到独立normalization：保持suspend先disable+drain，按影响面授权解除suspend（account-level含unrelated-job inventory），fresh两个false后重签Entry。
- [ ] Phase 0只读复核两个false；C5仅disposable且adapter无unsuspend/resume；Phase 6 provision和首次update-disabled前再次证明两个false及旧principals denied。
- [ ] only-disable耗尽触发suspend后本rollout立即终止，未自动unsuspend/enable/继续09:00；只有独立normalization签发全新Entry后才从入口重启。
- [ ] baseline/commit/publish 前 isolated named-ref lineage gates 与 refs/object receipts 完整；不使用 `FETCH_HEAD`/tracking cache，不修改 canonical Git metadata。
- [ ] `remote_ancestor_of_local` 时 local-only机械集合与独立 semantic reviewer receipt 完整；publish 前后 dirty bytes/index/untracked、inventory/object reachability不变，post ancestry 等于冻结图。
- [ ] provenance commit、REMOTE_BASE、candidate、SOURCE_SHA 四点 15-path tree entry/type/mode/OID/content/digest 完全相等；candidate 失败已在 publish 前 STOP。
- [ ] C1-C6 无环单链，parent/tree/review/tests/no-empty 与 CAS lease 完整。
- [ ] 15-path table、baseline、type/mode/OID/content/golden digest 全匹配；不一致即重修计划。
- [ ] approval schema=1，RFC 8785 JCS UTF-8 exact bytes、fixed ASCII domain、RFC 8032 pure Ed25519、hex key/signature encoding、deterministic key ID、issuer=`mycodexenv-runtime-control-v1`与 exact action/target/600s-or-300s TTL table均由 C1 golden vectors固定；duplicate/BOM/non-I-JSON/noncanonical/错误签名负例通过。
- [ ] root-owned trust policy path/owner/mode/ACL/version、cross-signed 24h rotation、permanent revocation与 monotonic policy-state rollback protection实证；actual public-key fingerprint receipt完整且 private key未进入 host/repo。
- [ ] wall+monotonic effective-time、2-second tolerance、same-boot/reboot/clock-rollback算法与 immutable watermark chain实证；automation identity 永拒，missing manifest 仅接受 `old_source_sha=null`。
- [ ] approval/time/watermark/TCB 在获锁、claim/no-op install、首写前均 fresh 验证；unknown/tampered/expired/replayed/binding mismatch 在允许的首个 control write前零写拒绝。
- [ ] mutating approval 以 same-filesystem temp+fsync+`renameatx_np(RENAME_EXCL)`+parent fsync durable install `CLAIMED`并同时推进 watermark，之后才创建 transaction child/PREPARED；CLAIMED-without-PREPARED restart zero-change后sealed为`ABORTED_BEFORE_PREPARE`，old approval永久消费，partial/invalid/ambiguous fail closed。
- [ ] equal 首次成功 exactly one `NOOP_COMMITTED` authoritative receipt包含 canonical-redacted argv/cwd/env、exit 0、bounded key output、sealed RFC3339 decision-completion timestamp；logical success仅 final+parent fsync后成立，restart沿用timestamp且不生成第二success receipt。
- [ ] sequential/concurrent replay loser 对 replay/control/live/backup/WAL zero durable write，只返回四字段 caller response；negative gate由独立 harness/collector在disposable evidence root保存，生产无collector时未强写 persistent reject receipt。
- [ ] manifest-present transition matrix 满足 equal=no-op、forward=expected-old CAS+ancestry+fresh remote binding；diverged/unknown/missing/rewrite 全 STOP。
- [ ] emergency downgrade 复用同一 runtime-approval profile/domain/issuer/authority map/lock/policy epoch/watermark chain，仅以 exact action、300s TTL、per-action key IDs 与 action-prefixed replay key 分隔；target 仅为已发布 immutable commit，复用同一 engine 完成 backup/WAL/manifest/replay/restart/postcondition；normal/force 拒绝，remote ref 未倒退，优先 forward revert。
- [ ] lock 前仅静态检查；锁后重跑 mutable-state preflight；双进程仅一者进入。
- [ ] trust/lock/replay/receipt/backup 不可被旧 identity 修改；launcher 退出自动恢复 deny。
- [ ] mode schema 精确分类并冻结：control/version dirs `root:wheel 0700`、immutable owner-executable bundle files `0500`、immutable non-executable bundle data/config/import sources `0400`、mutable control state `0600`；external system executable 仅接受 manifest 中 absolute root-owned `0555`/等强 non-writable mode。invoking user/group 全部无 write；不符即 kill gate。
- [ ] privileged launcher 不从 checkout/cwd/user-writable path 加载代码；同一 reviewed engine 只从 immutable versioned external-owner bundle 执行，无第二套 transaction semantics。
- [ ] TCB manifest/promotion receipt 覆盖 launcher、engine、interpreter、全部 imports/libraries、absolute helpers、config 的实际 category/owner/mode/hash 与 `SOURCE_SHA` object binding；approval 绑定 engine version/bundle/TCB digests。
- [ ] promotion 后、corridor 前从 sealed version root/absolute interpreter 执行 read-only self-check，exit 0且验证 engine/bundle/TCB/source binding、全 surface zero-write；旧 identity 无法修改 executable/bundle。
- [ ] absolute exec、clean env/cwd、`umask 077`、Python isolation/root-owned imports、Git/helper config/hooks/alias/pager denial 均在 Phase 0 实证。
- [ ] post-publish engine promotion 仅由 signed external-owner action 执行并有 immutable receipt；agent/普通 user 无 control-plane promotion authority。
- [ ] engine/interpreter/helper/env/import/config/hooks/cwd tamper、移除 execute bit、增加 user/group write bit、category/mode mismatch 任一在 corridor 前 nonzero + live/control/backup/replay zero-write。
- [ ] no-follow/path identity 防 symlink/hardlink/mount/parent replacement。
- [ ] recovery 与 manifest bootstrap 是同一 transaction；没有 recovery-only 或 metadata-only 成功路径。
- [ ] fixed backup root 每事务新 child；per-filesystem `required_free` formula、10%/1 GiB margin、preallocated reservation、race/ENOSPC/cleanup 语义均验证。
- [ ] backup child/payload/metadata/journal/receipt/reservation owner/group/mode/ACL/link-count 精确匹配；commit 后 sealed 不可覆盖/复用/删除。
- [ ] root/hooks/runtime/skills 的 created/overwritten/deleted receipts 完整。
- [ ] WAL/backup/staging/target/manifest/parent-directory fsync 按确定顺序执行；durable states 与每个 crash boundary verdict 完整，最终仅 exact before-state 或 committed after-state。
- [ ] plugin/MCP 与 file transaction 分离；canonical dirty main 与非目标 runtime 零变化。
- [ ] Phase 0/8 对 active sealed/control/live 只做成功也零修改的只读 introspection；全部 mutation/fault 仅在 disposable never-activated 独立 roots，真实 active/live/control/backup/replay 前后零变化。
- [ ] Phase 5/8 old-identity negatives 和 temp/report positives fresh 通过。
- [ ] repo tests/verify、plugin/MCP/doctor、ledger、W3 与全部四字段 receipt 通过。
- [ ] 状态保持 `rollout observation-pending`，直到真实 `09:00` observation 通过。

## 8. Residual risks、known unknowns 与停止条件

- **外层 OS capability 未决。** Phase 0 必须用真实 owner/config/probe 选定；无法实证即 kill gate，automation 保持暂停。
- **最终 remote SHA 未决。** review/publish 前不能预填；由 Phase 6 post-publish gate 冻结。
- **Local-only history。** publish 后 canonical local 与新 remote 可能形成预期的 `diverged-preserved-local-only`；只要 frozen merge-base、bytes/index/untracked 与 object reachability 不变即为保护成功，后续整合必须另立 scope，不能在本计划自动 rebase/merge。
- **Isolated fetch implementation。** named ref、config/hooks/aliases/pager denial 与 refs/object cleanup 任一不能被实证时 lineage 不可信；不得回退到 `FETCH_HEAD`、remote-tracking cache或 canonical repo fetch。
- **15-path mapping 已冻结。** implementation discovery 只能验证第 3.4 节，不得从 delete diff 增补第 16 项；不一致即停止、修订计划并重新评审。
- **Crash window。** 多文件更新非单一 filesystem atomic；安全依赖 external lock、确定顺序 WAL/fsync、immutable backup 与 restart recovery。无法裁决为 exact before 或 committed after、或 persistent restore failure 时只能 `recovery-required` fail closed。
- **Backup capacity/retention。** preallocated reservation 仍不能阻止同 filesystem 的外部 privileged consumer 耗尽空间；每步 race recheck/ENOSPC 回滚并 fail closed。v1 不自动 GC，retention/GC 需独立人工 scope。
- **Approval key/platform。** actual Ed25519 public key 由 Provision prerequisite 生成并冻结，Phase 0 只读验证；key/authority失陷仍超出签名防线。RFC 8785 byte validator、trusted boot/monotonic source或 macOS `renameatx_np(RENAME_EXCL)` 在真实 filesystem不能按 exact semantics实证时，首个 claim/no-op/control write前 kill gate，不能换弱 primitive或放宽 parser。
- **Replay ambiguity。** durable CLAIMED/NOOP record本身永久消费 approval；orphan temp、invalid record、hash-chain/watermark gap或无法证明 zero-change会进入incident并阻断新 transaction，可能需要 external-owner forensic repair，但不得删除记录或重用旧 approval。
- **NOOP reject audit gap。** 为保持 replay loser zero engine durable write，生产无独立 collector时不会留下 persistent reject receipt；这是明确接受的审计缺口。测试/验收 fresh negative receipt只能由 out-of-band harness在disposable evidence root保存，不能把 collector并入 engine/control authority。成功侧仍由 exactly-one `NOOP_COMMITTED` authoritative record完整覆盖。
- **TCB completeness。** interpreter、native library 或 helper 的 transitively loaded dependency 若不能被枚举、分类、锁定到 root-owned absolute path并以实际 category/mode 纳入 digest，maintenance corridor 保持关闭；不得以当前 shell resolution 代替 provenance。
- **Engine promotion。** versioned bundle 与 `SOURCE_SHA` 的绑定只由 signed external-owner promotion receipt 证明；缺失、未知或 tampered 时不能使用旧 bundle降级运行，也不能由 agent 就地修补。
- **Emergency downgrade。** 即使 target 是已发布 immutable commit，也可能重新引入已知漏洞并造成 runtime 落后于 remote；因此它不倒退 remote、不解除 scheduler pause，且仅作为 forward revert commit 暂不可用时的独立批准应急路径。
- **Plugin external state。** CLI 不保证事务性；仅以 snapshot/diff、幂等重试和 pause 控制，不伪造原子性。
- **Remote race/rewrite。** 任一 lineage gate 发现变化都停止；publish 使用 FF+expected-old lease，transaction commit 前 remote change 则回滚。
- **Scheduler normalization/authority。** 主rollout只接受Entry的`definition_enabled=false`、`scheduler_suspended=false`；suspend不是disabled的替代状态。解除job/account suspension可能影响unrelated jobs，必须由独立backend-admin scope冻结影响面并重签Entry；adapter永无unsuspend/resume权。Phase 6任一authority/CAS能力不明即首次mutation前撤权STOP。
- **Confinement bypass。** symlink/hardlink/mount/child/path replacement coverage 未通过即 kill gate。
- **Observation pending。** failure only-disable耗尽后的suspend是本rollout terminal condition，不是可恢复pause；禁止自动恢复或继续09:00，必须经独立normalization和全新Entry从头开始。
- 任一 gate 缺四字段、dirty main/local-only object 变化、lineage/SHA/digest/approval JCS/signature/time/trust/TCB/engine promotion/scheduler authority/CAS/denylist/lock/replay-watermark/backup/path identity 异常、非目标变化、restore 未验证或 confinement 不明，立即停止并保持 external runtime deny；scheduler 状态只按 fresh readback报告。
- 同一失败连续两轮且无新证据时停止并简化设计，不新增 wrapper 或旁路。
