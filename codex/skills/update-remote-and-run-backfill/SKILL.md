---
name: update-remote-and-run-backfill
description: Use when operating a remote fp-detector deployment over SSH and the task involves syncing the checkout in /home/ubuntu/fp-detector, rerunning backfill, checking docker compose services, or verifying remote FP writeback behavior.
---

# Update Remote And Run Backfill

## Overview

用于远端 `fp-detector` 运维场景：先安全同步远端代码，再按仓库现有部署方式执行一次 backfill，并补最小验证。

核心原则：
- 不覆盖远端未提交改动。
- 不改写 `deploy/realtime-fp-env/.env.remote`。
- 优先通过 `docker compose ... exec -T api` 执行 backfill，避免依赖宿主机 Python 环境。

## When to Use

- “更新远程代码，然后跑 backfill”
- “ssh 到远端拉最新代码并补跑 FP”
- “远端 realtime 环境要手动补一次 backfill”
- “部署后想验证 backfill / FP writeback”

不要用于：
- 本地开发环境 backfill
- 首次完整部署（优先看 `deploy/realtime-fp-env/README.md`）
- 需要强制覆盖远端工作区的场景

## Preconditions

必须先确认：
- 可 SSH 登录目标机器
- 远端仓库目录是 `/home/ubuntu/fp-detector`
- 远端已有 `deploy/realtime-fp-env/.env.remote`
- 远端已安装 `docker compose`

默认变量：

```bash
export REMOTE_HOST="ubuntu@<host>"
export REMOTE_ROOT="/home/ubuntu/fp-detector"
export COMPOSE_FILE="deploy/realtime-fp-env/docker-compose.remote.yml"
export ENV_FILE="deploy/realtime-fp-env/.env.remote"
```

## Workflow

### 1. 预检查远端状态

```bash
ssh "$REMOTE_HOST" "
set -euo pipefail
cd \"$REMOTE_ROOT\"
pwd
git status --short
test -f \"$ENV_FILE\"
docker compose version >/dev/null
"
```

如果 `git status --short` 非空，先停下，不要继续 `git pull`。

### 2. 快进同步远端代码

```bash
ssh "$REMOTE_HOST" "
set -euo pipefail
cd \"$REMOTE_ROOT\"
branch=\$(git rev-parse --abbrev-ref HEAD)
old_head=\$(git rev-parse HEAD)
git fetch origin --prune
git pull --ff-only origin \"\$branch\"
new_head=\$(git rev-parse HEAD)
printf 'branch=%s\nold_head=%s\nnew_head=%s\n' \"\$branch\" \"\$old_head\" \"\$new_head\"
git diff --name-only \"\$old_head\" \"\$new_head\" || true
"
```

只允许 `--ff-only`。不要用 `reset --hard`、`checkout -- .` 或批量清理。

### 3. 按变更决定是否跑 migration / 重建服务

如果上一步 diff 命中这些路径：
- `deploy/realtime-fp-env/sql/`
- `scripts/sql/`
- `deploy/realtime-fp-env/Dockerfile`
- `deploy/realtime-fp-env/docker-compose.remote.yml`
- `pyproject.toml`
- `src/fp_detector/server/`
- `src/fp_detector/realtime/`

则在远端执行：

```bash
ssh "$REMOTE_HOST" "
set -euo pipefail
cd \"$REMOTE_ROOT\"
set -a
source \"$ENV_FILE\"
set +a
HOST_DB_DSN=\${FP_DB_HOST_DSN:-\${FP_DB_DSN//@db:/@127.0.0.1:}}
psql \"\$HOST_DB_DSN\" -f deploy/realtime-fp-env/sql/006_migrate_live_tx_core_profit.sql
psql \"\$HOST_DB_DSN\" -f deploy/realtime-fp-env/sql/007_create_live_tx_fp_frontend_latest_v.sql
psql \"\$HOST_DB_DSN\" -f scripts/sql/001_create_live_tx_fp_results.sql
psql \"\$HOST_DB_DSN\" -f scripts/sql/002_create_live_tx_fp_latest_v.sql
psql \"\$HOST_DB_DSN\" -f scripts/sql/003_create_live_tx_fp_dynamic_rules.sql
psql \"\$HOST_DB_DSN\" -f scripts/sql/004_create_live_tx_fp_rule_hits.sql
psql \"\$HOST_DB_DSN\" -f scripts/sql/005_create_top1_union_dashboard_tables.sql
docker compose -f \"$COMPOSE_FILE\" --env-file \"$ENV_FILE\" up -d --build api realtime_ingest backfill_loop
"
```

如果只是纯代码小改动但涉及运行中服务，也至少执行：

```bash
ssh "$REMOTE_HOST" "
set -euo pipefail
cd \"$REMOTE_ROOT\"
docker compose -f \"$COMPOSE_FILE\" --env-file \"$ENV_FILE\" up -d --build api realtime_ingest backfill_loop
"
```

