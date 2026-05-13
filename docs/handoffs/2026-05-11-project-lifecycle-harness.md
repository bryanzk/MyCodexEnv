# Handoff: delivery-harness-framework

Date: 2026-05-11
Repo: `/Users/kezheng/Codes/CursorDeveloper/MyCodexEnv`
Branch: `main`
Latest commit at handoff: `e49f3d8 Add lifecycle harness skills`

## Purpose

This handoff is for a new MyCodexEnv session focused on the generic
`delivery-harness-framework` skill. The goal is to treat the generic skill as a
repo-managed global Codex skill, refine it from inside MyCodexEnv, and make sure
it stays synchronized into the runtime `~/.codex/skills` environment.

## Current State

New skills were added and committed in MyCodexEnv:

- `codex/skills/delivery-harness-framework/SKILL.md`
- `codex/skills/delivery-harness-framework/agents/openai.yaml`
- `codex/skills/shipq-lifecycle-harness/SKILL.md`

The generic skill also exists in the current runtime install:

- `/Users/kezheng/.codex/skills/delivery-harness-framework/SKILL.md`
- `/Users/kezheng/.codex/skills/delivery-harness-framework/agents/openai.yaml`

The ShipQ-specific skill was committed in the same MyCodexEnv commit to avoid a
repeat of the previous problem where ShipQ docs referenced a global skill that
only existed in the local runtime directory.

## Key Design Decisions

- `delivery-harness-framework` is generic. It must not mention ShipQ, workbook
  data, freight quote demos, or project-specific paths.
- Repo-specific lifecycle skills, such as `shipq-lifecycle-harness`, should act
  as adapters that add domain paths, commands, safety rules, and browser smoke
  matrices.
- The generic skill owns the common protocol:
  - startup probes
  - source-of-truth order
  - lifecycle stage classification
  - durable project state contract
  - append-only evidence rule
  - exception-handling principles
  - verification evidence requirements
  - delegation to repo-specific harnesses
- The generic skill is a router and protocol, not a full executor. It tells the
  next agent what to read, what stage it is in, which workflow to use, and what
  verification gates are required.

## What To Check First

From the MyCodexEnv repo:

```bash
git status --short --branch
git log --max-count=5 --pretty=format:'%h %ad %s' --date=short
sed -n '1,220p' README.md
sed -n '1,220p' AGENTS.md
sed -n '1,220p' codex/AGENTS.md
sed -n '1,260p' codex/skills/delivery-harness-framework/SKILL.md
sed -n '1,80p' codex/skills/delivery-harness-framework/agents/openai.yaml
```

Then verify whether runtime sync behavior is already covered by existing scripts:

```bash
rg -n "codex/skills|sync_codex_home|\\.codex/skills|bootstrap" README.md scripts test_runner.py docs codex
```

## Suggested Next Tasks

1. Decide whether `delivery-harness-framework` should be mentioned in
   `README.md` under global skills.
2. Confirm bootstrap or sync scripts copy `codex/skills/delivery-harness-framework`
   into `~/.codex/skills/delivery-harness-framework`.
3. Add or update a lightweight test if MyCodexEnv has skill-sync validation.
4. Run validation:
   - `python3 test_runner.py`
   - `python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py codex/skills/delivery-harness-framework`
   - `git diff --check`
5. If the change is good, commit any follow-up docs/tests and push the branch.

## Acceptance Criteria

- `delivery-harness-framework` remains generic and domain-free.
- MyCodexEnv documents how this generic skill relates to repo-specific lifecycle
  harness skills.
- Runtime sync/install path is verified, not assumed.
- Validation evidence includes `command`, `exit_code`, `key_output`, and
  `timestamp`.
- No private project data, local credentials, or environment-specific secrets are
  added.

## Copy-Paste Prompt For The New MyCodexEnv Session

```text
请在 MyCodexEnv 项目中继续处理通用 Codex skill：delivery-harness-framework。

工作目录：
/Users/kezheng/Codes/CursorDeveloper/MyCodexEnv

请先读取：
1. AGENTS.md
2. README.md
3. codex/AGENTS.md
4. docs/handoffs/2026-05-11-project-lifecycle-harness.md
5. codex/skills/delivery-harness-framework/SKILL.md
6. codex/skills/delivery-harness-framework/agents/openai.yaml

目标：
- 审查 delivery-harness-framework 是否适合作为通用生命周期 harness skill。
- 保持它 generic，不要加入 ShipQ 或其他项目专属路径。
- 检查 MyCodexEnv 的 bootstrap/sync/test 机制是否会把 codex/skills/delivery-harness-framework 正确同步到 ~/.codex/skills/delivery-harness-framework。
- 如有必要，更新 README/docs/test_runner.py 或相关同步测试。
- 运行 fresh verification，并在最终回复里给出 command、exit_code、key_output、timestamp。

注意：
- MyCodexEnv 当前已有提交 e49f3d8 Add lifecycle harness skills，包含 delivery-harness-framework 和 shipq-lifecycle-harness。
- shipq-lifecycle-harness 是 repo-specific adapter，不要把它的业务细节合并进通用 skill。
- 如果发现需要改公开同步行为、bootstrap 行为或全局 AGENTS 规则，先说明影响范围再改。
```
