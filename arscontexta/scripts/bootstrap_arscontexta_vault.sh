#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bootstrap_arscontexta_vault.sh <root_dir> [notes_dir] [inbox_dir]

Examples:
  bootstrap_arscontexta_vault.sh /path/to/workspace
  bootstrap_arscontexta_vault.sh /path/to/workspace claims captures
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

ROOT_INPUT="${1:-}"
NOTES_DIR="${2:-notes}"
INBOX_DIR="${3:-inbox}"

if [[ -z "$ROOT_INPUT" ]]; then
  usage
  exit 1
fi

mkdir -p "$ROOT_INPUT"
ROOT_DIR="$(cd "$ROOT_INPUT" && pwd)"

mkdir -p \
  "$ROOT_DIR/self" \
  "$ROOT_DIR/$NOTES_DIR" \
  "$ROOT_DIR/$INBOX_DIR" \
  "$ROOT_DIR/ops/queue" \
  "$ROOT_DIR/ops/health" \
  "$ROOT_DIR/ops/sessions" \
  "$ROOT_DIR/ops/tensions" \
  "$ROOT_DIR/ops/observations"

IDENTITY_FILE="$ROOT_DIR/self/identity.md"
if [[ ! -f "$IDENTITY_FILE" ]]; then
  cat >"$IDENTITY_FILE" <<'EOF'
# Identity

## Mission
Maintain a durable and navigable knowledge graph.

## Operating Principles
- Prefer explicit reasoning over opaque summaries.
- Update existing context before creating duplicate notes.
- Keep provenance for every important claim.
EOF
fi

MOC_FILE="$ROOT_DIR/$NOTES_DIR/moc-index.md"
if [[ ! -f "$MOC_FILE" ]]; then
  cat >"$MOC_FILE" <<'EOF'
---
type: moc
description: Top-level map of content.
---

# MOC Index

## Core Topics
- [[topic-example]]
EOF
fi

MANIFEST_FILE="$ROOT_DIR/ops/derivation-manifest.md"
if [[ ! -f "$MANIFEST_FILE" ]]; then
  cat >"$MANIFEST_FILE" <<EOF
# Derivation Manifest

## Vocabulary
- notes_dir: $NOTES_DIR
- inbox_dir: $INBOX_DIR

## Architecture
- spaces: self, $NOTES_DIR, ops
- methodology: arscontexta-6r
EOF
fi

QUEUE_FILE="$ROOT_DIR/ops/queue/queue.yaml"
if [[ ! -f "$QUEUE_FILE" ]]; then
  cat >"$QUEUE_FILE" <<'EOF'
version: 1
tasks: []
EOF
fi

SESSION_FILE="$ROOT_DIR/ops/sessions/session-template.md"
if [[ ! -f "$SESSION_FILE" ]]; then
  cat >"$SESSION_FILE" <<'EOF'
# Session Summary

## Changes
- 

## Verification
- 

## Next
- 
EOF
fi

echo "Ars Contexta workspace initialized at: $ROOT_DIR"
echo "Notes dir: $NOTES_DIR"
echo "Inbox dir: $INBOX_DIR"
