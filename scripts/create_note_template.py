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


def make_heading(level, text):
    t = f'heading_{level}'
    return {
        'object': 'block',
        'type': t,
        t: {
            'rich_text': [{'type': 'text', 'text': {'content': text}}],
            'is_toggleable': False,
            'color': 'default',
        },
    }


def make_paragraph(text):
    return {
        'object': 'block',
        'type': 'paragraph',
        'paragraph': {
            'rich_text': [{'type': 'text', 'text': {'content': text}}],
            'color': 'default',
        },
    }


def make_callout(emoji, text, color='gray_background'):
    return {
        'object': 'block',
        'type': 'callout',
        'callout': {
            'icon': {'type': 'emoji', 'emoji': emoji},
            'rich_text': [{'type': 'text', 'text': {'content': text}}],
            'color': color,
        },
    }


def make_todo(text, checked=False):
    return {
        'object': 'block',
        'type': 'to_do',
        'to_do': {
            'rich_text': [{'type': 'text', 'text': {'content': text}}],
            'checked': checked,
            'color': 'default',
        },
    }


def make_divider():
    return {'object': 'block', 'type': 'divider', 'divider': {}}


def make_quote(text):
    return {
        'object': 'block',
        'type': 'quote',
        'quote': {
            'rich_text': [{'type': 'text', 'text': {'content': text}}],
            'color': 'default',
        },
    }


def make_code(code, language='plain text'):
    return {
        'object': 'block',
        'type': 'code',
        'code': {
            'rich_text': [{'type': 'text', 'text': {'content': code}}],
            'caption': [],
            'language': language,
        },
    }


def create_template(parent_page_id, title, note_type='general'):
    blocks = [
        make_callout('📝', f'模板类型：{note_type}｜这页由 OpenClaw Notion skill 自动生成。', 'blue_background'),
        make_heading(1, title),
        make_paragraph('在这里先写一句总述，说明这页是干什么的。'),
        make_divider(),
        make_heading(2, '概要'),
        make_paragraph('一句话总结 / 背景 / 目的。'),
        make_heading(2, '重点'),
        make_todo('待补充重点 1'),
        make_todo('待补充重点 2'),
        make_todo('待补充重点 3'),
        make_heading(2, '正文'),
        make_paragraph('把主要内容写在这里。需要的话可以继续追加 heading、callout、code block。'),
        make_heading(2, '附录'),
        make_quote('重要的提醒、摘要，或者一句值得保留的话。'),
    ]

    if note_type == 'meeting':
        blocks = [
            make_callout('📅', '会议纪要模板｜建议会后 5 分钟内补完决议和待办。', 'green_background'),
            make_heading(1, title),
            make_paragraph('会议主题 / 时间 / 参会人先写在这里。'),
            make_heading(2, '会议背景'),
            make_paragraph('这次会为什么开，要解决什么问题。'),
            make_heading(2, '讨论要点'),
            make_todo('议题 1'),
            make_todo('议题 2'),
            make_todo('议题 3'),
            make_heading(2, '结论 / 决议'),
            make_paragraph('把拍板内容写清楚。'),
            make_heading(2, '行动项'),
            make_todo('负责人 / 截止时间 / 事项 1'),
            make_todo('负责人 / 截止时间 / 事项 2'),
            make_heading(2, '补充资料'),
            make_quote('相关链接、附件、上下文备注。'),
        ]
    elif note_type == 'project':
        blocks = [
            make_callout('🚀', '项目页模板｜适合持续补充进度、风险和下一步。', 'purple_background'),
            make_heading(1, title),
            make_paragraph('项目一句话介绍。'),
            make_heading(2, '目标'),
            make_paragraph('这个项目最终要达成什么。'),
            make_heading(2, '当前状态'),
            make_callout('📍', '这里写当前进度、阻塞点、近期变化。'),
            make_heading(2, '里程碑'),
            make_todo('里程碑 1'),
            make_todo('里程碑 2'),
            make_heading(2, '下一步'),
            make_todo('下一步动作 1'),
            make_todo('下一步动作 2'),
            make_heading(2, '命令 / 资料'),
            make_code('# 在这里放常用命令或关键配置', 'bash'),
        ]

    props = {
        'title': {
            'title': [
                {'type': 'text', 'text': {'content': title}}
            ]
        }
    }

    with tempfile.NamedTemporaryFile('w', encoding='utf-8', delete=False) as pf:
        json.dump(props, pf, ensure_ascii=False)
        props_path = pf.name
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', delete=False) as cf:
        json.dump(blocks, cf, ensure_ascii=False)
        children_path = cf.name

    try:
        result = run([
            'python3', str(NOTION_API), 'create-page',
            '--parent-page-id', parent_page_id,
            '--properties-file', props_path,
            '--children-file', children_path,
        ])
        emit_output_text(result.stdout)
    finally:
        for p in (props_path, children_path):
            try:
                os.unlink(p)
            except FileNotFoundError:
                pass


def main():
    if len(sys.argv) < 3:
        print('Usage: create_note_template.py <parent_page_id> <title> [general|meeting|project]', file=sys.stderr)
        raise SystemExit(2)
    parent_page_id = sys.argv[1]
    title = sys.argv[2]
    note_type = sys.argv[3] if len(sys.argv) > 3 else 'general'
    if note_type not in {'general', 'meeting', 'project'}:
        raise SystemExit('note_type must be one of: general, meeting, project')
    create_template(parent_page_id, title, note_type)


if __name__ == '__main__':
    main()
