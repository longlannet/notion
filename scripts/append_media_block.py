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


def rich_text(text):
    return [{"type": "text", "text": {"content": text}}] if text else []


def build_block(block_type, source_type, source_value, name=None, caption=None):
    if block_type not in {"file", "pdf", "image", "audio", "video"}:
        raise SystemExit('block_type must be one of: file, pdf, image, audio, video')
    body = {"caption": rich_text(caption or "")}
    if block_type == 'file' and name:
        body['name'] = name
    if source_type == 'file_upload':
        body['type'] = 'file_upload'
        body['file_upload'] = {'id': source_value}
    elif source_type == 'external':
        body['type'] = 'external'
        body['external'] = {'url': source_value}
        if block_type == 'file' and name:
            body['name'] = name
    else:
        raise SystemExit('source_type must be file_upload or external')
    return [{"object": "block", "type": block_type, block_type: body}]


def main():
    if len(sys.argv) < 5:
        print('Usage: append_media_block.py <page_id> <block_type> <source_type> <source_value> [name] [caption]', file=sys.stderr)
        raise SystemExit(2)
    page_id, block_type, source_type, source_value = sys.argv[1:5]
    name = sys.argv[5] if len(sys.argv) >= 6 else None
    caption = sys.argv[6] if len(sys.argv) >= 7 else None
    children = build_block(block_type, source_type, source_value, name=name, caption=caption)
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', delete=False) as tf:
        json.dump(children, tf, ensure_ascii=False)
        path = tf.name
    try:
        result = run(['python3', str(NOTION_API), 'append-blocks', '--block-id', page_id, '--children-file', path])
        emit_output_text(result.stdout)
    finally:
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass


if __name__ == '__main__':
    main()
