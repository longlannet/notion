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


def build_property(name, expression):
    return {
        name: {
            'name': name,
            'type': 'formula',
            'formula': {
                'expression': expression,
            },
        }
    }


def main():
    if len(sys.argv) < 4:
        print('Usage: add_formula_property.py <data_source_id> <property_name> <expression>', file=sys.stderr)
        raise SystemExit(2)
    data_source_id, property_name, expression = sys.argv[1:4]
    props = build_property(property_name, expression)
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
