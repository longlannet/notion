**🌐 Language / 语言：** [English](./README.md) | [简体中文](./README.zh-CN.md)

# Notion Skill

> A Notion Data API toolbox for **OpenClaw** and local automation workflows.  
> It combines one unified CLI, a set of high-frequency helpers, and runnable validation scripts to make the most valuable Notion workflows **reusable, maintainable, and verifiable**.

**Status at a glance**

- **API version**: `2026-03-11`
- **Core entrypoint**: `scripts/notion_api.py`
- **Current shape**: unified low-level CLI + high-level helper scripts + regression/validation scripts
- **Script count**: 32 Python scripts / 12 Shell scripts
- **Main capabilities**: pages, blocks, markdown, data sources/databases, schema, files, comments, views, templates

---

## Quick Navigation

- [What problem this repository solves](#what-problem-this-repository-solves)
- [Highlights](#highlights)
- [Project Structure](#project-structure)
- [Installation and Configuration](#installation-and-configuration)
- [Quick Start](#quick-start)
- [Common Commands](#common-commands)
- [Validation and Regression](#validation-and-regression)
- [Coverage and Boundaries](#coverage-and-boundaries)
- [When to Use This Repository](#when-to-use-this-repository)
- [License](#license)
- [Related Files](#related-files)

---

## What Problem This Repository Solves

If you only need to call the Notion API once in a while, hand-written requests are fine.

This repository is for a different class of work:

- the same Notion operations repeat over and over
- hand-building JSON payloads is slow and error-prone
- the main workflows need shorter, more stable command paths
- after changing code, you want a quick way to know whether you broke the main paths
- you want something reusable from OpenClaw, shell scripts, and local automation tasks

So this is not just a collection of API examples. It is a **local Notion automation toolbox**.

---

## Highlights

- **One clear entrypoint**: low-level capability is centralized in `scripts/notion_api.py`
- **Helpers for common work**: less manual JSON for day-to-day tasks
- **Not just happy-path wrappers**: includes self-check, capability diagnosis, template readiness waiting, property-item retrieval, and more
- **Not just "docs say it works"**: includes runnable validation and regression scripts
- **Version is explicit**: the mainline is pinned to `2026-03-11`
- **Scope is clear**: strong-coverage areas, edge cases, and out-of-scope surfaces are documented separately

---

## What You Can Do With It

### Pages and content

- Search pages and data sources
- Read pages, blocks, markdown, and property items
- Create pages and subpages
- Update page titles and properties
- Append, update, delete, and restore blocks
- Replace, insert, and update page content via markdown

### Data sources and databases

- Create databases and data sources
- Query data sources
- Create structured records
- Update item properties
- Manage schema fields, properties, and options
- Work with relation / rollup / formula / files and other common schema types

### Files, comments, views, templates

- Upload files and attach media content
- Set page / database icons and covers
- Create, read, update, and delete comments
- Create, read, update, and delete views
- Create pages from templates
- Wait for asynchronous template content hydration

### Engineering support

- Environment self-check
- Capability diagnosis
- Full-surface validation
- Helper regression validation
- Version-migration validation
- Regression matrix checks

---

## Project Structure

```text
notion/
├── README.md
├── README.zh-CN.md
├── SKILL.md
├── scripts/
│   ├── notion_api.py
│   ├── selfcheck.py
│   ├── diagnose_capabilities.py
│   ├── page_ops.py
│   ├── append_block.py
│   ├── update_page_markdown.py
│   ├── wait_for_page_content.py
│   ├── create_data_source.py
│   ├── create_database_item.py
│   ├── update_database_item.py
│   ├── update_database_item_value.py
│   ├── create_view_preset.py
│   ├── import_external_file.py
│   ├── import_webpage.py
│   ├── set_page_media.py
│   ├── set_database_media.py
│   ├── validate_full_surface.py
│   ├── validate_helper_wrappers.py
│   ├── validate_2026_migration.sh
│   └── validate_regression_matrix.sh
└── .gitignore
```

Root-level temporary fixtures and non-essential notes have been cleaned up.

### Layered design

**1) Unified low-level CLI**

`scripts/notion_api.py` is the core entrypoint. It handles:

- loading authentication
- setting the Notion API version header
- parsing JSON input
- returning consistent error output
- exposing subcommands for the major capability surfaces

**2) High-frequency helper scripts**

These scripts turn repeated tasks into shorter and more stable automation paths, for example:

- `page_ops.py`
- `append_block.py`
- `update_page_markdown.py`
- `create_data_source.py`
- `create_database_item.py`
- `update_database_item_value.py`
- `create_view_preset.py`
- `set_page_media.py`
- `set_database_media.py`

**3) Validation and regression scripts**

These scripts are here to prove that:

- the low-level command surface actually works
- helper scripts are not just decorative wrappers
- main workflows survive API version migration
- future changes can be checked quickly with regression runs

---

## Installation and Configuration

### 1) Prepare the runtime

Make sure you have:

- Python 3
- `requests`

Install dependencies if needed:

```bash
pip install requests
```

### 2) Get a Notion API key

This repository is designed around the **token-based path**, not OAuth as the main workflow.

Create a Notion integration first, then get its API key.

Once you have the key, scripts load it in this order:

1. `NOTION_API_KEY`
2. `~/.config/notion/api_key`

That means:

- **if both exist, the environment variable wins**
- **if you do not want to export it every time, the file-based setup is recommended**

### 3) Where to put the API key

You have two options.

#### Option A: environment variable

Best for temporary sessions:

```bash
export NOTION_API_KEY="your_notion_api_key"
```

Useful for:

- quick testing
- one-off shell sessions
- CI / automation environments

#### Option B: local config file

Best for long-term local use.

**File path:**

```bash
~/.config/notion/api_key
```

**Recommended setup:**

```bash
mkdir -p ~/.config/notion
printf '%s\n' 'your_notion_api_key' > ~/.config/notion/api_key
chmod 600 ~/.config/notion/api_key
```

**Important:**

- the file should contain **only the key itself on a single line**
- do not store JSON
- do not prefix it with `NOTION_API_KEY=`
- do not add extra comments or wrappers

Correct example:

```text
secret_xxx or notion_key_xxx
```

Wrong examples:

```text
NOTION_API_KEY=secret_xxx
```

```json
{"api_key":"secret_xxx"}
```

### 4) Share the target page/database with the integration

Even with the correct API key, you will still get permission errors if the target page, database, or data source is **not shared with the integration**.

After configuration, make sure the resources you want to operate on are shared with the right integration.

### 5) Verify the setup

The simplest check is:

```bash
python3 scripts/selfcheck.py
```

If you want a more direct identity check:

```bash
python3 scripts/notion_api.py get-self
```

### Current pinned API version

- **Notion-Version: `2026-03-11`**

### Optional: OAuth helper locations

OAuth is not the mainline workflow here, but if you later use the retained OAuth helpers, the code reads from:

- `NOTION_CLIENT_ID` or `~/.config/notion/client_id`
- `NOTION_CLIENT_SECRET` or `~/.config/notion/client_secret`

For most local use cases, **configuring `api_key` is enough**.

---

## Quick Start

### 1) Run a self-check

```bash
python3 scripts/selfcheck.py
```

### 2) Search and read a page

```bash
bash scripts/search_pages.sh "keyword"
bash scripts/read_page.sh PAGE_ID
python3 scripts/page_ops.py read-markdown PAGE_ID
```

### 3) Create a subpage and append content

```bash
python3 scripts/page_ops.py create-subpage PARENT_PAGE_ID "New Page"
python3 scripts/append_block.py PAGE_ID paragraph "A paragraph"
python3 scripts/append_block.py PAGE_ID heading 2 "Section Title"
```

### 4) Create a data source and write one record

```bash
python3 scripts/create_data_source.py PARENT_PAGE_ID "Example DB" rich
python3 scripts/create_database_item.py DATA_SOURCE_ID "Name" "First Record"
python3 scripts/update_database_item_value.py PAGE_ID "Status" status "In Progress"
```

### 5) Update markdown or create a comment

```bash
python3 scripts/update_page_markdown.py PAGE_ID replace --content-file page.md
python3 scripts/notion_api.py create-comment --page-id PAGE_ID --text "This page looks good"
```

---

## Common Commands

This section focuses on the most common 80% paths.

### Search and read

If you want safer summary output for public demos or pasted logs, use redaction mode:

```bash
NOTION_REDACT_OUTPUT=1 bash scripts/search_pages.sh "keyword"
```

`--redact` is also supported by the main shell wrappers. Many Python helper scripts that would otherwise print raw JSON also respect `NOTION_REDACT_OUTPUT=1`, and the low-level tools `scripts/notion_api.py`, `scripts/selfcheck.py`, and `scripts/diagnose_capabilities.py` now accept `--redact` as well. Note that `--json` still returns raw JSON.

```bash
bash scripts/search_pages.sh "keyword"
bash scripts/search_data_sources.sh "keyword"
bash scripts/read_page.sh PAGE_ID
bash scripts/get_data_source.sh DATA_SOURCE_ID
bash scripts/query_data_source.sh DATA_SOURCE_ID
python3 scripts/page_ops.py get-property PAGE_ID PROPERTY_ID
```

### Pages and blocks

```bash
python3 scripts/page_ops.py create-subpage PARENT_PAGE_ID "Title"
python3 scripts/page_ops.py update-title PAGE_ID "Updated Title"
python3 scripts/append_block.py PAGE_ID paragraph "text"
python3 scripts/append_block.py PAGE_ID todo "task" false
python3 scripts/notion_api.py delete-block --block-id BLOCK_ID
python3 scripts/notion_api.py restore-block --block-id BLOCK_ID
```

### Markdown

```bash
python3 scripts/update_page_markdown.py PAGE_ID replace --content-file page.md
python3 scripts/update_page_markdown.py PAGE_ID insert "content" "selector"
python3 scripts/wait_for_page_content.py PAGE_ID
```

### Data sources, items, schema

```bash
python3 scripts/create_data_source.py PARENT_PAGE_ID "Database" minimal
python3 scripts/create_database_item.py DATA_SOURCE_ID "Name" "Item"
python3 scripts/update_database_item.py PAGE_ID "Text" "Updated content" rich_text
python3 scripts/update_database_item_value.py PAGE_ID "Status" status "Done"
python3 scripts/add_database_property.py DATA_SOURCE_ID "Attachments" files
python3 scripts/add_select_property.py DATA_SOURCE_ID "Type" "A,B,C"
python3 scripts/add_relation_property.py DATA_SOURCE_ID "Related" RELATED_DATA_SOURCE_ID
```

### Files, views, comments

```bash
python3 scripts/import_external_file.py "https://example.com/file.pdf" sample.pdf application/pdf
python3 scripts/set_page_media.py PAGE_ID icon external "https://example.com/icon.png"
python3 scripts/create_view_preset.py DATABASE_ID DATA_SOURCE_ID table-basic "Overview"
python3 scripts/notion_api.py list-views --data-source-id DATA_SOURCE_ID
python3 scripts/notion_api.py create-comment --page-id PAGE_ID --text "Comment"
python3 scripts/notion_api.py update-comment --comment-id COMMENT_ID --markdown "**Updated comment**"
```

For the fuller command surface, check:

- `SKILL.md`
- `scripts/notion_api.py --help`

---

## Validation and Regression

Before running the validation scripts, set a shared parent page id explicitly:

```bash
export NOTION_TEST_PARENT_PAGE_ID="your_shared_parent_page_id"
```

If you want to keep raw validation artifacts under `/tmp` for debugging, also set:

```bash
export NOTION_KEEP_VALIDATION_ARTIFACTS=1
```

### Version-migration validation

```bash
bash scripts/validate_2026_migration.sh
```

Main checks include:

- version pinning
- trash / restore semantics
- compatibility aliases
- comment create / update / get / delete

### Regression matrix

```bash
bash scripts/validate_regression_matrix.sh
```

Runs a broader live regression check across the main workflows.

### Full low-level surface validation

```bash
python3 scripts/validate_full_surface.py
```

Success marker:

```text
OK_NOTION_FULL_SURFACE=1
```

### Helper-wrapper validation

```bash
python3 scripts/validate_helper_wrappers.py
```

Success marker:

```text
OK_NOTION_HELPER_WRAPPERS=1
```

Both validation scripts write a `summary.json` with:

- PASS / BLOCKED / WARN details
- temporary resource IDs
- cleanup notes

---

## Coverage and Boundaries

The goal of this repository is:

> **high practical coverage of the Notion Data API for local automation workflows**.

### Strongly covered areas

- pages
- blocks
- markdown
- databases / data sources
- schema / property operations
- files / media
- views
- comments
- templates

### Explicitly not the current main target

- public OAuth lifecycle as the primary workflow
- webhooks / event delivery
- compliance / SIEM
- MCP product surface
- link previews as a product surface
- integration gallery / publishing

### Known boundaries

These are better treated as edge surfaces than core helper guarantees:

- version-sensitive special block types such as `meeting_notes` / `transcription`
- returned-only / unsupported block families
- environment-dependent workflows such as webpage import
- some high-cardinality property edge cases that depend more on workspace conditions than script limitations

The practical boundaries above are the current working baseline for this repository.

---

## When to Use This Repository

This repository is a good fit if you need:

- local, scriptable Notion operations
- stable page and content automation
- structured data source / database writes
- schema and property management
- file, media, comment, and view automation
- a Notion toolchain with regression support

If you only need to try a few API calls once, raw requests may be enough.

If you want something:

- reusable
- maintainable
- verifiable
- suitable for OpenClaw, shell, or local automation

then this repository is a much better fit.

---

## License

This repository is released under the **MIT License**. See [`LICENSE`](./LICENSE).

---

## Related Files

- `SKILL.md` — agent-facing operational instructions
- `scripts/notion_api.py` — low-level CLI entrypoint

---

## Summary

This is not a repository of random example scripts for the Notion API.

It is better understood as a **local Notion automation toolbox**:

- broad coverage across the mainline Data API workflows
- clear layering: low-level CLI + helper scripts + validation scripts
- good fit for repeated local automation tasks
- explicit regression and version-migration awareness
- clear scope boundaries

If your goal is just to poke the API occasionally, it may be heavier than you need.

If your goal is to plug stable Notion workflows into OpenClaw, local shell tasks, or automation jobs, this repository is built for exactly that.

> **Make the most valuable local Notion workflows reliable, scriptable, and verifiable.**
