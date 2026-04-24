---
name: notion
description: Notion API workflow for searching, reading, creating, and updating pages, data sources, blocks, files, views, and structured records. Use when working with Notion content, schemas, data sources/databases, page markdown, uploads/media, or repeatable Notion automation from the local machine.
homepage: https://developers.notion.com
metadata:
  {
    "openclaw":
      {
        "emoji": "📝",
        "requires": { "env": ["NOTION_API_KEY"] },
        "primaryEnv": "NOTION_API_KEY"
      }
  }
---

# Notion

Use this skill for practical Notion work from the local machine.

For OpenClaw, this is the preferred Notion path right now: token-based, remote-friendly, and already proven to work here. Prefer this skill over hosted Notion MCP unless the user explicitly wants local-client MCP.

Prefer bundled scripts over raw curl or ad-hoc JSON.

## Mental model: page vs database vs data source

On Notion `2026-03-11`, keep these layers straight:

- **page**: normal document-like object; use for notes, freeform content, images, child pages
- **database**: the container/page shell for a structured collection; owns page-level metadata like `parent`, `title`, `is_inline`, `icon`, `cover`, `in_trash`
- **data source**: the structured data layer under a database; owns schema, properties, and query behavior

Practical rule:

- change schema / options / query records → **data source**
- change database title/icon/cover/trash state or inspect `data_sources[]` → **database**
- change freeform content blocks or normal page properties → **page**

## Scope

This skill is focused on the highest-value, local, token-based Notion Data API workflows in this environment.

### In scope

- search / users / pages / blocks
- data sources / databases (with `data_source` as the primary model)
- structured page/item creation and updates
- files / uploads / media
- views
- markdown content endpoints
- templates
- comments

### Out of scope

- full public OAuth lifecycle work
- webhooks / event delivery
- compliance / audit / SIEM surfaces
- official MCP product surface
- link preview product surface
- integration gallery / publishing flows
- legacy database doc parity as a wrapper-expansion goal

## What this skill can do

Use this skill when you need a practical Notion toolbox rather than one single workflow.

### Core capabilities

- search pages and data sources
- read pages, blocks, markdown, property items, users, databases, and data sources
- create/update pages and structured data source items
- append common text blocks and media blocks
- create/query/update data sources and database containers
- manage schema fields and select/multi-select options
- create/list/update/delete views and query cached view results
- upload files and attach external/media content
- create starter pages/templates and import webpages
- create/update/delete comments
- run health/diagnostic helpers before deeper work

### Known scope boundaries

- OAuth helper commands are retained but non-core
- enterprise/compliance/webhook/gallery/MCP surfaces are not the target here
- some special returned surfaces (`meeting_notes`, `transcription`, `unsupported`) should be treated as readback/edge cases, not normal creation targets

### Known bounded edge cases

- `link_to_page` works with `page_id`; `database_id` targets have stricter Notion object-type requirements
- large `relation` / `people` / `rich_text` / `title` / `formula` / `rollup` values may require `get-property` for the full result
- practical nuance from this workspace:
  - a 30-segment `rich_text` value round-trips correctly through property-item retrieval
  - a 30-piece title write was collapsed by Notion into one title segment, so title edge behavior should not be assumed to mirror rich_text exactly
  - `people` high-cardinality behavior is limited here by workspace size and the fact that bots cannot be written into a people property
- `meeting_notes` / `transcription` should be treated as version-sensitive, read-only special block surfaces
- `unsupported` should be treated as a returned/readback surface, not a normal creation target
- `template` block creation and `link_preview` append support should not be treated as missing wrapper work; they are public-API limitations / returned-only surfaces in this workflow

## Operating principles

1. Run `scripts/selfcheck.py` first when auth or connectivity is uncertain.
2. If a failure might be permission/capability/async related, run `scripts/diagnose_capabilities.py`.
3. Prefer the highest-level stable helper that fits the task.
4. Fall back to `scripts/notion_api.py` only when wrappers or unified helpers are not enough.
5. Treat this `SKILL.md` as the primary operating document.

## Validation / regression scripts

Use these when you want a quick confidence pass after changing the skill:

- `bash scripts/validate_2026_migration.sh`
  - focused migration check for the `2026-03-11` switch
  - verifies version pinning, `update-page --trash/--restore`, hidden legacy aliases, selfcheck, and live comment create/update/get/delete
