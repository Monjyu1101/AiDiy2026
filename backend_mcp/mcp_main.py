# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""
Chrome DevTools MCP サーバー (Python純正版)

chrome-devtools-mcp (Node.js) を廃止し、Python MCP SDK + CDPClient で直接実装。
- Chrome を --remote-debugging-port で自動起動
- CDP (Chrome DevTools Protocol) を MCP ツールとして公開
- SSE エンドポイント: http://localhost:8095/aidiy_chrome_devtools/sse

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
import base64
import json
import os
import sys
import threading
import time
from datetime import datetime
from typing import Optional

# UTF-8出力を強制（Windows文字化け対策）
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import uvicorn
from mcp.server.fastmcp import FastMCP
from mcp.types import ImageContent
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from log_config import setup_logging, get_logger
from mcp_proc.chrome_manager import ChromeManager
from mcp_proc.chrome_devtools import CDPClient
from mcp_proc.desktop_capture import DesktopCapture, DesktopCaptureError
from mcp_proc.sqlite_query import SqliteQuery, SqliteQueryError
from mcp_proc.postgres_query import PgQuery, PgQueryError
from mcp_proc.log_tailer import LogTailer, LogTailError
from mcp_proc.code_checker import CodeChecker, CodeCheckError
from mcp_proc.backup_check import BackupCheck, BackupCheckError
from mcp_proc.backup_save import BackupSave, BackupSaveError
from mcp_proc.image_generation import ImageGeneration, ImageGenerationError
from mcp_proc.speech_to_text import SpeechToText, SpeechToTextError
from mcp_proc.text_to_speech import TextToSpeech, TextToSpeechError
from mcp_proc.obs_studio_control import ObsStudioControl, ObsStudioControlError
from mcp_proc.ffmpeg_control import FfmpegControl, FfmpegControlError

setup_logging()
logger = get_logger(__name__)

# ------------------------------------------------------------------ #
# 設定
# ------------------------------------------------------------------ #

CHROME_PORT  = int(os.environ.get("CHROME_DEBUG_PORT", "9222"))
MCP_PORT     = int(os.environ.get("MCP_PORT", "8095"))
MOUNT        = os.environ.get("MCP_MOUNT_PATH", "/aidiy_chrome_devtools")
MOUNT_DC     = os.environ.get("MCP_DC_MOUNT_PATH", "/aidiy_desktop_capture")
MOUNT_SQ     = os.environ.get("MCP_SQ_MOUNT_PATH", "/aidiy_sqlite")
MOUNT_PG     = os.environ.get("MCP_PG_MOUNT_PATH", "/aidiy_postgres")
MOUNT_LG     = os.environ.get("MCP_LG_MOUNT_PATH", "/aidiy_logs")
MOUNT_CC     = os.environ.get("MCP_CC_MOUNT_PATH", "/aidiy_code_check")
MOUNT_BC     = os.environ.get("MCP_BC_MOUNT_PATH", "/aidiy_backup_check")
MOUNT_BS     = os.environ.get("MCP_BS_MOUNT_PATH", "/aidiy_backup_save")
MOUNT_IG     = os.environ.get("MCP_IG_MOUNT_PATH", "/aidiy_image_generation")
MOUNT_ST     = os.environ.get("MCP_ST_MOUNT_PATH", "/aidiy_speech_to_text")
MOUNT_TS     = os.environ.get("MCP_TS_MOUNT_PATH", "/aidiy_text_to_speech")
MOUNT_OB     = os.environ.get("MCP_OB_MOUNT_PATH", "/aidiy_obs_studio_control")
MOUNT_FF     = os.environ.get("MCP_FF_MOUNT_PATH", "/aidiy_ffmpeg_control")

chrome   = ChromeManager(debug_port=CHROME_PORT)
cdp      = CDPClient(port=CHROME_PORT)
capture  = DesktopCapture()
sqlite_q = SqliteQuery()
log_t    = LogTailer()
checker  = CodeChecker()
bchk     = BackupCheck()
bsave    = BackupSave()

ig       = ImageGeneration()

stt      = SpeechToText()

tts      = TextToSpeech()

obs      = ObsStudioControl()

ffmpeg_c = FfmpegControl()

# PostgreSQL は psycopg 未導入環境でもサーバー起動を阻害しないよう遅延初期化
_pg_q: Optional[PgQuery] = None
_pg_init_error: Optional[str] = None
try:
    _pg_q = PgQuery()
except PgQueryError as _e:
    _pg_init_error = str(_e)


def _get_pg() -> PgQuery:
    """PgQuery インスタンスを取得。未初期化なら明示エラー。"""
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
# Chrome 保証ヘルパー
# ------------------------------------------------------------------ #

async def _ensure_chrome(show_automation_banner: Optional[bool] = None):
    """Chrome が起動していなければ自動起動する"""
    if not chrome.is_running():
        await asyncio.to_thread(
            chrome.ensure_running,
            show_automation_banner=show_automation_banner,
        )

# ------------------------------------------------------------------ #
# MCP サーバー & ツール定義
# ------------------------------------------------------------------ #

mcp = FastMCP(
    "aidiy_chrome_devtools",
    host="0.0.0.0",
    port=MCP_PORT,
    sse_path=f"{MOUNT}/sse",
    message_path=f"{MOUNT}/messages/",
    warn_on_duplicate_tools=False,
)

mcp_dc = FastMCP(
    "aidiy_desktop_capture",
    host="0.0.0.0",
    port=MCP_PORT,
    sse_path=f"{MOUNT_DC}/sse",
    message_path=f"{MOUNT_DC}/messages/",
    warn_on_duplicate_tools=False,
)

mcp_sq = FastMCP(
    "aidiy_sqlite",
    host="0.0.0.0",
    port=MCP_PORT,
    sse_path=f"{MOUNT_SQ}/sse",
    message_path=f"{MOUNT_SQ}/messages/",
    warn_on_duplicate_tools=False,
)

mcp_pg = FastMCP(
    "aidiy_postgres",
    host="0.0.0.0",
    port=MCP_PORT,
    sse_path=f"{MOUNT_PG}/sse",
    message_path=f"{MOUNT_PG}/messages/",
    warn_on_duplicate_tools=False,
)

mcp_lg = FastMCP(
    "aidiy_logs",
    host="0.0.0.0",
    port=MCP_PORT,
    sse_path=f"{MOUNT_LG}/sse",
    message_path=f"{MOUNT_LG}/messages/",
    warn_on_duplicate_tools=False,
)

mcp_cc = FastMCP(
    "aidiy_code_check",
    host="0.0.0.0",
    port=MCP_PORT,
    sse_path=f"{MOUNT_CC}/sse",
    message_path=f"{MOUNT_CC}/messages/",
    warn_on_duplicate_tools=False,
)

mcp_bc = FastMCP(
    "aidiy_backup_check",
    host="0.0.0.0",
    port=MCP_PORT,
    sse_path=f"{MOUNT_BC}/sse",
    message_path=f"{MOUNT_BC}/messages/",
    warn_on_duplicate_tools=False,
)

mcp_bs = FastMCP(
    "aidiy_backup_save",
    host="0.0.0.0",
    port=MCP_PORT,
    sse_path=f"{MOUNT_BS}/sse",
    message_path=f"{MOUNT_BS}/messages/",
    warn_on_duplicate_tools=False,
)

mcp_ig = FastMCP(
    "aidiy_image_generation",
    host="0.0.0.0",
    port=MCP_PORT,
    sse_path=f"{MOUNT_IG}/sse",
    message_path=f"{MOUNT_IG}/messages/",
    warn_on_duplicate_tools=False,
)

mcp_st = FastMCP(
    "aidiy_speech_to_text",
    host="0.0.0.0",
    port=MCP_PORT,
    sse_path=f"{MOUNT_ST}/sse",
    message_path=f"{MOUNT_ST}/messages/",
    warn_on_duplicate_tools=False,
)

mcp_ts = FastMCP(
    "aidiy_text_to_speech",
    host="0.0.0.0",
    port=MCP_PORT,
    sse_path=f"{MOUNT_TS}/sse",
    message_path=f"{MOUNT_TS}/messages/",
    warn_on_duplicate_tools=False,
)

mcp_ob = FastMCP(
    "aidiy_obs_studio_control",
    host="0.0.0.0",
    port=MCP_PORT,
    sse_path=f"{MOUNT_OB}/sse",
    message_path=f"{MOUNT_OB}/messages/",
    warn_on_duplicate_tools=False,
)

mcp_ff = FastMCP(
    "aidiy_ffmpeg_control",
    host="0.0.0.0",
    port=MCP_PORT,
    sse_path=f"{MOUNT_FF}/sse",
    message_path=f"{MOUNT_FF}/messages/",
    warn_on_duplicate_tools=False,
)


# ナビゲーション

@mcp.tool()
async def navigate(
    url: str,
    tab_id: Optional[str] = None,
    show_automation_banner: bool = True,
) -> str:
    """
    指定URLへ移動する。

    Args:
        show_automation_banner: Chrome 未起動時の自動起動で「自動操作中」の帯を表示する。
                                省略時は True。
    """
    await _ensure_chrome(show_automation_banner=show_automation_banner)
    return await cdp.navigate(url, tab_id)

