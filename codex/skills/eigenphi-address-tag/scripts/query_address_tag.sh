#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="${EIGENPHI_ANALYSE_TX_REPO:-/Users/kezheng/Codes/CursorDeveloper/eigenphi-analyse-transaction}"
TARGET_SCRIPT="$REPO_ROOT/query-address-tag.sh"
ENSURE_SCRIPT="$(cd "$(dirname "$0")" && pwd)/ensure_local_api.sh"
SCAN_FALLBACK_SCRIPT="$(cd "$(dirname "$0")" && pwd)/query_scan_address_tag.sh"
LOCAL_API_BASE="${EIGENPHI_TX_API_BASE:-http://127.0.0.1:8889}"
ONLINE_API_BASE="${EIGENPHI_TX_API_BASE_ONLINE:-https://eigenphi.io}"
NEEDS_TX_CONTEXT=0
CHAIN=""
TX_HASH=""
ADDRESS=""
ORIG_ARGS=("$@")

while [ "$#" -gt 0 ]; do
  case "$1" in
    --tx)
      NEEDS_TX_CONTEXT=1
      TX_HASH="${2:-}"
      shift 2
      ;;
    --chain)
      CHAIN="${2:-}"
      shift 2
      ;;
    --address)
      ADDRESS="${2:-}"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

if [ ! -f "$TARGET_SCRIPT" ]; then
  echo "missing query script: $TARGET_SCRIPT" >&2
  echo "set EIGENPHI_ANALYSE_TX_REPO to the correct eigenphi-analyse-transaction repo path" >&2
  exit 2
fi

report_service() {
  printf 'service selection: %s\n' "$1" >&2
}

probe_local_service() {
  local health_url
  health_url="${LOCAL_API_BASE%/}/liveness"
  if [ "$NEEDS_TX_CONTEXT" -eq 1 ]; then
    health_url="${LOCAL_API_BASE%/}/readiness"
  fi
  curl -fsS --max-time 2 "$health_url" >/dev/null 2>&1
}

probe_online_service() {
  [ "$NEEDS_TX_CONTEXT" -eq 1 ] || return 1
  [ -n "$TX_HASH" ] || return 1
  [ -n "$CHAIN" ] || return 1
  command -v jq >/dev/null 2>&1 || return 1

  curl -fsS --max-time 20 \
    "${ONLINE_API_BASE%/}/api/v1/analyseTransaction?enableCallStack=on&enableCallStackAddressTag=on&chain=${CHAIN}&tx=${TX_HASH}" \
  | jq -e '.status == "ok"' >/dev/null 2>&1
}

chain_scan_base() {
  case "$1" in
    ethereum) printf 'https://etherscan.io' ;;
    bsc) printf 'https://bscscan.com' ;;
    fantom) printf 'https://ftmscan.com' ;;
    avalanche) printf 'https://snowtrace.io' ;;
    polygon) printf 'https://polygonscan.com' ;;
    optimism) printf 'https://optimistic.etherscan.io' ;;
    arbitrum) printf 'https://arbiscan.io' ;;
    cronos) printf 'https://cronoscan.com' ;;
    *) return 1 ;;
  esac
}

run_repo_query() {
  local api_base="$1"
  shift
  if [ -n "$api_base" ]; then
    bash "$TARGET_SCRIPT" --repo-root "$REPO_ROOT" --api-base "$api_base" "$@"
  else
    bash "$TARGET_SCRIPT" --repo-root "$REPO_ROOT" "$@"
  fi
}

run_query_with_fallback() {
  local api_base="$1"
  shift

  local stdout_file stderr_file fallback_stdout fallback_stderr status fallback_status
  stdout_file="$(mktemp)"
  stderr_file="$(mktemp)"
  fallback_stdout="$(mktemp)"
  fallback_stderr="$(mktemp)"

  set +e
  run_repo_query "$api_base" "$@" >"$stdout_file" 2>"$stderr_file"
  status=$?
  set -e

  if [ "$status" -eq 0 ]; then
    cat "$stderr_file" >&2
    cat "$stdout_file"
    rm -f "$stdout_file" "$stderr_file" "$fallback_stdout" "$fallback_stderr"
    return 0
  fi

  if [ "$status" -eq 1 ] && rg -q '^no tags found for address ' "$stderr_file" && [ -f "$SCAN_FALLBACK_SCRIPT" ]; then
    set +e
    bash "$SCAN_FALLBACK_SCRIPT" --chain "$CHAIN" --address "$ADDRESS" >"$fallback_stdout" 2>"$fallback_stderr"
    fallback_status=$?
    set -e

    if [ "$fallback_status" -eq 0 ]; then
      printf 'service selection: explorer-fallback (%s/address/%s)\n' "$(chain_scan_base "$CHAIN")" "$ADDRESS" >&2
      cat "$fallback_stderr" >&2
      cat "$fallback_stdout"
      rm -f "$stdout_file" "$stderr_file" "$fallback_stdout" "$fallback_stderr"
      return 0
    fi
  fi

  cat "$stderr_file" >&2
  cat "$stdout_file"
  rm -f "$stdout_file" "$stderr_file" "$fallback_stdout" "$fallback_stderr"
  return "$status"
}

if [ "$NEEDS_TX_CONTEXT" -eq 1 ]; then
  if probe_local_service; then
    report_service "local-fast (${LOCAL_API_BASE%/})"
    run_query_with_fallback "$LOCAL_API_BASE" "${ORIG_ARGS[@]}"
    exit $?
  fi

  if probe_online_service; then
    report_service "online-fallback (${ONLINE_API_BASE%/})"
    run_query_with_fallback "$ONLINE_API_BASE" "${ORIG_ARGS[@]}"
    exit $?
  fi

  if [ -f "$ENSURE_SCRIPT" ]; then
    EIGENPHI_ADDRESS_TAG_NEEDS_TX_CONTEXT=1 bash "$ENSURE_SCRIPT" || true
    if probe_local_service; then
      report_service "local-cold-start (${LOCAL_API_BASE%/})"
      run_query_with_fallback "$LOCAL_API_BASE" "${ORIG_ARGS[@]}"
      exit $?
    fi
  fi

  if probe_online_service; then
    report_service "online-last-resort (${ONLINE_API_BASE%/})"
    run_query_with_fallback "$ONLINE_API_BASE" "${ORIG_ARGS[@]}"
    exit $?
  fi
fi

run_query_with_fallback "" "${ORIG_ARGS[@]}"