- `bash scripts/validate_regression_matrix.sh`
  - broader live regression pass across page, block, markdown, database, data source, item creation, view creation/list/get/delete, and trash/restore paths
  - template behavior is validated in the most realistic available way for the current workspace:
    - if a live template exists in the temporary data source, it uses `template_id`
    - otherwise it asserts the official expected `default template not configured` validation error instead of falsely treating the environment as a code failure
- `python3 scripts/validate_full_surface.py`
  - full low-level command-surface validation for `scripts/notion_api.py`
  - creates a disposable temporary page tree, exercises page/block/markdown/database/data source/comment/file/view/template paths, and prints `OK_NOTION_FULL_SURFACE=1` on success
  - leaves file-upload objects behind because the current local toolset has no delete path for them; other temporary resources are cleaned up
- `python3 scripts/validate_helper_wrappers.py`
  - end-to-end validation for the high-level helper scripts and shell wrappers
  - creates disposable temporary resources, exercises helper workflows, and prints `OK_NOTION_HELPER_WRAPPERS=1` on success

These scripts require `NOTION_TEST_PARENT_PAGE_ID` to be set explicitly to a shared parent page id before you run them. If you want to retain raw validation artifacts under `/tmp`, set `NOTION_KEEP_VALIDATION_ARTIFACTS=1`.

`scripts/summary_lib.py` is an internal helper used by the shell wrappers for condensed output formatting; do not call it directly unless you are modifying wrapper behavior.

## Authentication / first-run setup

Install the runtime dependency first if needed:

- `pip install requests`

The scripts load the API key in this order:

1. `NOTION_API_KEY`
2. `~/.config/notion/api_key`

Practical rule:

- use `NOTION_API_KEY` for temporary sessions / CI / one-off runs
- use `~/.config/notion/api_key` for normal local use

Recommended long-lived local setup:

```bash
mkdir -p ~/.config/notion
printf '%s\n' 'YOUR_NOTION_API_KEY' > ~/.config/notion/api_key
chmod 600 ~/.config/notion/api_key
```

Important details:

- the file should contain the key itself on a single line
- do **not** store JSON there
- do **not** prefix it with `NOTION_API_KEY=`
- if both the env var and file exist, the env var wins

After setting the key:

1. share the target page, database, or data source with the integration
2. run `python3 scripts/selfcheck.py`
3. if you want a direct identity check, run `python3 scripts/notion_api.py get-self`

Optional retained OAuth helper config is loaded from:

- `NOTION_CLIENT_ID` or `~/.config/notion/client_id`
- `NOTION_CLIENT_SECRET` or `~/.config/notion/client_secret`

For normal local operation, the API key setup above is enough.

## Rules that matter

- Use Notion API version `2026-03-11`.
- The skill has now been migrated to the `2026-03-11` mainline for its primary local CLI/runtime paths (`scripts/notion_api.py`, `scripts/selfcheck.py`).
- Search results may include `data_source` objects as well as pages.
- Use `data_source_id` when querying or creating records under a structured collection.
- Share the target page or data source/database with the integration before assuming permissions are broken.
- Prefer fewer larger writes over many tiny writes.
- For page edits, prefer deterministic helper scripts before inventing custom JSON.
- For webpage ingestion, prefer `import_webpage.py`.
- For starter pages, prefer `create_note_template.py`.
- Comments are available through both shell/script wrappers and low-level API commands; still treat failures as page/capability/share issues before assuming the whole comments surface is broken.
- Current remaining caveats are mostly edge-behavior issues rather than main-path gaps: environment limits (for example `people` high-cardinality behavior), deeper property-item edge cases, and special returned/read-only surfaces (for example `meeting_notes`, `transcription`, `unsupported`).
- `template.type=default` depends on whether the target data source actually has a default template configured; content readiness still matters.
- For large `relation` / `people` / `rich_text` / `title` / `formula` / `rollup` values, prefer property-item retrieval when full results matter.
- Read-only / derived property values should be treated as non-writable: `created_by`, `created_time`, `last_edited_by`, `last_edited_time`, `unique_id`, `formula`, `rollup`, and derived verification fields such as `verification.verified_by` and `verification.date`.
- `place` property writes use live payload keys `lat` and `lon` in this workspace.
- If template-created content may be asynchronous, verify readiness with `wait_for_page_content.py`, block retrieval, or markdown retrieval before claiming success.
- For multiline markdown writes, prefer file-based input (`--content-file`, `--updates-file`) over shell-inline strings.
- For public demos / pasted logs, use redacted output with `NOTION_REDACT_OUTPUT=1` or the shell-wrapper flag `--redact`. This affects the summary wrappers built on `scripts/summary_lib.py`, the helper scripts that print raw JSON through `scripts/output_guard.py`, and the low-level tools `scripts/notion_api.py`, `scripts/selfcheck.py`, and `scripts/diagnose_capabilities.py`; `--json` still returns raw JSON.
- `update-comment` and `delete-comment` are now implemented in `scripts/notion_api.py`; comment create/update both support either `rich_text` or `markdown` request bodies.
- The `2026-03-11` migration is now done for the main local CLI/runtime paths that this skill documents.
- Practical migration notes:
  - `update-page` now writes `in_trash`; `--trash/--restore` are the primary flags
  - legacy `--archive/--unarchive` are kept as compatibility aliases in `scripts/notion_api.py`
  - `meeting_notes` / `transcription` still need to be treated as version-sensitive read-only special surfaces in docs and testing

