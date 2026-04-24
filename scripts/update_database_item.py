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


def run(cmd):
    return subprocess.run(cmd, check=True, text=True, capture_output=True)


def main():
    if len(sys.argv) < 4:
        print('Usage: update_database_item.py <page_id> <property_name> <property_value> [property_type]', file=sys.stderr)
        print('property_type: rich_text|title (default: rich_text)', file=sys.stderr)
        raise SystemExit(2)

    page_id = sys.argv[1]
    property_name = sys.argv[2]
    property_value = sys.argv[3]
    property_type = sys.argv[4] if len(sys.argv) >= 5 else 'rich_text'

    if property_type not in {'rich_text', 'title'}:
        raise SystemExit('property_type must be rich_text or title')

    if property_type == 'rich_text':
        prop = {
            property_name: {
                'rich_text': [
                    {'type': 'text', 'text': {'content': property_value}}
                ]
            }
        }
    else:
        prop = {
            property_name: {
                'title': [
                    {'type': 'text', 'text': {'content': property_value}}
                ]
            }
        }

    body = {'properties': prop}

    with tempfile.NamedTemporaryFile('w', encoding='utf-8', delete=False) as tf:
        json.dump(body, tf, ensure_ascii=False)
        body_path = tf.name

    try:
        result = run([
            'python3', str(NOTION_API), 'update-page',
            '--page-id', page_id,
            '--body-file', body_path,
        ])
        emit_output_text(result.stdout)
    finally:
        try:
            os.unlink(body_path)
        except FileNotFoundError:
            pass


if __name__ == '__main__':
    main()
