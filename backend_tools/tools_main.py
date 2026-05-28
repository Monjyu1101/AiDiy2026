# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""
AiDiy MCP サーバー エントリポイント

SSE + HTTP POST インターフェースを 1 ポート (8095) で提供する。
MCP ツールの実装は tools_proc/tools_*.py に分割してある。
"""

import os
import sys
import threading
import time
from typing import Optional

# UTF-8出力を強制（Windows文字化け対策）
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi import Response
from fastapi.routing import APIRoute
from mcp.server.fastmcp import FastMCP

from log_config import setup_logging, get_logger
from tools_proc.chrome_manager import ChromeManager
from tools_proc.chrome_devtools import CDPClient
from tools_proc.desktop_capture import DesktopCapture
from tools_proc.sqlite_query import SqliteQuery
from tools_proc.postgres_query import PgQuery, PgQueryError
from tools_proc.log_tailer import LogTailer
from tools_proc.code_checker import CodeChecker
from tools_proc.backup import BackupCheck, BackupSave
from tools_proc.image_generation import ImageGeneration
from tools_proc.movie_generation import MovieGeneration
from tools_proc.speech_to_text import SpeechToText
from tools_proc.text_to_speech import TextToSpeech
from tools_proc.obs_studio_control import ObsStudioControl
from tools_proc.ffmpeg_control import FfmpegControl
from tools_proc.code_agents import CodeAgents

from tools_proc import tools_chrome, tools_desktop, tools_db, tools_dev
from tools_proc import tools_backup, tools_media, tools_obs, tools_ffmpeg, tools_agents

setup_logging()
logger = get_logger(__name__)

# ------------------------------------------------------------------ #
# 設定
# ------------------------------------------------------------------ #

CHROME_PORT = int(os.environ.get("CHROME_DEBUG_PORT", "9222"))
MCP_PORT    = int(os.environ.get("MCP_PORT", "8095"))
MOUNT       = os.environ.get("MCP_MOUNT_PATH", "/aidiy_chrome_devtools")
MOUNT_DC    = os.environ.get("MCP_DC_MOUNT_PATH", "/aidiy_desktop_capture")
MOUNT_SQ    = os.environ.get("MCP_SQ_MOUNT_PATH", "/aidiy_sqlite")
MOUNT_PG    = os.environ.get("MCP_PG_MOUNT_PATH", "/aidiy_postgres")
MOUNT_LG    = os.environ.get("MCP_LG_MOUNT_PATH", "/aidiy_logs")
MOUNT_CC    = os.environ.get("MCP_CC_MOUNT_PATH", "/aidiy_code_check")
MOUNT_BK    = os.environ.get("MCP_BK_MOUNT_PATH", "/aidiy_backup")
MOUNT_IG    = os.environ.get("MCP_IG_MOUNT_PATH", "/aidiy_image_generation")
MOUNT_MG    = os.environ.get("MCP_MG_MOUNT_PATH", "/aidiy_movie_generation")
MOUNT_ST    = os.environ.get("MCP_ST_MOUNT_PATH", "/aidiy_speech_to_text")
MOUNT_TS    = os.environ.get("MCP_TS_MOUNT_PATH", "/aidiy_text_to_speech")
MOUNT_OB    = os.environ.get("MCP_OB_MOUNT_PATH", "/aidiy_obs_studio_control")
MOUNT_FF    = os.environ.get("MCP_FF_MOUNT_PATH", "/aidiy_ffmpeg_control")
MOUNT_CA    = os.environ.get("MCP_CA_MOUNT_PATH", "/aidiy_code_agents")

# ------------------------------------------------------------------ #
# サービスインスタンス生成
# ------------------------------------------------------------------ #

chrome      = ChromeManager(debug_port=CHROME_PORT)
cdp         = CDPClient(port=CHROME_PORT)
capture     = DesktopCapture()
sqlite_q    = SqliteQuery()
log_t       = LogTailer()
checker     = CodeChecker()
bchk        = BackupCheck()
bsave       = BackupSave()
ig          = ImageGeneration()
mg          = MovieGeneration()
stt         = SpeechToText()
tts         = TextToSpeech()
obs         = ObsStudioControl()
ffmpeg_c    = FfmpegControl()
code_agents = CodeAgents()
code_agents.version_info = code_agents._check_ai_versions()

# PostgreSQL は psycopg 未導入環境でもサーバー起動を阻害しないよう遅延初期化
_pg_q: Optional[PgQuery] = None
_pg_init_error: Optional[str] = None
try:
    _pg_q = PgQuery()
except PgQueryError as _e:
    _pg_init_error = str(_e)


def _get_pg() -> PgQuery:
    if _pg_q is None:
        raise ValueError(
            f"aidiy_postgres は初期化されていません: {_pg_init_error or '未知の理由'}"
        )
    return _pg_q

# ------------------------------------------------------------------ #
# 再起動フラグ監視
# ------------------------------------------------------------------ #

def _setup_reboot_watcher():
    temp_dir = os.path.join(os.path.dirname(__file__), "temp")
    os.makedirs(temp_dir, exist_ok=True)
    reboot_path = os.path.join(temp_dir, "reboot_mcp.txt")
    if os.path.isfile(reboot_path):
        try:
            os.remove(reboot_path)
        except Exception:
            pass
        raise SystemExit("reboot_mcp.txt detected")
    def watcher():
        while True:
            try:
                if os.path.isfile(reboot_path):
                    try:
                        os.remove(reboot_path)
                    except Exception:
                        pass
                    os._exit(0)
            except Exception:
                pass
            time.sleep(1)
    threading.Thread(target=watcher, daemon=True).start()

_setup_reboot_watcher()

# ------------------------------------------------------------------ #
# FastMCP インスタンス生成
# ------------------------------------------------------------------ #

def _make_mcp(name: str) -> FastMCP:
    return FastMCP(
        name,
        host="0.0.0.0",
        port=MCP_PORT,
        mount_path="/",
        sse_path="/sse",
        message_path="/messages/",
        warn_on_duplicate_tools=False,
    )

mcp    = _make_mcp("aidiy_chrome_devtools")
mcp_dc = _make_mcp("aidiy_desktop_capture")
mcp_sq = _make_mcp("aidiy_sqlite")
mcp_pg = _make_mcp("aidiy_postgres")
mcp_lg = _make_mcp("aidiy_logs")
mcp_cc = _make_mcp("aidiy_code_check")
mcp_bk = _make_mcp("aidiy_backup")
mcp_ig = _make_mcp("aidiy_image_generation")
mcp_mg = _make_mcp("aidiy_movie_generation")
mcp_st = _make_mcp("aidiy_speech_to_text")
mcp_ts = _make_mcp("aidiy_text_to_speech")
mcp_ob = _make_mcp("aidiy_obs_studio_control")
mcp_ff = _make_mcp("aidiy_ffmpeg_control")
mcp_ca = _make_mcp("aidiy_code_agents")

# ------------------------------------------------------------------ #
# MCP ツール登録
# ------------------------------------------------------------------ #

_ensure_chrome = tools_chrome.register_tools(mcp, chrome, cdp)
tools_desktop.register_tools(mcp_dc, capture)
tools_db.register_sqlite_tools(mcp_sq, sqlite_q)
tools_db.register_postgres_tools(mcp_pg, _get_pg)
tools_dev.register_logs_tools(mcp_lg, log_t)
tools_dev.register_code_check_tools(mcp_cc, checker)
tools_backup.register_tools(mcp_bk, bsave, bchk)
tools_media.register_image_gen_tools(mcp_ig, ig)
tools_media.register_movie_gen_tools(mcp_mg, mg)
tools_media.register_stt_tools(mcp_st, stt)
tools_media.register_tts_tools(mcp_ts, tts)
tools_obs.register_tools(mcp_ob, obs)
tools_ffmpeg.register_tools(mcp_ff, ffmpeg_c)
tools_agents.register_tools(mcp_ca, code_agents)

# TTS description を API キー状況に応じて動的設定
mcp_ts._tool_manager._tools["synthesize_speech"].description = tts.get_description()

# ------------------------------------------------------------------ #
# FastAPI アプリ
# ------------------------------------------------------------------ #

def _unique_op_id(route: APIRoute) -> str:
    """タグ + 関数名でユニークな operationId を生成する"""
    tag = route.tags[0] if route.tags else "root"
    return f"{tag}_{route.name}"

app = FastAPI(
    title="AiDiy TOOLs Server",
    description=(
        "AiDiy MCP サーバー — Chrome DevTools / Desktop Capture / SQLite / PostgreSQL / "
        "Logs / Code Check / Backup / Image Generation / Movie Generation / "
        "Speech-to-Text / Text-to-Speech / OBS Studio / FFmpeg / Code Agents の "
        "14 MCP ツールを HTTP POST で直接呼び出せます。\n\n"
        "各 MCP の詳細は `GET /{mcp_name}/docs` を参照してください。"
    ),
    version="1.0.0",
    generate_unique_id_function=_unique_op_id,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------ #
# MCP_MAP: initialize / list / ping 共通エンドポイント用
# ------------------------------------------------------------------ #

MCP_MAP: dict = {}  # mcp_name -> FastMCP instance (下部で設定)


@app.get("/")
async def root() -> Response:
    import json
    return Response(
        json.dumps({"mcps": list(MCP_MAP.keys())}, ensure_ascii=False),
        media_type="application/json",
    )


def _register_mcp_http_meta(mcp_name: str, mcp_instance) -> None:
    """initialize / list / ping の3エンドポイントを登録"""

    @app.post(f"/{mcp_name}/initialize", tags=[mcp_name],
              summary=f"{mcp_name} — MCP 初期化",
              operation_id=f"{mcp_name}_initialize")
    async def _initialize(mcp_name=mcp_name):
        return {
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": mcp_name, "version": "1.0"},
            "capabilities": {"tools": {}},
        }

    @app.get(f"/{mcp_name}/list", tags=[mcp_name],
             summary=f"{mcp_name} — ツール一覧",
             operation_id=f"{mcp_name}_list")
    async def _list(mcp_name=mcp_name, mcp_instance=mcp_instance):
        tools = [
            {
                "name": name,
                "description": tool.description or "",
                "inputSchema": tool.parameters if hasattr(tool, "parameters") else {},
            }
            for name, tool in mcp_instance._tool_manager._tools.items()
        ]
        return {"tools": tools}

    @app.get(f"/{mcp_name}/ping", tags=[mcp_name],
             summary=f"{mcp_name} — 疎通確認",
             operation_id=f"{mcp_name}_ping")
    async def _ping(mcp_name=mcp_name):
        return {"status": "ok", "name": mcp_name}


# ------------------------------------------------------------------ #
# HTTP ルート登録
# ------------------------------------------------------------------ #

app.include_router(tools_chrome.create_router(cdp, _ensure_chrome))
app.include_router(tools_desktop.create_router(capture))
app.include_router(tools_db.create_sqlite_router(sqlite_q))
app.include_router(tools_db.create_postgres_router(_get_pg))
app.include_router(tools_dev.create_logs_router(log_t))
app.include_router(tools_dev.create_code_check_router(checker))
app.include_router(tools_backup.create_router(bsave, bchk))
app.include_router(tools_media.create_router(ig, mg, stt, tts))
app.include_router(tools_obs.create_router(obs))
app.include_router(tools_ffmpeg.create_router(ffmpeg_c))
app.include_router(tools_agents.create_router(code_agents))

# ------------------------------------------------------------------ #
# initialize / list / ping エンドポイントを全 MCP に登録
# ------------------------------------------------------------------ #

MCP_MAP.update({
    "aidiy_chrome_devtools":    mcp,
    "aidiy_desktop_capture":    mcp_dc,
    "aidiy_sqlite":             mcp_sq,
    "aidiy_postgres":           mcp_pg,
    "aidiy_logs":               mcp_lg,
    "aidiy_code_check":         mcp_cc,
    "aidiy_backup":             mcp_bk,
    "aidiy_image_generation":   mcp_ig,
    "aidiy_movie_generation":   mcp_mg,
    "aidiy_speech_to_text":     mcp_st,
    "aidiy_text_to_speech":     mcp_ts,
    "aidiy_obs_studio_control": mcp_ob,
    "aidiy_ffmpeg_control":     mcp_ff,
    "aidiy_code_agents":        mcp_ca,
})
for _mcp_name, _mcp_instance in MCP_MAP.items():
    _register_mcp_http_meta(_mcp_name, _mcp_instance)

# ------------------------------------------------------------------ #
# MCP SSE サーバーをサブパスにマウント
# ------------------------------------------------------------------ #

app.mount(MOUNT,    mcp.sse_app())
app.mount(MOUNT_DC, mcp_dc.sse_app())
app.mount(MOUNT_SQ, mcp_sq.sse_app())
app.mount(MOUNT_PG, mcp_pg.sse_app())
app.mount(MOUNT_LG, mcp_lg.sse_app())
app.mount(MOUNT_CC, mcp_cc.sse_app())
app.mount(MOUNT_BK, mcp_bk.sse_app())
app.mount(MOUNT_IG, mcp_ig.sse_app())
app.mount(MOUNT_MG, mcp_mg.sse_app())
app.mount(MOUNT_ST, mcp_st.sse_app())
app.mount(MOUNT_TS, mcp_ts.sse_app())
app.mount(MOUNT_OB, mcp_ob.sse_app())
app.mount(MOUNT_FF, mcp_ff.sse_app())
app.mount(MOUNT_CA, mcp_ca.sse_app())

# ------------------------------------------------------------------ #
# OpenAPI パス順序カスタマイズ
# 各 MCP を docs → initialize → list → ping → {method_name} の順に統一
# ------------------------------------------------------------------ #

def _build_custom_openapi():
    from fastapi.openapi.utils import get_openapi
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    paths = schema.get("paths", {})
    ordered: dict = {}

    if "/" in paths:
        ordered["/"] = paths["/"]

    _PRIORITY = ["docs", "initialize", "list", "ping"]
    for mcp_name in MCP_MAP:
        for suffix in _PRIORITY:
            key = f"/{mcp_name}/{suffix}"
            if key in paths:
                ordered[key] = paths[key]
        # その他（save/{method_name}, check/{method_name} など）
        for key in paths:
            if key.startswith(f"/{mcp_name}/") and key not in ordered:
                ordered[key] = paths[key]

    for key, val in paths.items():
        if key not in ordered:
            ordered[key] = val

    schema["paths"] = ordered
    app.openapi_schema = schema
    return schema


app.openapi = _build_custom_openapi

# ------------------------------------------------------------------ #
# エントリポイント
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    base = f"http://localhost:{MCP_PORT}"
    logger.info(f"MCP Index            : {base}/")
    logger.info(f"--- initialize[POST] / list[GET] / ping[GET] / {{method}}[POST] ---")
    logger.info(f"Chrome               : {base}/aidiy_chrome_devtools/  SSE:{MOUNT}/sse")
    logger.info(f"DesktopCapture       : {base}/aidiy_desktop_capture/  SSE:{MOUNT_DC}/sse")
    logger.info(f"Sqlite               : {base}/aidiy_sqlite/  SSE:{MOUNT_SQ}/sse")
    logger.info(f"Postgres             : {base}/aidiy_postgres/  SSE:{MOUNT_PG}/sse"
                + (" [psycopg 未導入]" if _pg_init_error else ""))
    logger.info(f"Logs                 : {base}/aidiy_logs/  SSE:{MOUNT_LG}/sse")
    logger.info(f"CodeCheck            : {base}/aidiy_code_check/  SSE:{MOUNT_CC}/sse")
    logger.info(f"Backup               : {base}/aidiy_backup/  SSE:{MOUNT_BK}/sse")
    logger.info(f"ImageGeneration      : {base}/aidiy_image_generation/  SSE:{MOUNT_IG}/sse")
    logger.info(f"MovieGeneration      : {base}/aidiy_movie_generation/  SSE:{MOUNT_MG}/sse")
    logger.info(f"SpeechToText         : {base}/aidiy_speech_to_text/  SSE:{MOUNT_ST}/sse")
    logger.info(f"TextToSpeech         : {base}/aidiy_text_to_speech/  SSE:{MOUNT_TS}/sse")
    logger.info(f"ObsStudioControl     : {base}/aidiy_obs_studio_control/  SSE:{MOUNT_OB}/sse")
    logger.info(f"FfmpegControl        : {base}/aidiy_ffmpeg_control/  SSE:{MOUNT_FF}/sse")
    logger.info(f"CodeAgents           : {base}/aidiy_code_agents/  SSE:{MOUNT_CA}/sse")
    uvicorn.run(app, host="0.0.0.0", port=MCP_PORT, log_level="warning")
