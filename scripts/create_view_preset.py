#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import unquote
from output_guard import emit_output_text

SCRIPT_DIR = Path(__file__).resolve().parent
NOTION_API = SCRIPT_DIR / 'notion_api.py'

USAGE = '''Usage:
  create_view_preset.py <database_id> <data_source_id> <preset> <name>

Presets:
  table-basic   Minimal table view with common title/status/date fields visible when present
'''


def run(cmd):
    return subprocess.run(cmd, check=True, text=True, capture_output=True)


def get_database(database_id):
    out = run(['python3', str(NOTION_API), 'get-database', '--database-id', database_id]).stdout
    return json.loads(out)


def get_data_source(data_source_id):
    out = run(['python3', str(NOTION_API), 'get-data-source', '--data-source-id', data_source_id]).stdout
    return json.loads(out)


def pick_table_properties(ds):
    wanted = {'名称', '标题', '状态', '跟进时间', '截止日期', '联系人', '品类', '城市', '来源', '是否重点', '备注', '电话'}
    props = []
    for name, meta in ds.get('properties', {}).items():
        if name in wanted or meta.get('type') == 'title':
            props.append({
                'property_id': unquote(meta['id']),
                'property_name': name,
                'visible': True,
                'width': 140 if meta.get('type') != 'title' else 220,
            })
    seen = set()
    uniq = []
    for p in props:
        if p['property_id'] in seen:
            continue
        uniq.append(p)
        seen.add(p['property_id'])
    return uniq


def main():
    if len(sys.argv) != 5:
        print(USAGE, file=sys.stderr)
        raise SystemExit(2)
    database_id, data_source_id, preset, name = sys.argv[1:5]
    if preset != 'table-basic':
        print(USAGE, file=sys.stderr)
        raise SystemExit(2)
    get_database(database_id)  # validate early
    ds = get_data_source(data_source_id)
    body = {
        'database_id': database_id,
        'data_source_id': data_source_id,
        'name': name,
        'type': 'table',
        'configuration': {
            'type': 'table',
            'properties': pick_table_properties(ds),
        },
    }
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', delete=False) as tf:
        json.dump(body, tf, ensure_ascii=False)
        path = tf.name
    try:
        emit_output_text(run(['python3', str(NOTION_API), 'create-view', '--body-file', path]).stdout)
    finally:
        Path(path).unlink(missing_ok=True)


if __name__ == '__main__':
    main()
