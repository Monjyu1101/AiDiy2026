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
MCP ツールの実装は mcp_proc/tools_*.py に分割してある。
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
from mcp.server.fastmcp import FastMCP

from log_config import setup_logging, get_logger
from mcp_proc.chrome_manager import ChromeManager
from mcp_proc.chrome_devtools import CDPClient
from mcp_proc.desktop_capture import DesktopCapture
from mcp_proc.sqlite_query import SqliteQuery
from mcp_proc.postgres_query import PgQuery, PgQueryError
from mcp_proc.log_tailer import LogTailer
from mcp_proc.code_checker import CodeChecker
from mcp_proc.backup import BackupCheck, BackupSave
from mcp_proc.image_generation import ImageGeneration
from mcp_proc.movie_generation import MovieGeneration
from mcp_proc.speech_to_text import SpeechToText
from mcp_proc.text_to_speech import TextToSpeech
from mcp_proc.obs_studio_control import ObsStudioControl
from mcp_proc.ffmpeg_control import FfmpegControl
from mcp_proc.code_agents import CodeAgents

from mcp_proc import tools_chrome, tools_desktop, tools_db, tools_dev
from mcp_proc import tools_backup, tools_media, tools_obs, tools_ffmpeg, tools_agents

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

app = FastAPI(
    title="AiDiy MCP Server",
    docs_url="/docs",
    openapi_url="/openapi.json",
    redoc_url=None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
async def root() -> Response:
    return Response('{"message": "MCP Server is running"}', media_type="application/json")


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
# エントリポイント
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    logger.info(f"Swagger UI           : http://localhost:{MCP_PORT}/docs")
    logger.info(f"Chrome SSE           : http://localhost:{MCP_PORT}{MOUNT}/sse")
    logger.info(f"Chrome HTTP          : http://localhost:{MCP_PORT}/aidiy_chrome_devtools/{{method}}  [POST]")
    logger.info(f"DesktopCapture SSE   : http://localhost:{MCP_PORT}{MOUNT_DC}/sse")
    logger.info(f"DesktopCapture HTTP  : http://localhost:{MCP_PORT}/aidiy_desktop_capture/{{method}}  [POST]  (screenshot / cursor_pos / screen_info / list_windows)")
    logger.info(f"Sqlite SSE           : http://localhost:{MCP_PORT}{MOUNT_SQ}/sse")
    logger.info(f"Sqlite HTTP          : http://localhost:{MCP_PORT}/aidiy_sqlite/{{method}}  [POST]  (list_tables / describe_table / count / query / audit_summary)")
    logger.info(f"Postgres SSE         : http://localhost:{MCP_PORT}{MOUNT_PG}/sse"
                + (" [psycopg 未導入]" if _pg_init_error else ""))
    logger.info(f"Postgres HTTP        : http://localhost:{MCP_PORT}/aidiy_postgres/{{method}}  [POST]  (server_info / list_databases / list_schemas / list_tables / describe_table / count / query)")
    logger.info(f"Logs SSE             : http://localhost:{MCP_PORT}{MOUNT_LG}/sse")
    logger.info(f"Logs HTTP            : http://localhost:{MCP_PORT}/aidiy_logs/{{method}}  [POST]  (list / tail / recent_errors)")
    logger.info(f"CodeCheck SSE        : http://localhost:{MCP_PORT}{MOUNT_CC}/sse")
    logger.info(f"CodeCheck HTTP       : http://localhost:{MCP_PORT}/aidiy_code_check/{{method}}  [POST]  (list_targets / python_syntax / python_ruff / typescript)")
    logger.info(f"Backup SSE           : http://localhost:{MCP_PORT}{MOUNT_BK}/sse")
    logger.info(f"Backup HTTP (save)   : http://localhost:{MCP_PORT}/aidiy_backup/save/{{method}}  [POST]  (scan / run)")
    logger.info(f"Backup HTTP (check)  : http://localhost:{MCP_PORT}/aidiy_backup/check/{{method}}  [POST]  (info / before_after / versions / changed / diff_stats)")
    logger.info(f"ImageGeneration SSE  : http://localhost:{MCP_PORT}{MOUNT_IG}/sse")
    logger.info(f"ImageGeneration HTTP : http://localhost:{MCP_PORT}/aidiy_image_generation/{{method}}  [POST]  (generate)")
    logger.info(f"MovieGeneration SSE  : http://localhost:{MCP_PORT}{MOUNT_MG}/sse")
    logger.info(f"MovieGeneration HTTP : http://localhost:{MCP_PORT}/aidiy_movie_generation/{{method}}  [POST]  (generate)")
    logger.info(f"SpeechToText SSE     : http://localhost:{MCP_PORT}{MOUNT_ST}/sse")
    logger.info(f"SpeechToText HTTP    : http://localhost:{MCP_PORT}/aidiy_speech_to_text/{{method}}  [POST]  (recognize)")
    logger.info(f"TextToSpeech SSE     : http://localhost:{MCP_PORT}{MOUNT_TS}/sse")
    logger.info(f"TextToSpeech HTTP    : http://localhost:{MCP_PORT}/aidiy_text_to_speech/{{method}}  [POST]  (synthesize)")
    logger.info(f"ObsStudioControl SSE : http://localhost:{MCP_PORT}{MOUNT_OB}/sse")
    logger.info(f"ObsStudioControl HTTP: http://localhost:{MCP_PORT}/aidiy_obs_studio_control/{{method}}  [POST]  (startup_status / connection_info / status / request / ...)")
    logger.info(f"FfmpegControl SSE    : http://localhost:{MCP_PORT}{MOUNT_FF}/sse")
    logger.info(f"FfmpegControl HTTP   : http://localhost:{MCP_PORT}/aidiy_ffmpeg_control/{{method}}  [POST]  (versions / ffmpeg_run / ffprobe_run / media_duration / analyze_audio / video_trimming / ffplay_run)")
    logger.info(f"CodeAgents SSE       : http://localhost:{MCP_PORT}{MOUNT_CA}/sse")
    logger.info(f"CodeAgents HTTP      : http://localhost:{MCP_PORT}/aidiy_code_agents/{{method}}  [POST]  (config / run)")
    uvicorn.run(app, host="0.0.0.0", port=MCP_PORT, log_level="warning")
