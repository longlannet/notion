#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path
from output_guard import emit_output_text

SCRIPT_DIR = Path(__file__).resolve().parent
NOTION_API = SCRIPT_DIR / 'notion_api.py'
USAGE = 'Usage: import_external_file.py <https_url> [filename] [content_type]'


def run(cmd):
    return subprocess.run(cmd, check=True, text=True, capture_output=True)


def main():
    if len(sys.argv) < 2 or sys.argv[1] in {'-h', '--help'}:
        print(USAGE, file=sys.stderr)
        raise SystemExit(0 if len(sys.argv) >= 2 and sys.argv[1] in {'-h', '--help'} else 2)
    url = sys.argv[1]
    filename = sys.argv[2] if len(sys.argv) >= 3 else None
    content_type = sys.argv[3] if len(sys.argv) >= 4 else None
    cmd = ['python3', str(NOTION_API), 'create-file-upload', '--mode', 'external_url', '--external-url', url]
    if filename:
        cmd += ['--filename', filename]
    if content_type:
        cmd += ['--content-type', content_type]
    result = run(cmd)
    emit_output_text(result.stdout)


if __name__ == '__main__':
    main()
