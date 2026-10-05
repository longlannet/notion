# Safe staging validation for the Notion toolbox

Use this procedure for a skills-only merge, not for service availability certification.

1. Compare scripts against the selected source by SHA-256, retaining license notices and platform-specific setup. Exclude actual keys, environment/config files, caches and generated data before comparing.
2. Parse every Python script with `ast.parse(path.read_text())`; do not import arbitrary helpers, as some run immediately at import time. Check shell scripts with `bash -n` only.
3. Read `notion_api.py` and `output_guard.py` before executing the CLI. The reviewed main CLI builds argparse before dispatch; `--help` exits before credentials/network access. This is not true of every wrapper: never blanket-run all scripts with `--help`.
4. In a separate process with bytecode disabled and an isolated HOME/environment, block network/socket and subprocess events and credential-file reads, then execute only the reviewed main CLI `--help`. Load that reviewed module under a non-main name to call `build_parser()` and parse arguments without invoking `args.func`.
5. Check all subcommand help paths, the `2026-03-11` constant, `--trash`/`--restore` and hidden aliases, mutual exclusion rejection, and distinct page/data-source/database parent arguments. Parsed arguments are not API responses or proof of remote compatibility.
6. Never run selfcheck, diagnostics, `validate_*`, Worker deployment, or a remote create/delete cycle during a merge. Those require explicit service/target authorization separately.
7. Read back the staged diff, verify the source script parity, preserved references/licenses and absence of real config files; verify live source hashes are unchanged. Report syntax/argument checks separately from unavailable live tests.

Deployment prerequisites remain separate: correct target skill category, Python/requests and Bash availability, the current platform environment's key, shared Notion targets, and a skill-catalog reload. Do not copy another platform's credentials or install global dependencies merely to validate docs.
