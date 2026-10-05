# Optional ntn CLI and Workers reference

This is supplementary knowledge retained from the Hermes community skill (MIT, author: community). **Bundled Python/shell scripts remain the preferred workflow on both platforms.** This reference does not change their `2026-03-11` API pin or database/data-source model. Do not copy the old HTTP pin or old raw create/update/upload bodies into the current toolbox.

## Preconditions and scope

- Use `ntn` only if already available or the user authorizes a separate installation. Check `ntn --version` and local `ntn --help`; this merge does not install it.
- Historical Hermes notes described macOS/Linux support, Node 22+/npm 10+, and Windows via WSL2. Check the current official CLI docs before relying on those version/platform claims.
- Resolve `NOTION_API_KEY` from the current platform's authorized environment, not from another platform's secret store. In a child shell, when using token-based CLI authentication:

```bash
export NOTION_API_TOKEN="$NOTION_API_KEY"
export NOTION_KEYRING=0
```

- `NOTION_API_TOKEN` selects the integration token. `NOTION_KEYRING=0` avoids the OS keychain; older notes describe file-based credential storage at `~/.config/notion/auth.json`. Do not run an unnecessary login flow or print tokens.
- `NOTION_WORKSPACE_ID` can avoid a workspace picker. Confirm access by sharing the target with the integration; a 404 can be an access problem.
- `ntn` manages its own request headers. Inspect its current help/docs rather than assuming it uses the same version as the bundled scripts. For exact `2026-03-11` payload/version control, use the bundled scripts.

## CLI syntax and read-only recipes

- `key=value` assigns a string.
- `key[nested]=value` supplies nested fields; quote assignments in shells that glob brackets.
- `key:=value` supplies a typed value (boolean, number, null, array).
- `--json -` can accept a JSON request body via stdin (confirm with the installed CLI help).

```bash
ntn api v1/users
ntn api v1/search query="page title"
ntn api v1/pages/{page_id}
ntn api v1/pages/{page_id}/markdown
ntn api v1/blocks/{page_id}/children
ntn api v1/data_sources/{data_source_id}/query -X POST   'filter[property]=Status' 'filter[select][equals]=Active'
```

All of these contact Notion; they are **not offline merge validation**. Paginate result sets and preserve exact IDs. Queries use a `data_source_id`; databases remain separate containers. Respect rate limits and read back the exact target after authorized writes.

## File uploads (authorized writes only)

```bash
ntn files create < photo.png
ntn files create --external-url https://example.com/photo.png
ntn files list
```

These are optional CLI conveniences, not replacements for the main skill's reviewed upload helpers. The bundled flow uses create upload → send bytes → complete when required → reference upload ID. Do not reuse the old generic PUT-to-upload-URL example.

## Notion Workers (optional; outside the core toolbox)


Workers are TypeScript programs Notion hosts for you. One worker can expose any combination of:
- **Syncs** — pull data from external APIs into a Notion database on a schedule (default 30 min).
- **Tools** — appear as callable tools inside Notion's Custom Agents.
- **Webhooks** — receive HTTP events from external services (GitHub, Stripe, etc.) and act in Notion.

**Historical scope, recheck before deployment:** earlier Hermes notes described Business/Enterprise gating for Workers, macOS/Linux CLI support and credit-based billing after an introductory free period. These are not verified current entitlements or prices. Check https://developers.notion.com/workers and the installed CLI before deployment.

**Authorization boundary:** scaffold, deploy, trigger, pause and environment-setting commands below change local or remote state. They are examples for separately authorized Worker work, never skill-merge tests. Verify the deployed worker and target workspace after any authorized change; never treat successful CLI exit alone as delivery verification.

### Minimal Worker

```bash
ntn workers new my-worker      # scaffold
cd my-worker
# Edit src/index.ts
ntn workers deploy --name my-worker
```

`src/index.ts`:
```typescript
import { Worker } from "@notionhq/workers";

const worker = new Worker();
export default worker;

worker.tool("greet", {
  title: "Greet a User",
  description: "Returns a friendly greeting",
  inputSchema: { type: "object", properties: { name: { type: "string" } }, required: ["name"] },
  execute: async ({ name }) => `Hello, ${name}!`,
});
```

### Webhook capability

```typescript
worker.webhook("onGithubPush", {
  title: "GitHub Push Handler",
  execute: async (events, { notion }) => {
    for (const event of events) {
      // event.body, event.rawBody (for signature verification), event.headers
      console.log("got delivery", event.deliveryId);
    }
  },
});
```

After deploy: `ntn workers webhooks list` shows the URL Notion generates. Treat that URL as a secret — anyone with it can POST events unless you add signature verification.

### Worker lifecycle commands

```bash
ntn workers deploy
ntn workers list
ntn workers exec <capability-key> -d '{"name": "world"}'
ntn workers sync trigger <key>            # run a sync now
ntn workers sync pause <key>
ntn workers env set GITHUB_WEBHOOK_SECRET=...
ntn workers runs list                     # recent invocations
ntn workers runs logs <run-id>
ntn workers webhooks list
```

When separately authorized to build and deploy a Worker, scaffold with `ntn workers new`, write the code in `src/index.ts`, set any secrets with `ntn workers env set`, and deploy. Notion's docs at https://developers.notion.com/workers cover the full API surface.

## Property payload reference

Common property formats for database items:

- **Title:** `{"title": [{"text": {"content": "..."}}]}`
- **Rich text:** `{"rich_text": [{"text": {"content": "..."}}]}`
- **Select:** `{"select": {"name": "Option"}}`
- **Multi-select:** `{"multi_select": [{"name": "A"}, {"name": "B"}]}`
- **Date:** `{"date": {"start": "2026-01-15", "end": "2026-01-16"}}`
- **Checkbox:** `{"checkbox": true}`
- **Number:** `{"number": 42}`
- **URL:** `{"url": "https://..."}`
- **Email:** `{"email": "user@example.com"}`
- **Relation:** `{"relation": [{"id": "page_id"}]}`

## Notion-Flavored Markdown (used by `/markdown` endpoints)

Standard CommonMark plus XML-like tags for Notion-specific blocks. Use **tabs** for indentation.

**Blocks beyond CommonMark:**
```
<callout icon="🎯" color="blue_bg">
	Ship the MVP by **Friday**.
</callout>

<details color="gray">
<summary>Toggle title</summary>
	Children indented one tab
</details>

<columns>
	<column>Left side</column>
	<column>Right side</column>
</columns>

<table_of_contents color="gray"/>
```

**Inline:**
- Mentions: `<mention-user url="..."/>`, `<mention-page url="...">Title</mention-page>`, `<mention-date start="2026-05-15"/>`
- Underline: `<span underline="true">text</span>`
- Color: `<span color="blue">text</span>` or block-level `{color="blue"}` on the first line
- Math: inline `$x^2$`, block `$$ ... $$`
- Citations: `[^https://example.com]`

**Colors:** `gray brown orange yellow green blue purple pink red`, plus `*_bg` variants for backgrounds.

Headings 5/6 collapse to H4. Multiple `>` lines render as separate quote blocks — use `<br>` inside a single `>` for multi-line quotes.


Treat markdown dialect features as version-sensitive; the main script wrappers determine update request bodies. Do not infer that every tag can be created as a public API block. See [block types](block-types.md).
