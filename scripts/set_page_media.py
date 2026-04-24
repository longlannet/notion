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


def build_media(source_type, source_value):
    if source_type == 'file_upload':
        return {'type': 'file_upload', 'file_upload': {'id': source_value}}
    if source_type == 'external':
        return {'type': 'external', 'external': {'url': source_value}}
    raise SystemExit('source_type must be file_upload or external')


def main():
    if len(sys.argv) < 5:
        print('Usage: set_page_media.py <page_id> <target:icon|cover> <source_type> <source_value>', file=sys.stderr)
        raise SystemExit(2)
    page_id, target, source_type, source_value = sys.argv[1:5]
    if target not in {'icon', 'cover'}:
        raise SystemExit('target must be icon or cover')
    body = {target: build_media(source_type, source_value)}
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', delete=False) as tf:
        json.dump(body, tf, ensure_ascii=False)
        path = tf.name
    try:
        result = run(['python3', str(NOTION_API), 'update-page', '--page-id', page_id, '--body-file', path])
        emit_output_text(result.stdout)
    finally:
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass


if __name__ == '__main__':
    main()
