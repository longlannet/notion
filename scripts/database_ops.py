#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path
from output_guard import emit_output_text

SCRIPT_DIR = Path(__file__).resolve().parent
NOTION_API = SCRIPT_DIR / 'notion_api.py'

USAGE = '''Usage:
  database_ops.py get <database_id>
  database_ops.py move <database_id> <parent_page_id>
  database_ops.py trash <database_id>
  database_ops.py restore <database_id>
  database_ops.py set-icon <database_id> <emoji>
  database_ops.py set-cover <database_id> <external_url>
'''


def run(args):
    result = subprocess.run(['python3', str(NOTION_API), *args], check=True, text=True, capture_output=True)
    emit_output_text(result.stdout)


def run_script(script_name, *args):
    result = subprocess.run(['python3', str(SCRIPT_DIR / script_name), *args], check=True, text=True, capture_output=True)
    emit_output_text(result.stdout)


def main():
    if len(sys.argv) < 3:
        print(USAGE, file=sys.stderr)
        raise SystemExit(2)
    cmd = sys.argv[1]
    if cmd == 'get' and len(sys.argv) == 3:
        run(['get-database', '--database-id', sys.argv[2]])
    elif cmd == 'move' and len(sys.argv) == 4:
        run(['move-database', '--database-id', sys.argv[2], '--parent-page-id', sys.argv[3]])
    elif cmd == 'trash' and len(sys.argv) == 3:
        run(['trash-database', '--database-id', sys.argv[2]])
    elif cmd == 'restore' and len(sys.argv) == 3:
        run(['restore-database', '--database-id', sys.argv[2]])
    elif cmd == 'set-icon' and len(sys.argv) == 4:
        run_script('set_database_media.py', sys.argv[2], 'icon', 'emoji', sys.argv[3])
    elif cmd == 'set-cover' and len(sys.argv) == 4:
        run_script('set_database_media.py', sys.argv[2], 'cover', 'external', sys.argv[3])
    else:
        print(USAGE, file=sys.stderr)
        raise SystemExit(2)


if __name__ == '__main__':
    main()
