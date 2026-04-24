#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

: "${NOTION_TEST_PARENT_PAGE_ID:?Set NOTION_TEST_PARENT_PAGE_ID to a shared parent page id before running validate_regression_matrix.sh}"
PARENT_PAGE_ID="$NOTION_TEST_PARENT_PAGE_ID"
STAMP="$(date +%s)"
TMP_DIR="$(mktemp -d /tmp/notion-regression-${STAMP}-XXXXXX)"

cleanup() {
  set +e
  if [ -n "${VIEW_ID:-}" ]; then
    python3 scripts/notion_api.py delete-view --view-id "$VIEW_ID" >/dev/null 2>&1 || true
  fi
  if [ -n "${TEMP_DATABASE_ID:-}" ]; then
    python3 scripts/notion_api.py trash-database --database-id "$TEMP_DATABASE_ID" >/dev/null 2>&1 || true
  fi
  if [ -n "${TEMP_PAGE_ID:-}" ]; then
    python3 scripts/notion_api.py trash-page --page-id "$TEMP_PAGE_ID" >/dev/null 2>&1 || true
  fi
  if [ -z "${NOTION_KEEP_VALIDATION_ARTIFACTS:-}" ]; then
    rm -rf "$TMP_DIR"
  fi
}
trap cleanup EXIT

python3 -m py_compile \
  scripts/notion_api.py \
  scripts/selfcheck.py \
  scripts/page_ops.py \
  scripts/update_page_markdown.py \
  scripts/create_database_item.py \
  scripts/create_view_preset.py \
  scripts/wait_for_page_content.py

python3 scripts/selfcheck.py >"$TMP_DIR/selfcheck.json"
grep -q '"api_version": "2026-03-11"' "$TMP_DIR/selfcheck.json"
python3 scripts/notion_api.py get-self >"$TMP_DIR/get-self.json"
python3 scripts/notion_api.py search --query "Migration" --page-size 1 >"$TMP_DIR/search.json"

python3 scripts/page_ops.py create-subpage "$PARENT_PAGE_ID" "Regression page ${STAMP}" >"$TMP_DIR/page-create.json"
TEMP_PAGE_ID="$(python3 - <<PY
import json
print(json.load(open('${TMP_DIR}/page-create.json', 'r', encoding='utf-8'))['id'])
PY
)"

python3 scripts/page_ops.py update-title "$TEMP_PAGE_ID" "Regression page updated ${STAMP}" >"$TMP_DIR/page-update-title.json"
grep -q "Regression page updated ${STAMP}" "$TMP_DIR/page-update-title.json"
python3 scripts/append_block.py "$TEMP_PAGE_ID" paragraph "Regression block ${STAMP}" >"$TMP_DIR/page-append-block.json"
python3 scripts/notion_api.py get-blocks --block-id "$TEMP_PAGE_ID" --page-size 100 >"$TMP_DIR/page-blocks.json"
grep -q "Regression block ${STAMP}" "$TMP_DIR/page-blocks.json"
python3 scripts/update_page_markdown.py "$TEMP_PAGE_ID" replace "Regression markdown ${STAMP}" >"$TMP_DIR/page-markdown-replace.json"
python3 scripts/notion_api.py get-page-markdown --page-id "$TEMP_PAGE_ID" >"$TMP_DIR/page-markdown.json"
grep -q "Regression markdown ${STAMP}" "$TMP_DIR/page-markdown.json"

python3 scripts/notion_api.py create-comment --page-id "$TEMP_PAGE_ID" --markdown "Regression comment ${STAMP}" >"$TMP_DIR/comment-create.json"
COMMENT_ID="$(python3 - <<PY
import json
print(json.load(open('${TMP_DIR}/comment-create.json', 'r', encoding='utf-8'))['id'])
PY
)"
python3 scripts/notion_api.py update-comment --comment-id "$COMMENT_ID" --markdown "Regression comment updated ${STAMP}" >"$TMP_DIR/comment-update.json"
python3 scripts/notion_api.py get-comment --comment-id "$COMMENT_ID" >"$TMP_DIR/comment-get.json"
grep -q "Regression comment updated ${STAMP}" "$TMP_DIR/comment-get.json"
python3 scripts/notion_api.py delete-comment --comment-id "$COMMENT_ID" >"$TMP_DIR/comment-delete.json"

