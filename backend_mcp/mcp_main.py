# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
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

chrome   = ChromeManager(debug_port=CHROME_PORT)
cdp      = CDPClient(port=CHROME_PORT)
capture  = DesktopCapture()
sqlite_q = SqliteQuery()
log_t    = LogTailer()
checker  = CodeChecker()
bchk     = BackupCheck()
bsave    = BackupSave()

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

async def _ensure_chrome():
    """Chrome が起動していなければ自動起動する"""
    if not chrome.is_running():
        await asyncio.to_thread(chrome.ensure_running)

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


# ナビゲーション

@mcp.tool()
async def navigate(url: str, tab_id: Optional[str] = None) -> str:
    """指定URLへ移動する"""
    await _ensure_chrome()
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
    data = await cdp.screenshot(tab_id=tab_id, full_page=full_page)

    if save_path:
        raw = base64.b64decode(data)
        if os.path.isdir(save_path) or save_path.endswith(("/", "\\")):
            os.makedirs(save_path, exist_ok=True)
            fname = datetime.now().strftime("%Y%m%d.%H%M%S") + ".png"
            dest = os.path.join(save_path, fname)
        else:
            os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
            dest = save_path
        with open(dest, "wb") as f:
            f.write(raw)
        logger.info(f"screenshot saved: {dest}")

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
async def new_tab(url: str = "about:blank") -> str:
    """新規タブを開く"""
    await _ensure_chrome()
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
    parsed_params = json.loads(params) if params else {}
    if tab_id == "browser":
        ws_url = await asyncio.to_thread(cdp.get_browser_ws_url)
    else:
        tab = await asyncio.to_thread(cdp.resolve_tab, tab_id)
        ws_url = cdp.get_ws_url(tab)
    result = await cdp.send_command(ws_url, method, parsed_params)
    return json.dumps(result, ensure_ascii=False)

# ------------------------------------------------------------------ #
# 旧 chrome-devtools-mcp (Node.js版) との互換エイリアス
# AIが旧ツール名を使う場合に対応
# ------------------------------------------------------------------ #

@mcp.tool()
async def new_page(url: str = "about:blank") -> str:
    """新規タブを開く（new_tab の別名）"""
    return await new_tab(url)

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
                   ファイル指定なら指定ファイルに保存。省略時は保存しない。
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

        data = await asyncio.to_thread(capture.to_bytes, img, format, quality)
        b64  = base64.b64encode(data).decode("ascii")
        mime = "image/jpeg" if format.lower() in ("jpeg", "jpg") else "image/png"

        logger.info(
            f"screenshot: mode={'window' if window_title else 'region' if x is not None else 'cursor' if size else 'screen'}"
            f"  size={img.size}  format={format}"
        )

        if save_path:
            # フォルダかどうか判定
            if os.path.isdir(save_path) or save_path.endswith(("/", "\\")):
                os.makedirs(save_path, exist_ok=True)
                fname = datetime.now().strftime("%Y%m%d.%H%M%S") + ".png"
                dest = os.path.join(save_path, fname)
            else:
                os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
                dest = save_path
            with open(dest, "wb") as f:
                f.write(data)
            logger.info(f"screenshot saved: {dest}")

        return [ImageContent(type="image", data=b64, mimeType=mime)]

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
# アプリ（複数 MCP サーバーを 1 ポートで統合）
# ================================================================== #

async def _handle_root(request: Request) -> Response:
    return Response('{"message": "MCP Server is running"}', media_type="application/json")

app = Starlette(routes=[
    Route("/", _handle_root, methods=["GET"]),
    *mcp.sse_app().routes,
    *mcp_dc.sse_app().routes,
    *mcp_sq.sse_app().routes,
    *mcp_pg.sse_app().routes,
    *mcp_lg.sse_app().routes,
    *mcp_cc.sse_app().routes,
    *mcp_bc.sse_app().routes,
    *mcp_bs.sse_app().routes,
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
    uvicorn.run(app, host="0.0.0.0", port=MCP_PORT, log_level="warning")