@mcp.tool()
async def reload(tab_id: Optional[str] = None) -> str:
    """現在のページをリロードする"""
    await _ensure_chrome()
    return await cdp.reload(tab_id)

@mcp.tool()
async def go_back(tab_id: Optional[str] = None) -> str:
    """ブラウザの戻るボタン相当"""
    await _ensure_chrome()
    return await cdp.go_back(tab_id)

@mcp.tool()
async def go_forward(tab_id: Optional[str] = None) -> str:
    """ブラウザの進むボタン相当"""
    await _ensure_chrome()
    return await cdp.go_forward(tab_id)

# ページ情報取得

@mcp.tool()
async def screenshot(
    tab_id: Optional[str] = None,
    full_page: bool = False,
    save_path: Optional[str] = None,
) -> list:
    """
    スクリーンショットを撮る（PNG画像）。

    Args:
        save_path: 保存先。フォルダ指定なら yyyymmdd.hhmmss.png で保存。
                   ファイル指定なら指定ファイルに保存。省略時は保存しない。
    """
    await _ensure_chrome()
    data = await cdp.screenshot(tab_id=tab_id, full_page=full_page, save_path=save_path)
    if save_path and data:
        logger.info(f"screenshot saved: {save_path}")
    return [ImageContent(type="image", data=data, mimeType="image/png")]

@mcp.tool()
async def get_page_info(tab_id: Optional[str] = None) -> str:
    """ページのURL・タイトル・readyState などを取得する"""
    await _ensure_chrome()
    info = await cdp.get_page_info(tab_id)
    return json.dumps(info, ensure_ascii=False)

@mcp.tool()
async def get_html(tab_id: Optional[str] = None) -> str:
    """ページ全体のHTMLを取得する"""
    await _ensure_chrome()
    return await cdp.get_html(tab_id)

@mcp.tool()
async def get_text(tab_id: Optional[str] = None) -> str:
    """ページのテキストコンテンツを取得する"""
    await _ensure_chrome()
    return await cdp.get_text(tab_id)

# JavaScript・DOM操作

@mcp.tool()
async def eval_js(expression: str, tab_id: Optional[str] = None, await_promise: bool = False) -> str:
    """JavaScriptを実行して結果を返す"""
    await _ensure_chrome()
    result = await cdp.eval_js(expression, tab_id, await_promise)
    return json.dumps(result, ensure_ascii=False)

@mcp.tool()
async def click(selector: str, tab_id: Optional[str] = None) -> str:
    """CSSセレクターで要素をクリックする"""
    await _ensure_chrome()
    return await cdp.click(selector, tab_id)

@mcp.tool()
async def type_text(selector: str, text: str, tab_id: Optional[str] = None, clear_first: bool = True) -> str:
    """CSSセレクターで要素にテキストを入力する"""
    await _ensure_chrome()
    return await cdp.type_text(selector, text, tab_id, clear_first)

@mcp.tool()
async def scroll(delta_x: int = 0, delta_y: int = 0, tab_id: Optional[str] = None, selector: Optional[str] = None) -> str:
    """ページまたは要素をスクロールする"""
    await _ensure_chrome()
    return await cdp.scroll(delta_x, delta_y, tab_id, selector)

@mcp.tool()
async def find_elements(selector: str, tab_id: Optional[str] = None, limit: int = 20) -> str:
    """CSSセレクターで要素を検索してプロパティ一覧を返す"""
    await _ensure_chrome()
    result = await cdp.find_elements(selector, tab_id, limit)
    return json.dumps(result, ensure_ascii=False)

# タブ管理

@mcp.tool()
async def list_tabs() -> str:
    """開いているタブ一覧を取得する"""
    await _ensure_chrome()
    tabs = await asyncio.to_thread(cdp.list_tabs)
    return json.dumps(tabs, ensure_ascii=False)

@mcp.tool()
async def new_tab(
    url: str = "about:blank",
    show_automation_banner: bool = True,
) -> str:
    """
    新規タブを開く。

    Args:
        show_automation_banner: Chrome 未起動時の自動起動で「自動操作中」の帯を表示する。
                                省略時は True。
    """
    await _ensure_chrome(show_automation_banner=show_automation_banner)
    # Target.createTarget でタブ作成と URL 指定を一括実行（より確実）
    browser_ws = await asyncio.to_thread(cdp.get_browser_ws_url)
    result = await cdp.send_command(browser_ws, "Target.createTarget", {"url": url})
    target_id = result.get("targetId", "")
    return json.dumps({"id": target_id, "url": url}, ensure_ascii=False)

@mcp.tool()
async def close_tab(tab_id: str) -> str:
    """指定タブを閉じる"""
    await _ensure_chrome()
    ok = await asyncio.to_thread(cdp.close_tab_sync, tab_id)
    return "閉じました" if ok else "失敗しました"

@mcp.tool()
async def activate_tab(tab_id: str) -> str:
    """指定タブをアクティブにする"""
    await _ensure_chrome()
    ok = await asyncio.to_thread(cdp.activate_tab_sync, tab_id)
    return "アクティブにしました" if ok else "失敗しました"

# ビューポート・ロード待機

@mcp.tool()
async def set_viewport(width: int, height: int, tab_id: Optional[str] = None) -> str:
    """ビューポートサイズを設定する"""
    await _ensure_chrome()
    return await cdp.set_viewport(width, height, tab_id)

@mcp.tool()
async def wait_for_load(tab_id: Optional[str] = None, timeout: float = 10.0) -> str:
    """ページのロード完了を待つ（最大timeout秒）"""
    await _ensure_chrome()
    return await cdp.wait_for_load(tab_id, timeout)

# コンソール・ネットワークキャプチャ

@mcp.tool()
async def install_console_capture(tab_id: Optional[str] = None) -> str:
    """コンソールログのキャプチャをページに設置する"""
    await _ensure_chrome()
    return await cdp.install_console_capture(tab_id)

@mcp.tool()
async def get_console_logs(tab_id: Optional[str] = None, level: Optional[str] = None, limit: int = 50) -> str:
    """キャプチャされたコンソールログを取得する（事前にinstall_console_captureが必要）"""
    await _ensure_chrome()
    logs = await cdp.get_console_logs(tab_id, level, limit)
    return json.dumps(logs, ensure_ascii=False)

@mcp.tool()
async def install_network_capture(tab_id: Optional[str] = None) -> str:
    """XHR/fetchリクエストのキャプチャをページに設置する"""
    await _ensure_chrome()
    return await cdp.install_network_capture(tab_id)

@mcp.tool()
async def get_network_logs(tab_id: Optional[str] = None, limit: int = 50) -> str:
    """キャプチャされたネットワークリクエストを取得する（事前にinstall_network_captureが必要）"""
    await _ensure_chrome()
    logs = await cdp.get_network_logs(tab_id, limit)
    return json.dumps(logs, ensure_ascii=False)

# ストレージ・Cookie

@mcp.tool()
async def get_cookies(tab_id: Optional[str] = None) -> str:
    """ページのCookieを取得する"""
    await _ensure_chrome()
    cookies = await cdp.get_cookies(tab_id)
    return json.dumps(cookies, ensure_ascii=False)

@mcp.tool()
async def get_local_storage(tab_id: Optional[str] = None) -> str:
    """localStorageの内容を取得する"""
    await _ensure_chrome()
    data = await cdp.get_local_storage(tab_id)
    return json.dumps(data, ensure_ascii=False)

@mcp.tool()
async def get_session_storage(tab_id: Optional[str] = None) -> str:
    """sessionStorageの内容を取得する"""
    await _ensure_chrome()
    data = await cdp.get_session_storage(tab_id)
    return json.dumps(data, ensure_ascii=False)

@mcp.tool()
async def get_current_url(tab_id: Optional[str] = None) -> str:
    """現在のURLを取得する"""
    await _ensure_chrome()
    return await cdp.get_current_url(tab_id)

@mcp.tool()
async def get_title(tab_id: Optional[str] = None) -> str:
    """ページタイトルを取得する"""
    await _ensure_chrome()
    return await cdp.get_title(tab_id)

@mcp.tool()
async def scroll_to_element(selector: str, tab_id: Optional[str] = None) -> str:
    """要素が見えるようにスクロールする"""
    await _ensure_chrome()
    return await cdp.scroll_to_element(selector, tab_id)

@mcp.tool()
async def clear_console_logs(tab_id: Optional[str] = None) -> str:
    """キャプチャされたコンソールログをクリアする"""
    await _ensure_chrome()
    return await cdp.clear_console_logs(tab_id)

@mcp.tool()
async def clear_network_logs(tab_id: Optional[str] = None) -> str:
    """キャプチャされたネットワークログをクリアする"""
    await _ensure_chrome()
    return await cdp.clear_network_logs(tab_id)