cat >"$TMP_DIR/db-props.json" <<'JSON'
{
  "Name": {"title": {}},
  "Status": {"status": {}}
}
JSON

python3 scripts/notion_api.py create-database \
  --parent-page-id "$PARENT_PAGE_ID" \
  --title "Regression DB ${STAMP}" \
  --properties-file "$TMP_DIR/db-props.json" >"$TMP_DIR/db-create.json"
TEMP_DATABASE_ID="$(python3 - <<PY
import json
obj=json.load(open('${TMP_DIR}/db-create.json', 'r', encoding='utf-8'))
print(obj['id'])
PY
)"
TEMP_DATA_SOURCE_ID="$(python3 - <<PY
import json
obj=json.load(open('${TMP_DIR}/db-create.json', 'r', encoding='utf-8'))
print(obj['data_sources'][0]['id'])
PY
)"
python3 scripts/notion_api.py get-database --database-id "$TEMP_DATABASE_ID" >"$TMP_DIR/db-get.json"
grep -q "Regression DB ${STAMP}" "$TMP_DIR/db-get.json"
python3 scripts/notion_api.py get-data-source --data-source-id "$TEMP_DATA_SOURCE_ID" >"$TMP_DIR/ds-get.json"
TITLE_PROPERTY_NAME="$(python3 - <<PY
import json
props=json.load(open('${TMP_DIR}/ds-get.json', 'r', encoding='utf-8'))['properties']
for name, meta in props.items():
    if meta.get('type') == 'title':
        print(name)
        break
else:
    raise SystemExit('no title property found')
PY
)"
python3 scripts/notion_api.py query-data-source --data-source-id "$TEMP_DATA_SOURCE_ID" >"$TMP_DIR/ds-query-empty.json"
python3 scripts/create_database_item.py "$TEMP_DATA_SOURCE_ID" "$TITLE_PROPERTY_NAME" "Regression item ${STAMP}" >"$TMP_DIR/ds-item-create.json"
ITEM_PAGE_ID="$(python3 - <<PY
import json
print(json.load(open('${TMP_DIR}/ds-item-create.json', 'r', encoding='utf-8'))['id'])
PY
)"
python3 scripts/notion_api.py get-page --page-id "$ITEM_PAGE_ID" >"$TMP_DIR/ds-item-get.json"
grep -q "Regression item ${STAMP}" "$TMP_DIR/ds-item-get.json"

cat >"$TMP_DIR/template-props.json" <<JSON
{
  "$TITLE_PROPERTY_NAME": {
    "title": [
      {"type": "text", "text": {"content": "Regression template item ${STAMP}"}}
    ]
  }
}
JSON
python3 scripts/notion_api.py list-data-source-templates --data-source-id "$TEMP_DATA_SOURCE_ID" --page-size 10 >"$TMP_DIR/templates-list.json"
TEMPLATE_COUNT="$(python3 - <<PY
import json
print(len(json.load(open('${TMP_DIR}/templates-list.json', 'r', encoding='utf-8')).get('templates', [])))
PY
)"
TEMPLATE_PAGE_ID=""
TEMPLATE_MODE=""
if [ "$TEMPLATE_COUNT" -gt 0 ]; then
  TEMPLATE_ID="$(python3 - <<PY
import json
print(json.load(open('${TMP_DIR}/templates-list.json', 'r', encoding='utf-8'))['templates'][0]['id'])
PY
)"
  python3 scripts/notion_api.py create-page \
    --parent-data-source-id "$TEMP_DATA_SOURCE_ID" \
    --template-type template_id \
    --template-id "$TEMPLATE_ID" \
    --properties-file "$TMP_DIR/template-props.json" >"$TMP_DIR/template-create.json"
  TEMPLATE_PAGE_ID="$(python3 - <<PY
