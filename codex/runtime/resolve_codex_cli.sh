#!/usr/bin/env bash
set -u

# Resolve a functional Codex CLI instead of trusting a stale symlink or shim.
# CODEX_CLI_PATH is tried first. CODEX_CLI_FALLBACKS accepts colon-separated
# extra candidates and is primarily useful for deterministic automation/tests.

candidates=()
if [[ -n "${CODEX_CLI_PATH:-}" ]]; then
  candidates+=("${CODEX_CLI_PATH}")
fi

if command -v codex >/dev/null 2>&1; then
  candidates+=("$(command -v codex)")
fi

if [[ -n "${CODEX_CLI_FALLBACKS:-}" ]]; then
  old_ifs="${IFS}"
  IFS=':' read -r -a extra_candidates <<<"${CODEX_CLI_FALLBACKS}"
  IFS="${old_ifs}"
  candidates+=("${extra_candidates[@]}")
fi

if [[ "${CODEX_CLI_DISABLE_DEFAULTS:-0}" != "1" ]]; then
  candidates+=(
    "${HOME}/.npm-global/bin/codex"
    "/Applications/ChatGPT.app/Contents/Resources/codex"
    "/Applications/Codex.app/Contents/Resources/codex"
    "/opt/homebrew/bin/codex"
    "/usr/local/bin/codex"
  )
fi

seen=""
attempted=()
for candidate in "${candidates[@]}"; do
  [[ -n "${candidate}" ]] || continue
  if printf '%s\n' "${seen}" | grep -Fqx -- "${candidate}"; then
    continue
  fi
  seen="${seen}${candidate}"$'\n'
  attempted+=("${candidate}")
  if [[ ! -x "${candidate}" ]]; then
    continue
  fi
  if version_output="$("${candidate}" --version 2>/dev/null)" \
    && [[ "${version_output}" =~ ^(codex|codex-cli)[[:space:]]+[0-9] ]]; then
    printf '%s\n' "${candidate}"
    exit 0
  fi
done

echo "No functional Codex CLI found. Candidates must execute '--version' successfully." >&2
for candidate in "${attempted[@]}"; do
  echo "- ${candidate}" >&2
done
exit 127
