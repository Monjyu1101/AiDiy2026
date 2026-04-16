# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""
MCP ブラウザ自動操作テスト — Google ニュース検索

mcp_stdio.py をサブプロセスとして起動し、stdio MCP クライアントで
ツールを呼び出す。事前に backend_mcp (port 8095) が起動済みであること。

実行:
    cd backend_mcp
    .venv/Scripts/python.exe mcp_test.py
"""

import asyncio
import base64
import os
import sys
from pathlib import Path

# UTF-8出力を強制（Windows cp932 文字化け・エンコードエラー対策）
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# backend_mcp をパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

PYTHON     = str(Path(__file__).parent / ".venv" / "Scripts" / "python.exe")
STDIO_SCRIPT = str(Path(__file__).parent / "mcp_stdio.py")
SCREENSHOT_PATH = Path(__file__).parent / "temp" / "screenshot_news.png"


# ------------------------------------------------------------------ #
# ヘルパー
# ------------------------------------------------------------------ #

async def call(session: ClientSession, tool: str, **kwargs) -> str:
    """ツールを呼び出してテキスト結果を返す。エラー時は例外。"""
    result = await session.call_tool(tool, arguments=kwargs)
    if result.isError:
        msgs = [c.text for c in result.content if hasattr(c, "text")]
        raise RuntimeError(f"[{tool}] エラー: {' '.join(msgs)}")
    texts = []
    for c in result.content:
        if hasattr(c, "text"):
            texts.append(c.text)
    return "\n".join(texts)


async def save_screenshot(session: ClientSession, path: Path, **kwargs) -> None:
    """スクリーンショットを撮って PNG ファイルに保存する。"""
    result = await session.call_tool("screenshot", arguments=kwargs)
    for c in result.content:
        if getattr(c, "type", None) == "image" and hasattr(c, "data"):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(base64.b64decode(c.data))
            print(f"  -> 保存: {path}")
            return
    print("  -> スクリーンショット取得失敗")


# ------------------------------------------------------------------ #
# テストシナリオ
# ------------------------------------------------------------------ #

async def main() -> None:
    params = StdioServerParameters(
        command=PYTHON,
        args=[STDIO_SCRIPT],
        cwd=str(Path(__file__).parent),
    )

    print("=== mcp_stdio.py を起動してテスト開始 ===")
    print(f"  Python  : {PYTHON}")
    print(f"  Script  : {STDIO_SCRIPT}\n")

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # ツール一覧
            tools = await session.list_tools()
            print(f"=== ツール一覧 ({len(tools.tools)} 件) ===")
            for t in tools.tools:
                print(f"  [{t.name}] {t.description or ''}")
            print()

            # -------------------------------------------------- #
            # シナリオ: Yahoo! ニュース トップ確認 → キーワード検索
            # -------------------------------------------------- #

            print("=== [1] Yahoo! ニュース トップへ移動 ===")
            r = await call(session, "navigate", url="https://news.yahoo.co.jp/")
            print(f"  {r}")

            print("\n=== [2] ページロード待機 ===")
            r = await call(session, "wait_for_load", timeout=15.0)
            print(f"  {r}")
            await asyncio.sleep(1.5)

            print("\n=== [3] ページ情報取得 ===")
            r = await call(session, "get_page_info")
            import json as _json
            info = _json.loads(r)
            print(f"  URL  : {info.get('url', '')}")
            print(f"  Title: {info.get('title', '')}")

            print("\n=== [4] トップページのニュース見出しを取得 ===")
            r = await call(
                session, "eval_js",
                expression=(
                    "(function(){"
                    "  var items = Array.from(document.querySelectorAll("
                    "    'a[data-cl-params], .newsFeed_item_title a, .sc-gKclnd a, h1 a, h2 a, h3 a'"
                    "  ));"
                    "  var seen = {};"
                    "  var titles = [];"
                    "  items.forEach(function(a){"
                    "    var t = (a.innerText || a.textContent || '').trim();"
                    "    if(t.length > 10 && !seen[t]){ seen[t]=1; titles.push(t); }"
                    "  });"
                    "  return titles.slice(0, 10).join('\\n');"
                    "})()"
                ),
            )
            print(r if r else "  (見出し取得できず)")

            print("\n=== [5] スクリーンショット (トップ) ===")
            await save_screenshot(session, SCREENSHOT_PATH.with_name("screenshot_yahoo_top.png"))

            print("\n=== [6] 検索ボックスに「AI」と入力して検索 ===")
            r = await call(session, "navigate", url="https://news.yahoo.co.jp/search?p=AI&ei=UTF-8")
            print(f"  {r}")

            print("\n=== [7] 検索結果ロード待機 ===")
            r = await call(session, "wait_for_load", timeout=15.0)
            print(f"  {r}")
            await asyncio.sleep(1.5)

            print("\n=== [8] 検索結果の見出しを取得 ===")
            r = await call(
                session, "eval_js",
                expression=(
                    "(function(){"
                    "  var items = Array.from(document.querySelectorAll("
                    "    '.newsFeed_item_title a, [class*=\"title\"] a, h1 a, h2 a, h3 a'"
                    "  ));"
                    "  var seen = {};"
                    "  var titles = [];"
                    "  items.forEach(function(a){"
                    "    var t = (a.innerText || a.textContent || '').trim();"
                    "    if(t.length > 10 && !seen[t]){ seen[t]=1; titles.push(t); }"
                    "  });"
                    "  return titles.slice(0, 10).join('\\n');"
                    "})()"
                ),
            )
            print(r if r else "  (見出し取得できず)")

            print("\n=== [9] スクリーンショット (検索結果) ===")
            await save_screenshot(session, SCREENSHOT_PATH)

    print("\n=== テスト完了 ===")


if __name__ == "__main__":
    asyncio.run(main())
