#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Claude API smoke test for AiDiy Hermes.

This script intentionally does not print API keys. It loads
backend_server/_config/AiDiy_key.json, checks the auth style, then performs:

1. Anthropic models.list()
2. Anthropic messages.create() with a tiny prompt
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

PROJECT_ROOT = Path(__file__).resolve().parents[1]
HERMES_ROOT = Path(__file__).resolve().parent
BASE_DIR = HERMES_ROOT / "base"

for module_dir in (BASE_DIR, HERMES_ROOT):
    module_dir_text = str(module_dir)
    if module_dir_text not in sys.path:
        sys.path.insert(0, module_dir_text)

if "agent" not in sys.modules:
    import core as _agent_package

    sys.modules["agent"] = _agent_package

from agent.anthropic_adapter import (  # noqa: E402
    _api_key_betas_for_base_url,
    _common_betas_for_base_url,
    _is_oauth_token,
    build_anthropic_client,
)


def _load_aidiy_key(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"AiDiy key file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _mask_key(api_key: str) -> str:
    if not api_key:
        return "(empty)"
    if len(api_key) <= 12:
        return f"{api_key[:4]}...({len(api_key)} chars)"
    return f"{api_key[:8]}...{api_key[-4:]} ({len(api_key)} chars)"


def _auth_style(api_key: str) -> str:
    if not api_key:
        return "missing"
    if api_key.startswith("<"):
        return "placeholder"
    if _is_oauth_token(api_key):
        return "oauth/bearer"
    return "api_key/x-api-key"


def _default_headers(client: Any) -> dict[str, str]:
    headers = (
        getattr(client, "default_headers", None)
        or getattr(client, "_default_headers", None)
        or {}
    )
    return {str(k): str(v) for k, v in dict(headers).items()}


def main() -> int:
    parser = argparse.ArgumentParser(description="Claude API smoke test")
    parser.add_argument(
        "--key-file",
        default=str(PROJECT_ROOT / "backend_server" / "_config" / "AiDiy_key.json"),
        help="Path to AiDiy_key.json",
    )
    parser.add_argument("--model", default="claude-sonnet-4-6")
    parser.add_argument("--message", default="おはよう。短く返事してください。")
    parser.add_argument("--base-url", default="https://api.anthropic.com")
    parser.add_argument("--max-tokens", type=int, default=32)
    args = parser.parse_args()

    key_file = Path(args.key_file)
    config = _load_aidiy_key(key_file)
    api_key = str(config.get("claude_key_id", "") or "").strip()
    auth_style = _auth_style(api_key)

    print(f"key_file: {key_file}")
    print(f"claude_key_id: {_mask_key(api_key)}")
    print(f"auth_style: {auth_style}")
    print(f"base_url: {args.base_url}")
    print(f"model: {args.model}")

    if auth_style in {"missing", "placeholder"}:
        print("NG: claude_key_id is not configured.")
        return 2

    if auth_style == "oauth/bearer":
        betas = _common_betas_for_base_url(args.base_url)
    else:
        betas = _api_key_betas_for_base_url(args.base_url)
    print(f"expected_anthropic_beta: {','.join(betas) if betas else '(none)'}")

    client = build_anthropic_client(api_key, args.base_url)
    headers = _default_headers(client)
    beta_header = headers.get("anthropic-beta") or headers.get("x-anthropic-beta") or "(none)"
    print(f"client_anthropic_beta: {beta_header}")

    print("\n[1/2] models.list()")
    try:
        models = client.models.list()
        model_ids = [m.id for m in getattr(models, "data", []) if getattr(m, "id", None)]
        print(f"OK: {len(model_ids)} models")
        for model_id in model_ids[:10]:
            print(f"  - {model_id}")
    except Exception as exc:
        print(f"NG: models.list failed: {type(exc).__name__}: {exc}")
        return 1

    print("\n[2/2] messages.create()")
    try:
        response = client.messages.create(
            model=args.model,
            max_tokens=args.max_tokens,
            messages=[{"role": "user", "content": args.message}],
        )
        text = "".join(
            getattr(block, "text", "")
            for block in getattr(response, "content", [])
            if getattr(block, "type", "") == "text"
        ).strip()
        print(f"OK: response_id={getattr(response, 'id', '(unknown)')}")
        print(f"assistant: {text}")
        return 0
    except Exception as exc:
        print(f"NG: messages.create failed: {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