@mcp.tool()
async def get_resource_timing(tab_id: Optional[str] = None, limit: int = 30) -> str:
    """Performance APIからリソースタイミング情報を取得する"""
    await _ensure_chrome()
    data = await cdp.get_resource_timing(tab_id, limit)
    return json.dumps(data, ensure_ascii=False)

@mcp.tool()
async def get_version() -> str:
    """ChromeのバージョンとUserAgent情報を取得する"""
    await _ensure_chrome()
    data = await asyncio.to_thread(cdp.get_version)
    return json.dumps(data, ensure_ascii=False)

@mcp.tool()
async def cdp_command(method: str, params: Optional[str] = None, tab_id: Optional[str] = None) -> str:
    """
    Chrome DevTools Protocol (CDP) コマンドを直接送信する。
    既存ツールでカバーされない高度な操作に使用する。

    Args:
        method: CDP メソッド名 (例: "Page.printToPDF", "Network.setExtraHTTPHeaders")
        params: JSON 文字列形式のパラメータ (例: '{"landscape": true}')
        tab_id: 対象タブID (省略時は最初のタブ)。
                "browser" を指定するとブラウザレベルの WebSocket を使用する
                (Browser.* / Target.* / SystemInfo.* 等のコマンドに必要)。

    Returns:
        CDP レスポンスの JSON 文字列

    CDP メソッド例 (タブレベル):
        Page.printToPDF            — PDF出力
        Network.setExtraHTTPHeaders — リクエストヘッダー追加
        Emulation.setGeolocationOverride — 位置情報偽装
        Emulation.setUserAgentOverride   — UserAgent変更
        DOM.querySelector          — DOM要素取得
        Input.dispatchKeyEvent     — キーイベント送信

    CDP メソッド例 (ブラウザレベル: tab_id="browser"):
        Browser.getVersion         — Chrome バージョン情報
        Target.getTargets          — 全ターゲット一覧
        Target.createTarget        — 新規ターゲット作成
        SystemInfo.getInfo         — システム情報
    """
    await _ensure_chrome()
    parsed_params: dict = {}
    if params:
        if isinstance(params, dict):
            parsed_params = params
        else:
            stripped = params.strip()
            if stripped:
                loaded = json.loads(stripped)
                if not isinstance(loaded, dict):
                    raise ValueError(
                        f"params は JSON オブジェクトである必要があります (例: '{{\"accept\": true}}')"
                    )
                parsed_params = loaded
    if tab_id == "browser":
        ws_url = await asyncio.to_thread(cdp.get_browser_ws_url)
    else:
        tab = await asyncio.to_thread(cdp.resolve_tab, tab_id)
        ws_url = cdp.get_ws_url(tab)
    result = await cdp.send_command(ws_url, method, parsed_params)
    return json.dumps(result, ensure_ascii=False)

# [DIALOG_TOOLS_PATCH_APPLIED]

# ------------------------------------------------------------------ #
# ダイアログ操作ツール (js_confirm_result / js_alert_result 等)
# ------------------------------------------------------------------ #

@mcp.tool()
async def js_confirm_result(
    accept: bool = True,
    dialog_wait: float = 0.0,
    tab_id: Optional[str] = None,
) -> str:
    """
    現在表示中の confirm ダイアログを CDP 経由で操作する。

    Args:
        accept: True=OK（確認）、False=キャンセル
        dialog_wait: ダイアログが表示されるまで待機する最大秒数（デフォルト0=即時応答）。
                     事前に eval_js で setTimeout クリックをスケジュールした場合は
                     クリック遅延より大きな値を指定する（例: 30）。
                     待機中は Page.javascriptDialogOpening イベント駆動で検知する。
        tab_id: 対象タブID（省略時は最初のタブ）
    """
    await _ensure_chrome()
    return await cdp.handle_dialog(accept, "", tab_id, dialog_wait)

@mcp.tool()
async def js_alert_result(
    dialog_wait: float = 0.0,
    tab_id: Optional[str] = None,
) -> str:
    """
    現在表示中の alert ダイアログを CDP 経由で閉じる。

    典型的な使い方（ダイアログをキャプチャしてから応答する場合）:
      1. eval_js("setTimeout(()=>document.querySelector('button').click(), 2000)")
         → ボタンを2秒後に非同期クリック（即座にリターン）
      2. desktop_screenshot(delay=2.5)
         → ダイアログ表示中にデスクトップキャプチャ撮影
      3. js_alert_result(dialog_wait=30)
         → alert 表示を CDP イベントで検知して自動応答

    Args:
        dialog_wait: ダイアログが表示されるまで待機する最大秒数（デフォルト0=即時応答）。
                     事前に eval_js で setTimeout クリックをスケジュールした場合は
                     クリック遅延より大きな値を指定する（例: 30）。
                     待機中は Page.javascriptDialogOpening イベント駆動で検知する。
        tab_id: 対象タブID（省略時は最初のタブ）
    """
    await _ensure_chrome()
    return await cdp.handle_dialog(True, "", tab_id, dialog_wait)

@mcp.tool()
async def js_install_dialog_override(tab_id: Optional[str] = None) -> str:
    """
    window.confirm/alert/prompt をオーバーライドし、ネイティブダイアログの表示をブロックしない形に変更する。
    インストール後は js_set_confirm_result で confirm の戻り値を事前設定できる。

    Args:
        tab_id: 対象タブID（省略時は最初のタブ）
    """
    await _ensure_chrome()
    return await cdp.install_dialog_override(tab_id)

@mcp.tool()
async def js_set_confirm_result(accept: bool = True, tab_id: Optional[str] = None) -> str:
    """
    次の confirm() 呼び出しが返す値を設定する（js_install_dialog_override が必要）。
    ボタンクリック前に呼んでおくと、confirm が表示されずに自動で accept/dismiss される。

    Args:
        accept: True=OK（確認）、False=キャンセル
        tab_id: 対象タブID（省略時は最初のタブ）
    """
    await _ensure_chrome()
    return await cdp.set_confirm_result(accept, tab_id)

@mcp.tool()
async def js_get_dialog_state(tab_id: Optional[str] = None) -> str:
    """
    最後に呼ばれたダイアログの情報を取得する（js_install_dialog_override が必要）。
    last_type/last_message/last_result/next_confirm_result を返す。

    Args:
        tab_id: 対象タブID（省略時は最初のタブ）
    """
    await _ensure_chrome()
    state = await cdp.get_dialog_state(tab_id)
    return json.dumps(state, ensure_ascii=False)

# ------------------------------------------------------------------ #
# 旧 chrome-devtools-mcp (Node.js版) との互換エイリアス
# AIが旧ツール名を使う場合に対応
# ------------------------------------------------------------------ #

@mcp.tool()
async def new_page(
    url: str = "about:blank",
    show_automation_banner: bool = True,
) -> str:
    """新規タブを開く（new_tab の別名）"""
    return await new_tab(url, show_automation_banner)

@mcp.tool()
async def close_page(tab_id: str) -> str:
    """指定タブを閉じる（close_tab の別名）"""
    return await close_tab(tab_id)

@mcp.tool()
async def list_pages() -> str:
    """開いているタブ一覧を取得する（list_tabs の別名）"""
    return await list_tabs()

@mcp.tool()
async def click_element(selector: str, tab_id: Optional[str] = None) -> str:
    """CSSセレクターで要素をクリックする（click の別名）"""
    return await click(selector, tab_id)

@mcp.tool()
async def fill(selector: str, value: str, tab_id: Optional[str] = None) -> str:
    """CSSセレクターで要素にテキストを入力する（type_text の別名）"""
    return await type_text(selector, value, tab_id)

@mcp.tool()
async def evaluate(expression: str, tab_id: Optional[str] = None) -> str:
    """JavaScriptを実行して結果を返す（eval_js の別名）"""
    return await eval_js(expression, tab_id)

@mcp.tool()
async def get_page_content(tab_id: Optional[str] = None) -> str:
    """ページのテキストコンテンツを取得する（get_text の別名）"""
    return await get_text(tab_id)

# ================================================================== #
# aidiy_desktop_capture ツール
# ================================================================== #

