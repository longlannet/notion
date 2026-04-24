#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

import requests
from output_guard import emit_output_text

API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2026-03-11"
TIMEOUT = 20


def load_api_key():
    env_key = os.environ.get("NOTION_API_KEY", "").strip()
    file_path = Path.home() / ".config" / "notion" / "api_key"
    file_key = file_path.read_text(encoding="utf-8").strip() if file_path.exists() else ""
    key = env_key or file_key
    return {
        "has_env_key": bool(env_key),
        "has_file_key": bool(file_key),
        "key": key,
    }


def main():
    if '--redact' in sys.argv[1:]:
        os.environ['NOTION_REDACT_OUTPUT'] = '1'

    auth = load_api_key()
    out = {
        "ok": False,
        "api_version": NOTION_VERSION,
        "has_env_key": auth["has_env_key"],
        "has_file_key": auth["has_file_key"],
    }
    if not auth["key"]:
        out["error"] = "missing_api_key"
        emit_output_text(json.dumps(out, ensure_ascii=False, indent=2))
        raise SystemExit(1)

    key = auth["key"]
    out["key_prefix"] = key[:12]
    out["key_length"] = len(key)

    try:
        resp = requests.post(
            f"{API_BASE}/search",
            headers={
                "Authorization": f"Bearer {key}",
                "Notion-Version": NOTION_VERSION,
                "Content-Type": "application/json",
            },
            json={"query": ""},
            timeout=TIMEOUT,
        )
        out["http_status"] = resp.status_code
        try:
            data = resp.json()
        except Exception:
            data = {"text": resp.text}
        out["response_preview"] = data
        out["ok"] = resp.ok
    except Exception as e:
        out["error"] = repr(e)
        emit_output_text(json.dumps(out, ensure_ascii=False, indent=2))
        raise SystemExit(1)

    emit_output_text(json.dumps(out, ensure_ascii=False, indent=2))
    if not out["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
