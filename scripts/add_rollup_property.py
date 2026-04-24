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


def build_property(name, relation_property_name, rollup_property_name, function_name='show_original'):
    return {
        name: {
            'name': name,
            'type': 'rollup',
            'rollup': {
                'function': function_name,
                'relation_property_name': relation_property_name,
                'rollup_property_name': rollup_property_name,
            },
        }
    }


def main():
    if len(sys.argv) < 5:
        print('Usage: add_rollup_property.py <data_source_id> <property_name> <relation_property_name> <rollup_property_name> [function]', file=sys.stderr)
        raise SystemExit(2)
    data_source_id, property_name, relation_property_name, rollup_property_name = sys.argv[1:5]
    function_name = sys.argv[5] if len(sys.argv) >= 6 else 'show_original'
    props = build_property(property_name, relation_property_name, rollup_property_name, function_name)
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', delete=False) as tf:
        json.dump(props, tf, ensure_ascii=False)
        props_path = tf.name
    try:
        result = run([
            'python3', str(NOTION_API), 'update-data-source',
            '--data-source-id', data_source_id,
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
