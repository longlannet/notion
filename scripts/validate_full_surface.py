#!/usr/bin/env python3
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
NOTION_API = SCRIPT_DIR / 'notion_api.py'
PY = sys.executable
PARENT_PAGE_ID = os.environ.get('NOTION_TEST_PARENT_PAGE_ID', '').strip()
if not PARENT_PAGE_ID:
    raise SystemExit('Set NOTION_TEST_PARENT_PAGE_ID to a shared parent page id before running validate_full_surface.py')
KEEP_ARTIFACTS = os.environ.get('NOTION_KEEP_VALIDATION_ARTIFACTS', '').strip() == '1'
UUID_RE = re.compile(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', re.I)
STAMP = str(int(__import__('time').time()))
TMP = Path(f'/tmp/notion-full-surface-{STAMP}')
TMP.mkdir(parents=True, exist_ok=True)

results = []
notes = []


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


def run(args, expect_ok=True):
    cmd = [PY, str(NOTION_API), *args]
    cp = subprocess.run(cmd, text=True, capture_output=True)
    if expect_ok and cp.returncode != 0:
        raise RuntimeError(f'Command failed: {cmd}\nSTDOUT:\n{cp.stdout}\nSTDERR:\n{cp.stderr}')
    return cp


def run_json(args, label=None):
    cp = run(args, expect_ok=True)
    try:
        obj = json.loads(cp.stdout)
    except Exception as e:
        raise RuntimeError(f'JSON parse failed for {args}: {e}\nOUT:\n{cp.stdout}')
    if label and KEEP_ARTIFACTS:
        write_json(f'{label}.json', obj)
    return obj


def expect_local_block(name, args, needle):
    cp = run(args, expect_ok=False)
    merged = (cp.stdout or '') + '\n' + (cp.stderr or '')
    if cp.returncode == 0 or needle not in merged:
        raise RuntimeError(f'Expected blocked error containing {needle!r} for {args}, got rc={cp.returncode}\n{merged}')
    rec(name, 'BLOCKED', needle)


root_page_id = None
sibling_page_id = None
movable_page_id = None
update_target_page_id = None
db_id = None
ds_id = None
ds2_id = None
view_id = None
view_query_id = None
paragraph_block_id = None
heading_block_id = None
comment_id = None
single_upload_id = None
multi_upload_id = None


def cleanup():
    # best-effort cleanup; root page trash should cascade to nested pages/databases/items/comments/views.
    if root_page_id:
        try:
            run_json(['trash-page', '--page-id', root_page_id], 'cleanup-root-trash')
            rec('cleanup.root_page', 'PASS', root_page_id)
        except Exception as e:
            rec('cleanup.root_page', 'WARN', str(e))
    if single_upload_id or multi_upload_id:
        count = len([x for x in [single_upload_id, multi_upload_id] if x])
        rec('cleanup.file_upload_objects', 'WARN', f'Notion file upload objects are retained by API; count={count}')
    if not KEEP_ARTIFACTS:
        shutil.rmtree(TMP, ignore_errors=True)


def main():
    global root_page_id, sibling_page_id, movable_page_id, update_target_page_id
    global db_id, ds_id, ds2_id, view_id, view_query_id, paragraph_block_id, heading_block_id, comment_id
    global single_upload_id, multi_upload_id

    try:
        subprocess.run([PY, '-m', 'py_compile', str(NOTION_API)], check=True)
        rec('py_compile.notion_api', 'PASS', 'compiled')

        self_obj = run_json(['get-self'], 'get-self')
        self_user_id = self_obj['id']
        rec('get-self', 'PASS', 'identity retrieved')

        users = run_json(['list-users', '--page-size', '10'], 'list-users')
        rec('list-users', 'PASS', f"returned {len(users.get('results', []))} users")

        user = run_json(['get-user', '--user-id', self_user_id], 'get-user')
        rec('get-user', 'PASS', 'user retrieved')

        emojis = run_json(['list-custom-emojis'], 'list-custom-emojis')
        rec('list-custom-emojis', 'PASS', f"count={len(emojis.get('results', emojis.get('custom_emojis', [])))}")

        # Create isolated root + sibling pages under the lab parent page.
        root_props = write_json('root-props.json', {
            'title': {'title': [{'type': 'text', 'text': {'content': f'Full Surface Root {STAMP}'}}]}
        })
        root = run_json(['create-page', '--parent-page-id', PARENT_PAGE_ID, '--properties-file', str(root_props)], 'create-root-page')
        root_page_id = root['id']
        rec('create-page(parent_page)', 'PASS', 'root page created')

        search = run_json(['search', '--query', f'Full Surface Root {STAMP}', '--page-size', '10'], 'search')
        rec('search', 'PASS', f"results={len(search.get('results', []))}; note=search indexing may lag for newly created pages")

        page = run_json(['get-page', '--page-id', root_page_id], 'get-page-root')
        rec('get-page', 'PASS', 'page retrieved')

        update_props = write_json('update-root-props.json', {
            'title': {'title': [{'type': 'text', 'text': {'content': f'Full Surface Root Updated {STAMP}'}}]}
        })
        updated = run_json(['update-page', '--page-id', root_page_id, '--properties-file', str(update_props)], 'update-page-title')
        rec('update-page', 'PASS', 'page updated')

        children = write_json('append-children.json', [
            {
                'object': 'block',
                'type': 'paragraph',
                'paragraph': {
                    'rich_text': [{'type': 'text', 'text': {'content': f'Block paragraph {STAMP}'}}]
                }
            },
            {
                'object': 'block',
                'type': 'heading_2',
                'heading_2': {
                    'rich_text': [{'type': 'text', 'text': {'content': f'Block heading {STAMP}'}}]
                }
            }
        ])
        appended = run_json(['append-blocks', '--block-id', root_page_id, '--children-file', str(children)], 'append-blocks')
        created_blocks = appended.get('results', [])
        paragraph_block_id = created_blocks[0]['id']
        heading_block_id = created_blocks[1]['id']
        rec('append-blocks', 'PASS', '2 blocks appended')

        blocks = run_json(['get-blocks', '--block-id', root_page_id, '--page-size', '100'], 'get-blocks')
        rec('get-blocks', 'PASS', f"returned {len(blocks.get('results', []))} blocks")

        block = run_json(['get-block', '--block-id', paragraph_block_id], 'get-block')
        rec('get-block', 'PASS', 'block retrieved')

        update_block_body = write_json('update-block.json', {
            'paragraph': {
                'rich_text': [{'type': 'text', 'text': {'content': f'Block paragraph updated {STAMP}'}}]
            }
        })
        updated_block = run_json(['update-block', '--block-id', paragraph_block_id, '--body-file', str(update_block_body)], 'update-block')
        rec('update-block', 'PASS', 'block updated')

        comment = run_json(['create-comment', '--block-id', paragraph_block_id, '--markdown', f'Comment on block {STAMP}'], 'create-comment')
        comment_id = comment['id']
        rec('create-comment', 'PASS', 'comment created')

        listed_comments = run_json(['list-comments', '--block-id', paragraph_block_id, '--page-size', '20'], 'list-comments')
        comment_ids = [c.get('id') for c in listed_comments.get('results', listed_comments.get('comments', []))]
        if comment_id not in comment_ids:
            raise RuntimeError('list-comments did not include the created comment')
        rec('list-comments', 'PASS', 'comment present in list')

        comment_get = run_json(['get-comment', '--comment-id', comment_id], 'get-comment')
        rec('get-comment', 'PASS', 'comment retrieved')

        comment_upd = run_json(['update-comment', '--comment-id', comment_id, '--markdown', f'Comment updated {STAMP}'], 'update-comment')
        rec('update-comment', 'PASS', 'comment updated')

        run_json(['delete-comment', '--comment-id', comment_id], 'delete-comment')
        rec('delete-comment', 'PASS', 'comment deleted')

        deleted_block = run_json(['delete-block', '--block-id', paragraph_block_id], 'delete-block')
        rec('delete-block', 'PASS', 'block deleted')

        restored_block = run_json(['restore-block', '--block-id', paragraph_block_id], 'restore-block')
        rec('restore-block', 'PASS', 'block restored')

        md_body = write_json('update-page-markdown.json', {
            'type': 'replace_content',
            'replace_content': {
                'new_str': f'# Full Surface Markdown {STAMP}\n\nThis page is for isolated testing only.',
                'allow_deleting_content': True,
            }
        })
        md_upd = run_json(['update-page-markdown', '--page-id', root_page_id, '--body-file', str(md_body)], 'update-page-markdown')
        rec('update-page-markdown', 'PASS', md_upd.get('request_id', 'ok'))

        markdown = run_json(['get-page-markdown', '--page-id', root_page_id], 'get-page-markdown')
        if f'Full Surface Markdown {STAMP}' not in markdown.get('markdown', ''):
            raise RuntimeError('get-page-markdown did not return updated content')
        rec('get-page-markdown', 'PASS', 'markdown retrieved')

        db_props = write_json('db-props.json', {
            'Name': {'title': {}},
            'Status': {'status': {}}
        })
        db = run_json(['create-database', '--parent-page-id', root_page_id, '--title', f'Full Surface DB {STAMP}', '--properties-file', str(db_props)], 'create-database')
        db_id = db['id']
        ds_id = db['data_sources'][0]['id']
        rec('create-database', 'PASS', 'database and primary data source created')

        db_get = run_json(['get-database', '--database-id', db_id], 'get-database')
        rec('get-database', 'PASS', 'database retrieved')

        ds_get = run_json(['get-data-source', '--data-source-id', ds_id], 'get-data-source')
        rec('get-data-source', 'PASS', 'data source retrieved')

        title_prop_id = ds_get['properties']['Name']['id']

        ds_query = run_json(['query-data-source', '--data-source-id', ds_id], 'query-data-source')
        rec('query-data-source', 'PASS', f"results={len(ds_query.get('results', []))}")

        ds_item_props = write_json('ds-item-props.json', {
            'Name': {'title': [{'type': 'text', 'text': {'content': f'DS Item {STAMP}'}}]}
        })
        ds_item = run_json(['create-page', '--parent-data-source-id', ds_id, '--properties-file', str(ds_item_props)], 'create-page-parent-ds')
        ds_item_id = ds_item['id']
        rec('create-page(parent_data_source)', 'PASS', 'data-source item created')

        db_item_props = write_json('db-item-props.json', {
            'Name': {'title': [{'type': 'text', 'text': {'content': f'DB Item {STAMP}'}}]}
        })
        db_item = run_json(['create-page', '--parent-database-id', db_id, '--properties-file', str(db_item_props)], 'create-page-parent-db')
        db_item_id = db_item['id']
        rec('create-page(parent_database)', 'PASS', 'database item created')

        ds_item_get = run_json(['get-page', '--page-id', ds_item_id], 'get-page-ds-item')
        rec('get-page(ds item)', 'PASS', 'data-source item retrieved')

        prop_item = run_json(['get-page-property', '--page-id', ds_item_id, '--property-id', title_prop_id], 'get-page-property')
        rec('get-page-property', 'PASS', prop_item.get('object', 'ok'))

        ds2_props = write_json('ds2-props.json', {
            'AltName': {'title': {}}
        })
        ds2 = run_json(['create-data-source', '--parent-database-id', db_id, '--name', f'Secondary DS {STAMP}', '--properties-file', str(ds2_props)], 'create-data-source')
        ds2_id = ds2['id']
        rec('create-data-source', 'PASS', 'secondary data source created')

        ds2_get = run_json(['get-data-source', '--data-source-id', ds2_id], 'get-data-source-2')
        rec('get-data-source(secondary)', 'PASS', 'secondary data source retrieved')

        ds2_upd = run_json(['update-data-source', '--data-source-id', ds2_id, '--title', f'Secondary DS Updated {STAMP}'], 'update-data-source')
        rec('update-data-source', 'PASS', 'secondary data source updated')

        ds2_query = run_json(['query-data-source', '--data-source-id', ds2_id], 'query-data-source-2')
        rec('query-data-source(secondary)', 'PASS', f"results={len(ds2_query.get('results', []))}")

        templates = run_json(['list-data-source-templates', '--data-source-id', ds2_id, '--page-size', '10'], 'list-data-source-templates')
        rec('list-data-source-templates', 'PASS', f"templates={len(templates.get('templates', []))}")

        ds2_trash = run_json(['update-data-source', '--data-source-id', ds2_id, '--trash'], 'update-data-source-trash')
        rec('update-data-source(--trash)', 'PASS', 'secondary data source trashed')
        ds2_restore = run_json(['update-data-source', '--data-source-id', ds2_id, '--restore'], 'update-data-source-restore')
        rec('update-data-source(--restore)', 'PASS', 'secondary data source restored')

        db_upd = run_json(['update-database', '--database-id', db_id, '--title', f'Full Surface DB Updated {STAMP}', '--description', f'DB desc {STAMP}'], 'update-database')
        rec('update-database', 'PASS', 'database updated')

        # Leaf page for update-page trash/restore variant.
        leaf_props = write_json('leaf-page-props.json', {
            'title': {'title': [{'type': 'text', 'text': {'content': f'Leaf Page {STAMP}'}}]}
        })
        leaf_page = run_json(['create-page', '--parent-page-id', root_page_id, '--properties-file', str(leaf_props)], 'create-leaf-page')
        update_target_page_id = leaf_page['id']
        run_json(['update-page', '--page-id', update_target_page_id, '--trash'], 'update-page-trash')
        rec('update-page(--trash)', 'PASS', 'leaf page trashed')
        run_json(['update-page', '--page-id', update_target_page_id, '--restore'], 'update-page-restore')
        rec('update-page(--restore)', 'PASS', 'leaf page restored')

        sibling_props = write_json('sibling-props-late.json', {
            'title': {'title': [{'type': 'text', 'text': {'content': f'Sibling Holder {STAMP}'}}]}
        })
        sibling = run_json(['create-page', '--parent-page-id', root_page_id, '--properties-file', str(sibling_props)], 'create-sibling-page-late')
        sibling_page_id = sibling['id']
        rec('create-page(parent_page.sibling)', 'PASS', 'sibling page created')

        movable_props = write_json('movable-page-props.json', {
            'title': {'title': [{'type': 'text', 'text': {'content': f'Movable Page {STAMP}'}}]}
        })
        movable = run_json(['create-page', '--parent-page-id', root_page_id, '--properties-file', str(movable_props)], 'create-movable-page')
        movable_page_id = movable['id']
        moved = run_json(['move-page', '--page-id', movable_page_id, '--parent-page-id', sibling_page_id], 'move-page')
        rec('move-page', 'PASS', 'page moved')
        run_json(['trash-page', '--page-id', movable_page_id], 'trash-page')
        rec('trash-page', 'PASS', 'page trashed')
        run_json(['restore-page', '--page-id', movable_page_id], 'restore-page')
        rec('restore-page', 'PASS', 'page restored')

        # Views on primary database/data source.
        title_prop_id_unquoted = title_prop_id.replace('%', '%25') if '%' in title_prop_id else title_prop_id
        view_body = {
            'database_id': db_id,
            'data_source_id': ds_id,
            'name': f'Full Surface View {STAMP}',
            'type': 'table',
            'configuration': {
                'type': 'table',
                'properties': [
                    {
                        'property_id': title_prop_id,
                        'property_name': 'Name',
                        'visible': True,
                        'width': 220,
                    }
                ]
            }
        }
        view_body_file = write_json('create-view.json', view_body)
        view = run_json(['create-view', '--body-file', str(view_body_file)], 'create-view')
        view_id = view['id']
        rec('create-view', 'PASS', 'view created')

        list_views_db = run_json(['list-views', '--database-id', db_id, '--page-size', '20'], 'list-views-db')
        rec('list-views(database)', 'PASS', f"results={len(list_views_db.get('results', []))}")

        list_views_ds = run_json(['list-views', '--data-source-id', ds_id, '--page-size', '20'], 'list-views-ds')
        rec('list-views(data_source)', 'PASS', f"results={len(list_views_ds.get('results', []))}")

        view_get = run_json(['get-view', '--view-id', view_id], 'get-view')
        rec('get-view', 'PASS', 'view retrieved')

        view_query = run_json(['create-view-query', '--view-id', view_id, '--page-size', '1'], 'create-view-query')
        view_query_id = view_query['id']
        rec('create-view-query', 'PASS', 'view query created')

        view_results = run_json(['get-view-query-results', '--view-id', view_id, '--query-id', view_query_id, '--page-size', '1'], 'get-view-query-results')
        rec('get-view-query-results', 'PASS', f"results={len(view_results.get('results', []))}")

        del_q = run_json(['delete-view-query', '--view-id', view_id, '--query-id', view_query_id], 'delete-view-query')
        rec('delete-view-query', 'PASS', del_q.get('deleted', True))
        view_query_id = None

        view_upd_body = write_json('update-view.json', {'name': f'Full Surface View Updated {STAMP}'})
        view_upd = run_json(['update-view', '--view-id', view_id, '--body-file', str(view_upd_body)], 'update-view')
        rec('update-view', 'PASS', 'view updated')

        view_del = run_json(['delete-view', '--view-id', view_id], 'delete-view')
        rec('delete-view', 'PASS', view_del.get('deleted', True))
        view_id = None

        moved_db = run_json(['move-database', '--database-id', db_id, '--parent-page-id', sibling_page_id], 'move-database')
        rec('move-database', 'PASS', 'database moved')

        trash_db = run_json(['trash-database', '--database-id', db_id], 'trash-database')
        rec('trash-database', 'PASS', 'database trashed')

        restore_db = run_json(['restore-database', '--database-id', db_id], 'restore-database')
        rec('restore-database', 'PASS', 'database restored')

        # File uploads (single-part + multi-part)
        single_file = TMP / 'single.txt'
        single_file.write_text(f'single part upload {STAMP}', encoding='utf-8')
        single_create = run_json(['create-file-upload', '--mode', 'single_part', '--filename', f'single-{STAMP}.txt', '--content-type', 'text/plain'], 'create-file-upload-single')
        single_upload_id = single_create['id']
        rec('create-file-upload(single_part)', 'PASS', 'single-part upload created')
        single_send = run_json(['send-file-upload', '--file-upload-id', single_upload_id, '--file-path', str(single_file), '--content-type', 'text/plain'], 'send-file-upload-single')
        rec('send-file-upload(single_part)', 'PASS', 'single-part upload sent')
        single_get = run_json(['get-file-upload', '--file-upload-id', single_upload_id], 'get-file-upload-single')
        rec('get-file-upload(single_part)', 'PASS', 'single-part upload retrieved')

        multi_1 = TMP / 'multi-1.txt'
        multi_2 = TMP / 'multi-2.txt'
        multi_1.write_bytes((b'A' * (5 * 1024 * 1024)))
        multi_2.write_text(f'multi part tail {STAMP}', encoding='utf-8')
        multi_create = run_json(['create-file-upload', '--mode', 'multi_part', '--filename', f'multi-{STAMP}.txt', '--content-type', 'text/plain', '--number-of-parts', '2'], 'create-file-upload-multi')
        multi_upload_id = multi_create['id']
        rec('create-file-upload(multi_part)', 'PASS', 'multi-part upload created')
        run_json(['send-file-upload', '--file-upload-id', multi_upload_id, '--file-path', str(multi_1), '--content-type', 'text/plain', '--part-number', '1'], 'send-file-upload-multi-1')
        rec('send-file-upload(multi_part.part1)', 'PASS', 'multi-part upload part1 sent')
        run_json(['send-file-upload', '--file-upload-id', multi_upload_id, '--file-path', str(multi_2), '--content-type', 'text/plain', '--part-number', '2'], 'send-file-upload-multi-2')
        rec('send-file-upload(multi_part.part2)', 'PASS', 'multi-part upload part2 sent')
        comp = run_json(['complete-file-upload', '--file-upload-id', multi_upload_id], 'complete-file-upload')
        rec('complete-file-upload', 'PASS', 'multi-part upload completed')
        multi_get = run_json(['get-file-upload', '--file-upload-id', multi_upload_id], 'get-file-upload-multi')
        rec('get-file-upload(multi_part)', 'PASS', 'multi-part upload retrieved')

        uploads = run_json(['list-file-uploads', '--page-size', '20'], 'list-file-uploads')
        upload_ids = [u.get('id') for u in uploads.get('results', uploads.get('file_uploads', []))]
        if single_upload_id not in upload_ids and multi_upload_id not in upload_ids:
            notes.append('list-file-uploads did not include newly created upload ids in first page; command still returned successfully.')
        rec('list-file-uploads', 'PASS', 'file uploads listed')

        # Retained OAuth helpers: intentionally local blocked checks only.
        expect_local_block('introspect-token', ['introspect-token'], 'Notion OAuth client id not found')
        expect_local_block('create-token', ['create-token', '--grant-type', 'authorization_code', '--code', 'dummy'], 'Notion OAuth client id not found')
        expect_local_block('revoke-token', ['revoke-token', '--token', 'dummy'], 'Notion OAuth client id not found')

        # Optional edge note: default template path may validly fail when no default template is configured.
        template_page_props = write_json('template-page-props.json', {
            'AltName': {'title': [{'type': 'text', 'text': {'content': f'Template Candidate {STAMP}'}}]}
        })
        cp = run(['create-page', '--parent-data-source-id', ds2_id, '--template-type', 'default', '--properties-file', str(template_page_props)], expect_ok=False)
        merged = (cp.stdout or '') + '\n' + (cp.stderr or '')
        if cp.returncode != 0 and 'No default template is configured for this data source' in merged:
            rec('create-page(template_type=default)', 'BLOCKED', 'No default template configured on fresh temp data source')
        elif cp.returncode == 0:
            rec('create-page(template_type=default)', 'PASS', 'default template existed on temp data source')
        else:
            raise RuntimeError(f'Unexpected template-default result\nSTDOUT:{cp.stdout}\nSTDERR:{cp.stderr}')

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
        print('OK_NOTION_FULL_SURFACE=1')
    finally:
        cleanup()


if __name__ == '__main__':
    main()
