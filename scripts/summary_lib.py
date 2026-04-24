#!/usr/bin/env python3
from __future__ import annotations
import json
import os
import sys
from typing import Any, Iterable


REDACT_OUTPUT = False


def env_truthy(name: str) -> bool:
    return os.environ.get(name, '').strip().lower() in {'1', 'true', 'yes', 'on'}


def redacted(label: str) -> str:
    return f'<redacted:{label}>'


def redact_text(text: str, label: str = 'text') -> str:
    if not text:
        return ''
    return redacted(label) if REDACT_OUTPUT else text


def load_stdin_json(stdin) -> Any:
    return json.load(stdin)


def join_rich_text(items: Iterable[dict]) -> str:
    parts = []
    for x in items or []:
        txt = x.get('plain_text') or (x.get('text') or {}).get('content') or ''
        if txt:
            parts.append(txt)
    return ''.join(parts).strip()


def truncate(text: str, limit: int = 80) -> str:
    text = (text or '').strip()
    return text[:limit] + ('…' if len(text) > limit else '')


def page_title(obj: dict, default: str = '(untitled)') -> str:
    props = obj.get('properties', {}) or {}
    for v in props.values():
        if isinstance(v, dict) and v.get('type') == 'title':
            t = join_rich_text(v.get('title', []))
            if t:
                return t
    return default


def data_source_title(obj: dict, default: str = '(untitled)') -> str:
    t = join_rich_text(obj.get('title', []))
    return t or default


def object_title(obj: dict, default: str = '(untitled)') -> str:
    kind = obj.get('object')
    if kind == 'data_source':
        return data_source_title(obj, default)
    return page_title(obj, default)


def print_list_header(label: str, count: int) -> None:
    print(f"{label}: {count}")


def print_more(data: dict, item_label: str, shown: int, total: int) -> None:
    if total > shown:
        print(f"... and {total-shown} more {item_label}")
    if data.get('has_more'):
        cursor = data.get('next_cursor')
        cursor_text = redacted('cursor') if REDACT_OUTPUT and cursor else cursor
        print(f"More available: next_cursor={cursor_text}")


def summarize_search_results(data: dict, limit: int = 50) -> None:
    results = data.get('results', [])
    print(f"Found {len(results)} result(s)")
    shown = min(len(results), limit)
    for i, item in enumerate(results[:limit], 1):
        kind = item.get('object', 'unknown')
        title = redact_text(object_title(item), 'title')
        print(f"{i}. [{kind}] {title}")
        print(f"   id: {redact_text(item.get('id', '-'), 'id')}")
        print(f"   parent: {(item.get('parent') or {}).get('type', '-')}")
        print(f"   url: {redact_text(item.get('url', '-'), 'url')}")
    print_more(data, 'result(s)', shown, len(results))


def summarize_query_results(data: dict, limit: int = 20) -> None:
    results = data.get('results', [])
    print(f"Query returned {len(results)} page(s)")
    shown = min(len(results), limit)
    for i, item in enumerate(results[:limit], 1):
        print(f"{i}. {redact_text(page_title(item), 'title')}")
        print(f"   id: {redact_text(item.get('id', '-'), 'id')}")
        print(f"   url: {redact_text(item.get('url', '-'), 'url')}")
    print_more(data, 'page(s)', shown, len(results))


def summarize_blocks(data: dict, limit: int = 20) -> None:
    results = data.get('results', [])
    print(f"Blocks: {len(results)} child block(s)")
    shown = min(len(results), limit)
    for i, block in enumerate(results[:limit], 1):
        btype = block.get('type', 'unknown')
        payload = block.get(btype, {}) if isinstance(block.get(btype), dict) else {}
        line = ''
        rich = payload.get('rich_text', [])
        if rich:
            line = truncate(join_rich_text(rich))
        elif payload.get('caption'):
            line = truncate(join_rich_text(payload.get('caption', [])))
        suffix = '' if REDACT_OUTPUT else (f": {line}" if line else '')
        print(f"{i}. {btype}{suffix}")
    if len(results) > shown:
        print(f"... and {len(results)-shown} more block(s)")
    if data.get('has_more'):
        print('More block pages available via start_cursor')


def summarize_data_source(ds: dict) -> None:
    print(f"Data source: {redact_text(data_source_title(ds), 'title')}")
    print(f"id: {redact_text(ds.get('id', '-'), 'id')}")
    print(f"url: {redact_text(ds.get('url', '-'), 'url')}")
    print(f"parent: {(ds.get('parent') or {}).get('type', '-')}")
    props = ds.get('properties', {}) or {}
    print(f"properties: {len(props)}")
    for name, prop in props.items():
        prop_name = redacted('property_name') if REDACT_OUTPUT else name
        print(f"- {prop_name} [{prop.get('type', 'unknown')}]")


def summarize_users(data: dict, limit: int = 30) -> None:
    results = data.get('results', [])
    print_list_header('Users', len(results))
    shown = min(len(results), limit)
    for i, user in enumerate(results[:limit], 1):
        name = redact_text(user.get('name') or '(unnamed)', 'name')
        utype = user.get('type', 'unknown')
        extra = ''
        if utype == 'person':
            extra = (user.get('person') or {}).get('email', '')
        elif utype == 'bot':
            extra = ((user.get('bot') or {}).get('workspace_name') or '')
        print(f"{i}. {name} [{utype}]")
        print(f"   id: {redact_text(user.get('id', '-'), 'id')}")
        if extra:
            label = 'email' if utype == 'person' else 'workspace'
            print(f"   info: {redact_text(extra, label)}")
    print_more(data, 'user(s)', shown, len(results))


