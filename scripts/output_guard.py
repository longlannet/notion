#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
from typing import Any

UUID_RE = re.compile(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', re.I)
EMAIL_RE = re.compile(r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b', re.I)
URL_RE = re.compile(r'https?://\S+', re.I)

REDACT_KEYS = {
    'id',
    'url',
    'public_url',
    'next_cursor',
    'email',
    'workspace_name',
    'name',
    'filename',
    'key_prefix',
    'plain_text',
    'content',
    'caption',
}


def redaction_enabled() -> bool:
    return os.environ.get('NOTION_REDACT_OUTPUT', '').strip().lower() in {'1', 'true', 'yes', 'on'}


def redacted(label: str) -> str:
    return f'<redacted:{label}>'


def _redact_string(value: str, key: str | None = None) -> str:
    if not value:
        return value
    if key in {'url', 'public_url'}:
        return redacted('url')
    if key in {'id', 'next_cursor'}:
        return redacted('id')
    if key == 'email' or EMAIL_RE.search(value):
        return redacted('email')
    if key == 'workspace_name':
        return redacted('workspace')
    if key in {'name', 'plain_text', 'content', 'caption'}:
        return redacted(key)
    if UUID_RE.search(value):
        return UUID_RE.sub(redacted('id'), value)
    if URL_RE.search(value):
        return URL_RE.sub(redacted('url'), value)
    return value


def redact_json_obj(obj: Any, *, key: str | None = None) -> Any:
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k in REDACT_KEYS:
                if isinstance(v, str):
                    out[k] = _redact_string(v, k)
                elif isinstance(v, list):
                    out[k] = [redacted(k)] if v else []
                elif isinstance(v, dict):
                    out[k] = redacted(k)
                else:
                    out[k] = v
            else:
                out[k] = redact_json_obj(v, key=k)
        return out
    if isinstance(obj, list):
        return [redact_json_obj(x, key=key) for x in obj]
    if isinstance(obj, str):
        return _redact_string(obj, key)
    return obj


def redact_json_text(text: str) -> str:
    try:
        obj = json.loads(text)
    except Exception:
        return _redact_string(text)
    return json.dumps(redact_json_obj(obj), ensure_ascii=False, indent=2)


def emit_output_text(text: str) -> None:
    if redaction_enabled():
        text = redact_json_text(text)
    if text.endswith('\n'):
        print(text, end='')
    else:
        print(text)


def main() -> int:
    emit_output_text(sys.stdin.read())
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
