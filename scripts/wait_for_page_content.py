#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
NOTION_API = SCRIPT_DIR / 'notion_api.py'


def run_json(cmd):
    p = subprocess.run(cmd, check=True, text=True, capture_output=True)
    return json.loads(p.stdout)


def main():
    if len(sys.argv) < 2:
        print('Usage: wait_for_page_content.py <page_id> [timeout_seconds] [interval_seconds]', file=sys.stderr)
        raise SystemExit(2)
    page_id = sys.argv[1]
    timeout = float(sys.argv[2]) if len(sys.argv) >= 3 else 60.0
    interval = float(sys.argv[3]) if len(sys.argv) >= 4 else 3.0
    deadline = time.time() + timeout
    last_blocks = None
    last_markdown = None

    while time.time() < deadline:
        blocks = run_json(['python3', str(NOTION_API), 'get-blocks', '--block-id', page_id, '--page-size', '100'])
        markdown = run_json(['python3', str(NOTION_API), 'get-page-markdown', '--page-id', page_id])
        last_blocks = blocks
        last_markdown = markdown
        if blocks.get('results') or markdown.get('markdown'):
            print(json.dumps({
                'ready': True,
                'page_id': page_id,
                'blocks_count': len(blocks.get('results', [])),
                'markdown_nonempty': bool(markdown.get('markdown')),
                'blocks': blocks,
                'markdown': markdown,
            }, ensure_ascii=False, indent=2))
            return
        time.sleep(interval)

    print(json.dumps({
        'ready': False,
        'page_id': page_id,
        'blocks_count': len((last_blocks or {}).get('results', [])),
        'markdown_nonempty': bool((last_markdown or {}).get('markdown')),
        'last_blocks': last_blocks,
        'last_markdown': last_markdown,
    }, ensure_ascii=False, indent=2))
    raise SystemExit(1)


if __name__ == '__main__':
    main()
