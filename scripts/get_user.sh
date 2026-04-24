#!/usr/bin/env bash
set -euo pipefail
USER_ID="${1:-}"
if [[ -z "$USER_ID" ]]; then
  echo "Usage: $0 <user_id> [--json] [--redact]" >&2
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
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT
python3 "$(dirname "$0")/notion_api.py" get-user --user-id "$USER_ID" > "$TMP"
if [[ "$MODE" == "--json" ]]; then
  cat "$TMP"
else
  NOTION_REDACT_OUTPUT="$REDACT" python3 "$(dirname "$0")/summary_lib.py" user < "$TMP"
fi
