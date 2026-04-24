#!/usr/bin/env bash
set -euo pipefail
PAGE_ID="${1:-}"
TEXT="${2:-}"
REDACT="${NOTION_REDACT_OUTPUT:-}"
MODE="${3:-}"
if [[ -z "$PAGE_ID" || -z "$TEXT" ]]; then
  echo "Usage: $0 <page_id> <text> [--redact]" >&2
  exit 2
fi
if [[ "$MODE" == "--redact" ]]; then
  REDACT=1
elif [[ -n "$MODE" ]]; then
  echo "Unknown option: $MODE" >&2
  exit 2
fi
if [[ -n "$REDACT" ]]; then
  python3 "$(dirname "$0")/notion_api.py" create-comment --page-id "$PAGE_ID" --text "$TEXT" | \
    NOTION_REDACT_OUTPUT=1 python3 "$(dirname "$0")/output_guard.py"
else
  python3 "$(dirname "$0")/notion_api.py" create-comment --page-id "$PAGE_ID" --text "$TEXT"
fi