@mcp_dc.tool()
async def screenshot(
    screen_number: str = "auto",
    size: Optional[int] = None,
    x: Optional[int] = None,
    y: Optional[int] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
    window_title: Optional[str] = None,
    delay: float = 0.0,
    format: str = "png",
    quality: int = 85,
    crosshair: bool = False,
    label: bool = False,
    save_path: Optional[str] = None,
) -> list:
    """
    OS のスクリーンショットを撮る（PNG/JPEG 画像）。

    撮影モードはパラメータの組み合わせで自動判定する（優先順位順）:
      1. window_title 指定あり → ウィンドウキャプチャ（Windows 専用）
      2. x,y,width,height 全指定 → 指定領域キャプチャ
      3. size 指定あり → screen_number モニター上でカーソル中心の矩形切り出し
      4. それ以外 → screen_number モニター全体（デフォルト）

    Args:
        screen_number: モニター指定。"auto"=カーソルのあるモニター, "all"=全画面結合,
                       "0"/"1"/...=モニター番号。デフォルト "auto"
        size: カーソル中心切り出しの一辺 px（例: 600）
        x: region モードの左上 X 座標（絶対座標）
        y: region モードの左上 Y 座標（絶対座標）
        width: region モードの幅 px
        height: region モードの高さ px
        window_title: ウィンドウタイトルの部分一致文字列
        delay: 撮影前の遅延秒数（ツールチップ・メニュー表示待ちに有効）
        format: "png"（デフォルト）または "jpeg"
        quality: JPEG 品質 1-100（デフォルト 85）
        crosshair: True でカーソル位置に赤い十字線を描画（size モード時）
        label: True で座標・サイズのラベルを右下に追記
        save_path: 保存先。フォルダ指定なら yyyymmdd.hhmmss.png で保存。
                   ファイル指定なら指定ファイルに保存。省略時は backend_server/temp/output/ に保存。
    """
    if delay > 0:
        await asyncio.sleep(delay)

    try:
        img             = None
        info            = {}
        crosshair_pos   = None

        if window_title:
            img, info = await asyncio.to_thread(capture.grab_window, window_title)
        elif x is not None and y is not None and width is not None and height is not None:
            img  = await asyncio.to_thread(capture.grab_region, x, y, width, height)
            info = {"x": x, "y": y, "width": width, "height": height}
        elif size is not None:
            img, info = await asyncio.to_thread(capture.grab_cursor_region, size, screen_number)
            if crosshair:
                cx = info["cursor_x"] - info["x"] - info.get("crop_rel_x", 0)
                cy = info["cursor_y"] - info["y"] - info.get("crop_rel_y", 0)
                crosshair_pos = (cx, cy)
        else:
            img, info = await asyncio.to_thread(capture.grab_screen, screen_number)

        label_text = None
        if label:
            cx, cy = info.get("cursor_x", 0), info.get("cursor_y", 0)
            label_text = (
                f"cursor=({cx},{cy})  "
                f"region=({info.get('x',0)},{info.get('y',0)}"
                f" {info.get('width', img.width)}x{info.get('height', img.height)})"
            )

        if crosshair_pos or label_text:
            img = await asyncio.to_thread(capture.annotate, img, crosshair_pos, label_text)

        # 保存先は capture.to_base64 が解決（save_path=None → DEFAULT_OUTPUT_DIR）
        data = await asyncio.to_thread(capture.to_base64, img, format, quality, save_path)
        mime = "image/jpeg" if format.lower() in ("jpeg", "jpg") else "image/png"

        logger.info(
            f"screenshot: mode={'window' if window_title else 'region' if x is not None else 'cursor' if size else 'screen'}"
            f"  size={img.size}  format={format}"
            f"  save_path={save_path or '(default)'}"
        )

        return [ImageContent(type="image", data=data, mimeType=mime)]

    except DesktopCaptureError as e:
        raise ValueError(str(e)) from e


@mcp_dc.tool()
async def get_cursor_pos() -> str:
    """現在のマウスカーソル座標を返す"""
    x, y = await asyncio.to_thread(capture.cursor_pos)
    return json.dumps({"x": x, "y": y}, ensure_ascii=False)


@mcp_dc.tool()
async def get_screen_info() -> str:
    """
    全モニターの解像度・座標・プライマリフラグを返す。

    Returns:
        JSON 配列 [{index, x, y, width, height, primary}, ...]
    """
    mons = await asyncio.to_thread(capture.monitors)
    return json.dumps(mons, ensure_ascii=False)


@mcp_dc.tool()
async def list_windows() -> str:
    """
    表示中ウィンドウの一覧を返す（Windows 専用）。

    Returns:
        JSON 配列 [{hwnd, title, x, y, width, height}, ...]
    """
    wins = await asyncio.to_thread(capture.list_windows)
    return json.dumps(wins, ensure_ascii=False)


# ================================================================== #
# aidiy_sqlite ツール（AiDiy の SQLite DB を自己検証用に読み書き）
# ================================================================== #

@mcp_sq.tool()
async def sqlite_list_tables() -> str:
    """AiDiy DB の全テーブル・VIEW 一覧を返す"""
    try:
        items = await asyncio.to_thread(sqlite_q.list_tables)
    except SqliteQueryError as e:
        raise ValueError(str(e)) from e
    return json.dumps(items, ensure_ascii=False)


@mcp_sq.tool()
async def sqlite_describe_table(table_name: str) -> str:
    """指定テーブルのスキーマ（列・FK・索引・件数）を返す"""
    try:
        info = await asyncio.to_thread(sqlite_q.describe_table, table_name)
    except SqliteQueryError as e:
        raise ValueError(str(e)) from e
    return json.dumps(info, ensure_ascii=False, default=str)


@mcp_sq.tool()
async def sqlite_count(table_name: str, where: Optional[str] = None) -> str:
    """件数を返す。where は必要なら SQL の WHERE 節を文字列で渡す（`;` 禁止）"""
    try:
        info = await asyncio.to_thread(sqlite_q.count, table_name, where)
    except SqliteQueryError as e:
        raise ValueError(str(e)) from e
    return json.dumps(info, ensure_ascii=False)


@mcp_sq.tool()
async def sqlite_query(
    sql: str,
    params: Optional[list] = None,
    max_rows: int = 200,
    allow_write: bool = False,
) -> str:
    """
    SELECT を実行して行を返す。既定は読み取り専用。
    書き込み系は allow_write=True を明示したときのみ許可。
    複数ステートメント不可。
    """
    try:
        result = await asyncio.to_thread(
            sqlite_q.query, sql, params, max_rows, allow_write
        )
    except SqliteQueryError as e:
        raise ValueError(str(e)) from e
    return json.dumps(result, ensure_ascii=False, default=str)


@mcp_sq.tool()
async def sqlite_audit_summary(table_name: str, limit: int = 5) -> str:
    """監査フィールドのあるテーブルの直近 N 件を返す（更新日時 降順）"""
    try:
        info = await asyncio.to_thread(sqlite_q.audit_summary, table_name, limit)
    except SqliteQueryError as e:
        raise ValueError(str(e)) from e
    return json.dumps(info, ensure_ascii=False, default=str)


# ================================================================== #
# aidiy_postgres ツール（外部 PostgreSQL に対する read-only 中心クエリ）
# ================================================================== #

@mcp_pg.tool()
async def postgres_server_info(dsn: Optional[str] = None) -> str:
    """接続先 PostgreSQL のバージョン・現在 DB・ユーザー等を返す"""
    try:
        info = await asyncio.to_thread(_get_pg().server_info, dsn)
    except PgQueryError as e:
        raise ValueError(str(e)) from e
    return json.dumps(info, ensure_ascii=False, default=str)


@mcp_pg.tool()
async def postgres_list_databases(dsn: Optional[str] = None) -> str:
    """テンプレート以外の DB 一覧"""
    try:
        items = await asyncio.to_thread(_get_pg().list_databases, dsn)
    except PgQueryError as e:
        raise ValueError(str(e)) from e
    return json.dumps(items, ensure_ascii=False)


@mcp_pg.tool()
async def postgres_list_schemas(dsn: Optional[str] = None) -> str:
    """ユーザースキーマ一覧（pg_catalog / information_schema は除外）"""
    try:
        items = await asyncio.to_thread(_get_pg().list_schemas, dsn)
    except PgQueryError as e:
        raise ValueError(str(e)) from e
    return json.dumps(items, ensure_ascii=False)


@mcp_pg.tool()
async def postgres_list_tables(
    schema: str = "public",
    dsn: Optional[str] = None,
) -> str:
    """指定スキーマのテーブル・VIEW 一覧"""
    try:
        items = await asyncio.to_thread(_get_pg().list_tables, schema, dsn)
    except PgQueryError as e:
        raise ValueError(str(e)) from e
    return json.dumps(items, ensure_ascii=False)


@mcp_pg.tool()
async def postgres_describe_table(
    table: str,
    schema: str = "public",
    dsn: Optional[str] = None,
) -> str:
    """列情報・PK・FK・件数を返す"""
    try:
        info = await asyncio.to_thread(
            _get_pg().describe_table, table, schema, dsn
        )
    except PgQueryError as e:
        raise ValueError(str(e)) from e
    return json.dumps(info, ensure_ascii=False, default=str)


@mcp_pg.tool()
async def postgres_count(
    table: str,
    schema: str = "public",
    where: Optional[str] = None,
    dsn: Optional[str] = None,
) -> str:
    """件数取得（`where` 内の `;` は禁止）"""
    try:
        info = await asyncio.to_thread(_get_pg().count, table, schema, where, dsn)
    except PgQueryError as e:
        raise ValueError(str(e)) from e
    return json.dumps(info, ensure_ascii=False, default=str)


@mcp_pg.tool()
async def postgres_query(
    sql: str,
    params: Optional[list] = None,
    max_rows: int = 200,
    allow_write: bool = False,
    dsn: Optional[str] = None,
) -> str:
    """
    任意 SQL を実行。既定は読み取り専用トランザクション。
    複数ステートメント不可。書き込みは allow_write=True が必要。
    """
    try:
        result = await asyncio.to_thread(
            _get_pg().query, sql, params, max_rows, allow_write, dsn
        )
    except PgQueryError as e:
        raise ValueError(str(e)) from e
    return json.dumps(result, ensure_ascii=False, default=str)


