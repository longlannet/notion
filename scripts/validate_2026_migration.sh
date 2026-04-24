#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

: "${NOTION_TEST_PARENT_PAGE_ID:?Set NOTION_TEST_PARENT_PAGE_ID to a shared parent page id before running validate_2026_migration.sh}"
PAGE_ID="$NOTION_TEST_PARENT_PAGE_ID"
STAMP="$(date +%s)"
TMP_DIR="$(mktemp -d /tmp/notion-migration-${STAMP}-XXXXXX)"
export TMP_DIR

cleanup() {
  set +e
  if [ -z "${NOTION_KEEP_VALIDATION_ARTIFACTS:-}" ]; then
    rm -rf "$TMP_DIR"
  fi
}
trap cleanup EXIT

python3 scripts/notion_api.py --help >"$TMP_DIR/notion-help.txt"
grep -q 'update-comment' "$TMP_DIR/notion-help.txt"
grep -q 'delete-comment' "$TMP_DIR/notion-help.txt"
python3 scripts/notion_api.py update-page --help >"$TMP_DIR/notion-update-page-help.txt"
grep -q -- '--trash' "$TMP_DIR/notion-update-page-help.txt"
grep -q -- '--restore' "$TMP_DIR/notion-update-page-help.txt"
if grep -q -- '--archive' "$TMP_DIR/notion-update-page-help.txt"; then
  echo 'legacy --archive alias should be hidden from help' >&2
  exit 1
fi

python3 -m py_compile scripts/notion_api.py scripts/selfcheck.py scripts/page_ops.py scripts/update_page_markdown.py
python3 scripts/selfcheck.py >"$TMP_DIR/notion-selfcheck.json"
grep -q '"api_version": "2026-03-11"' "$TMP_DIR/notion-selfcheck.json"
python3 scripts/notion_api.py get-self >"$TMP_DIR/notion-get-self.json"

python3 scripts/notion_api.py create-comment --page-id "$PAGE_ID" --markdown "migration comment create ${STAMP}" >"$TMP_DIR/notion-comment-create.json"
COMMENT_ID="$(python3 - <<'PY'
import json
import os
path = os.environ['TMP_DIR'] + '/notion-comment-create.json'
print(json.load(open(path, 'r', encoding='utf-8'))['id'])
PY
)"
python3 scripts/notion_api.py update-comment --comment-id "$COMMENT_ID" --markdown "migration comment updated ${STAMP}" >"$TMP_DIR/notion-comment-update.json"
python3 scripts/notion_api.py get-comment --comment-id "$COMMENT_ID" >"$TMP_DIR/notion-comment-get.json"
grep -q "migration comment updated ${STAMP}" "$TMP_DIR/notion-comment-get.json"
python3 scripts/notion_api.py delete-comment --comment-id "$COMMENT_ID" >"$TMP_DIR/notion-comment-delete.json"
grep -q '"object": "comment"' "$TMP_DIR/notion-comment-delete.json"

python3 scripts/page_ops.py create-subpage "$PAGE_ID" "Migration temp ${STAMP}" >"$TMP_DIR/notion-temp-page-create.json"
TEMP_PAGE_ID="$(python3 - <<'PY'
import json
import os
path = os.environ['TMP_DIR'] + '/notion-temp-page-create.json'
print(json.load(open(path, 'r', encoding='utf-8'))['id'])
PY
)"

python3 scripts/notion_api.py update-page --page-id "$TEMP_PAGE_ID" --trash >"$TMP_DIR/notion-temp-page-trash.json"
grep -q '"in_trash": true' "$TMP_DIR/notion-temp-page-trash.json"
python3 scripts/notion_api.py update-page --page-id "$TEMP_PAGE_ID" --restore >"$TMP_DIR/notion-temp-page-restore.json"
grep -q '"in_trash": false' "$TMP_DIR/notion-temp-page-restore.json"
python3 scripts/notion_api.py update-page --page-id "$TEMP_PAGE_ID" --archive >"$TMP_DIR/notion-temp-page-archive-alias.json"
grep -q '"in_trash": true' "$TMP_DIR/notion-temp-page-archive-alias.json"
python3 scripts/notion_api.py update-page --page-id "$TEMP_PAGE_ID" --unarchive >"$TMP_DIR/notion-temp-page-unarchive-alias.json"
grep -q '"in_trash": false' "$TMP_DIR/notion-temp-page-unarchive-alias.json"
python3 scripts/notion_api.py update-page --page-id "$TEMP_PAGE_ID" --trash >"$TMP_DIR/notion-temp-page-cleanup-trash.json"
grep -q '"in_trash": true' "$TMP_DIR/notion-temp-page-cleanup-trash.json"

echo "STAMP=$STAMP"
if [ -n "${NOTION_KEEP_VALIDATION_ARTIFACTS:-}" ]; then
  echo "ARTIFACTS_DIR=$TMP_DIR"
else
  echo 'ARTIFACTS_RETAINED=0'
fi
echo 'OK_NOTION_2026_MIGRATION_VALIDATION=1'
