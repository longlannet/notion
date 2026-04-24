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


def build_property(name, related_data_source_id, relation_mode='single_property'):
    relation = {
        'data_source_id': related_data_source_id,
        'type': relation_mode,
        relation_mode: {}
    }
    return {
        name: {
            'name': name,
            'type': 'relation',
            'relation': relation,
        }
    }


def main():
    if len(sys.argv) < 4:
        print('Usage: add_relation_property.py <data_source_id> <property_name> <related_data_source_id> [single_property|dual_property]', file=sys.stderr)
        raise SystemExit(2)
    data_source_id, property_name, related_data_source_id = sys.argv[1:4]
    relation_mode = sys.argv[4] if len(sys.argv) >= 5 else 'single_property'
    if relation_mode not in {'single_property', 'dual_property'}:
        raise SystemExit('relation mode must be single_property or dual_property')
    props = build_property(property_name, related_data_source_id, relation_mode)
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
