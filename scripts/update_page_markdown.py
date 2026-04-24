#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path
from output_guard import emit_output_text

SCRIPT_DIR = Path(__file__).resolve().parent
NOTION_API = SCRIPT_DIR / 'notion_api.py'


def run(cmd):
    return subprocess.run(cmd, check=True, text=True, capture_output=True)


def read_text_arg(text, text_file):
    if text and text_file:
        raise SystemExit('Use either inline text or --content-file, not both')
    if text_file:
        return Path(text_file).read_text(encoding='utf-8')
    return text


def read_json_arg(text, text_file):
    if text and text_file:
        raise SystemExit('Use either inline JSON or --updates-file, not both')
    if text_file:
        return json.loads(Path(text_file).read_text(encoding='utf-8'))
    if text:
        return json.loads(text)
    return None


def main():
    parser = argparse.ArgumentParser(description='Update a Notion page using markdown endpoint')
    parser.add_argument('page_id')
    parser.add_argument('mode', choices=['replace', 'insert', 'update'])
    parser.add_argument('content', nargs='?')
    parser.add_argument('selector', nargs='?')
    parser.add_argument('--content-file')
    parser.add_argument('--updates-json')
    parser.add_argument('--updates-file')
    parser.add_argument('--allow-deleting-content', action='store_true')
    args = parser.parse_args()

    if args.mode == 'replace':
        content = read_text_arg(args.content, args.content_file)
        if content is None:
            raise SystemExit('replace mode requires inline content or --content-file')
        body = {
            'type': 'replace_content',
            'replace_content': {
                'new_str': content,
                'allow_deleting_content': args.allow_deleting_content,
            },
        }
    elif args.mode == 'insert':
        content = read_text_arg(args.content, args.content_file)
        if content is None:
            raise SystemExit('insert mode requires inline content or --content-file')
        body = {
            'type': 'insert_content',
            'insert_content': {'content': content},
        }
        if args.selector:
            body['insert_content']['after'] = args.selector
    else:
        updates = read_json_arg(args.updates_json or args.content, args.updates_file)
        if updates is None:
            raise SystemExit('update mode requires --updates-json, --updates-file, or inline JSON content_updates array')
        body = {
            'type': 'update_content',
            'update_content': {
                'content_updates': updates,
                'allow_deleting_content': args.allow_deleting_content,
            },
        }

    with tempfile.NamedTemporaryFile('w', encoding='utf-8', delete=False) as tf:
        json.dump(body, tf, ensure_ascii=False)
        path = tf.name
    try:
        result = run(['python3', str(NOTION_API), 'update-page-markdown', '--page-id', args.page_id, '--body-file', path])
        emit_output_text(result.stdout)
    finally:
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass


if __name__ == '__main__':
    main()
