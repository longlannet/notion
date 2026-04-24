#!/usr/bin/env bash
set -euo pipefail
STATUS=""
MODE=""
REDACT="${NOTION_REDACT_OUTPUT:-}"
for arg in "$@"; do
  case "$arg" in
    --json) MODE="--json" ;;
    --redact) REDACT=1 ;;
    *)
      if [[ -z "$STATUS" ]]; then
        STATUS="$arg"
      else
        echo "Unexpected extra argument: $arg" >&2
        exit 2
      fi
      ;;
  esac
done
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT
CMD=(python3 "$(dirname "$0")/notion_api.py" list-file-uploads --page-size 100)
if [[ -n "$STATUS" ]]; then
  CMD+=(--status "$STATUS")
fi
"${CMD[@]}" > "$TMP"
if [[ "$MODE" == "--json" ]]; then
  cat "$TMP"
else
  NOTION_REDACT_OUTPUT="$REDACT" python3 "$(dirname "$0")/summary_lib.py" file-uploads < "$TMP"
fi
