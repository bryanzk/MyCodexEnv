#!/usr/bin/env bash

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
RUNTIME_DIR="$SKILL_DIR/runtime"
LEASE_FILE="$RUNTIME_DIR/api-lease.env"
LOG_FILE="$RUNTIME_DIR/local-analysis-api.log"
ENSURE_ETH_RPC_SCRIPT="$SKILL_DIR/scripts/ensure_local_eth_rpc.sh"

REPO_ROOT="${EIGENPHI_ANALYSE_TX_REPO:-/Users/kezheng/Codes/CursorDeveloper/eigenphi-analyse-transaction}"
API_BASE="${EIGENPHI_TX_API_BASE:-http://127.0.0.1:8889}"
LEASE_TTL_SECONDS="${EIGENPHI_TX_API_TTL_SECONDS:-43200}"
ETH_RPC_URL="${ETHEREUM_MAINNET_URL:-http://127.0.0.1:8545}"
LIBFIXPOSIX_PREFIX="${EIGENPHI_LIBFIXPOSIX_PREFIX:-$HOME/.local}"

mkdir -p "$RUNTIME_DIR"

parse_api_base() {
  local url rest host_port scheme

  url="${1%/}"
  scheme="${url%%://*}"
  rest="${url#*://}"
  host_port="${rest%%/*}"

  API_HOST="${host_port%%:*}"
  if [ "$API_HOST" = "$host_port" ]; then
    if [ "$scheme" = "https" ]; then
      API_PORT="443"
    else
      API_PORT="80"
    fi
  else
    API_PORT="${host_port##*:}"
  fi
}

is_local_api_host() {
  [ "$API_HOST" = "127.0.0.1" ] || [ "$API_HOST" = "localhost" ]
}

check_liveness() {
  curl -fsS --max-time 2 "${API_BASE%/}/liveness" >/dev/null 2>&1
}

check_readiness() {
  curl -fsS --max-time 2 "${API_BASE%/}/readiness" >/dev/null 2>&1
}

write_lease() {
  local now lease_until pid readiness
  now="$1"
  lease_until="$2"
  pid="${3:-}"
  readiness="${4:-unknown}"

  cat >"$LEASE_FILE" <<EOF
LEASE_API_BASE=$API_BASE
LEASE_API_HOST=$API_HOST
LEASE_API_PORT=$API_PORT
LEASE_STARTED_AT_EPOCH=$now
LEASE_UNTIL_EPOCH=$lease_until
LEASE_PID=$pid
LEASE_LAST_READINESS=$readiness
EOF
}

read_lease() {
  LEASE_UNTIL_EPOCH=0
  LEASE_PID=""
  LEASE_LAST_READINESS="unknown"
  LEASE_STARTED_AT_EPOCH=0
  LEASE_API_BASE=""
  LEASE_API_HOST=""
  LEASE_API_PORT=""

  if [ -f "$LEASE_FILE" ]; then
    # shellcheck disable=SC1090
    . "$LEASE_FILE"
  fi
}

print_status() {
  printf '%s\n' "$1" >&2
}

print_suggestion() {
  printf 'suggestion: %s\n' "$1" >&2
}

brew_prefix_for() {
  if command -v brew >/dev/null 2>&1; then
    brew --prefix "$1" 2>/dev/null || true
  fi
}

brew_cellar_for() {
  if command -v brew >/dev/null 2>&1; then
    brew --cellar "$1" 2>/dev/null || true
  fi
}

brew_versions_for() {
  if command -v brew >/dev/null 2>&1; then
    brew list --versions "$1" 2>/dev/null || true
  fi
}