# Capability map

This section is the primary map of what the skill can do, what to use first, and what low-level path exists underneath.

## 1. Health / diagnosis / identity

### Use these first

- `python3 scripts/selfcheck.py`
- `python3 scripts/diagnose_capabilities.py --page-id PAGE_ID [--check-comments] [--check-markdown] [--template-page-id PAGE_ID]`
- `python3 scripts/notion_api.py get-self`

### What this covers

- auth and API connectivity
- page access / capability diagnostics
- markdown endpoint readiness
- template readiness
- current integration identity

## 2. Search / inspect / read

### Recommended entry points

- `bash scripts/search_pages.sh "关键词" [--json]`
- `bash scripts/search_data_sources.sh "关键词" [--json]`
- `bash scripts/read_page.sh PAGE_ID [--json]`
- `bash scripts/get_data_source.sh DATA_SOURCE_ID [--json]`
- `python3 scripts/page_ops.py read-markdown PAGE_ID`
- `python3 scripts/page_ops.py get-property PAGE_ID PROPERTY_ID`

### What this covers

- page/data source search
- page metadata + block summary readback
- markdown readback
- property-item retrieval for large relations/people/rich_text/title/formula/rollup
- data source schema/metadata inspection

### Low-level alternatives

- `python3 scripts/notion_api.py search --query "关键词" --page-size 10 [--start-cursor CURSOR]`
- `python3 scripts/notion_api.py get-page --page-id PAGE_ID`
- `python3 scripts/notion_api.py get-blocks --block-id PAGE_ID`
- `python3 scripts/notion_api.py get-data-source --data-source-id DATA_SOURCE_ID`
- `python3 scripts/notion_api.py get-page-markdown --page-id PAGE_ID`
- `python3 scripts/notion_api.py get-page-property --page-id PAGE_ID --property-id PROPERTY_ID`

## 3. Page operations

### Recommended entry point

- `python3 scripts/page_ops.py create-subpage PARENT_PAGE_ID "标题"`
- `python3 scripts/page_ops.py update-title PAGE_ID "新标题"`
- `python3 scripts/page_ops.py read-markdown PAGE_ID`
- `python3 scripts/page_ops.py get-property PAGE_ID PROPERTY_ID`

### What this covers

- create child page under a page
- update page title
- retrieve page markdown
- retrieve one page property item

### When to use something else

- if the task is a full content rewrite/update → use `update_page_markdown.py`
- if the task is block append → use `append_block.py`
- if the task needs unusual page-body JSON → use `notion_api.py update-page`

## 4. Block creation / append

### Recommended entry point

- `python3 scripts/append_block.py PAGE_ID paragraph "一段文字"`
- `python3 scripts/append_block.py PAGE_ID heading 2 "二级标题"`
- `python3 scripts/append_block.py PAGE_ID callout "💡" "提示内容"`
- `python3 scripts/append_block.py PAGE_ID todo "待办事项" false`
- `python3 scripts/append_block.py PAGE_ID quote "一句引用"`
- `python3 scripts/append_block.py PAGE_ID divider`
- `python3 scripts/append_block.py PAGE_ID bulleted_list_item "无序列表项"`
- `python3 scripts/append_block.py PAGE_ID numbered_list_item "有序列表项"`
- `python3 scripts/append_block.py PAGE_ID toggle "折叠标题"`
- `python3 scripts/append_block.py PAGE_ID code bash "echo hello"`

