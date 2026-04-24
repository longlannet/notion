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

USAGE = 'Usage: create_data_source.py <parent_page_id> <database_title> [minimal|rich] [title_property_name]'


def run(cmd):
    return subprocess.run(cmd, check=True, text=True, capture_output=True)


def minimal_schema(title_name='名称'):
    return {
        title_name: {'title': {}},
        '文本': {'rich_text': {}}
    }


def rich_schema(title_name='名称'):
    return {
        title_name: {'title': {}},
        '文本': {'rich_text': {}},
        '状态': {'status': {'options': [
            {'name': '未开始', 'color': 'default'},
            {'name': '进行中', 'color': 'blue'},
            {'name': '已完成', 'color': 'green'}]}},
        '标签': {'multi_select': {'options': [
            {'name': '重要', 'color': 'red'},
            {'name': '跟进', 'color': 'yellow'},
            {'name': '资料', 'color': 'gray'}]}},
        '是否完成': {'checkbox': {}},
        '截止日期': {'date': {}},
        '优先级': {'select': {'options': [
            {'name': '低', 'color': 'gray'},
            {'name': '中', 'color': 'yellow'},
            {'name': '高', 'color': 'red'}]}},
        '分数': {'number': {'format': 'number'}},
        '链接': {'url': {}},
        '邮箱': {'email': {}},
        '电话': {'phone_number': {}},
        '负责人': {'people': {}},
    }


def main():
    if len(sys.argv) < 3:
        print(USAGE, file=sys.stderr)
        raise SystemExit(2)
    parent_page_id = sys.argv[1]
    database_title = sys.argv[2]
    preset = sys.argv[3] if len(sys.argv) >= 4 else 'minimal'
    title_name = sys.argv[4] if len(sys.argv) >= 5 else '名称'
    if preset not in {'minimal', 'rich'}:
        print(USAGE, file=sys.stderr)
        raise SystemExit(2)
    props = minimal_schema(title_name) if preset == 'minimal' else rich_schema(title_name)
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', delete=False) as pf:
        json.dump(props, pf, ensure_ascii=False)
        props_path = pf.name
    try:
        result = run([
            'python3', str(NOTION_API), 'create-database',
            '--parent-page-id', parent_page_id,
            '--title', database_title,
            '--is-inline',
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