find_sbcl() {
  local prefix cellar versions version

  if [ -n "${EIGENPHI_SBCL_BIN:-}" ] && [ -x "${EIGENPHI_SBCL_BIN:-}" ]; then
    printf '%s\n' "$EIGENPHI_SBCL_BIN"
    return 0
  fi

  if command -v sbcl >/dev/null 2>&1; then
    command -v sbcl
    return 0
  fi

  for candidate in \
    /opt/homebrew/opt/sbcl/bin/sbcl \
    /opt/homebrew/bin/sbcl \
    /usr/local/bin/sbcl \
    /usr/bin/sbcl
  do
    if [ -x "$candidate" ]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done

  versions="$(brew_versions_for sbcl)"
  prefix="$(brew_prefix_for sbcl)"
  cellar="$(brew_cellar_for sbcl)"

  if [ -n "$versions" ]; then
    if [ -n "$prefix" ] && [ -x "$prefix/bin/sbcl" ]; then
      printf '%s\n' "$prefix/bin/sbcl"
      return 0
    fi

    for version in $(printf '%s\n' "$versions" | awk '{for (i = 2; i <= NF; i++) print $i}'); do
      if [ -n "$cellar" ] && [ -x "$cellar/$version/bin/sbcl" ]; then
        printf '%s\n' "$cellar/$version/bin/sbcl"
        return 0
      fi
    done
  fi

  return 1
}

resolve_libfixposix_prefix() {
  local candidate

  for candidate in \
    "${EIGENPHI_LIBFIXPOSIX_PREFIX:-}" \
    "$HOME/.local" \
    "$HOME/.local/libfixposix" \
    /opt/homebrew \
    /usr/local
  do
    [ -n "$candidate" ] || continue
    if [ -f "$candidate/lib/libfixposix.dylib" ]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done

  return 1
}

ensure_repo_libfixposix_symlink() {
  local prefix dylib link_path

  prefix="$1"
  dylib="$prefix/lib/libfixposix.dylib"
  link_path="$REPO_ROOT/libfixposix.dylib"

  [ -f "$dylib" ] || return 0
  ln -sfn "$dylib" "$link_path"
}

report_missing_sbcl_dependency() {
  local prefix cellar versions

  if [ -n "${EIGENPHI_SBCL_BIN:-}" ] && [ ! -x "${EIGENPHI_SBCL_BIN:-}" ]; then
    print_status "WARN: missing dependency: EIGENPHI_SBCL_BIN points to a non-executable path: ${EIGENPHI_SBCL_BIN}"
    print_suggestion "set EIGENPHI_SBCL_BIN to a real sbcl binary path, then rerun the skill"
    return 0
  fi

  prefix="$(brew_prefix_for sbcl)"
  cellar="$(brew_cellar_for sbcl)"
  versions="$(brew_versions_for sbcl)"

  if [ -n "$versions" ]; then
    print_status "WARN: missing dependency: sbcl appears installed via Homebrew (${versions}) but no executable was found in PATH or common locations; try ${prefix}/bin/sbcl or set EIGENPHI_SBCL_BIN"
    if [ -n "$prefix" ]; then
      print_suggestion "export EIGENPHI_SBCL_BIN='${prefix}/bin/sbcl'"
    fi
    print_suggestion "or add the sbcl binary to PATH, then rerun the skill"
    return 0
  fi

  if [ -n "$prefix" ] || [ -n "$cellar" ]; then
    print_status "WARN: missing dependency: sbcl is not installed; Homebrew formula paths exist (${prefix:-n/a}, ${cellar:-n/a}) but no installed versions were found. Run 'brew install sbcl' or set EIGENPHI_SBCL_BIN"
    print_suggestion "brew install sbcl"
    return 0
  fi

  print_status "WARN: missing dependency: sbcl executable not found. Install SBCL or set EIGENPHI_SBCL_BIN"
  print_suggestion "brew install sbcl"
  print_suggestion "or export EIGENPHI_SBCL_BIN='/absolute/path/to/sbcl'"
}