### Supported block types in `append_block.py`

- `paragraph`
- `heading` (`1|2|3`)
- `callout`
- `todo`
- `quote`
- `divider`
- `bulleted_list_item`
- `numbered_list_item`
- `toggle`
- `code`

### Low-level alternative

- `python3 scripts/notion_api.py append-blocks --block-id PAGE_ID --children-file body.json`

## 5. Markdown content workflows

### Recommended entry points

- `python3 scripts/update_page_markdown.py PAGE_ID replace --content-file page.md`
- `python3 scripts/update_page_markdown.py PAGE_ID insert "内容" "selector"`
- `python3 scripts/update_page_markdown.py PAGE_ID update --updates-file updates.json`
- `python3 scripts/wait_for_page_content.py PAGE_ID [timeout_seconds] [interval_seconds]`

### What this covers

- replace markdown content
- insert markdown content
- structured markdown update operations
- wait for async template/content hydration

### Notes

- prefer file-based input for multiline content
- `update_page_markdown.py` / `notion_api.py update-page-markdown` do **not** accept arbitrary page-update JSON; they call the special `/pages/{page_id}/markdown` endpoint and require that endpoint's own body schema. Before a first nontrivial write, verify the exact body shape from the wrapper/example script (for example `scripts/diagnose_capabilities.py`) instead of guessing.
- use readiness checks when template-generated content may appear asynchronously

## 6. High-level page workflows

### Recommended entry points

- `python3 scripts/import_webpage.py PARENT_PAGE_ID "页面标题" "https://example.com"`
- `python3 scripts/create_note_template.py PARENT_PAGE_ID "页面标题" general`
- `python3 scripts/create_note_template.py PARENT_PAGE_ID "会议纪要" meeting`
- `python3 scripts/create_note_template.py PARENT_PAGE_ID "项目页" project`

### What this covers

- webpage ingestion into a child page
- structured starter pages/templates

## 7. Data source creation / schema / query

Important distinction:

- `create_data_source.py` is a convenience wrapper that creates an **inline database** with starter schema under a page.
- If you need a normal non-inline database page (for example because you want to manage container cover separately), prefer low-level `notion_api.py create-database`.

### Recommended entry points

- `python3 scripts/create_data_source.py PARENT_PAGE_ID "数据库标题" minimal`
- `python3 scripts/create_data_source.py PARENT_PAGE_ID "数据库标题" rich`
- `bash scripts/get_data_source.sh DATA_SOURCE_ID [--json]`
- `bash scripts/query_data_source.sh DATA_SOURCE_ID [query_json_file] [--json]`
- `python3 scripts/query_data_source_items.py DATA_SOURCE_ID --title-property "名称" --title-query "关键词"`
- `python3 scripts/query_data_source_items.py DATA_SOURCE_ID --property-name "状态" --property-type status --operator equals --value "进行中"`
- `python3 scripts/query_data_source_items.py DATA_SOURCE_ID --filter-file /tmp/filter.json --sorts-file /tmp/sorts.json --page-size 10`

### `create_data_source.py` presets

- `minimal` — title + basic rich_text field
- `rich` — title + richer starter schema (`status`, `multi_select`, `checkbox`, `date`, `select`, `number`, `url`, `email`, `phone_number`, `people`)

### `query_data_source_items.py` modes

- title query: `--title-property` + `--title-query`
- typed property filter: `--property-name` + `--property-type` + `--operator` + `--value`
- advanced query: `--filter-json/--filter-file`, `--sorts-json/--sorts-file`, `--page-size`, `--start-cursor`

### Low-level alternatives

- `python3 scripts/notion_api.py create-database ...`
- `python3 scripts/notion_api.py create-data-source --parent-database-id DATABASE_ID --name "Data source title" [--properties-file schema.json]`
- `python3 scripts/notion_api.py update-database --database-id DATABASE_ID --body-json '{"icon":{"type":"emoji","emoji":"🤝"}}'`
- `python3 scripts/notion_api.py update-data-source --data-source-id DATA_SOURCE_ID --title "New title"`
- `python3 scripts/notion_api.py get-data-source --data-source-id DATA_SOURCE_ID`
- `python3 scripts/notion_api.py query-data-source --data-source-id DATA_SOURCE_ID --body-file body.json`

