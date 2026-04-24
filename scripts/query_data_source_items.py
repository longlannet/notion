#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path
from output_guard import emit_output_text

SCRIPT_DIR = Path(__file__).resolve().parent
NOTION_API = SCRIPT_DIR / 'notion_api.py'


def run(cmd):
    return subprocess.run(cmd, check=True, text=True, capture_output=True)


def load_json_arg(json_text=None, file_path=None):
    if json_text and file_path:
        raise SystemExit('Use either inline JSON or --*-file, not both')
    if file_path:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    if json_text:
        return json.loads(json_text)
    return None


def build_property_filter(property_name, property_type, operator, value):
    if property_type in {'title', 'rich_text', 'select', 'status'}:
        return {'property': property_name, property_type: {operator: value}}
    if property_type == 'checkbox':
        return {'property': property_name, 'checkbox': {'equals': value.lower() == 'true'}}
    if property_type == 'date':
        return {'property': property_name, 'date': {operator: value}}
    if property_type == 'number':
        return {'property': property_name, 'number': {operator: float(value)}}
    raise SystemExit('property_type must be one of: title, rich_text, select, status, checkbox, date, number')


def main():
    p = argparse.ArgumentParser(description='Unified query helper for a Notion data source')
    p.add_argument('data_source_id')
    p.add_argument('--title-property')
    p.add_argument('--title-query')
    p.add_argument('--property-name')
    p.add_argument('--property-type')
    p.add_argument('--operator')
    p.add_argument('--value')
    p.add_argument('--filter-json')
    p.add_argument('--filter-file')
    p.add_argument('--sorts-json')
    p.add_argument('--sorts-file')
    p.add_argument('--page-size', type=int)
    p.add_argument('--start-cursor')
    args = p.parse_args()

    body = {}
    if args.title_property or args.title_query:
        if not (args.title_property and args.title_query):
            raise SystemExit('--title-property and --title-query must be used together')
        body['filter'] = {'property': args.title_property, 'title': {'contains': args.title_query}}
    elif args.property_name or args.property_type or args.operator or args.value:
        if not all([args.property_name, args.property_type, args.operator, args.value]):
            raise SystemExit('--property-name --property-type --operator --value must be used together')
        body['filter'] = build_property_filter(args.property_name, args.property_type, args.operator, args.value)
    else:
        filter_obj = load_json_arg(args.filter_json, args.filter_file)
        sorts_obj = load_json_arg(args.sorts_json, args.sorts_file)
        if filter_obj is not None:
            body['filter'] = filter_obj
        if sorts_obj is not None:
            body['sorts'] = sorts_obj
    if args.page_size is not None:
        body['page_size'] = args.page_size
    if args.start_cursor:
        body['start_cursor'] = args.start_cursor

    with tempfile.NamedTemporaryFile('w', encoding='utf-8', delete=False) as tf:
        json.dump(body, tf, ensure_ascii=False)
        body_path = tf.name
    try:
        result = run([
            'python3', str(NOTION_API), 'query-data-source',
            '--data-source-id', args.data_source_id,
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
