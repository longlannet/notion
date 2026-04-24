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


def build_property(name, prop_type):
    if prop_type == 'rich_text':
        return {name: {'name': name, 'type': 'rich_text', 'rich_text': {}}}
    if prop_type == 'url':
        return {name: {'name': name, 'type': 'url', 'url': {}}}
    if prop_type == 'email':
        return {name: {'name': name, 'type': 'email', 'email': {}}}
    if prop_type == 'phone_number':
        return {name: {'name': name, 'type': 'phone_number', 'phone_number': {}}}
    if prop_type == 'checkbox':
        return {name: {'name': name, 'type': 'checkbox', 'checkbox': {}}}
    if prop_type == 'date':
        return {name: {'name': name, 'type': 'date', 'date': {}}}
    if prop_type == 'people':
        return {name: {'name': name, 'type': 'people', 'people': {}}}
    if prop_type == 'number':
        return {name: {'name': name, 'type': 'number', 'number': {'format': 'number'}}}
    if prop_type == 'files':
        return {name: {'name': name, 'type': 'files', 'files': {}}}
    raise SystemExit('Supported types for add_database_property.py: rich_text, url, email, phone_number, checkbox, date, people, number, files')


def main():
    if len(sys.argv) < 4:
        print('Usage: add_database_property.py <data_source_id> <property_name> <property_type>', file=sys.stderr)
        raise SystemExit(2)
    data_source_id, property_name, property_type = sys.argv[1:4]
    props = build_property(property_name, property_type)
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
