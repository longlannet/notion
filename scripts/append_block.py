#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

USAGE = """Usage:
  append_block.py <page_id> paragraph <text>
  append_block.py <page_id> heading <level:1|2|3> <text>
  append_block.py <page_id> callout <emoji> <text>
  append_block.py <page_id> todo <text> [true|false]
  append_block.py <page_id> quote <text>
  append_block.py <page_id> divider
  append_block.py <page_id> bulleted_list_item <text>
  append_block.py <page_id> numbered_list_item <text>
  append_block.py <page_id> toggle <text>
  append_block.py <page_id> code <language> <code>
"""


def text_obj(text: str) -> list:
    return [{"type": "text", "text": {"content": text}}]


def build_block(kind: str, args: list[str]) -> dict:
    if kind == 'paragraph':
        if len(args) != 1:
            raise SystemExit(USAGE)
        return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": text_obj(args[0])}}
    if kind == 'heading':
        if len(args) != 2 or args[0] not in {'1', '2', '3'}:
            raise SystemExit(USAGE)
        btype = f"heading_{args[0]}"
        return {"object": "block", "type": btype, btype: {"rich_text": text_obj(args[1]), "is_toggleable": False, "color": "default"}}
    if kind == 'callout':
        if len(args) != 2:
            raise SystemExit(USAGE)
        return {"object": "block", "type": "callout", "callout": {"icon": {"type": "emoji", "emoji": args[0]}, "rich_text": text_obj(args[1]), "color": "gray_background"}}
    if kind == 'todo':
        if len(args) not in {1, 2}:
            raise SystemExit(USAGE)
        checked = False if len(args) == 1 else args[1].lower() == 'true'
        return {"object": "block", "type": "to_do", "to_do": {"rich_text": text_obj(args[0]), "checked": checked, "color": "default"}}
    if kind == 'quote':
        if len(args) != 1:
            raise SystemExit(USAGE)
        return {"object": "block", "type": "quote", "quote": {"rich_text": text_obj(args[0]), "color": "default"}}
    if kind == 'divider':
        if args:
            raise SystemExit(USAGE)
        return {"object": "block", "type": "divider", "divider": {}}
    if kind == 'bulleted_list_item':
        if len(args) != 1:
            raise SystemExit(USAGE)
        return {"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": text_obj(args[0]), "color": "default"}}
    if kind == 'numbered_list_item':
        if len(args) != 1:
            raise SystemExit(USAGE)
        return {"object": "block", "type": "numbered_list_item", "numbered_list_item": {"rich_text": text_obj(args[0]), "color": "default"}}
    if kind == 'toggle':
        if len(args) != 1:
            raise SystemExit(USAGE)
        return {"object": "block", "type": "toggle", "toggle": {"rich_text": text_obj(args[0]), "color": "default", "children": []}}
    if kind == 'code':
        if len(args) != 2:
            raise SystemExit(USAGE)
        return {"object": "block", "type": "code", "code": {"rich_text": text_obj(args[1]), "caption": [], "language": args[0]}}
    raise SystemExit(USAGE)


def main() -> int:
    if len(sys.argv) < 3:
        print(USAGE, file=sys.stderr)
        return 2
    page_id = sys.argv[1]
    kind = sys.argv[2]
    args = sys.argv[3:]
    block = build_block(kind, args)
    children_json = json.dumps([block], ensure_ascii=False)
    notion_api = Path(__file__).with_name('notion_api.py')
    cmd = ['python3', str(notion_api), 'append-blocks', '--block-id', page_id, '--children-json', children_json]
    return subprocess.call(cmd)


if __name__ == '__main__':
    raise SystemExit(main())
