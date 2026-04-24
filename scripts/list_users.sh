#!/usr/bin/env bash
set -euo pipefail
MODE=""
REDACT="${NOTION_REDACT_OUTPUT:-}"
for arg in "$@"; do
  case "$arg" in
    --json) MODE="--json" ;;
    --redact) REDACT=1 ;;
    *) echo "Unknown option: $arg" >&2; exit 2 ;;
  esac
done
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT
python3 "$(dirname "$0")/notion_api.py" list-users --page-size 100 > "$TMP"
if [[ "$MODE" == "--json" ]]; then
  cat "$TMP"
else
  NOTION_REDACT_OUTPUT="$REDACT" python3 "$(dirname "$0")/summary_lib.py" users < "$TMP"
fi
