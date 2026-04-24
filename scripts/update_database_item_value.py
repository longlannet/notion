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


def build_property(property_name, property_value, property_type):
    if property_type == 'rich_text':
        return {property_name: {'rich_text': [{'type': 'text', 'text': {'content': property_value}}]}}
    if property_type == 'title':
        return {property_name: {'title': [{'type': 'text', 'text': {'content': property_value}}]}}
    if property_type == 'select':
        return {property_name: {'select': {'name': property_value}}}
    if property_type == 'status':
        return {property_name: {'status': {'name': property_value}}}
    if property_type == 'checkbox':
        return {property_name: {'checkbox': property_value.lower() == 'true'}}
    if property_type == 'date':
        return {property_name: {'date': {'start': property_value, 'end': None, 'time_zone': None}}}
    if property_type == 'number':
        return {property_name: {'number': float(property_value)}}
    if property_type == 'multi_select':
        values = [v.strip() for v in property_value.split(',') if v.strip()]
        return {property_name: {'multi_select': [{'name': v} for v in values]}}
    if property_type == 'url':
        return {property_name: {'url': property_value}}
    if property_type == 'email':
        return {property_name: {'email': property_value}}
    if property_type == 'phone_number':
        return {property_name: {'phone_number': property_value}}
    if property_type == 'people':
        values = [v.strip() for v in property_value.split(',') if v.strip()]
        return {property_name: {'people': [{'object': 'user', 'id': v} for v in values]}}
    if property_type == 'relation':
        values = [v.strip() for v in property_value.split(',') if v.strip()]
        return {property_name: {'relation': [{'id': v} for v in values]}}
    if property_type == 'files_file_upload':
        values = [v.strip() for v in property_value.split(',') if v.strip()]
        return {property_name: {'files': [{'type': 'file_upload', 'file_upload': {'id': v}} for v in values]}}
    if property_type == 'files_external':
        values = [v.strip() for v in property_value.split(',') if v.strip()]
        return {property_name: {'files': [{'name': Path(v).name or 'external-file', 'type': 'external', 'external': {'url': v}} for v in values]}}
    raise SystemExit('property_type must be one of: rich_text, title, select, status, checkbox, date, number, multi_select, url, email, phone_number, people, relation, files_file_upload, files_external')


def main():
    if len(sys.argv) < 5:
        print('Usage: update_database_item_value.py <page_id> <property_name> <property_type> <property_value>', file=sys.stderr)
        raise SystemExit(2)

    page_id = sys.argv[1]
    property_name = sys.argv[2]
    property_type = sys.argv[3]
    property_value = sys.argv[4]

    body = {'properties': build_property(property_name, property_value, property_type)}

    with tempfile.NamedTemporaryFile('w', encoding='utf-8', delete=False) as tf:
        json.dump(body, tf, ensure_ascii=False)
        body_path = tf.name

    try:
        result = run([
            'python3', str(NOTION_API), 'update-page',
            '--page-id', page_id,
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
