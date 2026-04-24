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

USAGE = '''Usage:
  page_ops.py create-subpage <parent_page_id> <title>
  page_ops.py update-title <page_id> <new_title>
  page_ops.py read-markdown <page_id>
  page_ops.py get-property <page_id> <property_id>
'''


def run(cmd):
    return subprocess.run(cmd, check=True, text=True, capture_output=True)


def create_subpage(parent_page_id: str, title: str):
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', delete=False) as tf:
        json.dump({
            'title': {
                'title': [
                    {'type': 'text', 'text': {'content': title}}
                ]
            }
        }, tf, ensure_ascii=False)
        path = tf.name
    try:
        result = run(['python3', str(NOTION_API), 'create-page', '--parent-page-id', parent_page_id, '--properties-file', path])
        emit_output_text(result.stdout)
    finally:
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass


def update_title(page_id: str, title: str):
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', delete=False) as tf:
        json.dump({
            'properties': {
                'title': {
                    'title': [
                        {'type': 'text', 'text': {'content': title}}
                    ]
                }
            }
        }, tf, ensure_ascii=False)
        path = tf.name
    try:
        result = run(['python3', str(NOTION_API), 'update-page', '--page-id', page_id, '--body-file', path])
        emit_output_text(result.stdout)
    finally:
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass


def passthrough(*args):
    result = run(['python3', str(NOTION_API), *args])
    emit_output_text(result.stdout)


def main():
    if len(sys.argv) < 3:
        print(USAGE, file=sys.stderr)
        raise SystemExit(2)
    cmd = sys.argv[1]
    if cmd == 'create-subpage':
        if len(sys.argv) != 4:
            print(USAGE, file=sys.stderr)
            raise SystemExit(2)
        create_subpage(sys.argv[2], sys.argv[3])
    elif cmd == 'update-title':
        if len(sys.argv) != 4:
            print(USAGE, file=sys.stderr)
            raise SystemExit(2)
        update_title(sys.argv[2], sys.argv[3])
    elif cmd == 'read-markdown':
        if len(sys.argv) != 3:
            print(USAGE, file=sys.stderr)
            raise SystemExit(2)
        passthrough('get-page-markdown', '--page-id', sys.argv[2])
    elif cmd == 'get-property':
        if len(sys.argv) != 4:
            print(USAGE, file=sys.stderr)
            raise SystemExit(2)
        passthrough('get-page-property', '--page-id', sys.argv[2], '--property-id', sys.argv[3])
    else:
        print(USAGE, file=sys.stderr)
        raise SystemExit(2)


if __name__ == '__main__':
    main()