### 4. 执行一次手工 backfill

默认用 24h / Top 1% / no-incremental，直接重跑当前窗口，避免漏掉已进入窗口但未被增量挑中的候选：

```bash
ssh "$REMOTE_HOST" "
set -euo pipefail
cd \"$REMOTE_ROOT\"
RUN_ID=manual_backfill_\$(date -u +%Y%m%dT%H%M%SZ)
docker compose -f \"$COMPOSE_FILE\" --env-file \"$ENV_FILE\" exec -T api \
  python scripts/backfill_fp_results.py \
  --chain ethereum \
  --window-hours 24 \
  --top-percent 0.01 \
  --no-incremental \
  --batch-size 500 \
  --run-id \"\$RUN_ID\"
printf 'RUN_ID=%s\n' \"\$RUN_ID\"
"
```

只有在用户明确接受 LLM 成本时，才追加：

```bash
--enable-llm --llm-max-per-cycle 20
```

如果用户明确要求只补增量、避免重跑当前窗口，可改回：

```bash
--incremental
```

## Verification

最小验证：

```bash
ssh "$REMOTE_HOST" "
set -euo pipefail
cd \"$REMOTE_ROOT\"
deploy/realtime-fp-env/scripts/verify_realtime_env.sh --quick
"
```

如果刚执行过实际 backfill，建议补一条 `RUN_ID` 校验：

```bash
ssh "$REMOTE_HOST" "
set -euo pipefail
cd \"$REMOTE_ROOT\"
set -a
source \"$ENV_FILE\"
set +a
HOST_DB_DSN=\${FP_DB_HOST_DSN:-\${FP_DB_DSN//@db:/@127.0.0.1:}}
psql \"\$HOST_DB_DSN\" -c \"SELECT COUNT(*) FROM public.live_tx_fp_results WHERE run_id='${RUN_ID}';\"
"
```

并补一条“最后一次 backfill 按规则命中的 tx 数”汇总：

```bash
ssh "$REMOTE_HOST" "
set -euo pipefail
cd \"$REMOTE_ROOT\"
set -a
source \"$ENV_FILE\"
set +a
HOST_DB_DSN=\${FP_DB_HOST_DSN:-\${FP_DB_DSN//@db:/@127.0.0.1:}}
psql \"\$HOST_DB_DSN\" -c \"
WITH run_rows AS (
  SELECT tx_hash, triggered_rules
  FROM public.live_tx_fp_results
  WHERE run_id='${RUN_ID}'
),
rule_rows AS (
  SELECT tx_hash, jsonb_array_elements_text(triggered_rules) AS rule_id
  FROM run_rows
  WHERE jsonb_typeof(triggered_rules) = 'array'
    AND jsonb_array_length(triggered_rules) > 0
)
SELECT rule_id, COUNT(DISTINCT tx_hash) AS tx_count
FROM rule_rows
GROUP BY rule_id
ORDER BY tx_count DESC, rule_id ASC;\"
"
```

如果需要同时看到“本次 backfill 有多少条结果没有命中规则”，再补：

```bash
ssh "$REMOTE_HOST" "
set -euo pipefail
cd \"$REMOTE_ROOT\"
set -a
source \"$ENV_FILE\"
set +a
HOST_DB_DSN=\${FP_DB_HOST_DSN:-\${FP_DB_DSN//@db:/@127.0.0.1:}}
psql \"\$HOST_DB_DSN\" -c \"
SELECT
  COUNT(*) AS total_rows,
  COUNT(*) FILTER (
    WHERE jsonb_typeof(triggered_rules) = 'array'
      AND jsonb_array_length(triggered_rules) = 0
  ) AS no_rule_rows
FROM public.live_tx_fp_results
WHERE run_id='${RUN_ID}';\"
"
```

## Output Requirements

执行此 skill 后，回答里至少要包含：
- `remote_host`
- `branch`
- `old_head` / `new_head`
- 是否执行了 migration / compose rebuild
- `RUN_ID`
- `backfill_row_count`
- `rule_hit_breakdown`（按 `rule_id -> tx_count` 汇总；动态规则保留 `DR:*` 前缀）
- 若查询了空规则行，也要给出 `no_rule_rows`
- 验证命令与结果

## Common Mistakes

- 远端工作区有脏改动还继续 `git pull`
- 修改或覆盖 `deploy/realtime-fp-env/.env.remote`
- 在宿主机直接跑 `python scripts/backfill_fp_results.py`
- SQL / Docker 变更后没重建服务
- 误以为 `FP_REALTIME_START_AT` 仍会裁剪当前 backfill 候选
- 只汇报 `RUN_ID` 总条数，不汇报“哪些规则更新了多少条 tx”
