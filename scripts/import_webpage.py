#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from output_guard import emit_output_text

SCRIPT_DIR = Path(__file__).resolve().parent
NOTION_API = SCRIPT_DIR / 'notion_api.py'
GOOGLE_SEARCH_SCRIPT = SCRIPT_DIR.parent.parent / 'google-search' / 'scripts' / 'search.py'


def run(cmd):
    return subprocess.run(cmd, check=True, text=True, capture_output=True)


def chunk_text(text, size=1800):
    parts = []
    current = []
    current_len = 0
    for para in text.split('\n\n'):
        para = para.strip()
        if not para:
            continue
        add_len = len(para) + 2
        if current and current_len + add_len > size:
            parts.append('\n\n'.join(current))
            current = [para]
            current_len = len(para)
        else:
            current.append(para)
            current_len += add_len
    if current:
        parts.append('\n\n'.join(current))
    return parts


def make_block(text):
    return {
        'object': 'block',
        'type': 'paragraph',
        'paragraph': {
            'rich_text': [
                {'type': 'text', 'text': {'content': text}}
            ]
        }
    }


def main():
    if len(sys.argv) < 4:
        print('Usage: import_webpage.py <parent_page_id> <title> <url>', file=sys.stderr)
        raise SystemExit(2)

    parent_page_id, title, url = sys.argv[1:4]

    if not GOOGLE_SEARCH_SCRIPT.exists():
        raise SystemExit(f'Missing dependency script: {GOOGLE_SEARCH_SCRIPT}')

    fetch = run(['python3', str(GOOGLE_SEARCH_SCRIPT), 'webpage', url, '--json'])
    fetch_data = json.loads(fetch.stdout)
    text = fetch_data.get('response', {}).get('text') or fetch_data.get('response', {}).get('markdown') or ''
    if not text.strip():
        raise SystemExit('No webpage text extracted')

    props = {
        'title': {
            'title': [
                {'type': 'text', 'text': {'content': title}}
            ]
        }
    }
    children = [
        {
            'object': 'block',
            'type': 'callout',
            'callout': {
                'icon': {'type': 'emoji', 'emoji': '🔗'},
                'rich_text': [
                    {'type': 'text', 'text': {'content': f'来源网页： {url}'}}
                ],
                'color': 'gray_background'
            }
        }
    ]
    for part in chunk_text(text):
        children.append(make_block(part))

    with tempfile.NamedTemporaryFile('w', encoding='utf-8', delete=False) as pf:
        json.dump(props, pf, ensure_ascii=False)
        props_path = pf.name
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', delete=False) as cf:
        json.dump(children[:100], cf, ensure_ascii=False)
        children_path = cf.name

    try:
        result = run(['python3', str(NOTION_API), 'create-page', '--parent-page-id', parent_page_id, '--properties-file', props_path, '--children-file', children_path])
        emit_output_text(result.stdout)
    finally:
        for p in (props_path, children_path):
            try:
                os.unlink(p)
            except FileNotFoundError:
                pass


if __name__ == '__main__':
    main()
