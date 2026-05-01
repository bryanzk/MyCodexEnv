#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./query_scan_address_tag.sh --chain <chain> --address <address>

Examples:
  ./query_scan_address_tag.sh --chain ethereum --address 0x63242a4ea82847b20e506b63b0e2e2eff0cc6cb0
EOF
}

normalize_lower() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]'
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "missing command: $1" >&2
    exit 2
  fi
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
    *)
      echo "unsupported scan fallback chain: $1" >&2
      return 1
      ;;
  esac
}

html_unescape() {
  perl -CS -Mutf8 -pe '
    s/&amp;/&/g;
    s/&quot;/"/g;
    s/&#39;/'"'"'/g;
    s/&lt;/</g;
    s/&gt;/>/g;
    s/&#10;/\n/g;
    s/&#x([0-9A-Fa-f]+);/chr(hex($1))/eg;
    s/&#([0-9]+);/chr($1)/eg;
  '
}

extract_public_name_tag() {
  perl -0ne '
    if (/title='\''Public Name Tag \(viewable by anyone\)[^'\'']*'\''.*?<span class='\''hash-tag[^'\'']*'\''[^>]*>([^<]+)<\/span>/s) {
      print "$1\n";
    }
  '
}

extract_labels() {
  perl -0ne '
    while (/href='\''(\/accounts\/label\/[^'\'']+)'\''[^>]*>.*?<span class='\''hash-tag[^'\'']*'\''[^>]*>([^<]+)<\/span>/sg) {
      print "$1\t$2\n";
    }
  '
}

CHAIN=""
ADDRESS=""
USER_AGENT="${EIGENPHI_SCAN_USER_AGENT:-Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0 Safari/537.36}"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --chain)
      CHAIN="${2:-}"
      shift 2
      ;;
    --address)
      ADDRESS="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [ -z "$CHAIN" ] || [ -z "$ADDRESS" ]; then
  usage >&2
  exit 2
fi

CHAIN="$(normalize_lower "$CHAIN")"
ADDRESS="$(normalize_lower "$ADDRESS")"

if ! printf '%s\n' "$ADDRESS" | rg -q '^0x[0-9a-f]{40}$'; then
  echo "invalid address: $ADDRESS" >&2
  exit 2
fi

require_cmd curl
require_cmd perl
require_cmd rg

SCAN_BASE="$(chain_scan_base "$CHAIN")"
ADDRESS_URL="${SCAN_BASE%/}/address/$ADDRESS"
HTML="$(curl -L -A "$USER_AGENT" -fsS "$ADDRESS_URL")"

FOUND=0
HEADER_PRINTED=0

print_header_once() {
  if [ "$HEADER_PRINTED" -eq 0 ]; then
    printf '== explorer ==\n'
    HEADER_PRINTED=1
  fi
}

PUBLIC_TAG="$(
  printf '%s' "$HTML" \
  | extract_public_name_tag \
  | html_unescape \
  | awk 'NF { print; exit }'
)"

if [ -n "$PUBLIC_TAG" ]; then
  print_header_once
  printf 'tag: %s\n' "$PUBLIC_TAG"
  printf 'source: %s\n' "$ADDRESS_URL"
  printf 'detail: public name tag\n\n'
  FOUND=1
fi

LABEL_ROWS="$(
  printf '%s' "$HTML" \
  | extract_labels \
  | while IFS=$'\t' read -r href label; do
      [ -n "$href" ] || continue
      [ -n "$label" ] || continue
      printf '%s\t%s\n' "${SCAN_BASE%/}${href}" "$label"
    done \
  | awk '!seen[$0]++'
)"

if [ -n "$LABEL_ROWS" ]; then
  while IFS=$'\t' read -r source label; do
    [ -n "$source" ] || continue
    [ -n "$label" ] || continue
    print_header_once
    printf 'tag: %s\n' "$label"
    printf 'source: %s\n' "$source"
    printf 'detail: explorer label\n\n'
    FOUND=1
  done <<EOF
$LABEL_ROWS
EOF
fi

if [ "$FOUND" -eq 0 ]; then
  printf 'no explorer tags found for address %s on chain %s\n' "$ADDRESS" "$CHAIN" >&2
  exit 1
fi
