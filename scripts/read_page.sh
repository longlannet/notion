#!/usr/bin/env bash
set -euo pipefail

PAGE_ID="${1:-}"
if [[ -z "$PAGE_ID" ]]; then
  echo "Usage: $0 <page_id> [--json] [--redact]" >&2
  exit 2
fi

MODE=""
REDACT="${NOTION_REDACT_OUTPUT:-}"
for arg in "${@:2}"; do
  case "$arg" in
    --json) MODE="--json" ;;
    --redact) REDACT=1 ;;
    *) echo "Unknown option: $arg" >&2; exit 2 ;;
  esac
done

PAGE_TMP="$(mktemp)"
BLOCKS_TMP="$(mktemp)"
trap 'rm -f "$PAGE_TMP" "$BLOCKS_TMP"' EXIT

python3 "$(dirname "$0")/notion_api.py" get-page --page-id "$PAGE_ID" > "$PAGE_TMP"
python3 "$(dirname "$0")/notion_api.py" get-blocks --block-id "$PAGE_ID" > "$BLOCKS_TMP"

if [[ "$MODE" == "--json" ]]; then
  cat "$PAGE_TMP"
  printf '\n'
  cat "$BLOCKS_TMP"
else
  NOTION_REDACT_OUTPUT="$REDACT" python3 "$(dirname "$0")/summary_lib.py" page < "$PAGE_TMP"
  printf '\n'
  NOTION_REDACT_OUTPUT="$REDACT" python3 "$(dirname "$0")/summary_lib.py" blocks < "$BLOCKS_TMP"
fi
