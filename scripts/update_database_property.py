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
        print('Usage: update_database_property.py <data_source_id> <property_name> <new_name>', file=sys.stderr)
        raise SystemExit(2)
    data_source_id, property_name, new_name = sys.argv[1:4]
    body = {
        'properties': {
            property_name: {
                'name': new_name
            }
        }
    }
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', delete=False) as tf:
        json.dump(body, tf, ensure_ascii=False)
        body_path = tf.name
    try:
        result = run([
            'python3', str(NOTION_API), 'update-data-source',
            '--data-source-id', data_source_id,
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
