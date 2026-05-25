# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""
backend_mcp MCP/SSE スモークテスト

前提:
  backend_mcp (port 8095) が起動済みであること。

方針:
  14 MCP の SSE 接続、list_tools、代表的な副作用の少ない tool call を確認する。
  外部 AI 生成、AI agent 実行、書き込み系 backup run は行わない。

実行:
    cd backend_mcp
    .venv/Scripts/python.exe tests/test_mcp_smoke.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

os.environ["NO_PROXY"] = "localhost,127.0.0.1"
os.environ["no_proxy"] = "localhost,127.0.0.1"

from mcp.client.sse import sse_client
from mcp.client.session import ClientSession


BASE_URL = os.environ.get("AIDIY_MCP_BASE_URL", "http://localhost:8095").rstrip("/")


SERVERS = [
    {
        "name": "aidiy_chrome_devtools",
        "expected": {"get_version", "list_tabs", "navigate", "screenshot"},
        "call": ("get_version", {}),
    },
    {
        "name": "aidiy_desktop_capture",
        "expected": {"get_cursor_pos", "get_screen_info", "screenshot"},
        "call": ("get_cursor_pos", {}),
    },
    {
        "name": "aidiy_sqlite",
        "expected": {"sqlite_list_tables", "sqlite_query"},
        "call": ("sqlite_query", {"sql": "SELECT 1 AS ok"}),
    },
    {
        "name": "aidiy_postgres",
        "expected": {"postgres_server_info", "postgres_query"},
        "call": ("postgres_server_info", {}),
        "allow_error": True,
    },
    {
        "name": "aidiy_logs",
        "expected": {"logs_list", "logs_tail", "logs_recent_errors"},
        "call": ("logs_list", {}),
    },
    {
        "name": "aidiy_code_check",
        "expected": {"check_list_targets", "check_python_syntax"},
        "call": ("check_python_syntax", {"file_path": "backend_mcp/mcp_main.py", "venv_project": "backend_mcp"}),
    },
    {
        "name": "aidiy_backup",
        "expected": {"backup_info", "backup_diff_scan", "backup_list_versions"},
        "call": ("backup_info", {}),
    },
    {
        "name": "aidiy_image_generation",
        "expected": {"generate_image"},
    },
    {
        "name": "aidiy_movie_generation",
        "expected": {"generate_movie"},
    },
    {
        "name": "aidiy_speech_to_text",
        "expected": {"recognize_speech"},
    },
    {
        "name": "aidiy_text_to_speech",
        "expected": {"synthesize_speech"},
        "call": (
            "synthesize_speech",
            {
                "speech_text": "MCP SSE のテストです。",
                "provider": "edge",
                "voice": "female",
                "ratio": 1,
            },
        ),
    },
    {
        "name": "aidiy_obs_studio_control",
        "expected": {"obs_startup_status", "obs_connection_info", "obs_status"},
        "call": ("obs_startup_status", {}),
    },
    {
        "name": "aidiy_ffmpeg_control",
        "expected": {"ffmpeg_versions"},
        "call": ("ffmpeg_versions", {}),
    },
    {
        "name": "aidiy_code_agents",
        "expected": {"code_agents_config"},
        "call": ("code_agents_config", {}),
    },
]


def _content_text(result) -> str:
    return "\n".join(c.text for c in result.content if hasattr(c, "text"))


async def _check_server(spec: dict) -> None:
    url = f"{BASE_URL}/{spec['name']}/sse"
    async with sse_client(url, timeout=10, sse_read_timeout=60) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            tool_names = {t.name for t in tools.tools}
            missing = spec["expected"] - tool_names
            if missing:
                raise AssertionError(f"{spec['name']}: tools missing {sorted(missing)}")

            call_spec = spec.get("call")
            if call_spec:
                tool_name, arguments = call_spec
                result = await session.call_tool(tool_name, arguments=arguments)
                if result.isError and not spec.get("allow_error"):
                    raise AssertionError(f"{spec['name']}:{tool_name}: {_content_text(result)}")
                if not result.content:
                    raise AssertionError(f"{spec['name']}:{tool_name}: content が空です")
                text = _content_text(result)
                if text:
                    try:
                        json.loads(text)
                    except json.JSONDecodeError:
                        if not text.strip():
                            raise
            print(f"  OK {spec['name']} ({len(tool_names)} tools)")


async def main() -> None:
    print("=== backend_mcp MCP/SSE スモークテスト ===")
    print(f"BASE_URL: {BASE_URL}")
    for spec in SERVERS:
        await _check_server(spec)
    print("\nOK")


if __name__ == "__main__":
    asyncio.run(main())