def summarize_user(user: dict) -> None:
    print(f"User: {redact_text(user.get('name') or '(unnamed)', 'name')}")
    print(f"id: {redact_text(user.get('id', '-'), 'id')}")
    print(f"type: {user.get('type', 'unknown')}")
    if user.get('type') == 'person':
        email = (user.get('person') or {}).get('email')
        if email:
            print(f"email: {redact_text(email, 'email')}")
    elif user.get('type') == 'bot':
        ws = (user.get('bot') or {}).get('workspace_name')
        if ws:
            print(f"workspace: {redact_text(ws, 'workspace')}")


def summarize_file_uploads(data: dict, limit: int = 20) -> None:
    results = data.get('results', [])
    print_list_header('File uploads', len(results))
    shown = min(len(results), limit)
    for i, item in enumerate(results[:limit], 1):
        print(f"{i}. {redact_text(item.get('filename') or item.get('name') or '-', 'filename')}")
        print(f"   id: {redact_text(item.get('id', '-'), 'id')}")
        print(f"   status: {item.get('status', '-')}")
        print(f"   content_type: {item.get('content_type') or '-'}")
    print_more(data, 'upload(s)', shown, len(results))


def summarize_file_upload(item: dict) -> None:
    print(f"File upload: {redact_text(item.get('filename') or item.get('name') or '-', 'filename')}")
    print(f"id: {redact_text(item.get('id', '-'), 'id')}")
    print(f"status: {item.get('status', '-')}")
    if item.get('content_type'):
        print(f"content_type: {item.get('content_type')}")
    if item.get('expiry_time'):
        print(f"expiry_time: {item.get('expiry_time')}")


def summarize_page(page: dict) -> None:
    print(f"Page: {redact_text(page_title(page), 'title')}")
    print(f"id: {redact_text(page.get('id', '-'), 'id')}")
    print(f"url: {redact_text(page.get('url', '-'), 'url')}")
    print(f"parent: {(page.get('parent') or {}).get('type', '-')}")
    print('properties:')
    for name, prop in (page.get('properties') or {}).items():
        ptype = prop.get('type', 'unknown')
        value = ''
        if ptype == 'title':
            value = join_rich_text(prop.get('title', []))
        elif ptype == 'status':
            value = (prop.get('status') or {}).get('name', '')
        elif ptype == 'select':
            value = (prop.get('select') or {}).get('name', '')
        elif ptype == 'multi_select':
            value = ', '.join(x.get('name', '') for x in prop.get('multi_select', []))
        elif ptype == 'checkbox':
            value = str(prop.get('checkbox'))
        elif ptype == 'number':
            value = str(prop.get('number'))
        elif ptype == 'date':
            value = (prop.get('date') or {}).get('start', '')
        elif ptype == 'url':
            value = prop.get('url') or ''
        elif ptype == 'email':
            value = prop.get('email') or ''
        elif ptype == 'phone_number':
            value = prop.get('phone_number') or ''
        elif ptype == 'people':
            value = ', '.join(x.get('name', '') or x.get('id', '') for x in prop.get('people', []))
        elif ptype == 'relation':
            rel = prop.get('relation', [])
            value = f"{len(rel)} item(s)" + (' (has_more)' if prop.get('has_more') else '')
        elif ptype == 'rich_text':
            value = truncate(join_rich_text(prop.get('rich_text', [])))
        elif ptype == 'formula':
            f = prop.get('formula') or {}
            value = str(f.get(f.get('type', ''), ''))
        elif ptype == 'rollup':
            r = prop.get('rollup') or {}
            value = str(r.get(r.get('type', ''), ''))
        elif ptype == 'files':
            value = f"{len(prop.get('files', []))} file(s)"
        prop_name = redacted('property_name') if REDACT_OUTPUT else name
        if value and not REDACT_OUTPUT:
            print(f"- {prop_name} [{ptype}]: {value}")
        else:
            print(f"- {prop_name} [{ptype}]")


def main(argv: list[str]) -> int:
    global REDACT_OUTPUT
    if len(argv) not in (2, 3):
        print('Usage: summary_lib.py <search|query|blocks|data-source|page|users|user|file-uploads|file-upload> [--redact]', file=sys.stderr)
        return 2
    mode = argv[1]
    REDACT_OUTPUT = env_truthy('NOTION_REDACT_OUTPUT') or (len(argv) == 3 and argv[2] == '--redact')
    data = load_stdin_json(sys.stdin)
    mapping = {
        'search': summarize_search_results,
        'query': summarize_query_results,
        'blocks': summarize_blocks,
        'data-source': summarize_data_source,
        'page': summarize_page,
        'users': summarize_users,
        'user': summarize_user,
        'file-uploads': summarize_file_uploads,
        'file-upload': summarize_file_upload,
    }
    fn = mapping.get(mode)
    if not fn:
        print(f'Unknown mode: {mode}', file=sys.stderr)
        return 2
    fn(data)
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
