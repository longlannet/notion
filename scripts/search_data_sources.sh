#!/usr/bin/env bash
set -euo pipefail

QUERY="${1:-}"
if [[ -z "$QUERY" ]]; then
  echo "Usage: $0 <query> [--json] [--redact]" >&2
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

FILTER='{"value":"data_source","property":"object"}'
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT
python3 "$(dirname "$0")/notion_api.py" search --query "$QUERY" --filter-json "$FILTER" > "$TMP"
if [[ "$MODE" == "--json" ]]; then
  cat "$TMP"
else
  NOTION_REDACT_OUTPUT="$REDACT" python3 "$(dirname "$0")/summary_lib.py" search < "$TMP"
fi