check_local_eth_rpc_dependency() {
  local response

  response="$(
    curl -sS --max-time 2 \
      -H 'Content-Type: application/json' \
      -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
      "$ETH_RPC_URL" 2>&1
  )" || {
    print_status "WARN: missing dependency: Ethereum JSON-RPC at ${ETH_RPC_URL} is unavailable; eth_blockNumber request failed: ${response}"
    if [ "$ETH_RPC_URL" = "http://127.0.0.1:8545" ]; then
      print_suggestion "start a local Ethereum JSON-RPC server on 127.0.0.1:8545"
      print_suggestion "or export ETHEREUM_MAINNET_URL='https://your-ethereum-rpc' before running the skill"
    else
      print_suggestion "verify ETHEREUM_MAINNET_URL='${ETH_RPC_URL}' is reachable, or point it to a healthy Ethereum RPC endpoint"
    fi
    return 1
  }

  if printf '%s' "$response" | grep -Eq '"result"[[:space:]]*:[[:space:]]*"0x[0-9a-fA-F]+'; then
    return 0
  fi

  print_status "WARN: missing dependency: Ethereum JSON-RPC at ${ETH_RPC_URL} returned an unexpected response to eth_blockNumber: ${response}"
  print_suggestion "verify ETHEREUM_MAINNET_URL='${ETH_RPC_URL}' points to a standard Ethereum JSON-RPC endpoint"
  return 1
}

