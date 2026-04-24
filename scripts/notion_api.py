#!/usr/bin/env python3
import argparse
import json
import os
import sys
from pathlib import Path

import requests
from output_guard import emit_output_text

API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2026-03-11"
TIMEOUT = 30


def maybe_enable_redaction(argv: list[str]) -> list[str]:
    cleaned = []
    redact = False
    for arg in argv:
        if arg == '--redact':
            redact = True
        else:
            cleaned.append(arg)
    if redact:
        os.environ['NOTION_REDACT_OUTPUT'] = '1'
    return cleaned


def load_api_key() -> str:
    env_key = os.environ.get("NOTION_API_KEY", "").strip()
    if env_key:
        return env_key
    p = Path.home() / ".config" / "notion" / "api_key"
    if p.exists():
        key = p.read_text(encoding="utf-8").strip()
        if key:
            return key
    raise SystemExit("Notion API key not found. Set NOTION_API_KEY or ~/.config/notion/api_key")


def headers() -> dict:
    return {
        "Authorization": f"Bearer {load_api_key()}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def oauth_client_id() -> str:
    v = os.environ.get("NOTION_CLIENT_ID", "").strip()
    if v:
        return v
    p = Path.home() / ".config" / "notion" / "client_id"
    if p.exists():
        v = p.read_text(encoding="utf-8").strip()
        if v:
            return v
    raise SystemExit("Notion OAuth client id not found. Set NOTION_CLIENT_ID or ~/.config/notion/client_id")


def oauth_client_secret() -> str:
    v = os.environ.get("NOTION_CLIENT_SECRET", "").strip()
    if v:
        return v
    p = Path.home() / ".config" / "notion" / "client_secret"
    if p.exists():
        v = p.read_text(encoding="utf-8").strip()
        if v:
            return v
    raise SystemExit("Notion OAuth client secret not found. Set NOTION_CLIENT_SECRET or ~/.config/notion/client_secret")


def load_json_arg(json_text: str | None, file_path: str | None, default=None):
    if json_text and file_path:
        raise SystemExit("Use either inline JSON or --*-file, not both")
    if file_path:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    if json_text:
        return json.loads(json_text)
    return default


def request(method: str, path: str, body=None):
    url = f"{API_BASE}{path}"
    resp = requests.request(method, url, headers=headers(), json=body, timeout=TIMEOUT)
    try:
        data = resp.json()
    except Exception:
        data = {"status_code": resp.status_code, "text": resp.text}
    if not resp.ok:
        emit_output_text(json.dumps({"ok": False, "status_code": resp.status_code, "response": data}, ensure_ascii=False, indent=2))
        raise SystemExit(1)
    emit_output_text(json.dumps(data, ensure_ascii=False, indent=2))


def oauth_request(path: str, body: dict, client_id: str, client_secret: str):
    resp = requests.post(
        f"{API_BASE}{path}",
        headers={
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        },
        auth=(client_id, client_secret),
        json=body,
        timeout=TIMEOUT,
    )
    try:
        data = resp.json()
    except Exception:
        data = {"status_code": resp.status_code, "text": resp.text}
    if not resp.ok:
        emit_output_text(json.dumps({"ok": False, "status_code": resp.status_code, "response": data}, ensure_ascii=False, indent=2))
        raise SystemExit(1)
    emit_output_text(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_search(args):
    body = {"query": args.query}
    if args.filter_json or args.filter_file:
        body["filter"] = load_json_arg(args.filter_json, args.filter_file)
    if args.page_size:
        body["page_size"] = args.page_size
    if args.start_cursor:
        body["start_cursor"] = args.start_cursor
    request("POST", "/search", body)


def cmd_get_page(args):
    request("GET", f"/pages/{args.page_id}")


def cmd_get_page_property(args):
    path = f"/pages/{args.page_id}/properties/{args.property_id}"
    query = []
    if args.start_cursor:
        query.append(f"start_cursor={args.start_cursor}")
    if args.page_size:
        query.append(f"page_size={args.page_size}")
    if query:
        path += "?" + "&".join(query)
    request("GET", path)


def cmd_get_blocks(args):
    suffix = f"?page_size={args.page_size}"
    if args.start_cursor:
        suffix += f"&start_cursor={args.start_cursor}"
    request("GET", f"/blocks/{args.block_id}/children{suffix}")


def cmd_create_page(args):
    body = {}
    if args.parent_database_id:
        body["parent"] = {"database_id": args.parent_database_id}
    elif args.parent_data_source_id:
        body["parent"] = {"type": "data_source_id", "data_source_id": args.parent_data_source_id}
    elif args.parent_page_id:
        body["parent"] = {"page_id": args.parent_page_id}
    else:
        raise SystemExit("Provide --parent-database-id, --parent-data-source-id, or --parent-page-id")

    props = load_json_arg(args.properties_json, args.properties_file, default={})
    children = load_json_arg(args.children_json, args.children_file)
    if props:
        body["properties"] = props

    if args.template_type or args.template_id or args.template_timezone:
        template = {"type": args.template_type or ("template_id" if args.template_id else "default")}
        if template["type"] == "template_id":
            if not args.template_id:
                raise SystemExit("template_id template type requires --template-id")
            template["template_id"] = args.template_id
        elif args.template_id:
            raise SystemExit("--template-id requires --template-type template_id")
        if args.template_timezone:
            template["timezone"] = args.template_timezone
        body["template"] = template
        if children is not None:
            raise SystemExit("children cannot be specified when using a template")
    elif children is not None:
        body["children"] = children
    request("POST", "/pages", body)


def cmd_update_page(args):
    body = load_json_arg(args.body_json, args.body_file, default={})
    if not body and (args.properties_json or args.properties_file):
        body = {"properties": load_json_arg(args.properties_json, args.properties_file, default={})}
    if args.in_trash is not None:
        body["in_trash"] = args.in_trash
    if not body:
        raise SystemExit("No update payload provided")
    request("PATCH", f"/pages/{args.page_id}", body)


def cmd_append_blocks(args):
    children = load_json_arg(args.children_json, args.children_file)
    if not isinstance(children, list) or not children:
        raise SystemExit("children must be a non-empty JSON array")
    request("PATCH", f"/blocks/{args.block_id}/children", {"children": children})


def cmd_query_data_source(args):
    body = load_json_arg(args.body_json, args.body_file, default={})
    request("POST", f"/data_sources/{args.data_source_id}/query", body)


def cmd_get_data_source(args):
    request("GET", f"/data_sources/{args.data_source_id}")


def cmd_list_users(args):
    path = "/users"
    query = []
    if args.start_cursor:
        query.append(f"start_cursor={args.start_cursor}")
    if args.page_size:
        query.append(f"page_size={args.page_size}")
    if query:
        path += "?" + "&".join(query)
    request("GET", path)


def cmd_get_user(args):
    request("GET", f"/users/{args.user_id}")


def cmd_list_custom_emojis(args):
    path = '/custom_emojis'
    query = []
    if args.name:
        query.append(f'name={args.name}')
    if args.start_cursor:
        query.append(f'start_cursor={args.start_cursor}')
    if args.page_size:
        query.append(f'page_size={args.page_size}')
    if query:
        path += '?' + '&'.join(query)
    request('GET', path)


def cmd_get_self(args):
    request("GET", "/users/me")


def cmd_introspect_token(args):
    client_id = args.client_id or oauth_client_id()
    client_secret = args.client_secret or oauth_client_secret()
    token = args.token or load_api_key()
    oauth_request('/oauth/introspect', {"token": token}, client_id, client_secret)


def cmd_create_token(args):
    client_id = args.client_id or oauth_client_id()
    client_secret = args.client_secret or oauth_client_secret()
    body = load_json_arg(args.body_json, args.body_file)
    if body is None:
        if args.grant_type == 'authorization_code':
            if not args.code:
                raise SystemExit('authorization_code flow requires --code')
            body = {
                'grant_type': 'authorization_code',
                'code': args.code,
            }
            if args.redirect_uri:
                body['redirect_uri'] = args.redirect_uri
            if args.external_account_key or args.external_account_name:
                if not (args.external_account_key and args.external_account_name):
                    raise SystemExit('external account requires both --external-account-key and --external-account-name')
                body['external_account'] = {
                    'key': args.external_account_key,
                    'name': args.external_account_name,
                }
        else:
            if not args.refresh_token:
                raise SystemExit('refresh_token flow requires --refresh-token')
            body = {
                'grant_type': 'refresh_token',
                'refresh_token': args.refresh_token,
            }
    oauth_request('/oauth/token', body, client_id, client_secret)


def cmd_revoke_token(args):
    client_id = args.client_id or oauth_client_id()
    client_secret = args.client_secret or oauth_client_secret()
    body = load_json_arg(args.body_json, args.body_file)
    if body is None:
        if not args.token:
            raise SystemExit('revoke-token requires --token or --body-json/--body-file')
        body = {'token': args.token}
    oauth_request('/oauth/revoke', body, client_id, client_secret)


def cmd_create_database(args):
    body = {}
    if args.parent_page_id:
        body["parent"] = {"type": "page_id", "page_id": args.parent_page_id}
    elif args.workspace:
        body["parent"] = {"type": "workspace", "workspace": True}
    else:
        raise SystemExit("Provide --parent-page-id or --workspace")

    if args.title:
        body["title"] = [{"type": "text", "text": {"content": args.title}}]
    if args.description:
        body["description"] = [{"type": "text", "text": {"content": args.description}}]
    if args.is_inline:
        body["is_inline"] = True

    initial_properties = load_json_arg(args.properties_json, args.properties_file)
    if initial_properties is not None:
        body["initial_data_source"] = {"properties": initial_properties}

    request("POST", "/databases", body)


def cmd_get_database(args):
    request("GET", f"/databases/{args.database_id}")


def cmd_create_data_source(args):
    body = load_json_arg(args.body_json, args.body_file, default={})
    if args.parent_database_id:
        body["parent"] = {"type": "database_id", "database_id": args.parent_database_id}
    if args.name:
        body["name"] = args.name
    if args.description:
        body["description"] = [{"type": "text", "text": {"content": args.description}}]
    if args.properties_json or args.properties_file:
        body["properties"] = load_json_arg(args.properties_json, args.properties_file, default={})
    if not body or "parent" not in body:
        raise SystemExit("create-data-source requires --parent-database-id plus optional body/properties/name")
    request("POST", "/data_sources", body)


def cmd_update_data_source(args):
    body = load_json_arg(args.body_json, args.body_file, default={})
    if not body and (args.properties_json or args.properties_file):
        body = {"properties": load_json_arg(args.properties_json, args.properties_file, default={})}
    if args.title:
        body["title"] = [{"type": "text", "text": {"content": args.title}}]
    if args.in_trash is not None:
        body["in_trash"] = args.in_trash
    if not body:
        raise SystemExit("No update payload provided")
    request("PATCH", f"/data_sources/{args.data_source_id}", body)


def cmd_update_database(args):
    body = load_json_arg(args.body_json, args.body_file, default={})
    if args.title:
        body["title"] = [{"type": "text", "text": {"content": args.title}}]
    if args.description:
        body["description"] = [{"type": "text", "text": {"content": args.description}}]
    if args.in_trash is not None:
        body["in_trash"] = args.in_trash
    if not body:
        raise SystemExit("No update payload provided")
    request("PATCH", f"/databases/{args.database_id}", body)


def build_comment_body(args, require_parent=False):
    body = load_json_arg(getattr(args, 'body_json', None), getattr(args, 'body_file', None))
    if body is not None:
        if not isinstance(body, dict) or not body:
            raise SystemExit('comment body must be a non-empty JSON object')
    else:
        rich_text = load_json_arg(getattr(args, 'rich_text_json', None), getattr(args, 'rich_text_file', None))
        has_text = getattr(args, 'text', None) is not None
        has_markdown = getattr(args, 'markdown', None) is not None
        has_rich_text = rich_text is not None
        if sum(1 for flag in [has_text, has_markdown, has_rich_text] if flag) != 1:
            raise SystemExit('Provide exactly one of --text, --markdown, --rich-text-json/--rich-text-file, or --body-json/--body-file')
        if has_text:
            body = {
                'rich_text': [
                    {
                        'type': 'text',
                        'text': {'content': args.text}
                    }
                ]
            }
        elif has_markdown:
            body = {'markdown': args.markdown}
        else:
            if not isinstance(rich_text, list) or not rich_text:
                raise SystemExit('rich_text must be a non-empty JSON array')
            body = {'rich_text': rich_text}

    if require_parent:
        if args.page_id:
            body['parent'] = {'page_id': args.page_id}
        elif args.block_id:
            body['parent'] = {'block_id': args.block_id}
        elif args.discussion_id:
            body['discussion_id'] = args.discussion_id
        else:
            raise SystemExit('Provide --page-id, --block-id, or --discussion-id')
    return body


def cmd_create_comment(args):
    body = build_comment_body(args, require_parent=True)
    request('POST', '/comments', body)


def cmd_update_comment(args):
    body = build_comment_body(args, require_parent=False)
    request('PATCH', f'/comments/{args.comment_id}', body)


def cmd_delete_comment(args):
    request('DELETE', f'/comments/{args.comment_id}')


def cmd_create_file_upload(args):
    body = {}
    if args.mode:
        body['mode'] = args.mode
    if args.filename:
        body['filename'] = args.filename
    if args.content_type:
        body['content_type'] = args.content_type
    if args.number_of_parts is not None:
        body['number_of_parts'] = args.number_of_parts
    if args.external_url:
        body['external_url'] = args.external_url
    request('POST', '/file_uploads', body)


def cmd_complete_file_upload(args):
    request('POST', f'/file_uploads/{args.file_upload_id}/complete', {})


def cmd_send_file_upload(args):
    url = f'{API_BASE}/file_uploads/{args.file_upload_id}/send'
    hdrs = {
        'Authorization': f'Bearer {load_api_key()}',
        'Notion-Version': NOTION_VERSION,
    }
    with open(args.file_path, 'rb') as f:
        files = {'file': (args.filename or Path(args.file_path).name, f, args.content_type or 'application/octet-stream')}
        data = {}
        if args.part_number is not None:
            data['part_number'] = str(args.part_number)
        resp = requests.post(url, headers=hdrs, files=files, data=data, timeout=TIMEOUT)
    try:
        obj = resp.json()
    except Exception:
        obj = {'status_code': resp.status_code, 'text': resp.text}
    if not resp.ok:
        emit_output_text(json.dumps({'ok': False, 'status_code': resp.status_code, 'response': obj}, ensure_ascii=False, indent=2))
        raise SystemExit(1)
    emit_output_text(json.dumps(obj, ensure_ascii=False, indent=2))


def cmd_get_file_upload(args):
    request('GET', f'/file_uploads/{args.file_upload_id}')


def cmd_list_file_uploads(args):
    path = '/file_uploads'
    query = []
    if args.status:
        query.append(f'status={args.status}')
    if args.start_cursor:
        query.append(f'start_cursor={args.start_cursor}')
    if args.page_size:
        query.append(f'page_size={args.page_size}')
    if query:
        path += '?' + '&'.join(query)
    request('GET', path)


def cmd_list_views(args):
    path = '/views'
    query = []
    if args.database_id:
        query.append(f'database_id={args.database_id}')
    if args.data_source_id:
        query.append(f'data_source_id={args.data_source_id}')
    if args.start_cursor:
        query.append(f'start_cursor={args.start_cursor}')
    if args.page_size:
        query.append(f'page_size={args.page_size}')
    if query:
        path += '?' + '&'.join(query)
    request('GET', path)


def cmd_get_view(args):
    request('GET', f'/views/{args.view_id}')


def cmd_create_view_query(args):
    body = {}
    if args.page_size:
        body['page_size'] = args.page_size
    request('POST', f'/views/{args.view_id}/queries', body)


def cmd_get_view_query_results(args):
    path = f'/views/{args.view_id}/queries/{args.query_id}'
    query = []
    if args.start_cursor:
        query.append(f'start_cursor={args.start_cursor}')
    if args.page_size:
        query.append(f'page_size={args.page_size}')
    if query:
        path += '?' + '&'.join(query)
    request('GET', path)


def cmd_delete_view_query(args):
    request('DELETE', f'/views/{args.view_id}/queries/{args.query_id}')


def cmd_create_view(args):
    body = load_json_arg(args.body_json, args.body_file)
    if not isinstance(body, dict) or not body:
        raise SystemExit('create-view requires a non-empty JSON object via --body-json or --body-file')
    request('POST', '/views', body)


def cmd_update_view(args):
    body = load_json_arg(args.body_json, args.body_file)
    if not isinstance(body, dict) or not body:
        raise SystemExit('update-view requires a non-empty JSON object via --body-json or --body-file')
    request('PATCH', f'/views/{args.view_id}', body)


def cmd_delete_view(args):
    request('DELETE', f'/views/{args.view_id}')


def cmd_get_page_markdown(args):
    path = f'/pages/{args.page_id}/markdown'
    query = []
    if args.include_transcript:
        query.append('include_transcript=true')
    if query:
        path += '?' + '&'.join(query)
    request('GET', path)


def cmd_list_comments(args):
    path = '/comments'
    query = []
    if args.block_id:
        query.append(f'block_id={args.block_id}')
    if args.start_cursor:
        query.append(f'start_cursor={args.start_cursor}')
    if args.page_size:
        query.append(f'page_size={args.page_size}')
    if query:
        path += '?' + '&'.join(query)
    request('GET', path)


def cmd_get_comment(args):
    request('GET', f'/comments/{args.comment_id}')


def cmd_get_block(args):
    request('GET', f'/blocks/{args.block_id}')


def cmd_update_block(args):
    body = load_json_arg(args.body_json, args.body_file)
    if not isinstance(body, dict) or not body:
        raise SystemExit('update-block requires a non-empty JSON object via --body-json or --body-file')
    request('PATCH', f'/blocks/{args.block_id}', body)


def cmd_delete_block(args):
    request('DELETE', f'/blocks/{args.block_id}')


def cmd_move_page(args):
    body = {'parent': {}}
    if args.parent_page_id:
        body['parent'] = {'type': 'page_id', 'page_id': args.parent_page_id}
    elif args.parent_data_source_id:
        body['parent'] = {'type': 'data_source_id', 'data_source_id': args.parent_data_source_id}
    else:
        raise SystemExit('move-page requires --parent-page-id or --parent-data-source-id')
    request('POST', f'/pages/{args.page_id}/move', body)


def cmd_trash_page(args):
    request('PATCH', f'/pages/{args.page_id}', {'in_trash': True})


def cmd_restore_page(args):
    request('PATCH', f'/pages/{args.page_id}', {'in_trash': False})


def cmd_restore_block(args):
    request('PATCH', f'/blocks/{args.block_id}', {'in_trash': False})


def cmd_move_database(args):
    body = {'parent': {}}
    if args.parent_page_id:
        body['parent'] = {'type': 'page_id', 'page_id': args.parent_page_id}
    elif args.workspace:
        body['parent'] = {'type': 'workspace', 'workspace': True}
    else:
        raise SystemExit('move-database requires --parent-page-id or --workspace')
    request('PATCH', f'/databases/{args.database_id}', body)


def cmd_trash_database(args):
    request('PATCH', f'/databases/{args.database_id}', {'in_trash': True})


def cmd_restore_database(args):
    request('PATCH', f'/databases/{args.database_id}', {'in_trash': False})


def cmd_update_page_markdown(args):
    body = load_json_arg(args.body_json, args.body_file)
    if not isinstance(body, dict) or not body:
        raise SystemExit('update-page-markdown requires a non-empty JSON object via --body-json or --body-file')
    request('PATCH', f'/pages/{args.page_id}/markdown', body)


def cmd_list_data_source_templates(args):
    path = f'/data_sources/{args.data_source_id}/templates'
    query = []
    if args.name:
        query.append(f'name={args.name}')
    if args.start_cursor:
        query.append(f'start_cursor={args.start_cursor}')
    if args.page_size:
        query.append(f'page_size={args.page_size}')
    if query:
        path += '?' + '&'.join(query)
    request('GET', path)


def build_parser():
    p = argparse.ArgumentParser(description="Notion API CLI")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("search", help="Search pages and data sources")
    s.add_argument("--query", required=True)
    s.add_argument("--filter-json")
    s.add_argument("--filter-file")
    s.add_argument("--page-size", type=int)
    s.add_argument("--start-cursor")
    s.set_defaults(func=cmd_search)

    s = sub.add_parser("get-page", help="Get page metadata")
    s.add_argument("--page-id", required=True)
    s.set_defaults(func=cmd_get_page)

    s = sub.add_parser("get-database", help="Get database metadata")
    s.add_argument("--database-id", required=True)
    s.set_defaults(func=cmd_get_database)

    s = sub.add_parser("get-page-property", help="Get one page property item")
    s.add_argument("--page-id", required=True)
    s.add_argument("--property-id", required=True)
    s.add_argument("--page-size", type=int)
    s.add_argument("--start-cursor")
    s.set_defaults(func=cmd_get_page_property)

    s = sub.add_parser("get-blocks", help="Get block children")
    s.add_argument("--block-id", required=True)
    s.add_argument("--page-size", type=int, default=100)
    s.add_argument("--start-cursor")
    s.set_defaults(func=cmd_get_blocks)

    s = sub.add_parser("create-page", help="Create a page under a page, database, or data source")
    s.add_argument("--parent-database-id")
    s.add_argument("--parent-data-source-id")
    s.add_argument("--parent-page-id")
    s.add_argument("--properties-json")
    s.add_argument("--properties-file")
    s.add_argument("--children-json")
    s.add_argument("--children-file")
    s.add_argument("--template-type", choices=["default", "template_id", "none"])
    s.add_argument("--template-id")
    s.add_argument("--template-timezone")
    s.set_defaults(func=cmd_create_page)

    s = sub.add_parser("update-page", help="Update page properties or trash state")
    s.add_argument("--page-id", required=True)
    s.add_argument("--body-json")
    s.add_argument("--body-file")
    s.add_argument("--properties-json")
    s.add_argument("--properties-file")
    ag = s.add_mutually_exclusive_group()
    ag.add_argument("--trash", dest="in_trash", action="store_true")
    ag.add_argument("--restore", dest="in_trash", action="store_false")
    ag.add_argument("--archive", dest="in_trash", action="store_true", help=argparse.SUPPRESS)
    ag.add_argument("--unarchive", dest="in_trash", action="store_false", help=argparse.SUPPRESS)
    s.set_defaults(in_trash=None)
    s.set_defaults(func=cmd_update_page)

    s = sub.add_parser("append-blocks", help="Append child blocks")
    s.add_argument("--block-id", required=True)
    s.add_argument("--children-json")
    s.add_argument("--children-file")
    s.set_defaults(func=cmd_append_blocks)

    s = sub.add_parser("query-data-source", help="Query a data source")
    s.add_argument("--data-source-id", required=True)
    s.add_argument("--body-json")
    s.add_argument("--body-file")
    s.set_defaults(func=cmd_query_data_source)

    s = sub.add_parser("get-data-source", help="Get data source metadata")
    s.add_argument("--data-source-id", required=True)
    s.set_defaults(func=cmd_get_data_source)

    s = sub.add_parser("list-users", help="List workspace users")
    s.add_argument("--start-cursor")
    s.add_argument("--page-size", type=int)
    s.set_defaults(func=cmd_list_users)

    s = sub.add_parser("get-user", help="Get one user by id")
    s.add_argument("--user-id", required=True)
    s.set_defaults(func=cmd_get_user)

    s = sub.add_parser("list-custom-emojis", help="List custom emojis in the workspace")
    s.add_argument("--name")
    s.add_argument("--page-size", type=int)
    s.add_argument("--start-cursor")
    s.set_defaults(func=cmd_list_custom_emojis)

    s = sub.add_parser("get-self", help="Retrieve the bot user for the current token")
    s.set_defaults(func=cmd_get_self)

    s = sub.add_parser("introspect-token", help="Introspect a token using OAuth client credentials")
    s.add_argument("--token")
    s.add_argument("--client-id")
    s.add_argument("--client-secret")
    s.set_defaults(func=cmd_introspect_token)

    s = sub.add_parser("create-token", help="Exchange an authorization code or refresh token for access/refresh tokens")
    s.add_argument("--grant-type", required=True, choices=["authorization_code", "refresh_token"])
    s.add_argument("--code")
    s.add_argument("--redirect-uri")
    s.add_argument("--external-account-key")
    s.add_argument("--external-account-name")
    s.add_argument("--refresh-token")
    s.add_argument("--client-id")
    s.add_argument("--client-secret")
    s.add_argument("--body-json")
    s.add_argument("--body-file")
    s.set_defaults(func=cmd_create_token)

    s = sub.add_parser("revoke-token", help="Revoke an access token using OAuth client credentials")
    s.add_argument("--token")
    s.add_argument("--client-id")
    s.add_argument("--client-secret")
    s.add_argument("--body-json")
    s.add_argument("--body-file")
    s.set_defaults(func=cmd_revoke_token)

    s = sub.add_parser("create-database", help="Create a database under a page or workspace")
    s.add_argument("--parent-page-id")
    s.add_argument("--workspace", action="store_true")
    s.add_argument("--title")
    s.add_argument("--description")
    s.add_argument("--is-inline", action="store_true")
    s.add_argument("--properties-json")
    s.add_argument("--properties-file")
    s.set_defaults(func=cmd_create_database)

    s = sub.add_parser("create-data-source", help="Create a data source under a database")
    s.add_argument("--parent-database-id", required=True)
    s.add_argument("--name")
    s.add_argument("--description")
    s.add_argument("--body-json")
    s.add_argument("--body-file")
    s.add_argument("--properties-json")
    s.add_argument("--properties-file")
    s.set_defaults(func=cmd_create_data_source)

    s = sub.add_parser("update-database", help="Update a database title/description/icon/cover/in_trash via JSON body")
    s.add_argument("--database-id", required=True)
    s.add_argument("--body-json")
    s.add_argument("--body-file")
    s.add_argument("--title")
    s.add_argument("--description")
    tg = s.add_mutually_exclusive_group()
    tg.add_argument("--trash", dest="in_trash", action="store_true")
    tg.add_argument("--restore", dest="in_trash", action="store_false")
    s.set_defaults(in_trash=None)
    s.set_defaults(func=cmd_update_database)

    s = sub.add_parser("update-data-source", help="Update a data source schema/title")
    s.add_argument("--data-source-id", required=True)
    s.add_argument("--body-json")
    s.add_argument("--body-file")
    s.add_argument("--properties-json")
    s.add_argument("--properties-file")
    s.add_argument("--title")
    tg = s.add_mutually_exclusive_group()
    tg.add_argument("--trash", dest="in_trash", action="store_true")
    tg.add_argument("--restore", dest="in_trash", action="store_false")
    s.set_defaults(in_trash=None)
    s.set_defaults(func=cmd_update_data_source)

    s = sub.add_parser("create-comment", help="Create a comment on a page, block, or discussion")
    s.add_argument("--page-id")
    s.add_argument("--block-id")
    s.add_argument("--discussion-id")
    s.add_argument("--text")
    s.add_argument("--markdown")
    s.add_argument("--rich-text-json")
    s.add_argument("--rich-text-file")
    s.add_argument("--body-json")
    s.add_argument("--body-file")
    s.set_defaults(func=cmd_create_comment)

    s = sub.add_parser("update-comment", help="Update a comment")
    s.add_argument("--comment-id", required=True)
    s.add_argument("--text")
    s.add_argument("--markdown")
    s.add_argument("--rich-text-json")
    s.add_argument("--rich-text-file")
    s.add_argument("--body-json")
    s.add_argument("--body-file")
    s.set_defaults(func=cmd_update_comment)

    s = sub.add_parser("delete-comment", help="Delete a comment")
    s.add_argument("--comment-id", required=True)
    s.set_defaults(func=cmd_delete_comment)

    s = sub.add_parser("create-file-upload", help="Create a file upload object")
    s.add_argument("--mode", choices=["single_part", "multi_part", "external_url"])
    s.add_argument("--filename")
    s.add_argument("--content-type")
    s.add_argument("--number-of-parts", type=int)
    s.add_argument("--external-url")
    s.set_defaults(func=cmd_create_file_upload)

    s = sub.add_parser("send-file-upload", help="Send file content for a file upload")
    s.add_argument("--file-upload-id", required=True)
    s.add_argument("--file-path", required=True)
    s.add_argument("--filename")
    s.add_argument("--content-type")
    s.add_argument("--part-number", type=int)
    s.set_defaults(func=cmd_send_file_upload)

    s = sub.add_parser("complete-file-upload", help="Complete a multi-part file upload")
    s.add_argument("--file-upload-id", required=True)
    s.set_defaults(func=cmd_complete_file_upload)

    s = sub.add_parser("get-file-upload", help="Retrieve one file upload")
    s.add_argument("--file-upload-id", required=True)
    s.set_defaults(func=cmd_get_file_upload)

    s = sub.add_parser("list-file-uploads", help="List file uploads")
    s.add_argument("--status", choices=["pending", "uploaded", "expired", "failed"])
    s.add_argument("--page-size", type=int)
    s.add_argument("--start-cursor")
    s.set_defaults(func=cmd_list_file_uploads)

    s = sub.add_parser("list-views", help="List views for a database or data source")
    s.add_argument("--database-id")
    s.add_argument("--data-source-id")
    s.add_argument("--page-size", type=int)
    s.add_argument("--start-cursor")
    s.set_defaults(func=cmd_list_views)

    s = sub.add_parser("get-view", help="Retrieve a view")
    s.add_argument("--view-id", required=True)
    s.set_defaults(func=cmd_get_view)

    s = sub.add_parser("create-view-query", help="Execute a view query and return first page")
    s.add_argument("--view-id", required=True)
    s.add_argument("--page-size", type=int)
    s.set_defaults(func=cmd_create_view_query)

    s = sub.add_parser("get-view-query-results", help="Paginate cached view query results")
    s.add_argument("--view-id", required=True)
    s.add_argument("--query-id", required=True)
    s.add_argument("--page-size", type=int)
    s.add_argument("--start-cursor")
    s.set_defaults(func=cmd_get_view_query_results)

    s = sub.add_parser("delete-view-query", help="Delete a cached view query")
    s.add_argument("--view-id", required=True)
    s.add_argument("--query-id", required=True)
    s.set_defaults(func=cmd_delete_view_query)

    s = sub.add_parser("create-view", help="Create a view from a JSON body")
    s.add_argument("--body-json")
    s.add_argument("--body-file")
    s.set_defaults(func=cmd_create_view)

    s = sub.add_parser("update-view", help="Update a view from a JSON body")
    s.add_argument("--view-id", required=True)
    s.add_argument("--body-json")
    s.add_argument("--body-file")
    s.set_defaults(func=cmd_update_view)

    s = sub.add_parser("delete-view", help="Delete a view")
    s.add_argument("--view-id", required=True)
    s.set_defaults(func=cmd_delete_view)

    s = sub.add_parser("get-page-markdown", help="Retrieve page content as markdown")
    s.add_argument("--page-id", required=True)
    s.add_argument("--include-transcript", action="store_true")
    s.set_defaults(func=cmd_get_page_markdown)

    s = sub.add_parser("list-comments", help="List comments")
    s.add_argument("--block-id")
    s.add_argument("--page-size", type=int)
    s.add_argument("--start-cursor")
    s.set_defaults(func=cmd_list_comments)

    s = sub.add_parser("get-comment", help="Retrieve a comment")
    s.add_argument("--comment-id", required=True)
    s.set_defaults(func=cmd_get_comment)

    s = sub.add_parser("get-block", help="Retrieve a block")
    s.add_argument("--block-id", required=True)
    s.set_defaults(func=cmd_get_block)

    s = sub.add_parser("update-block", help="Update a block from a JSON body")
    s.add_argument("--block-id", required=True)
    s.add_argument("--body-json")
    s.add_argument("--body-file")
    s.set_defaults(func=cmd_update_block)

    s = sub.add_parser("delete-block", help="Delete a block")
    s.add_argument("--block-id", required=True)
    s.set_defaults(func=cmd_delete_block)

    s = sub.add_parser("move-page", help="Move a page to a new page or data source parent")
    s.add_argument("--page-id", required=True)
    s.add_argument("--parent-page-id")
    s.add_argument("--parent-data-source-id")
    s.set_defaults(func=cmd_move_page)

    s = sub.add_parser("trash-page", help="Move a page to trash")
    s.add_argument("--page-id", required=True)
    s.set_defaults(func=cmd_trash_page)

    s = sub.add_parser("restore-page", help="Restore a page from trash")
    s.add_argument("--page-id", required=True)
    s.set_defaults(func=cmd_restore_page)

    s = sub.add_parser("move-database", help="Move a database to a new page or workspace parent")
    s.add_argument("--database-id", required=True)
    s.add_argument("--parent-page-id")
    s.add_argument("--workspace", action="store_true")
    s.set_defaults(func=cmd_move_database)

    s = sub.add_parser("trash-database", help="Move a database to trash")
    s.add_argument("--database-id", required=True)
    s.set_defaults(func=cmd_trash_database)

    s = sub.add_parser("restore-database", help="Restore a database from trash")
    s.add_argument("--database-id", required=True)
    s.set_defaults(func=cmd_restore_database)

    s = sub.add_parser("restore-block", help="Restore a block from trash")
    s.add_argument("--block-id", required=True)
    s.set_defaults(func=cmd_restore_block)

    s = sub.add_parser("update-page-markdown", help="Update page content using markdown commands")
    s.add_argument("--page-id", required=True)
    s.add_argument("--body-json")
    s.add_argument("--body-file")
    s.set_defaults(func=cmd_update_page_markdown)

    s = sub.add_parser("list-data-source-templates", help="List page templates in a data source")
    s.add_argument("--data-source-id", required=True)
    s.add_argument("--name")
    s.add_argument("--page-size", type=int)
    s.add_argument("--start-cursor")
    s.set_defaults(func=cmd_list_data_source_templates)

    return p


def main():
    parser = build_parser()
    argv = maybe_enable_redaction(sys.argv[1:])
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
