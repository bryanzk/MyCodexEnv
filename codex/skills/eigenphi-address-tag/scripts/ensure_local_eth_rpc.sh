#!/usr/bin/env bash

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
RUNTIME_DIR="$SKILL_DIR/runtime"
LEASE_FILE="$RUNTIME_DIR/eth-rpc-lease.env"
LOG_FILE="$RUNTIME_DIR/local-eth-rpc-proxy.log"
FORWARDER="$SKILL_DIR/scripts/http_jsonrpc_forwarder.py"

ETH_RPC_URL="${ETHEREUM_MAINNET_URL:-http://127.0.0.1:8545}"
UPSTREAM_RPC_URL="${EIGENPHI_ETH_RPC_UPSTREAM:-http://123.118.108.250:9999}"
LEASE_TTL_SECONDS="${EIGENPHI_ETH_RPC_TTL_SECONDS:-43200}"

mkdir -p "$RUNTIME_DIR"

parse_url() {
  local url rest host_port scheme

  url="${1%/}"
  scheme="${url%%://*}"
  rest="${url#*://}"
  host_port="${rest%%/*}"

  RPC_HOST="${host_port%%:*}"
  if [ "$RPC_HOST" = "$host_port" ]; then
    if [ "$scheme" = "https" ]; then
      RPC_PORT="443"
    else
      RPC_PORT="80"
    fi
  else
    RPC_PORT="${host_port##*:}"
  fi
}

is_local_rpc_host() {
  [ "$RPC_HOST" = "127.0.0.1" ] || [ "$RPC_HOST" = "localhost" ]
}

print_status() {
  printf '%s\n' "$1" >&2
}

probe_rpc() {
  local url response

  url="$1"
  response="$(
    curl -sS --max-time 3 \
      -H 'Content-Type: application/json' \
      -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
      "$url" 2>&1
  )" || return 1

  printf '%s' "$response" | grep -Eq '"result"[[:space:]]*:[[:space:]]*"0x[0-9a-fA-F]+'
}

write_lease() {
  local now lease_until pid
  now="$1"
  lease_until="$2"
  pid="${3:-}"

  cat >"$LEASE_FILE" <<EOF
LEASE_RPC_URL=$ETH_RPC_URL
LEASE_RPC_HOST=$RPC_HOST
LEASE_RPC_PORT=$RPC_PORT
LEASE_STARTED_AT_EPOCH=$now
LEASE_UNTIL_EPOCH=$lease_until
LEASE_PID=$pid
EOF
}

read_lease() {
  LEASE_UNTIL_EPOCH=0
  LEASE_PID=""
  LEASE_STARTED_AT_EPOCH=0
  LEASE_RPC_URL=""
  LEASE_RPC_HOST=""
  LEASE_RPC_PORT=""

  if [ -f "$LEASE_FILE" ]; then
    # shellcheck disable=SC1090
    . "$LEASE_FILE"
  fi
}

wait_for_rpc() {
  local pid retries
  pid="$1"
  retries=30

  while [ "$retries" -gt 0 ]; do
    if probe_rpc "$ETH_RPC_URL"; then
      return 0
    fi

    if ! kill -0 "$pid" >/dev/null 2>&1; then
      return 1
    fi

    retries=$((retries - 1))
    sleep 1
  done

  return 1
}

start_proxy() {
  local pid

  if [ ! -f "$FORWARDER" ]; then
    print_status "WARN: missing rpc forwarder: $FORWARDER"
    return 1
  fi

  if ! command -v python3 >/dev/null 2>&1; then
    print_status "WARN: missing dependency: python3 executable not found"
    return 1
  fi

  if [ "$UPSTREAM_RPC_URL" = "$ETH_RPC_URL" ]; then
    print_status "WARN: cannot proxy local Ethereum RPC to itself: ${ETH_RPC_URL}"
    return 1
  fi

  if ! probe_rpc "$UPSTREAM_RPC_URL"; then
    print_status "WARN: upstream Ethereum RPC is unavailable: ${UPSTREAM_RPC_URL}"
    return 1
  fi

  print_status "rpc status: starting local Ethereum RPC proxy at ${ETH_RPC_URL} -> ${UPSTREAM_RPC_URL}"

  pid="$(
    python3 - "$FORWARDER" "$RPC_HOST" "$RPC_PORT" "$UPSTREAM_RPC_URL" "$LOG_FILE" <<'PY'
import subprocess
import sys

forwarder, host, port, upstream, log_file = sys.argv[1:]
with open(log_file, "ab", buffering=0) as log:
    proc = subprocess.Popen(
        ["python3", forwarder, "--listen-host", host, "--listen-port", port, "--upstream", upstream],
        stdin=subprocess.DEVNULL,
        stdout=log,
        stderr=log,
        start_new_session=True,
        close_fds=True,
    )
    print(proc.pid)
PY
  )"
  printf '%s\n' "$pid"
}

parse_url "$ETH_RPC_URL"
read_lease

NOW_EPOCH="$(date +%s)"
LEASE_VALID=0
if [ "${LEASE_UNTIL_EPOCH:-0}" -gt "$NOW_EPOCH" ] && [ "${LEASE_RPC_URL:-}" = "$ETH_RPC_URL" ]; then
  LEASE_VALID=1
fi

if probe_rpc "$ETH_RPC_URL"; then
  NEW_LEASE_UNTIL=$((NOW_EPOCH + LEASE_TTL_SECONDS))
  write_lease "$NOW_EPOCH" "$NEW_LEASE_UNTIL" "${LEASE_PID:-}"
  if [ "$LEASE_VALID" -eq 1 ]; then
    print_status "rpc status: reusing local Ethereum RPC; lease valid until ${LEASE_UNTIL_EPOCH}"
  else
    print_status "rpc status: local Ethereum RPC already running; lease refreshed for 12h"
  fi
  exit 0
fi

if ! is_local_rpc_host; then
  print_status "rpc status: ETHEREUM_MAINNET_URL is remote (${ETH_RPC_URL}); skip local start"
  exit 0
fi

PID="$(start_proxy || true)"
if [ -z "${PID:-}" ]; then
  exit 1
fi

if ! wait_for_rpc "$PID"; then
  print_status "WARN: failed to bring up local Ethereum RPC at ${ETH_RPC_URL}"
  if [ -f "$LOG_FILE" ]; then
    tail -20 "$LOG_FILE" >&2 || true
  fi
  exit 1
fi

NEW_LEASE_UNTIL=$((NOW_EPOCH + LEASE_TTL_SECONDS))
write_lease "$NOW_EPOCH" "$NEW_LEASE_UNTIL" "$PID"
print_status "rpc status: local Ethereum RPC proxy started; lease valid for 12h"