start_server() {
  local pid sbcl_bin resolved_libfixposix_prefix

  if [ ! -d "$REPO_ROOT" ]; then
    print_status "WARN: repo root not found: $REPO_ROOT"
    return 1
  fi

  if ! sbcl_bin="$(find_sbcl)"; then
    report_missing_sbcl_dependency
    return 1
  fi

  print_status "api status: starting local analysis API at ${API_BASE%/} (lease 12h)"

  if resolved_libfixposix_prefix="$(resolve_libfixposix_prefix)"; then
    ensure_repo_libfixposix_symlink "$resolved_libfixposix_prefix"
  else
    resolved_libfixposix_prefix="$LIBFIXPOSIX_PREFIX"
  fi

  pid="$(
    python3 - "$LOG_FILE" "$REPO_ROOT" "$sbcl_bin" "$API_PORT" "$resolved_libfixposix_prefix" <<'PY'
import os
import subprocess
import sys

log_file, repo_root, sbcl_bin, api_port, libfixposix_prefix = sys.argv[1:]

env = os.environ.copy()
env["PATH"] = f"/opt/homebrew/bin:{env.get('PATH', '')}"
env["ENV"] = env.get("ENV", "local")
env["DYNAMIC_SPACE_SIZE"] = env.get("DYNAMIC_SPACE_SIZE", "2048")
env["ETHEREUM_MAINNET_URL"] = env.get("ETHEREUM_MAINNET_URL", "http://127.0.0.1:8545")
env["BSC_MAINNET_URL"] = env.get("BSC_MAINNET_URL", "https://archive-bsc-ca.w3node.com/64ce0821b4588867476dbfe29cfca8f6b289e5df99421752d49534f702620aec/api")
env["CHAIN_NAMES_SUPPORT_CALL_STACK"] = env.get("CHAIN_NAMES_SUPPORT_CALL_STACK", "ethereum,bsc")
env["SERVER_PORT"] = api_port

include_dir = os.path.join(libfixposix_prefix, "include")
lib_dir = os.path.join(libfixposix_prefix, "lib")
pkgconfig_dir = os.path.join(lib_dir, "pkgconfig")
if os.path.isdir(include_dir):
    env["CPATH"] = f"{include_dir}:{env['CPATH']}" if env.get("CPATH") else include_dir
    env["C_INCLUDE_PATH"] = f"{include_dir}:{env['C_INCLUDE_PATH']}" if env.get("C_INCLUDE_PATH") else include_dir
if os.path.isdir(lib_dir):
    for key in ("LIBRARY_PATH", "DYLD_LIBRARY_PATH", "DYLD_FALLBACK_LIBRARY_PATH", "LD_LIBRARY_PATH"):
        env[key] = f"{lib_dir}:{env[key]}" if env.get(key) else lib_dir
    env["PKG_CONFIG_PATH"] = f"{pkgconfig_dir}:{env['PKG_CONFIG_PATH']}" if env.get("PKG_CONFIG_PATH") else pkgconfig_dir
if not env.get("CL_DOT_DOT"):
    dot_bin = subprocess.run(["/bin/zsh", "-lc", "command -v dot || true"], capture_output=True, text=True).stdout.strip()
    if dot_bin:
      env["CL_DOT_DOT"] = dot_bin

cmd = [
    sbcl_bin,
    "--dynamic-space-size", env["DYNAMIC_SPACE_SIZE"],
    "--eval", "(ql:quickload 'mu-arbitrage)",
    "--eval", "(loop do (sleep 86400))",
]

with open(log_file, "ab", buffering=0) as log:
    proc = subprocess.Popen(
        cmd,
        cwd=repo_root,
        env=env,
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

wait_for_liveness() {
  local pid retries
  pid="$1"
  retries=90

  while [ "$retries" -gt 0 ]; do
    if check_liveness; then
      return 0
    fi

    if ! kill -0 "$pid" >/dev/null 2>&1; then
      return 1
    fi

    retries=$((retries - 1))
    sleep 2
  done

  return 1
}

tail_log() {
  if [ -f "$LOG_FILE" ]; then
    print_status "api status: recent log tail"
    tail -20 "$LOG_FILE" >&2 || true
  fi
}

parse_api_base "$API_BASE"
read_lease

NOW_EPOCH="$(date +%s)"
LEASE_VALID=0
if [ "${LEASE_UNTIL_EPOCH:-0}" -gt "$NOW_EPOCH" ] && [ "${LEASE_API_BASE:-}" = "$API_BASE" ]; then
  LEASE_VALID=1
fi

if [ "${EIGENPHI_ADDRESS_TAG_NEEDS_TX_CONTEXT:-0}" = "1" ]; then
  if [ -f "$ENSURE_ETH_RPC_SCRIPT" ]; then
    bash "$ENSURE_ETH_RPC_SCRIPT" || true
  fi
  check_local_eth_rpc_dependency || true
fi

if check_liveness; then
  if [ "$LEASE_VALID" -eq 1 ]; then
    if check_readiness; then
      print_status "api status: reusing local analysis API; lease valid until ${LEASE_UNTIL_EPOCH}; readiness OK"
      exit 0
    fi
    print_status "api status: reusing local analysis API; lease valid until ${LEASE_UNTIL_EPOCH}; readiness unavailable (check 127.0.0.1:8545)"
    exit 0
  fi

  NEW_LEASE_UNTIL=$((NOW_EPOCH + LEASE_TTL_SECONDS))
  if check_readiness; then
    write_lease "$NOW_EPOCH" "$NEW_LEASE_UNTIL" "${LEASE_PID:-}" "ok"
    print_status "api status: local analysis API already running; lease refreshed for 12h; readiness OK"
  else
    write_lease "$NOW_EPOCH" "$NEW_LEASE_UNTIL" "${LEASE_PID:-}" "fail"
    print_status "api status: local analysis API already running; lease refreshed for 12h; readiness unavailable (check 127.0.0.1:8545)"
  fi
  exit 0
fi

if ! is_local_api_host; then
  print_status "WARN: API base is not local (${API_BASE%/}); skip auto-start"
  exit 0
fi

PID="$(start_server || true)"
if [ -z "${PID:-}" ]; then
  exit 1
fi

if ! wait_for_liveness "$PID"; then
  print_status "WARN: failed to bring up local analysis API at ${API_BASE%/}"
  tail_log
  exit 1
fi

NEW_LEASE_UNTIL=$((NOW_EPOCH + LEASE_TTL_SECONDS))
if check_readiness; then
  write_lease "$NOW_EPOCH" "$NEW_LEASE_UNTIL" "$PID" "ok"
  print_status "api status: local analysis API started; lease valid for 12h; readiness OK"
else
  write_lease "$NOW_EPOCH" "$NEW_LEASE_UNTIL" "$PID" "fail"
  print_status "api status: local analysis API started; lease valid for 12h; readiness unavailable (check 127.0.0.1:8545)"
fi