# ================================================================== #
# aidiy_logs ツール（バックエンドのログを tail する）
# ================================================================== #

@mcp_lg.tool()
async def logs_list() -> str:
    """監視対象のログファイル一覧を返す（server / mcp）"""
    try:
        items = await asyncio.to_thread(log_t.list_logs)
    except LogTailError as e:
        raise ValueError(str(e)) from e
    return json.dumps(items, ensure_ascii=False)


@mcp_lg.tool()
async def logs_tail(
    server: str = "server",
    lines: int = 100,
    grep: Optional[str] = None,
) -> str:
    """
    指定サーバーのログ末尾を返す。

    Args:
        server: 'server'（core/apps 共通）/ 'mcp' / 'core' / 'apps'
        lines:  末尾 N 行（最大 2000）
        grep:   指定時は正規表現で抽出
    """
    try:
        result = await asyncio.to_thread(log_t.tail, server, lines, grep)
    except LogTailError as e:
        raise ValueError(str(e)) from e
    return json.dumps(result, ensure_ascii=False)


@mcp_lg.tool()
async def logs_recent_errors(server: str = "server", lines: int = 500) -> str:
    """直近ログから ERROR/Traceback を抽出し、前後 2 行の文脈付きで返す"""
    try:
        result = await asyncio.to_thread(log_t.recent_errors, server, lines)
    except LogTailError as e:
        raise ValueError(str(e)) from e
    return json.dumps(result, ensure_ascii=False)


# ================================================================== #
# aidiy_code_check ツール（型チェック・構文チェック・lint）
# ================================================================== #

@mcp_cc.tool()
async def check_list_targets() -> str:
    """チェック対象（Python venv / TS プロジェクト）の存在確認"""
    try:
        info = await asyncio.to_thread(checker.list_targets)
    except CodeCheckError as e:
        raise ValueError(str(e)) from e
    return json.dumps(info, ensure_ascii=False)


@mcp_cc.tool()
async def check_python_syntax(
    file_path: str,
    venv_project: str = "backend_server",
) -> str:
    """Python ファイル 1 つを py_compile で構文チェック（相対パスはプロジェクトルート基準）"""
    try:
        result = await asyncio.to_thread(checker.python_syntax, file_path, venv_project)
    except CodeCheckError as e:
        raise ValueError(str(e)) from e
    return json.dumps(result, ensure_ascii=False)


@mcp_cc.tool()
async def check_python_ruff(
    path: str = "backend_server",
    venv_project: str = "backend_server",
) -> str:
    """Python プロジェクトを ruff check で lint（未インストール時はエラーを返す）"""
    try:
        result = await asyncio.to_thread(checker.python_ruff, path, venv_project)
    except CodeCheckError as e:
        raise ValueError(str(e)) from e
    return json.dumps(result, ensure_ascii=False)


@mcp_cc.tool()
async def check_typescript(project: str = "frontend_web") -> str:
    """npm run type-check を実行（project: 'frontend_web' / 'frontend_avatar'）"""
    try:
        result = await asyncio.to_thread(checker.typescript_check, project)
    except CodeCheckError as e:
        raise ValueError(str(e)) from e
    return json.dumps(result, ensure_ascii=False)


# ================================================================== #
# aidiy_backup_check ツール（変更前/変更後ソースの一括抽出）
# ================================================================== #

@mcp_bc.tool()
async def backup_info() -> str:
    """バックアップルートの絶対パスと存在フラグを返す"""
    try:
        info = await asyncio.to_thread(bchk.backup_root_path)
    except BackupCheckError as e:
        raise ValueError(str(e)) from e
    return json.dumps(info, ensure_ascii=False)


@mcp_bc.tool()
async def backup_get_before_after(
    path: str,
    base_ts: Optional[str] = None,
) -> str:
    """
    指定ソースの現行版（after）と、直前のバックアップ版（before）を同時に返す。

    Args:
        path: プロジェクトルート相対のファイルパス（例: 'backend_server/core_main.py'）
        base_ts: 'YYYYMMDD_HHMMSS' 形式。指定時はこの日時より前のバックアップから before を探す
    """
    try:
        info = await asyncio.to_thread(bchk.get_before_after, path, base_ts)
    except BackupCheckError as e:
        raise ValueError(str(e)) from e
    return json.dumps(info, ensure_ascii=False)


@mcp_bc.tool()
async def backup_list_versions(path: str) -> str:
    """指定ファイルがバックアップに出現する全日時を新しい順で返す"""
    try:
        info = await asyncio.to_thread(bchk.list_versions, path)
    except BackupCheckError as e:
        raise ValueError(str(e)) from e
    return json.dumps(info, ensure_ascii=False)


@mcp_bc.tool()
async def backup_find_changed(
    from_ts: str,
    to_ts: Optional[str] = None,
) -> str:
    """
    指定期間のバックアップに含まれる相対パス一覧を返す（= 変更のあったファイル）。

    Args:
        from_ts: 'YYYYMMDD_HHMMSS' 形式の開始日時（必須）
        to_ts:   終了日時（任意）
    """
    try:
        info = await asyncio.to_thread(bchk.find_changed, from_ts, to_ts)
    except BackupCheckError as e:
        raise ValueError(str(e)) from e
    return json.dumps(info, ensure_ascii=False)


@mcp_bc.tool()
async def backup_diff_stats(
    path: str,
    base_ts: Optional[str] = None,
) -> str:
    """指定ファイルの before/after の追加・削除行数を軽量サマリで返す"""
    try:
        info = await asyncio.to_thread(bchk.diff_stats, path, base_ts)
    except BackupCheckError as e:
        raise ValueError(str(e)) from e
    return json.dumps(info, ensure_ascii=False)


# ================================================================== #
# aidiy_backup_save ツール（ネイティブ `バックアップ実行` を流用）
# ================================================================== #

@mcp_bs.tool()
async def backup_run() -> str:
    """
    AiDiy ネイティブの差分バックアップを実行する。
    初回は全件スナップショット（HHMMSS.all）、以降は差分のみ（HHMMSS）を保存。
    """
    try:
        info = await asyncio.to_thread(bsave.run)
    except BackupSaveError as e:
        raise ValueError(str(e)) from e
    return json.dumps(info, ensure_ascii=False)


@mcp_bs.tool()
async def backup_diff_scan() -> str:
    """
    バックアップを作成せず、現時点で差分対象となるファイル一覧のみ返す（dry-run）。
    """
    try:
        info = await asyncio.to_thread(bsave.diff_scan)
    except BackupSaveError as e:
        raise ValueError(str(e)) from e
    return json.dumps(info, ensure_ascii=False)


# ================================================================== #
# aidiy_image_generation ツール（AI 画像生成）
# ================================================================== #

@mcp_ig.tool()
async def generate_image(
    prompt: str,
    provider: str = "auto",
    model: str = "auto",
    size: str = "auto",
    quality: str = "auto",
    original_path: Optional[str] = None,
    save_path: Optional[str] = None,
) -> list:
    """
    AI で画像を生成する。

    Args:
        prompt: 生成プロンプト（例: "かわいい猫の画像"）
        provider: "auto"=freeai / "gemini"（gemini_key_id が必要） /
                  "freeai"（freeai_key_id が必要） / "openai"
        model:
          OpenAI: "auto"=gpt-image-2 / "gpt-image-2" / "gpt-image-1" / "dall-e-3"
          Gemini/FreeAI: "auto"=gemini-3.1-flash-image-preview /
                         "gemini-3.1-flash-image-preview" / "gemini-3-pro-image-preview" /
                         "gemini-2.5-flash-image"
        size:
          OpenAI: "auto"=1024x1024 / "1024x1024" / "1536x1024" / "1024x1536" / ...
          Gemini/FreeAI: "auto"=1024x1024 / "512x512" / "1024x1024" / "1920x1080" / "1080x1920"
        quality: OpenAI only — "auto"（モデル既定値） /
                 gpt-image-2: "low" / "medium" / "high" /
                 dall-e-3: "standard" / "hd"
        original_path: 参照画像のパス（省略可）
        save_path: 保存先。フォルダ指定なら yyyymmdd.hhmmss.png で保存。
                   ファイル指定なら指定ファイルに保存。省略時は backend_server/temp/output/ に保存。

    Note:
        MCP ツール経由のほか、HTTP POST でも同等の処理を呼び出せる。
        POST http://localhost:8095/imgGen
        Content-Type: application/json
        Body: {
            "prompt": "かわいい猫の画像",
            "provider": "auto",   # auto / openai / gemini / freeai
            "model": "auto",
            "size": "auto",       # 1024x1024 / 1920x1080 など
            "quality": "auto",    # OpenAI only: low / medium / high / standard / hd
            "original_path": null,
            "save_path": null
        }
        Response: image/png バイナリ
    """
    try:
        img, info = await asyncio.to_thread(
            ig.generate, prompt, provider, original_path,
            model=model, size=size, quality=quality,
        )

        # 保存先は ig.to_base64 が解決（save_path=None → DEFAULT_OUTPUT_DIR）
        data = await asyncio.to_thread(ig.to_base64, img, "png", 85, save_path)
        mime = "image/png"

        logger.info(
            f"generate_image: provider={info['provider']}  "
            f"model={info.get('model', '?')}  "
            f"size={img.size}  prompt={info['prompt'][:60]}  "
            f"save_path={save_path or '(default)'}"
        )

        return [ImageContent(type="image", data=data, mimeType=mime)]

    except ImageGenerationError as e:
        raise ValueError(str(e)) from e