### `database_ops.py` database container commands

Use these when you want short database-container operations without building JSON by hand:

- `python3 scripts/database_ops.py get DATABASE_ID`
- `python3 scripts/database_ops.py move DATABASE_ID PARENT_PAGE_ID`
- `python3 scripts/database_ops.py trash DATABASE_ID`
- `python3 scripts/database_ops.py restore DATABASE_ID`
- `python3 scripts/database_ops.py set-icon DATABASE_ID "🤝"`
- `python3 scripts/database_ops.py set-cover DATABASE_ID "https://example.com/cover.png"`

## 8. Data source item creation / update

### Recommended entry points

- `python3 scripts/create_database_item.py DATA_SOURCE_ID "Name" "新条目标题"`
- `python3 scripts/update_database_item.py PAGE_ID "文本" "新的字段内容" rich_text`
- `python3 scripts/update_database_item_value.py PAGE_ID "状态" status "已完成"`

### `create_database_item.py`

Creates one new item/page under a `data_source_id`, with a title property plus optional extra properties file.

### `update_database_item.py`

Simple helper for updating one property as:
- `rich_text`
- `title`

### `update_database_item_value.py` supported `property_type`

- `rich_text`
- `title`
- `select`
- `status`
- `checkbox`
- `date`
- `number`
- `multi_select`
- `url`
- `email`
- `phone_number`
- `people`
- `relation`
- `files_file_upload`
- `files_external`

### Notes

- use `update_database_item.py` for simple text/title edits
- use `update_database_item_value.py` for typed property writes
- avoid trying to write read-only/derived properties

## 9. Schema/property operations

### Recommended entry points

- `python3 scripts/add_database_property.py DATA_SOURCE_ID "附件" files`
- `python3 scripts/add_select_property.py DATA_SOURCE_ID "类型" "A,B,C"`
- `python3 scripts/add_multi_select_property.py DATA_SOURCE_ID "标签组" "红,蓝,绿"`
- `python3 scripts/add_relation_property.py DATA_SOURCE_ID "关联记录" RELATED_DATA_SOURCE_ID`
- `python3 scripts/add_rollup_property.py DATA_SOURCE_ID "关联分数" "关联记录" "分数" max`
- `python3 scripts/add_formula_property.py DATA_SOURCE_ID "公式字段" 'prop("分数") + 1'`
- `python3 scripts/add_unique_id_property.py DATA_SOURCE_ID "编号" [prefix]`
- `python3 scripts/update_select_options.py DATA_SOURCE_ID "类型" select "A,B,C,D"`

### What this covers

- add generic schema fields
- add select/multi-select convenience fields
- add relation / rollup / formula / unique-id fields
- update select / multi-select options

## 10. Users / identity lookup

### Recommended entry points

- `bash scripts/list_users.sh [--json]`
- `bash scripts/get_user.sh USER_ID [--json]`
- `python3 scripts/notion_api.py get-self`

### What this covers

- visible workspace users
- one user by id
- current integration/bot identity

### Low-level alternatives

- `python3 scripts/notion_api.py list-users [--page-size 50] [--start-cursor CURSOR]`
- `python3 scripts/notion_api.py get-user --user-id USER_ID`
- `python3 scripts/notion_api.py get-self`

## 11. Files / uploads / media

### Recommended entry points

- `python3 scripts/import_external_file.py "https://example.com/file.pdf" [filename] [content_type]`
- `bash scripts/list_file_uploads.sh [pending|uploaded|expired|failed] [--json]`
- `bash scripts/get_file_upload.sh FILE_UPLOAD_ID [--json]`
- `python3 scripts/append_media_block.py PAGE_ID pdf file_upload FILE_UPLOAD_ID [name] [caption]`
- `python3 scripts/append_media_block.py PAGE_ID image external "https://example.com/a.png" [name] [caption]`
- `python3 scripts/set_page_media.py PAGE_ID icon file_upload FILE_UPLOAD_ID`
- `python3 scripts/set_page_media.py PAGE_ID cover external "https://example.com/cover.png"`
- `python3 scripts/set_database_media.py DATABASE_ID icon emoji "🤝"`
- `python3 scripts/database_ops.py set-cover DATABASE_ID "https://example.com/cover.png"`
- `python3 scripts/notion_api.py create-file-upload --mode single_part --filename file.txt --content-type text/plain`
- `python3 scripts/notion_api.py send-file-upload --file-upload-id FILE_UPLOAD_ID --file-path ./local-file.txt`
- `python3 scripts/notion_api.py complete-file-upload --file-upload-id FILE_UPLOAD_ID`