import json
print(json.load(open('${TMP_DIR}/template-create.json', 'r', encoding='utf-8'))['id'])
PY
)"
  python3 scripts/notion_api.py get-page --page-id "$TEMPLATE_PAGE_ID" >"$TMP_DIR/template-get.json"
  grep -q "Regression template item ${STAMP}" "$TMP_DIR/template-get.json"
  TEMPLATE_MODE="template_id_success"
else
  if python3 scripts/notion_api.py create-page \
    --parent-data-source-id "$TEMP_DATA_SOURCE_ID" \
    --template-type default \
    --properties-file "$TMP_DIR/template-props.json" >"$TMP_DIR/template-create.json"; then
    TEMPLATE_PAGE_ID="$(python3 - <<PY
import json
print(json.load(open('${TMP_DIR}/template-create.json', 'r', encoding='utf-8'))['id'])
PY
)"
    python3 scripts/notion_api.py get-page --page-id "$TEMPLATE_PAGE_ID" >"$TMP_DIR/template-get.json"
    grep -q "Regression template item ${STAMP}" "$TMP_DIR/template-get.json"
    TEMPLATE_MODE="default_template_success"
  else
    grep -q 'No default template is configured for this data source' "$TMP_DIR/template-create.json"
    TEMPLATE_MODE="expected_no_default_template"
  fi
fi

python3 scripts/create_view_preset.py "$TEMP_DATABASE_ID" "$TEMP_DATA_SOURCE_ID" table-basic "Regression View ${STAMP}" >"$TMP_DIR/view-create.json"
VIEW_ID="$(python3 - <<PY
import json
print(json.load(open('${TMP_DIR}/view-create.json', 'r', encoding='utf-8'))['id'])
PY
)"
python3 scripts/notion_api.py list-views --database-id "$TEMP_DATABASE_ID" --page-size 20 >"$TMP_DIR/view-list.json"
grep -q "$VIEW_ID" "$TMP_DIR/view-list.json"
python3 scripts/notion_api.py get-view --view-id "$VIEW_ID" >"$TMP_DIR/view-get.json"
grep -q "Regression View ${STAMP}" "$TMP_DIR/view-get.json"
python3 scripts/notion_api.py delete-view --view-id "$VIEW_ID" >"$TMP_DIR/view-delete.json"
VIEW_ID=""

python3 scripts/notion_api.py trash-database --database-id "$TEMP_DATABASE_ID" >"$TMP_DIR/db-trash.json"
grep -q '"in_trash": true' "$TMP_DIR/db-trash.json"
python3 scripts/notion_api.py restore-database --database-id "$TEMP_DATABASE_ID" >"$TMP_DIR/db-restore.json"
grep -q '"in_trash": false' "$TMP_DIR/db-restore.json"
python3 scripts/notion_api.py trash-database --database-id "$TEMP_DATABASE_ID" >"$TMP_DIR/db-final-trash.json"
grep -q '"in_trash": true' "$TMP_DIR/db-final-trash.json"
TEMP_DATABASE_ID=""

python3 scripts/notion_api.py trash-page --page-id "$TEMP_PAGE_ID" >"$TMP_DIR/page-trash.json"
grep -q '"in_trash": true' "$TMP_DIR/page-trash.json"
TEMP_PAGE_ID=""

echo "STAMP=$STAMP"
echo "TEMPLATE_MODE=$TEMPLATE_MODE"
if [ -n "${NOTION_KEEP_VALIDATION_ARTIFACTS:-}" ]; then
  echo "ARTIFACTS_DIR=$TMP_DIR"
else
  echo 'ARTIFACTS_RETAINED=0'
fi
echo 'OK_NOTION_REGRESSION_MATRIX=1'
