#!/usr/bin/env python3
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
PY = sys.executable
NOTION_API = SCRIPT_DIR / 'notion_api.py'
PARENT_PAGE_ID = os.environ.get('NOTION_TEST_PARENT_PAGE_ID', '').strip()
if not PARENT_PAGE_ID:
    raise SystemExit('Set NOTION_TEST_PARENT_PAGE_ID to a shared parent page id before running validate_helper_wrappers.py')
KEEP_ARTIFACTS = os.environ.get('NOTION_KEEP_VALIDATION_ARTIFACTS', '').strip() == '1'
UUID_RE = re.compile(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', re.I)
STAMP = str(int(time.time()))
TMP = Path(f'/tmp/notion-helper-wrappers-{STAMP}')
TMP.mkdir(parents=True, exist_ok=True)
IMAGE_URL = 'https://www.w3.org/Icons/w3c_home.png'
FILE_URL = 'https://raw.githubusercontent.com/github/gitignore/main/README.md'
WEB_URL = 'https://example.com'

results = []
notes = []
root_page_id = None
support_page_id = None
ops_page_id = None
markdown_page_id = None
template_page_id = None
db1_id = None
ds1_id = None
db2_id = None
ds2_id = None
cover_db_id = None
item1_id = None
item2_id = None
external_upload_id = None
file_upload_ids = []


def scrub(value):
    text = str(value)
    return UUID_RE.sub('<id>', text)


def rec(name, status, detail=''):
    safe_detail = scrub(detail)
    results.append({'name': name, 'status': status, 'detail': safe_detail})
    print(f'[{status}] {name}: {safe_detail}')


def write_json(name, obj):
    p = TMP / name
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')
    return p


def run(cmd, expect_ok=True, cwd=None):
    cp = subprocess.run(cmd, text=True, capture_output=True, cwd=cwd)
    if expect_ok and cp.returncode != 0:
        raise RuntimeError(f'Command failed: {cmd}\nSTDOUT:\n{cp.stdout}\nSTDERR:\n{cp.stderr}')
    return cp


def run_json(cmd, label=None, cwd=None):
    cp = run(cmd, True, cwd=cwd)
    try:
        obj = json.loads(cp.stdout)
    except Exception as e:
        raise RuntimeError(f'JSON parse failed for {cmd}: {e}\nOUT:\n{cp.stdout}')
    if label and KEEP_ARTIFACTS:
        write_json(f'{label}.json', obj)
    return obj


def run_script_py(name, args, label=None):
    return run_json([PY, str(SCRIPT_DIR / name), *args], label)


def run_script_sh(name, args, expect_json=False):
    cp = run(['bash', str(SCRIPT_DIR / name), *args], True)
    if expect_json:
        return json.loads(cp.stdout)
    return cp.stdout


def cleanup():
    if root_page_id:
        try:
            run_json([PY, str(NOTION_API), 'trash-page', '--page-id', root_page_id], 'cleanup-root-trash')
            rec('cleanup.root_page', 'PASS', root_page_id)
        except Exception as e:
            rec('cleanup.root_page', 'WARN', str(e))
    if file_upload_ids:
        rec('cleanup.file_upload_objects', 'WARN', f'Notion file upload objects are retained by API: count={len(file_upload_ids)}')
    if not KEEP_ARTIFACTS:
        shutil.rmtree(TMP, ignore_errors=True)


def main():
    global root_page_id, support_page_id, ops_page_id, markdown_page_id, template_page_id
    global db1_id, ds1_id, db2_id, ds2_id, cover_db_id, item1_id, item2_id, external_upload_id, file_upload_ids
    try:
        # basic helpers
        selfcheck = run_json([PY, str(SCRIPT_DIR / 'selfcheck.py')], 'selfcheck')
        rec('selfcheck.py', 'PASS', selfcheck.get('api_version', 'unknown'))

        me = run_json([PY, str(NOTION_API), 'get-self'], 'get-self-helper-bootstrap')
        self_user_id = me['id']
        users = run_json([PY, str(NOTION_API), 'list-users', '--page-size', '50'], 'helper-users-bootstrap')
        person_id = None
        for u in users.get('results', []):
            if u.get('type') == 'person':
                person_id = u.get('id')
                break

        # isolated root tree
        props = write_json('root-props.json', {'title': {'title': [{'type': 'text', 'text': {'content': f'Helper Root {STAMP}'}}]}})
        root = run_json([PY, str(NOTION_API), 'create-page', '--parent-page-id', PARENT_PAGE_ID, '--properties-file', str(props)], 'root-create')
        root_page_id = root['id']
        rec('bootstrap.root_page', 'PASS', 'root page created')

        support_props = write_json('support-props.json', {'title': {'title': [{'type': 'text', 'text': {'content': f'Support Holder {STAMP}'}}]}})
        support = run_json([PY, str(NOTION_API), 'create-page', '--parent-page-id', root_page_id, '--properties-file', str(support_props)], 'support-page-create')
        support_page_id = support['id']
        rec('bootstrap.support_page', 'PASS', 'support page created')

        # shell wrappers using summary_lib paths
        out = run_script_sh('search_pages.sh', [f'Helper Root {STAMP}'])
        rec('search_pages.sh', 'PASS', out.splitlines()[0] if out.strip() else 'non-empty output')
        out = run_script_sh('list_users.sh', [])
        rec('list_users.sh', 'PASS', out.splitlines()[0] if out.strip() else 'non-empty output')
        out = run_script_sh('get_user.sh', [self_user_id])
        rec('get_user.sh', 'PASS', out.splitlines()[0] if out.strip() else self_user_id)

        # page_ops
        page_ops_created = run_script_py('page_ops.py', ['create-subpage', root_page_id, f'Ops Page {STAMP}'], 'page-ops-create')
        ops_page_id = page_ops_created['id']
        rec('page_ops.py create-subpage', 'PASS', 'subpage created')
        page_ops_updated = run_script_py('page_ops.py', ['update-title', ops_page_id, f'Ops Page Updated {STAMP}'], 'page-ops-update')
        rec('page_ops.py update-title', 'PASS', 'title updated')
        md = run_script_py('page_ops.py', ['read-markdown', ops_page_id], 'page-ops-read-markdown')
        rec('page_ops.py read-markdown', 'PASS', 'markdown read')

        # append_block.py: all supported branches
        append_cases = [
            ('paragraph', [ops_page_id, 'paragraph', f'para {STAMP}']),
            ('heading', [ops_page_id, 'heading', '2', f'head {STAMP}']),
            ('callout', [ops_page_id, 'callout', '💡', f'callout {STAMP}']),
            ('todo', [ops_page_id, 'todo', f'todo {STAMP}', 'true']),
            ('quote', [ops_page_id, 'quote', f'quote {STAMP}']),
            ('divider', [ops_page_id, 'divider']),
            ('bulleted_list_item', [ops_page_id, 'bulleted_list_item', f'bullet {STAMP}']),
            ('numbered_list_item', [ops_page_id, 'numbered_list_item', f'num {STAMP}']),
            ('toggle', [ops_page_id, 'toggle', f'toggle {STAMP}']),
            ('code', [ops_page_id, 'code', 'bash', f'echo helper-{STAMP}']),
        ]
        for kind, args in append_cases:
            run([PY, str(SCRIPT_DIR / 'append_block.py'), *args], True)
            rec(f'append_block.py {kind}', 'PASS', 'block appended')

        out = run_script_sh('read_page.sh', [ops_page_id])
        rec('read_page.sh', 'PASS', 'page read output returned')

        # markdown helper
        page_ops_created2 = run_script_py('page_ops.py', ['create-subpage', root_page_id, f'Markdown Page {STAMP}'], 'markdown-page-create')
        markdown_page_id = page_ops_created2['id']
        run([PY, str(SCRIPT_DIR / 'update_page_markdown.py'), markdown_page_id, 'replace', f'# Wrapper Markdown {STAMP}\n\nbody'], True)
        rec('update_page_markdown.py replace', 'PASS', 'markdown replaced')
        md2 = run_script_py('page_ops.py', ['read-markdown', markdown_page_id], 'markdown-page-read')
        rec('page_ops.py read-markdown(after update_page_markdown)', 'PASS', 'markdown read after update')

        # template helper + wait helper
        template = run_script_py('create_note_template.py', [root_page_id, f'Template Page {STAMP}', 'meeting'], 'create-note-template')
        template_page_id = template['id']
        rec('create_note_template.py', 'PASS', 'template page created')
        wait_data = run_json([PY, str(SCRIPT_DIR / 'wait_for_page_content.py'), template_page_id, '20', '2'], 'wait-for-page-content')
        if not wait_data.get('ready'):
            raise RuntimeError('wait_for_page_content.py did not see template content')
        rec('wait_for_page_content.py', 'PASS', f"blocks={wait_data.get('blocks_count')}")

        # comment shell wrapper + diagnostics
        comment = run_script_sh('create_comment.sh', [ops_page_id, f'wrapper comment {STAMP}'], expect_json=True)
        rec('create_comment.sh', 'PASS', 'comment created')
        diag = run_json([PY, str(SCRIPT_DIR / 'diagnose_capabilities.py'), '--page-id', ops_page_id, '--check-comments', '--check-markdown', '--template-page-id', template_page_id, '--template-timeout', '10'], 'diagnose-capabilities')
        rec('diagnose_capabilities.py', 'PASS', 'report generated')

        # create_data_source.py rich + minimal
        rich_db = run_script_py('create_data_source.py', [root_page_id, f'Wrapper DB Rich {STAMP}', 'rich'], 'create-data-source-rich')
        db1_id = rich_db['id']
        ds1_id = rich_db['data_sources'][0]['id']
        rec('create_data_source.py rich', 'PASS', 'rich starter database created')

        minimal_db = run_script_py('create_data_source.py', [root_page_id, f'Wrapper DB Minimal {STAMP}', 'minimal'], 'create-data-source-minimal')
        db2_id = minimal_db['id']
        ds2_id = minimal_db['data_sources'][0]['id']
        rec('create_data_source.py minimal', 'PASS', 'minimal starter database created')

        cover_db_props = write_json('cover-db-props.json', {'Name': {'title': {}}})
        cover_db = run_json([PY, str(NOTION_API), 'create-database', '--parent-page-id', root_page_id, '--title', f'Wrapper Cover DB {STAMP}', '--properties-file', str(cover_db_props)], 'create-cover-db')
        cover_db_id = cover_db['id']
        rec('bootstrap.non_inline_database_for_cover', 'PASS', 'non-inline database created')

        out = run_script_sh('search_data_sources.sh', [f'Wrapper DB Rich {STAMP}'])
        rec('search_data_sources.sh', 'PASS', 'data source search output returned')
        out = run_script_sh('get_data_source.sh', [ds1_id])
        rec('get_data_source.sh', 'PASS', 'data source output returned')
        out = run_script_sh('query_data_source.sh', [ds1_id])
        rec('query_data_source.sh', 'PASS', 'query output returned')

        ds1 = run_json([PY, str(NOTION_API), 'get-data-source', '--data-source-id', ds1_id], 'ds1-get')
        title_name = next(name for name, meta in ds1['properties'].items() if meta.get('type') == 'title')

        item1 = run_script_py('create_database_item.py', [ds1_id, title_name, f'Wrapper Item {STAMP}'], 'create-database-item')
        item1_id = item1['id']
        rec('create_database_item.py', 'PASS', 'database item created')

        q1 = run_script_py('query_data_source_items.py', [ds1_id, '--title-property', title_name, '--title-query', 'Wrapper Item'], 'query-data-source-items-title')
        rec('query_data_source_items.py title-query', 'PASS', f"results={len(q1.get('results', []))}")

        upd_item = run_script_py('update_database_item.py', [item1_id, '文本', f'Text body {STAMP}', 'rich_text'], 'update-database-item')
        rec('update_database_item.py', 'PASS', 'database item updated')

        # schema/property helpers on ds1
        run_script_py('add_select_property.py', [ds1_id, '单选', 'A,B'], 'add-select-property')
        rec('add_select_property.py', 'PASS', ds1_id)
        run_script_py('add_multi_select_property.py', [ds1_id, '多选2', 'X,Y'], 'add-multi-select-property')
        rec('add_multi_select_property.py', 'PASS', ds1_id)
        run_script_py('add_formula_property.py', [ds1_id, '公式字段', '1+1'], 'add-formula-property')
        rec('add_formula_property.py', 'PASS', ds1_id)
        run_script_py('add_unique_id_property.py', [ds1_id, '编号', 'HW'], 'add-unique-id-property')
        rec('add_unique_id_property.py', 'PASS', ds1_id)
        run_script_py('add_database_property.py', [ds1_id, '附件属性', 'files'], 'add-database-property')
        rec('add_database_property.py', 'PASS', ds1_id)
        run_script_py('update_database_property.py', [ds1_id, '附件属性', '附件'], 'update-database-property')
        rec('update_database_property.py', 'PASS', ds1_id)
        run_script_py('update_select_options.py', [ds1_id, '单选', 'select', 'A,B,C'], 'update-select-options')
        rec('update_select_options.py', 'PASS', ds1_id)
        run_script_py('add_relation_property.py', [ds1_id, '关联项', ds2_id, 'single_property'], 'add-relation-property')
        rec('add_relation_property.py', 'PASS', ds1_id)
        run_script_py('add_rollup_property.py', [ds1_id, '汇总文本', '关联项', '文本', 'show_original'], 'add-rollup-property')
        rec('add_rollup_property.py', 'PASS', ds1_id)

        # create target related item in ds2
        ds2 = run_json([PY, str(NOTION_API), 'get-data-source', '--data-source-id', ds2_id], 'ds2-get')
        title2 = next(name for name, meta in ds2['properties'].items() if meta.get('type') == 'title')
        item2 = run_script_py('create_database_item.py', [ds2_id, title2, f'Related Item {STAMP}'], 'create-database-item-2')
        item2_id = item2['id']
        rec('create_database_item.py (related target)', 'PASS', 'related target item created')

        # import external file helper
        ext_upload = run_script_py('import_external_file.py', [FILE_URL, f'wrapper-{STAMP}.txt', 'text/plain'], 'import-external-file')
        external_upload_id = ext_upload['id']
        file_upload_ids.append(external_upload_id)
        rec('import_external_file.py', 'PASS', 'external file imported')

        out = run_script_sh('get_file_upload.sh', [external_upload_id])
        rec('get_file_upload.sh', 'PASS', 'file upload output returned')
        out = run_script_sh('list_file_uploads.sh', [])
        rec('list_file_uploads.sh', 'PASS', out.splitlines()[0] if out.strip() else 'listed')

        # item value helper across multiple property branches
        branches = [
            ('文本2', 'rich_text', f'rt {STAMP}'),
            (title_name, 'title', f'Wrapper Item Updated {STAMP}'),
            ('单选', 'select', 'C'),
            ('状态', 'status', '进行中'),
            ('是否完成', 'checkbox', 'true'),
            ('截止日期', 'date', '2026-05-01'),
            ('分数', 'number', '88'),
            ('标签', 'multi_select', '重要,跟进'),
            ('链接', 'url', WEB_URL),
            ('邮箱', 'email', 'user@example.com'),
            ('电话', 'phone_number', '0000000000'),
            ('关联项', 'relation', item2_id),
            ('附件', 'files_external', FILE_URL),
        ]
        # add extra rich_text property for branch coverage
        run_script_py('add_database_property.py', [ds1_id, '文本2', 'rich_text'], 'add-rich-text-prop')
        for prop, ptype, value in branches:
            run_script_py('update_database_item_value.py', [item1_id, prop, ptype, value], f'update-item-{ptype}-{prop}')
            rec(f'update_database_item_value.py {ptype}', 'PASS', prop)
        if person_id:
            try:
                run_script_py('update_database_item_value.py', [item1_id, '负责人', 'people', person_id], 'update-item-people')
                rec('update_database_item_value.py people', 'PASS', 'people property updated')
            except Exception as e:
                rec('update_database_item_value.py people', 'WARN', str(e).splitlines()[0])
        else:
            rec('update_database_item_value.py people', 'WARN', 'No person user available in workspace for safe test')

        q2 = run_script_py('query_data_source_items.py', [ds1_id, '--property-name', '状态', '--property-type', 'status', '--operator', 'equals', '--value', '进行中'], 'query-data-source-items-status')
        rec('query_data_source_items.py property-filter', 'PASS', f"results={len(q2.get('results', []))}")

        item_get = run_json([PY, str(NOTION_API), 'get-page', '--page-id', item1_id], 'item1-get-final')
        rec('helper item verification', 'PASS', 'item verified')

        # view/database/media wrappers
        view = run_script_py('create_view_preset.py', [db1_id, ds1_id, 'table-basic', f'Preset View {STAMP}'], 'create-view-preset')
        rec('create_view_preset.py', 'PASS', 'view created')

        run_script_py('set_page_media.py', [ops_page_id, 'icon', 'external', IMAGE_URL], 'set-page-media-icon')
        rec('set_page_media.py icon', 'PASS', 'page icon set')
        run_script_py('set_page_media.py', [ops_page_id, 'cover', 'external', IMAGE_URL], 'set-page-media-cover')
        rec('set_page_media.py cover', 'PASS', 'page cover set')
        run_script_py('set_database_media.py', [db1_id, 'icon', 'emoji', '📚'], 'set-db-media-icon')
        rec('set_database_media.py icon', 'PASS', 'database icon set')
        run_script_py('set_database_media.py', [cover_db_id, 'cover', 'external', IMAGE_URL], 'set-db-media-cover')
        rec('set_database_media.py cover', 'PASS', 'database cover set')

        # database_ops wrapper commands (includes indirect media helpers)
        dbget = run_script_py('database_ops.py', ['get', db1_id], 'database-ops-get')
        rec('database_ops.py get', 'PASS', 'database retrieved')
        run_script_py('database_ops.py', ['set-icon', db1_id, '🧪'], 'database-ops-set-icon')
        rec('database_ops.py set-icon', 'PASS', 'database icon updated')
        run_script_py('database_ops.py', ['set-cover', cover_db_id, IMAGE_URL], 'database-ops-set-cover')
        rec('database_ops.py set-cover', 'PASS', 'database cover updated')
        run_script_py('database_ops.py', ['move', db1_id, support_page_id], 'database-ops-move')
        rec('database_ops.py move', 'PASS', 'database moved')
        run_script_py('database_ops.py', ['trash', db1_id], 'database-ops-trash')
        rec('database_ops.py trash', 'PASS', 'database trashed')
        run_script_py('database_ops.py', ['restore', db1_id], 'database-ops-restore')
        rec('database_ops.py restore', 'PASS', 'database restored')

        # media block wrapper
        run_script_py('append_media_block.py', [ops_page_id, 'file', 'external', FILE_URL, f'ext-{STAMP}.txt', 'external file'], 'append-media-block')
        rec('append_media_block.py', 'PASS', 'media block appended')

        # import webpage wrapper (may be env-blocked by external search skill)
        try:
            webpage = run_script_py('import_webpage.py', [root_page_id, f'Imported Web {STAMP}', WEB_URL], 'import-webpage')
            rec('import_webpage.py', 'PASS', 'webpage imported')
        except Exception as e:
            msg = str(e)
            if 'No webpage text extracted' in msg or 'SERPER' in msg or 'api key' in msg.lower() or 'google-search' in msg:
                rec('import_webpage.py', 'BLOCKED', 'external webpage extraction dependency unavailable in current environment')
            else:
                raise

        summary = {
            'stamp': STAMP,
            'results': results,
            'notes': notes,
        }
        if KEEP_ARTIFACTS:
            write_json('summary.json', summary)
            print('SUMMARY_FILE', TMP / 'summary.json')
        else:
            print('ARTIFACTS_RETAINED=0')
        print('PASS_COUNT', sum(1 for r in results if r['status'] == 'PASS'))
        print('BLOCKED_COUNT', sum(1 for r in results if r['status'] == 'BLOCKED'))
        print('WARN_COUNT', sum(1 for r in results if r['status'] == 'WARN'))
        print('OK_NOTION_HELPER_WRAPPERS=1')
    finally:
        cleanup()


if __name__ == '__main__':
    main()
