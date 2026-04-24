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
USAGE = 'Usage: create_database_item.py <data_source_id> <title_property_name> <title_text> [properties_json_file]'


def run(cmd):
    return subprocess.run(cmd, check=True, text=True, capture_output=True)


def main():
    if len(sys.argv) < 4 or sys.argv[1] in {'-h', '--help'}:
        print(USAGE, file=sys.stderr)
        raise SystemExit(0 if len(sys.argv) >= 2 and sys.argv[1] in {'-h', '--help'} else 2)

    data_source_id = sys.argv[1]
    title_property_name = sys.argv[2]
    title_text = sys.argv[3]
    extra_properties = {}

    if len(sys.argv) >= 5:
        with open(sys.argv[4], 'r', encoding='utf-8') as f:
            extra_properties = json.load(f)
        if not isinstance(extra_properties, dict):
            raise SystemExit('properties_json_file must contain a JSON object')

    props = {
        title_property_name: {
            'title': [
                {'type': 'text', 'text': {'content': title_text}}
            ]
        }
    }
    props.update(extra_properties)

    with tempfile.NamedTemporaryFile('w', encoding='utf-8', delete=False) as pf:
        json.dump(props, pf, ensure_ascii=False)
        props_path = pf.name

    try:
        result = run([
            'python3', str(NOTION_API), 'create-page',
            '--parent-data-source-id', data_source_id,
            '--properties-file', props_path,
        ])
        emit_output_text(result.stdout)
    finally:
        try:
            os.unlink(props_path)
        except FileNotFoundError:
            pass


if __name__ == '__main__':
    main()