### `append_media_block.py` supported block/media combinations

Block types:
- `file`
- `pdf`
- `image`
- `audio`
- `video`

Source types:
- `file_upload`
- `external`

### `set_page_media.py` supported targets

- `icon`
- `cover`

Source types:
- `file_upload`
- `external`

### `set_database_media.py` supported targets

- `icon`
- `cover`

Source types:
- `emoji`
- `file_upload`
- `external`

### Low-level alternatives

- `python3 scripts/notion_api.py get-file-upload --file-upload-id FILE_UPLOAD_ID`
- `python3 scripts/notion_api.py list-file-uploads [--status pending|uploaded|expired|failed]`
- `python3 scripts/notion_api.py create-file-upload --mode single_part --filename file.txt --content-type text/plain`
- `python3 scripts/notion_api.py send-file-upload --file-upload-id FILE_UPLOAD_ID --file-path ./local-file.txt`
- `python3 scripts/notion_api.py complete-file-upload --file-upload-id FILE_UPLOAD_ID`

Notes:
- `cover` should be used on a **non-inline database page**.
- If the database lives under an archived ancestor, unarchive/move the ancestor first before editing cover/icon.

## 12. Views

### Recommended entry points

- `python3 scripts/create_view_preset.py DATABASE_ID DATA_SOURCE_ID table-basic "视图名"`
- `python3 scripts/notion_api.py list-views --data-source-id DATA_SOURCE_ID`
- `python3 scripts/notion_api.py get-view --view-id VIEW_ID`
- `python3 scripts/notion_api.py create-view --body-file create-view.json`
- `python3 scripts/notion_api.py update-view --view-id VIEW_ID --body-file update-view.json`
- `python3 scripts/notion_api.py delete-view --view-id VIEW_ID`
- `python3 scripts/notion_api.py create-view-query --view-id VIEW_ID`
- `python3 scripts/notion_api.py get-view-query-results --view-id VIEW_ID --query-id QUERY_ID`
- `python3 scripts/notion_api.py delete-view-query --view-id VIEW_ID --query-id QUERY_ID`

### Note

- `create_view_preset.py` is the quickest path when you just want a usable table view.
- Low-level view commands remain available when you need exact JSON control.

## 13. Templates

### Recommended path

- `python3 scripts/create_note_template.py ...`
- `python3 scripts/wait_for_page_content.py PAGE_ID ...`

### Low-level path

- `python3 scripts/notion_api.py list-data-source-templates --data-source-id DATA_SOURCE_ID`
- `python3 scripts/notion_api.py create-page --parent-data-source-id DATA_SOURCE_ID --template-type default --properties-file props.json`
- `python3 scripts/notion_api.py create-page --parent-data-source-id DATA_SOURCE_ID --template-type template_id --template-id TEMPLATE_ID --properties-file props.json`

### Note

Template-created content may hydrate asynchronously; verify readiness before declaring success.

## 14. Comments

### Available commands

- `bash scripts/create_comment.sh PAGE_ID "评论内容"`
- `python3 scripts/notion_api.py create-comment --page-id PAGE_ID --text "评论内容"`
- `python3 scripts/notion_api.py create-comment --page-id PAGE_ID --markdown "**inline** _markdown_"`
- `python3 scripts/notion_api.py update-comment --comment-id COMMENT_ID --text "新内容"`
- `python3 scripts/notion_api.py update-comment --comment-id COMMENT_ID --markdown "**Updated** comment"`
- `python3 scripts/notion_api.py delete-comment --comment-id COMMENT_ID`
- `python3 scripts/notion_api.py list-comments [--block-id BLOCK_ID]`
- `python3 scripts/notion_api.py get-comment --comment-id COMMENT_ID`

### Practical note

If comments fail on some target, treat it as a page/capability/share issue first, not as proof that the whole comments feature is unavailable.