# ================================================================== #
# aidiy_speech_to_text ツール（音声認識）
# ================================================================== #

@mcp_st.tool()
async def recognize_speech(
    base64_wav16k: Optional[str] = None,
    file_path: Optional[str] = None,
    provider: str = "auto",
    model: str = "auto",
) -> str:
    """
    音声データ（base64 WAV またはファイルパス）をテキストに変換する。

    Args:
        base64_wav16k: 16kHz モノラル WAV の base64 文字列（file_path と排他）
        file_path: WAV ファイルのパス（base64_wav16k と排他）
        provider: "auto"（speech_recognition、デフォルト） /
                  "openai"（AiDiy_key.json の openai_key_id が必要）
        model: "auto" のみ（デフォルト、openai 時は whisper-1）
    """
    try:
        result = await asyncio.to_thread(
            stt.recognize, base64_wav16k, file_path, provider, model
        )
        logger.info(
            f"recognize_speech: provider={result['provider']}  "
            f"model={result['model']}  "
            f"source={result.get('source', '?')}  "
            f"bytes={result['audio_bytes_length']}"
        )
        return json.dumps(result, ensure_ascii=False)

    except SpeechToTextError as e:
        raise ValueError(str(e)) from e


# ================================================================== #
# aidiy_text_to_speech ツール（テキスト音声合成）
# ================================================================== #

@mcp_ts.tool()
async def synthesize_speech(
    speech_text: str,
    language: str = "ja",
    provider: str = "auto",
    model: str = "auto",
    voice: str = "auto",
    ratio: Optional[float] = None,
    save_path: Optional[str] = None,
    local_play: bool = False,
) -> str:
    """
    テキストを音声（MP3/WAV）に変換する。

    Args:
        speech_text: 合成するテキスト
        language: 言語コード（デフォルト "ja"）
        provider: "auto"=edge→freeai /
                  "edge"（無料） / "gemini"（GEMINI_API_KEY） /
                  "freeai"（FREEAI_API_KEY） / "openai"（OPENAI_API_KEY）
                  フォールバック順: auto→edge→freeai / edge→freeai /
                  freeai→gemini→edge / gemini→freeai→edge / openai→edge
        model: "auto"（自動選択、デフォルト）
        voice: "auto"（= "female" として扱う）。"female" / "male" の指定も可:
               openai: female=marin / male=echo に内部変換。
                       直接指定 → alloy / ash / ballad / coral / echo / fable / nova /
                       onyx / sage / shimmer / verse / marin（既定） / cedar
               edge:   female / male を language に応じて
                       ja-JP-NanamiNeural / ja-JP-KeitaNeural などへ内部変換。
                       直接 ja-JP-NanamiNeural などの Microsoft Edge ニューラル音声名でも可。
               gemini/freeai: female=Zephyr（既定） / male=Charon に内部変換。
                       直接指定可能な voice（出典: Gemini TTS docs）:
                       female系 → Achernar / Aoede / Autonoe / Callirrhoe / Despina /
                                  Erinome / Gacrux / Kore / Laomedeia / Leda /
                                  Pulcherrima / Sulafat / Vindemiatrix / Zephyr
                       male系  → Achird / Algenib / Algieba / Alnilam / Charon /
                                  Enceladus / Fenrir / Iapetus / Orus / Puck /
                                  Rasalgethi / Sadachbia / Sadaltager / Schedar /
                                  Umbriel / Zubenelgenubi
        ratio: 話速倍率。None は既定値 1.2 として扱う。0 / 1 は速度調整なし。1.2 なら 20% 増し。
               有効レンジは 0.5..2.0 に clamp（範囲外は端で丸める）。
               edge は rate 文字列、openai は speed 引数、gemini/freeai は ffmpeg atempo で適用。
        save_path: 保存先。フォルダ指定なら yyyymmdd.hhmmss.<mp3|wav> で保存。
                   ファイル指定なら可能な限りその拡張子形式で出力（mp3↔wav は ffmpeg 自動変換）。
                   変換できない場合は実データの拡張子に差し替えて保存。
                   省略時は backend_server/temp/output/ に保存。
        local_play: True でローカル再生を試行（デフォルト False、速度は ratio 反映済み）

    Note:
        MCP ツール経由のほか、HTTP POST でも同等の処理を呼び出せる。
        POST http://localhost:8095/tts
        Content-Type: application/json
        Body: {
            "text": "...",        # speech_text に相当
            "language": "ja",
            "provider": "edge",
            "model": "auto",
            "voice": "female",
            "ratio": null,
            "save_path": null,    # 保存先（省略時は backend_server/temp/output/）
            "local_play": false   # True でサーバー側ローカル再生
        }
        Response: audio/mpeg バイナリ
    """
    try:
        audio_bytes, info = await asyncio.to_thread(
            tts.synthesize, speech_text, language, provider, model, voice, ratio
        )

        # 保存先は tts.to_base64 が解決（save_path=None → DEFAULT_OUTPUT_DIR）
        base64_audio = await asyncio.to_thread(tts.to_base64, audio_bytes, save_path)

        if local_play and audio_bytes:
            play_ok = await asyncio.to_thread(tts.play_mp3, audio_bytes)
            info["local_play_executed"] = play_ok

        logger.info(
            f"synthesize_speech: requested={info['requested_provider']}  "
            f"used={info['used_provider']}  "
            f"language={info['language']}  "
            f"ratio={info['ratio']}  "
            f"text_length={len(speech_text)}  "
            f"audio_format={info['audio_format']}  "
            f"audio_bytes={info['audio_bytes_length']}  "
            f"save_path={save_path or '(default)'}"
        )

        return json.dumps({
            **info,
            "base64_audio": base64_audio,
            "base64_mp3": base64_audio,  # backward compat
            "local_play": local_play,
        }, ensure_ascii=False)

    except TextToSpeechError as e:
        raise ValueError(str(e)) from e


# ================================================================== #
# aidiy_obs_studio_control ツール（OBS Studio WebSocket 制御）
# ================================================================== #
# OBS Studio は使用時に立ち上げられる前提のため、ツールは常時公開する。
# 起動時チェックは診断ログ目的のみで、各ツールは呼び出し時に都度接続を試みる。
# 接続情報は backend_server/_config/aidiy_obs_studio_control.json で管理。

@mcp_ob.tool()
async def obs_startup_status() -> str:
    """
    MCP 起動時に確認した OBS WebSocket 接続/認証の結果（スナップショット）を返す。
    実際の接続可否は呼び出し時に判定されるため、現在の状態を見たい場合は
    obs_connection_info を使うこと。
    """
    return json.dumps(obs.get_startup_status(), ensure_ascii=False)


@mcp_ob.tool()
async def obs_connection_info(
    host: Optional[str] = None,
    port: Optional[int] = None,
) -> str:
    """
    OBS Studio WebSocket へ接続し、バージョン情報を返す。

    省略時は backend_server/_config/aidiy_obs_studio_control.json の値を使う。
    """
    try:
        info = await obs.connection_info(host, port)
    except ObsStudioControlError as e:
        raise ValueError(str(e)) from e
    return json.dumps(info, ensure_ascii=False)


@mcp_ob.tool()
async def obs_status() -> str:
    """OBS Studio のバージョン、統計、配信、録画、現在シーンを返す。"""
    try:
        info = await obs.status()
    except ObsStudioControlError as e:
        raise ValueError(str(e)) from e
    return json.dumps(info, ensure_ascii=False)


@mcp_ob.tool()
async def obs_request(
    request_type: str,
    request_data: Optional[str] = None,
) -> str:
    """
    OBS WebSocket v5 の任意リクエストを実行する。

    Args:
        request_type: 例: GetVersion, GetSceneList, SetCurrentProgramScene
        request_data: JSON オブジェクト文字列。例: {"sceneName":"Scene"}
    """
    try:
        data = obs.parse_request_data(request_data)
        result = await obs.request(request_type, data)
    except ObsStudioControlError as e:
        raise ValueError(str(e)) from e
    return json.dumps(result, ensure_ascii=False)


@mcp_ob.tool()
async def obs_list_scenes() -> str:
    """OBS Studio のシーン一覧と現在シーンを返す。"""
    try:
        result = await obs.scene_list()
    except ObsStudioControlError as e:
        raise ValueError(str(e)) from e
    return json.dumps(result, ensure_ascii=False)


