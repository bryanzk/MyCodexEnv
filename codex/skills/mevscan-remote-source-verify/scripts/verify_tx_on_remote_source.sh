#!/usr/bin/env bash
set -euo pipefail

TX_HASH="${1:?usage: $0 <tx_hash> [rpc_url] [remote_alias]}"
RPC_URL="${2:-${MEVSCAN_PUBLIC_RPC_URL:-http://43.135.168.74:8851}}"
REMOTE_ALIAS="${3:-mevscan-source}"
REMOTE_ROOT="${MEVSCAN_REMOTE_ROOT:-/mnt/data/mevscan/runtime-data}"

tx_lower="$(printf '%s' "$TX_HASH" | tr '[:upper:]' '[:lower:]')"
if [[ "$tx_lower" != 0x* ]]; then
  tx_lower="0x$tx_lower"
fi

tx_json="$(
  curl -s --connect-timeout 20 -X POST "$RPC_URL" \
    -H 'Content-Type: application/json' \
    -d "{\"jsonrpc\":\"2.0\",\"method\":\"eth_getTransactionByHash\",\"params\":[\"$tx_lower\"],\"id\":1}"
)"

block_hex="$(
  printf '%s' "$tx_json" | python3 -c 'import sys, json; d=json.load(sys.stdin); r=d.get("result") or {}; print(r.get("blockNumber",""))'
)"

if [[ -z "$block_hex" || "$block_hex" == "null" ]]; then
  echo "tx not found on RPC: $tx_lower" >&2
  exit 1
fi

block_num="$(
  python3 -c "print(int('$block_hex', 16))"
)"

remote_json_path="$(
  ssh "$REMOTE_ALIAS" "find '$REMOTE_ROOT' -type f -name '${block_num}.json' | sort | head -1"
)"

if [[ -z "$remote_json_path" ]]; then
  echo "remote block json not found for block $block_num on $REMOTE_ALIAS" >&2
  exit 1
fi

ssh "$REMOTE_ALIAS" python3 - "$remote_json_path" "$tx_lower" <<'PY'
import json, sys
path = sys.argv[1]
tx = sys.argv[2].lower()
d = json.load(open(path))
block_number = d.get('block_number')
pipeline_state = d.get('pipeline_state')
mev_summary = d.get('mev_summary')
print(f'verdict: tx={tx} block={block_number} mev=unknown')
print('block_number:', block_number)
print('pipeline_state:', pipeline_state)
print('mev_summary:', mev_summary)
for item in d.get('transactions', []):
    if item.get('tx_hash', '').lower() != tx:
        continue
    reports = item.get('mev_reports', [])
    verdict = 'YES' if reports else 'NO'
    mev_type = ','.join(sorted({str(r.get('mev_type')) for r in reports if r.get('mev_type')})) or 'none'
    print(f'verdict: tx={tx} block={block_number} mev={verdict} count={len(reports)} types={mev_type}')
    print('tx_hash:', item.get('tx_hash'))
    print('has_mev_reports:', 'mev_reports' in item)
    print('mev_report_count:', len(reports))
    for r in reports:
        print('mev_type:', r.get('mev_type'))
        print('event_id:', r.get('event_id'))
        print('searchers:', r.get('searchers'))
        print('input_asset:', r.get('input_asset'))
        print('output_asset:', r.get('output_asset'))
    break
else:
    print(f'verdict: tx={tx} block={block_number} mev=NO tx_not_found')
    print('tx not found in block json')
PY

echo "command: eth_getTransactionByHash + remote block json verify"
echo "block_number: $block_num"
echo "remote_json: $remote_json_path"
