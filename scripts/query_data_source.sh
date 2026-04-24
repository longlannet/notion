#!/usr/bin/env bash
set -euo pipefail

DATA_SOURCE_ID="${1:-}"
if [[ -z "$DATA_SOURCE_ID" ]]; then
  echo "Usage: $0 <data_source_id> [query_json_file] [--json] [--redact]" >&2
  exit 2
fi

BODY_FILE=""
MODE=""
REDACT="${NOTION_REDACT_OUTPUT:-}"
for arg in "${@:2}"; do
  case "$arg" in
    --json) MODE="--json" ;;
    --redact) REDACT=1 ;;
    *)
      if [[ -z "$BODY_FILE" ]]; then
        BODY_FILE="$arg"
      else
        echo "Unexpected extra argument: $arg" >&2
        exit 2
      fi
      ;;
  esac
done

TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT
if [[ -n "$BODY_FILE" ]]; then
  python3 "$(dirname "$0")/notion_api.py" query-data-source --data-source-id "$DATA_SOURCE_ID" --body-file "$BODY_FILE" > "$TMP"
else
  python3 "$(dirname "$0")/notion_api.py" query-data-source --data-source-id "$DATA_SOURCE_ID" > "$TMP"
fi

if [[ "$MODE" == "--json" ]]; then
  cat "$TMP"
else
  NOTION_REDACT_OUTPUT="$REDACT" python3 "$(dirname "$0")/summary_lib.py" query < "$TMP"
fi