@mcp_ob.tool()
async def obs_set_current_scene(scene_name: str) -> str:
    """OBS Studio の現在シーンを切り替える。"""
    try:
        result = await obs.set_current_scene(scene_name)
    except ObsStudioControlError as e:
        raise ValueError(str(e)) from e
    return json.dumps(result, ensure_ascii=False)


@mcp_ob.tool()
async def obs_stream(action: str = "toggle") -> str:
    """配信を制御する。action: start / stop / toggle"""
    try:
        result = await obs.stream_control(action)
    except ObsStudioControlError as e:
        raise ValueError(str(e)) from e
    return json.dumps(result, ensure_ascii=False)


@mcp_ob.tool()
async def obs_record(action: str = "toggle") -> str:
    """録画を制御する。action: start / stop / toggle / pause / resume"""
    try:
        result = await obs.record_control(action)
    except ObsStudioControlError as e:
        raise ValueError(str(e)) from e
    return json.dumps(result, ensure_ascii=False)


@mcp_ob.tool()
async def obs_set_source_visible(
    scene_name: str,
    source_name: str,
    visible: bool,
) -> str:
    """指定シーン内のソース表示/非表示を切り替える。"""
    try:
        result = await obs.set_scene_item_enabled(scene_name, source_name, visible)
    except ObsStudioControlError as e:
        raise ValueError(str(e)) from e
    return json.dumps(result, ensure_ascii=False)


@mcp_ob.tool()
async def obs_set_input_mute(input_name: str, muted: bool) -> str:
    """音声入力をミュート/ミュート解除する。"""
    try:
        result = await obs.set_input_mute(input_name, muted)
    except ObsStudioControlError as e:
        raise ValueError(str(e)) from e
    return json.dumps(result, ensure_ascii=False)


# ================================================================== #
# aidiy_ffmpeg_control ツール（ffmpeg / ffprobe / ffplay）
# ================================================================== #
# 各ツールは args_str に ffmpeg 等の引数文字列を直接渡す。
# 実行ファイルパスや既定タイムアウトは
# backend_server/_config/aidiy_ffmpeg_control.json で管理する。
# 起動時の -version 確認に成功したバイナリのみツールを公開する。

@mcp_ff.tool()
async def ffmpeg_versions() -> str:
    """
    ffmpeg / ffprobe / ffplay の実行ファイルパスと起動時 -version 確認結果を返す。
    PATH 解決やバイナリ未配置の切り分けに使う。常時公開される診断ツール。
    """
    return json.dumps(ffmpeg_c.get_versions(), ensure_ascii=False)


if ffmpeg_c.version_info.get("ffmpeg", {}).get("ok"):
    @mcp_ff.tool()
    async def ffmpeg_run(args_str: str, timeout_sec: Optional[int] = None) -> str:
        """
        ffmpeg を実行する。args_str に ffmpeg の引数を文字列で渡す。

        Args:
            args_str: 例: '-y -i in.mp4 -c:v libx264 -c:a aac out.mp4'
                      '-i image.png -i narration.mp3 -t 10 -shortest out.mp4'
                      字幕焼き込み: '-i in.mp4 -vf subtitles=subs.srt out.mp4'
                      オーバーレイ: '-i base.mp4 -i logo.png -filter_complex overlay=10:10 out.mp4'
                      リサイズ: '-i in.mp4 -vf scale=1280:720 out.mp4'
            timeout_sec: タイムアウト秒。省略時は設定ファイルの default_timeout_sec を使う。

        Returns:
            {"command": [...], "returncode": int, "stdout": "...", "stderr": "...", "timeout_sec": ...}
        """
        try:
            result = await ffmpeg_c.run_ffmpeg(args_str, timeout_sec)
        except FfmpegControlError as e:
            raise ValueError(str(e)) from e
        return json.dumps(result, ensure_ascii=False)


if ffmpeg_c.version_info.get("ffprobe", {}).get("ok"):
    @mcp_ff.tool()
    async def ffprobe_run(args_str: str, timeout_sec: Optional[int] = None) -> str:
        """
        ffprobe を実行する。args_str に ffprobe の引数を文字列で渡す。

        Args:
            args_str: 例: '-v error -print_format json -show_format -show_streams in.mp4'
                      '-i in.mp4'  （標準的な情報表示）
            timeout_sec: タイムアウト秒。省略時は設定ファイルの default_timeout_sec を使う。
        """
        try:
            result = await ffmpeg_c.run_ffprobe(args_str, timeout_sec)
        except FfmpegControlError as e:
            raise ValueError(str(e)) from e
        return json.dumps(result, ensure_ascii=False)


if ffmpeg_c.version_info.get("ffprobe", {}).get("ok"):
    @mcp_ff.tool()
    async def get_media_duration(
        input_path: str,
        timeout_sec: Optional[int] = None,
    ) -> str:
        """
        メディアファイル（MP3 / MP4 / WAV など）の再生時間を ffprobe で取得する。
        ナレーション音声の実尺確認や scenario.js の duration_sec 更新に使う。

        Args:
            input_path: 対象ファイルの絶対パス。
            timeout_sec: ffprobe のタイムアウト秒。省略時は設定ファイルの値を使う。

        Returns:
            {"input_path": str, "duration_sec": float, "size_bytes": int}
        """
        try:
            result = await ffmpeg_c.get_media_duration(input_path, timeout_sec=timeout_sec)
        except FfmpegControlError as e:
            raise ValueError(str(e)) from e
        return json.dumps(result, ensure_ascii=False)


if ffmpeg_c.version_info.get("ffmpeg", {}).get("ok"):
    @mcp_ff.tool()
    async def ffmpeg_analyze_audio_timerange(
        input_path: str,
        threshold_db: float = -40.0,
        window_ms: float = 100.0,
        sample_rate: int = 8000,
        padding_sec: float = 2.0,
        timeout_sec: Optional[int] = None,
    ) -> str:
        """
        入力ファイル（動画/音声）を 16bit mono PCM (WAV 相当) に変換し、
        RMS 信号強度で「最初の発話開始秒（audio_start_sec）」と
        「最後の発話終了秒（audio_end_sec）」を検出する。
        前後 padding_sec の余白を付けた推奨トリム値（trim_start_sec / trim_end_sec）も返すので、
        その値を ffmpeg_trim にそのまま渡せば自動で余白付きトリムができる。

        Args:
            input_path: 解析対象ファイルの絶対パス。
            threshold_db: dBFS 閾値。これを超えるウィンドウを発話ありと判定（既定 -40 dB）。
            window_ms: RMS 計算のウィンドウ長（既定 100 ms）。
            sample_rate: 解析用サンプリングレート Hz（既定 8000）。
            padding_sec: 検出位置の前後に付ける余白秒（既定 2.0 秒）。
            timeout_sec: ffmpeg のタイムアウト秒。

        Returns:
            duration_sec / audio_start_sec / audio_end_sec /
            trim_start_sec / trim_end_sec / max_rms_db ほか。
            発話が検出できなかった場合は audio_start_sec / audio_end_sec が null。
        """
        try:
            result = await ffmpeg_c.analyze_audio_timerange(
                input_path,
                threshold_db=threshold_db,
                window_ms=window_ms,
                sample_rate=sample_rate,
                padding_sec=padding_sec,
                timeout_sec=timeout_sec,
            )
        except FfmpegControlError as e:
            raise ValueError(str(e)) from e
        return json.dumps(result, ensure_ascii=False)


    @mcp_ff.tool()
    async def video_trimming(
        input_path: str,
        start_sec: float,
        end_sec: float,
        output_path: str,
        timeout_sec: Optional[int] = None,
    ) -> str:
        """
        input_path の [start_sec, end_sec] 区間を output_path に再エンコードで切り出す。
        H.264 (libx264 CRF 20) + AAC 192kbps + +faststart の Web 配信向け既定値を使う。
        ffmpeg_analyze_audio_timerange の戻り値 trim_start_sec / trim_end_sec を
        そのまま渡せば、余白付き自動トリムが完了する。

        Args:
            input_path: 入力ファイルの絶対パス。
            start_sec: 切り出し開始秒（0 以上）。
            end_sec: 切り出し終了秒（start_sec より大）。
            output_path: 出力ファイルの絶対パス。親ディレクトリは自動作成。
            timeout_sec: ffmpeg のタイムアウト秒。

        Returns:
            input_path / output_path / start_sec / end_sec / duration_sec /
            returncode / command / output_size_bytes。
        """
        try:
            result = await ffmpeg_c.video_trimming(
                input_path,
                start_sec,
                end_sec,
                output_path,
                timeout_sec=timeout_sec,
            )
        except FfmpegControlError as e:
            raise ValueError(str(e)) from e
        return json.dumps(result, ensure_ascii=False)


