# Copyright (c) 2026 monjyu1101@gmail.com
"""
Chrome DevTools MCP サーバー (共有ブラウザモード)

複数クライアントが同じ Chrome を共有する:
  - subprocess は 1 つだけ起動し全接続で共有
  - subprocess の stdout は全クライアントにブロードキャスト
  - どのクライアントからの POST も同じ subprocess stdin へ

    Client A ─┐  POST → stdin ─┐
    Client B ─┤                 ├─ [chrome-devtools-mcp] ─ Chrome
    Client C ─┘  stdout ────────┴→ 全員に配信

起動:
    uv run uvicorn mcp_main:app --host 0.0.0.0 --port 8095

SSE エンドポイント:
    http://localhost:8095/aidiy_chrome_devtools/sse

Claude Code への登録 (~/.claude/settings.json):
    {
      "mcpServers": {
        "aidiy_chrome_devtools": {
          "type": "sse",
          "url": "http://localhost:8095/aidiy_chrome_devtools/sse"
        }
      }
    }
"""

import asyncio
import os
import uuid
from pathlib import Path
from typing import Set

import uvicorn
from starlette.applications import Starlette
from starlette.responses import Response, StreamingResponse
from starlette.routing import Mount, Route

from log_config import setup_logging, get_logger
from mcp_proc.chrome_manager import ChromeManager

setup_logging()
logger = get_logger(__name__)

# ------------------------------------------------------------------ #
# 設定
# ------------------------------------------------------------------ #

CHROME_PORT = int(os.environ.get("CHROME_DEBUG_PORT", "9222"))
MCP_PORT    = int(os.environ.get("MCP_PORT", "8095"))
MOUNT       = os.environ.get("MCP_MOUNT_PATH", "/aidiy_chrome_devtools")

NODE_BIN = str(
    Path(__file__).parent / "node_modules/chrome-devtools-mcp/build/src/index.js"
)

chrome = ChromeManager(debug_port=CHROME_PORT)

# ------------------------------------------------------------------ #
# 共有 subprocess 管理
# ------------------------------------------------------------------ #

_proc:   asyncio.subprocess.Process | None = None
_queues: Set[asyncio.Queue]                = set()   # 接続中の SSE クライアント
_lock    = asyncio.Lock()                             # 同時起動防止


async def _start_subprocess() -> asyncio.subprocess.Process:
    """subprocess を起動してブロードキャストタスクを開始する"""
    global _proc
    await asyncio.to_thread(chrome.ensure_running)
    _proc = await asyncio.create_subprocess_exec(
        "node", NODE_BIN,
        "--browserUrl", f"http://localhost:{CHROME_PORT}",
        "--usageStatistics=false",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    logger.info(f"subprocess 起動 (PID={_proc.pid})")
    asyncio.create_task(_broadcast(_proc))
    return _proc


async def _get_proc() -> asyncio.subprocess.Process:
    """起動していなければ起動して返す (ロックで同時起動を防ぐ)"""
    async with _lock:
        if _proc is None or _proc.returncode is not None:
            return await _start_subprocess()
    return _proc


async def _broadcast(proc: asyncio.subprocess.Process):
    """subprocess stdout を接続中の全クライアントへ配信する"""
    async for raw in proc.stdout:
        text = raw.decode().strip()
        if not text:
            continue
        dead = set()
        for q in _queues:
            try:
                q.put_nowait(text)
            except asyncio.QueueFull:
                dead.add(q)
        _queues.difference_update(dead)

    # subprocess 終了 → 全クライアントに終了を通知
    logger.info(f"subprocess 終了 (接続数={len(_queues)})")
    for q in list(_queues):
        q.put_nowait(None)

# ------------------------------------------------------------------ #
# ローカル接続チェック
# ------------------------------------------------------------------ #

_ALLOWED_HOSTS = {"127.0.0.1", "::1", "localhost"}

def _is_local(request) -> bool:
    host = request.client.host if request.client else ""
    return host in _ALLOWED_HOSTS

# ------------------------------------------------------------------ #
# SSE エンドポイント
# ------------------------------------------------------------------ #

async def handle_sse(request):
    if not _is_local(request):
        logger.warning(f"SSE 接続拒否: {request.client.host}")
        return Response("Forbidden", status_code=403)
    await _get_proc()                   # 未起動なら起動
    sid = str(uuid.uuid4())
    q   = asyncio.Queue(maxsize=200)
    _queues.add(q)
    logger.info(f"接続 sid={sid[:8]} (計{len(_queues)}接続)")

    async def stream():
        try:
            message_endpoint = f"{MOUNT.rstrip('/')}/messages?sessionId={sid}"
            yield f"id: {sid}\nevent: endpoint\ndata: {message_endpoint}\n\n"
            while True:
                msg = await q.get()
                if msg is None:         # subprocess 終了シグナル
                    break
                yield f"event: message\ndata: {msg}\n\n"
        finally:
            _queues.discard(q)
            logger.info(f"切断 sid={sid[:8]} (計{len(_queues)}接続)")

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
    )

# ------------------------------------------------------------------ #
# POST エンドポイント (sessionId は無視して共有 stdin へ)
# ------------------------------------------------------------------ #

async def handle_post(request):
    if not _is_local(request):
        logger.warning(f"POST 接続拒否: {request.client.host}")
        return Response("Forbidden", status_code=403)
    proc = await _get_proc()
    proc.stdin.write(await request.body() + b"\n")
    await proc.stdin.drain()
    return Response(status_code=202)

# ------------------------------------------------------------------ #
# アプリ
# ------------------------------------------------------------------ #

app = Starlette(routes=[
    Mount(MOUNT, app=Starlette(routes=[
        Route("/sse",       handle_sse,  methods=["GET"]),
        Route("/messages",  handle_post, methods=["POST"]),
        Route("/messages/", handle_post, methods=["POST"]),
    ]))
])

if __name__ == "__main__":
    logger.info(f"SSE: http://localhost:{MCP_PORT}{MOUNT}/sse")
    uvicorn.run(app, host="0.0.0.0", port=MCP_PORT, log_level="warning")
