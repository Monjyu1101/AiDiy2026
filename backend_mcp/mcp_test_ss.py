# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""
aidiy_desktop_capture MCP テスト

backend_mcp (port 8095) が起動済みの状態で実行すること。
SSE エンドポイント: http://localhost:8095/aidiy_desktop_capture/sse

実行:
    cd backend_mcp
    .venv/Scripts/python.exe mcp_test_ss.py
"""

import asyncio
import base64
import json
import os
import sys
from pathlib import Path

# UTF-8 出力強制（Windows cp932 文字化け対策）
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

os.environ["NO_PROXY"] = "localhost,127.0.0.1"
os.environ["no_proxy"] = "localhost,127.0.0.1"

from mcp.client.sse import sse_client
from mcp.client.session import ClientSession

SSE_URL    = "http://localhost:8095/aidiy_desktop_capture/sse"
SAVE_DIR   = Path(__file__).parent / "temp"


# ------------------------------------------------------------------ #
# ヘルパー
# ------------------------------------------------------------------ #

async def call_text(session: ClientSession, tool: str, **kwargs) -> str:
    """ツールを呼び出してテキスト結果を返す。"""
    result = await session.call_tool(tool, arguments=kwargs)
    if result.isError:
        msgs = [c.text for c in result.content if hasattr(c, "text")]
        raise RuntimeError(f"[{tool}] エラー: {' '.join(msgs)}")
    return "\n".join(c.text for c in result.content if hasattr(c, "text"))


async def save_image(session: ClientSession, tool: str, filename: str, **kwargs) -> bool:
    """ツールを呼び出して画像を保存する。成功時 True。"""
    result = await session.call_tool(tool, arguments=kwargs)
    if result.isError:
        msgs = [c.text for c in result.content if hasattr(c, "text")]
        print(f"  [ERROR] {' '.join(msgs)}")
        return False
    for c in result.content:
        if getattr(c, "type", None) == "image" and hasattr(c, "data"):
            SAVE_DIR.mkdir(parents=True, exist_ok=True)
            path = SAVE_DIR / filename
            path.write_bytes(base64.b64decode(c.data))
            print(f"  -> 保存: {path}")
            return True
    print("  -> 画像コンテンツなし")
    return False


# ------------------------------------------------------------------ #
# テスト本体
# ------------------------------------------------------------------ #

async def main() -> None:
    print("=== aidiy_desktop_capture MCP テスト ===")
    print(f"  SSE URL: {SSE_URL}\n")

    async with sse_client(SSE_URL, timeout=10, sse_read_timeout=30) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # ツール一覧
            tools = await session.list_tools()
            print(f"=== ツール一覧 ({len(tools.tools)} 件) ===")
            for t in tools.tools:
                print(f"  [{t.name}] {t.description or ''}")
            print()

            # -------------------------------------------------- #
            # [1] カーソル位置
            # -------------------------------------------------- #
            print("=== [1] カーソル座標取得 ===")
            r = await call_text(session, "get_cursor_pos")
            pos = json.loads(r)
            print(f"  cursor: x={pos['x']}, y={pos['y']}")

            # -------------------------------------------------- #
            # [2] モニター情報
            # -------------------------------------------------- #
            print("\n=== [2] モニター情報取得 ===")
            r = await call_text(session, "get_screen_info")
            mons = json.loads(r)
            for m in mons:
                primary = " [primary]" if m.get("primary") else ""
                print(f"  [{m['index']}] {m['width']}x{m['height']}  ({m['x']},{m['y']}){primary}")

            # -------------------------------------------------- #
            # [3] ウィンドウ一覧 (Windows のみ)
            # -------------------------------------------------- #
            print("\n=== [3] ウィンドウ一覧 ===")
            try:
                r = await call_text(session, "list_windows")
                wins = json.loads(r)
                for w in wins[:10]:
                    title = w.get("title", "")[:50]
                    print(f"  [{w['hwnd']}] {title}  ({w['width']}x{w['height']})")
                if len(wins) > 10:
                    print(f"  ... 他 {len(wins) - 10} 件")
            except Exception as e:
                print(f"  (スキップ: {e})")

            # -------------------------------------------------- #
            # [4] スクリーンショット — auto (カーソルのあるモニター)
            # -------------------------------------------------- #
            print("\n=== [4] screenshot  screen_number='auto' ===")
            await save_image(session, "screenshot", "ss_auto.png",
                             screen_number="auto")

            # -------------------------------------------------- #
            # [5] スクリーンショット — all (全モニター結合)
            # -------------------------------------------------- #
            print("\n=== [5] screenshot  screen_number='all' ===")
            await save_image(session, "screenshot", "ss_all.png",
                             screen_number="all")

            # -------------------------------------------------- #
            # [6] カーソル中心 600px 切り出し + 十字線 + ラベル
            # -------------------------------------------------- #
            print("\n=== [6] screenshot  size=600  crosshair=True  label=True ===")
            await save_image(session, "screenshot", "ss_cursor600.png",
                             size=600, crosshair=True, label=True)

            # -------------------------------------------------- #
            # [7] JPEG 品質 70 で保存
            # -------------------------------------------------- #
            print("\n=== [7] screenshot  format='jpeg'  quality=70 ===")
            await save_image(session, "screenshot", "ss_jpeg70.jpg",
                             format="jpeg", quality=70)

            # -------------------------------------------------- #
            # [8] 1秒遅延後にスクリーンショット
            # -------------------------------------------------- #
            print("\n=== [8] screenshot  delay=1.0  label=True ===")
            await save_image(session, "screenshot", "ss_delay1.png",
                             delay=1.0, label=True)

    print("\n=== テスト完了 ===")
    print(f"  保存先: {SAVE_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