## 15. Optional retained OAuth helpers (non-core)

These command paths are still present in `scripts/notion_api.py`, but they are **not part of the core local skill scope, core validation, or completion bar** for this workspace.

### Available commands

- `python3 scripts/notion_api.py create-token --grant-type authorization_code --code CODE [--redirect-uri URI --client-id ID --client-secret SECRET]`
- `python3 scripts/notion_api.py create-token --grant-type refresh_token --refresh-token TOKEN [--client-id ID --client-secret SECRET]`
- `python3 scripts/notion_api.py revoke-token --token TOKEN [--client-id ID --client-secret SECRET]`
- `python3 scripts/notion_api.py introspect-token [--token TOKEN --client-id CLIENT_ID --client-secret CLIENT_SECRET]`

### Status

Retained for completeness and future productization, but intentionally excluded from the current main workflow and main validation story.

## 16. Lower-level but available commands

Use these when the higher-level helpers are not enough:

- `python3 scripts/notion_api.py get-block --block-id BLOCK_ID`
- `python3 scripts/notion_api.py get-database --database-id DATABASE_ID`
- `python3 scripts/notion_api.py update-block --block-id BLOCK_ID --body-file body.json`
- `python3 scripts/notion_api.py delete-block --block-id BLOCK_ID`
- `python3 scripts/notion_api.py move-page --page-id PAGE_ID --parent-page-id PAGE_ID`
- `python3 scripts/notion_api.py trash-page --page-id PAGE_ID`
- `python3 scripts/notion_api.py restore-page --page-id PAGE_ID`
- `python3 scripts/notion_api.py move-database --database-id DATABASE_ID --parent-page-id PAGE_ID`
- `python3 scripts/notion_api.py trash-database --database-id DATABASE_ID`
- `python3 scripts/notion_api.py restore-database --database-id DATABASE_ID`
- `python3 scripts/notion_api.py restore-block --block-id BLOCK_ID`
- `python3 scripts/notion_api.py create-data-source --parent-database-id DATABASE_ID ...`
- `python3 scripts/notion_api.py update-data-source --data-source-id DATA_SOURCE_ID ...`
- `python3 scripts/notion_api.py list-users [--page-size 50]`
- `python3 scripts/notion_api.py get-user --user-id USER_ID`
- `python3 scripts/notion_api.py get-file-upload --file-upload-id FILE_UPLOAD_ID`
- `python3 scripts/notion_api.py list-file-uploads [--status STATUS]`
- `python3 scripts/notion_api.py list-custom-emojis [--name EMOJI_NAME]`

## Fast-path command summary

If you only need the shortest route:

- search page/data source → `search_pages.sh` / `search_data_sources.sh`
- read page → `read_page.sh`
- read markdown / property → `page_ops.py`
- create subpage / update title → `page_ops.py`
- append common blocks → `append_block.py`
- create inline starter database → `create_data_source.py`
- create normal non-inline database → `notion_api.py create-database`
- inspect/query data source → `get_data_source.sh`, `query_data_source.sh`, `query_data_source_items.py`
- inspect database container → `notion_api.py get-database` or `database_ops.py get`
- create/update structured item → `create_database_item.py`, `update_database_item.py`, `update_database_item_value.py`
- schema/property changes → `add_*_property.py`, `update_database_property.py`, `update_select_options.py`
- file/media work → `import_external_file.py`, `append_media_block.py`, `set_page_media.py`, `set_database_media.py`
- database container ops → `database_ops.py`
- quick view preset creation → `create_view_preset.py`
- template/start page creation → `create_note_template.py`
- webpage import → `import_webpage.py`
- diagnose issues → `selfcheck.py`, `diagnose_capabilities.py`
- validate low-level command surface → `validate_full_surface.py`
- validate helper wrappers → `validate_helper_wrappers.py`

## Failure handling

- If `selfcheck.py` fails with auth issues, verify `NOTION_API_KEY` or `~/.config/notion/api_key`.
- If reads/writes return permission errors, verify the target page or data source/database is shared with the integration.
- If search returns a `data_source`, do not treat it as a page automatically; use the correct ID type for the next step.
- If a template-created page looks empty, check readiness rather than assuming failure.
- If a large property looks truncated, use `page_ops.py get-property` / low-level property-item retrieval.
- If database cover edits fail, check whether the target is inline or under an archived ancestor.