if ffmpeg_c.version_info.get("ffplay", {}).get("ok"):
    @mcp_ff.tool()
    async def ffplay_run(args_str: str, timeout_sec: Optional[int] = None) -> str:
        """
        ffplay を実行する。args_str に ffplay の引数を文字列で渡す。

        プレイモード（プレビュー再生）。ffplay はウィンドウを開く対話アプリのため、
        呼び出し側で `-autoexit` と `-t <秒>` を付けて自然終了させること。
        そうしない場合は timeout_sec で強制終了される。

        Args:
            args_str: 例: '-autoexit -t 10 in.mp4'
                      '-autoexit -nodisp narration.mp3'  （音声のみ）
                      '-autoexit -window_title preview -x 640 -y 360 in.mp4'
            timeout_sec: タイムアウト秒。省略時は設定ファイルの default_play_timeout_sec を使う。
        """
        try:
            result = await ffmpeg_c.run_ffplay(args_str, timeout_sec)
        except FfmpegControlError as e:
            raise ValueError(str(e)) from e
        return json.dumps(result, ensure_ascii=False)


# 公開ツール一覧をログに残す
_ff_exposed = sorted(mcp_ff._tool_manager._tools.keys())
_ff_skipped = [
    label for label in ("ffmpeg", "ffprobe", "ffplay")
    if not ffmpeg_c.version_info.get(label, {}).get("ok")
]
logger.info(f"aidiy_ffmpeg_control 公開ツール: {_ff_exposed}")
if _ff_skipped:
    logger.warning(
        f"aidiy_ffmpeg_control 非公開（-version 失敗）: {_ff_skipped} — "
        f"backend_server/_config/aidiy_ffmpeg_control.json のパスを確認してください"
    )


# ------------------------------------------------------------------ #
# description 動的生成（API キー状況に応じて利用可能 provider を明示）
# ------------------------------------------------------------------ #

mcp_ts._tool_manager._tools["synthesize_speech"].description = tts.get_description()

# ================================================================== #
# アプリ（複数 MCP サーバーを 1 ポートで統合）
# ================================================================== #

async def _handle_root(request: Request) -> Response:
    return Response('{"message": "MCP Server is running"}', media_type="application/json")


async def _handle_img_gen(request: Request) -> Response:
    """
    REST HTTP エンドポイント: POST /imgGen
    ブラウザから aidiy_image_generation 相当の画像生成を呼び出すためのシンプルな HTTP API。
    Body: {"prompt": "...", "provider": "auto", "model": "auto", "size": "auto", "quality": "auto",
           "original_path": null, "save_path": null}
    Response: image/png バイナリ
    """
    if request.method == "OPTIONS":
        return Response(
            "",
            status_code=204,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
            },
        )

    try:
        body = await request.json()
    except Exception:
        body = {}

    prompt = body.get("prompt", "").strip()
    if not prompt:
        return Response(
            json.dumps({"error": "prompt is required"}, ensure_ascii=False),
            status_code=400,
            media_type="application/json",
        )

    provider     = body.get("provider", "auto")
    model        = body.get("model", "auto")
    size         = body.get("size", "auto")
    quality      = body.get("quality", "auto")
    original_path = body.get("original_path", None)
    save_path    = body.get("save_path", None)

    try:
        img, info = await asyncio.to_thread(
            ig.generate, prompt, provider, original_path,
            model=model, size=size, quality=quality,
        )
        base64_data = await asyncio.to_thread(ig.to_base64, img, "png", 85, save_path)
        import base64 as _b64
        png_bytes = _b64.b64decode(base64_data)
        logger.info(
            f"_handle_img_gen: provider={info['provider']} model={info.get('model','?')} "
            f"size={img.size} prompt={info['prompt'][:60]}"
        )
        return Response(
            png_bytes,
            media_type="image/png",
            headers={
                "Access-Control-Allow-Origin": "*",
                "X-AiDiy-MCP-Tool": "aidiy_image_generation.generate_image",
                "X-AiDiy-Provider": info.get("provider", ""),
                "X-AiDiy-Model": info.get("model", ""),
            },
        )
    except Exception as e:
        logger.warning(f"_handle_img_gen error: {e}")
        return Response(
            json.dumps({"error": str(e)}, ensure_ascii=False),
            status_code=500,
            media_type="application/json",
        )


async def _handle_tts(request: Request) -> Response:
    """
    REST HTTP エンドポイント: POST /tts
    ブラウザから aidiy_text_to_speech 相当の TTS を呼び出すためのシンプルな HTTP API。
    Body: {"text": "...", "speech_text": "...", "language": "ja", "provider": "edge", "voice": "female",
           "ratio": null, "save_path": null, "local_play": false}
    Response: audio/mpeg バイナリ
    """
    if request.method == "OPTIONS":
        return Response(
            "",
            status_code=204,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
            },
        )

    try:
        body = await request.json()
    except Exception:
        body = {}

    text = body.get("text") or body.get("speech_text", "")
    language = body.get("language", "ja")
    provider = body.get("provider", "edge")
    model = body.get("model", "auto")
    voice = body.get("voice", "female")
    ratio      = body.get("ratio", None)
    save_path  = body.get("save_path", None)
    local_play = bool(body.get("local_play", False))

    if not text:
        return Response(
            json.dumps({"error": "text is required"}, ensure_ascii=False),
            status_code=400,
            media_type="application/json",
        )

    try:
        audio_bytes, info = await asyncio.to_thread(
            tts.synthesize, text, language, provider, model, voice, ratio
        )
        # 保存先は tts.to_base64 が解決（save_path=None → DEFAULT_OUTPUT_DIR）
        await asyncio.to_thread(tts.to_base64, audio_bytes, save_path)
        logger.info(
            f"_handle_tts: provider={info.get('used_provider')} voice={info.get('voice')} "
            f"bytes={info.get('audio_bytes_length')} text_len={len(text)} "
            f"save_path={save_path or '(default)'}"
        )
        if local_play and audio_bytes:
            play_ok = await asyncio.to_thread(tts.play_mp3, audio_bytes)
            info["local_play_executed"] = play_ok

        # Starlette Response は bytearray を受け付けないため bytes に正規化
        if isinstance(audio_bytes, (bytearray, memoryview)):
            audio_bytes = bytes(audio_bytes)
        return Response(
            audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Access-Control-Allow-Origin": "*",
                "X-AiDiy-MCP-Tool": "aidiy_text_to_speech.synthesize_speech",
            },
        )
    except Exception as e:
        logger.warning(f"_handle_tts error: {e}")
        return Response(
            json.dumps({"error": str(e)}, ensure_ascii=False),
            status_code=500,
            media_type="application/json",
        )


app = Starlette(routes=[
    Route("/", _handle_root, methods=["GET"]),
    Route("/imgGen", _handle_img_gen, methods=["POST", "OPTIONS"]),
    Route("/tts", _handle_tts, methods=["POST", "OPTIONS"]),
    *mcp.sse_app().routes,
    *mcp_dc.sse_app().routes,
    *mcp_sq.sse_app().routes,
    *mcp_pg.sse_app().routes,
    *mcp_lg.sse_app().routes,
    *mcp_cc.sse_app().routes,
    *mcp_bc.sse_app().routes,
    *mcp_bs.sse_app().routes,
    *mcp_ig.sse_app().routes,
    *mcp_st.sse_app().routes,
    *mcp_ts.sse_app().routes,
    *mcp_ob.sse_app().routes,
    *mcp_ff.sse_app().routes,
])

if __name__ == "__main__":
    logger.info(f"Chrome SSE         : http://localhost:{MCP_PORT}{MOUNT}/sse")
    logger.info(f"DesktopCapture SSE : http://localhost:{MCP_PORT}{MOUNT_DC}/sse")
    logger.info(f"Sqlite SSE         : http://localhost:{MCP_PORT}{MOUNT_SQ}/sse")
    logger.info(f"Postgres SSE       : http://localhost:{MCP_PORT}{MOUNT_PG}/sse"
                + (" [psycopg 未導入]" if _pg_init_error else ""))
    logger.info(f"Logs SSE           : http://localhost:{MCP_PORT}{MOUNT_LG}/sse")
    logger.info(f"CodeCheck SSE      : http://localhost:{MCP_PORT}{MOUNT_CC}/sse")
    logger.info(f"BackupCheck SSE    : http://localhost:{MCP_PORT}{MOUNT_BC}/sse")
    logger.info(f"BackupSave SSE     : http://localhost:{MCP_PORT}{MOUNT_BS}/sse")
    logger.info(f"ImageGeneration SSE: http://localhost:{MCP_PORT}{MOUNT_IG}/sse")
    logger.info(f"ImageGeneration HTTP: http://localhost:{MCP_PORT}/imgGen  [POST]")
    logger.info(f"SpeechToText SSE   : http://localhost:{MCP_PORT}{MOUNT_ST}/sse")
    logger.info(f"TextToSpeech SSE   : http://localhost:{MCP_PORT}{MOUNT_TS}/sse")
    logger.info(f"ObsStudioControl SSE: http://localhost:{MCP_PORT}{MOUNT_OB}/sse")
    logger.info(f"FfmpegControl SSE  : http://localhost:{MCP_PORT}{MOUNT_FF}/sse")
    uvicorn.run(app, host="0.0.0.0", port=MCP_PORT, log_level="warning")
