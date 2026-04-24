#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from output_guard import emit_output_text

SCRIPT_DIR = Path(__file__).resolve().parent
NOTION_API = SCRIPT_DIR / 'notion_api.py'
WAIT_HELPER = SCRIPT_DIR / 'wait_for_page_content.py'


def run(cmd):
    return subprocess.run(cmd, text=True, capture_output=True)


def run_json(cmd):
    p = run(cmd)
    data = None
    try:
        data = json.loads(p.stdout) if p.stdout.strip() else None
    except Exception:
        data = {'raw_stdout': p.stdout, 'raw_stderr': p.stderr}
    return p.returncode, data, p.stderr


def summarize_result(ok, details=None, hint=None):
    out = {'ok': ok}
    if details is not None:
        out['details'] = details
    if hint:
        out['hint'] = hint
    return out


def check_auth():
    code, data, stderr = run_json(['python3', str(NOTION_API), 'search', '--query', ''])
    if code == 0:
        return summarize_result(True, {'request': 'search', 'result_type': (data or {}).get('object')})
    return summarize_result(False, data or stderr, 'Check NOTION_API_KEY / ~/.config/notion/api_key and integration access.')


def check_page_read(page_id):
    code, data, stderr = run_json(['python3', str(NOTION_API), 'get-page', '--page-id', page_id])
    if code == 0:
        return summarize_result(True, {'page_id': page_id, 'object': (data or {}).get('object')})
    return summarize_result(False, data or stderr, 'Page may not exist or integration lacks access.')


def check_comment_create(page_id):
    code, data, stderr = run_json(['python3', str(NOTION_API), 'create-comment', '--page-id', page_id, '--text', 'capability probe'])
    if code == 0:
        return summarize_result(True, {'page_id': page_id})
    hint = 'If response code is 403 restricted_resource, comment capability is probably disabled for the integration.'
    return summarize_result(False, data or stderr, hint)


def check_markdown_update(page_id):
    body = {
        'type': 'update_content',
        'update_content': {
            'content_updates': [
                {
                    'old_str': '__openclaw_capability_probe_missing__',
                    'new_str': '__openclaw_capability_probe__'
                }
            ]
        }
    }
    import tempfile, os
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', delete=False) as tf:
        json.dump(body, tf, ensure_ascii=False)
        path = tf.name
    try:
        code, data, stderr = run_json(['python3', str(NOTION_API), 'update-page-markdown', '--page-id', page_id, '--body-file', path])
    finally:
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass

    if code == 0:
        return summarize_result(True, {'page_id': page_id, 'note': 'Unexpectedly succeeded; page content likely contained the probe string.'})

    hint = '403 usually means markdown update capability is missing; 400 validation_error with old_str not found usually means capability exists but probe string did not match.'
    return summarize_result(False, data or stderr, hint)


def check_template_ready(page_id, timeout_seconds):
    code, data, stderr = run_json(['python3', str(WAIT_HELPER), page_id, str(timeout_seconds), '3'])
    if code == 0:
        return summarize_result(True, {'page_id': page_id, 'blocks_count': data.get('blocks_count'), 'markdown_nonempty': data.get('markdown_nonempty')})
    return summarize_result(False, data or stderr, 'Template/content population may still be pending, or the page may genuinely be blank.')


def main():
    argv = sys.argv[1:]
    if '--redact' in argv:
        os.environ['NOTION_REDACT_OUTPUT'] = '1'
        argv = [a for a in argv if a != '--redact']

    parser = argparse.ArgumentParser(description='Diagnose Notion auth/capability/readiness issues')
    parser.add_argument('--page-id', help='Page to use for read / markdown / comment probes')
    parser.add_argument('--check-comments', action='store_true')
    parser.add_argument('--check-markdown', action='store_true')
    parser.add_argument('--template-page-id', help='Page created from a template to wait on')
    parser.add_argument('--template-timeout', type=int, default=30)
    args = parser.parse_args(argv)

    report = {'auth': check_auth()}

    if args.page_id:
        report['page_read'] = check_page_read(args.page_id)
        if args.check_comments:
            report['comments_create'] = check_comment_create(args.page_id)
        if args.check_markdown:
            report['markdown_update_probe'] = check_markdown_update(args.page_id)

    if args.template_page_id:
        report['template_readiness'] = check_template_ready(args.template_page_id, args.template_timeout)

    emit_output_text(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
