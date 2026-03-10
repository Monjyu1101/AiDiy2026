# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101
# -------------------------------------------------------------------------

from __future__ import annotations

import argparse
import faulthandler
import logging
import sys
from pathlib import Path

from GUI制御 import DesktopGuiApp
from 通信制御 import LoginDialog
from log_config import get_current_log_path, get_logger, setup_logging
from util import AuthSession, GuiSettings

_CRASH_LOG_HANDLE = None


def 引数を解析() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AiDiy desktop GUI")
    parser.add_argument(
        "--settings",
        type=Path,
        default=Path(__file__).with_name("settings.json"),
        help="settings json path",
    )
    parser.add_argument(
        "--check-assets",
        action="store_true",
        help="resolve assets and print summary without starting the UI",
    )
    parser.add_argument(
        "--demo-seconds",
        type=float,
        default=None,
        help="auto close after N seconds",
    )
    parser.add_argument(
        "--skip-login",
        action="store_true",
        help="start GUI without authentication dialog",
    )
    parser.add_argument(
        "--skip-core-connect",
        action="store_true",
        help="start GUI without AI core websocket connections",
    )
    return parser.parse_args()


def ネイティブクラッシュログを有効化(script_dir: Path) -> None:
    global _CRASH_LOG_HANDLE
    crash_log_path = get_current_log_path() or (script_dir / "temp" / "logs" / "frontend_gui.crash.log")
    crash_log_path.parent.mkdir(parents=True, exist_ok=True)
    _CRASH_LOG_HANDLE = crash_log_path.open("a", encoding="utf-8")
    _CRASH_LOG_HANDLE.write("\n=== frontend_gui start ===\n")
    _CRASH_LOG_HANDLE.flush()
    faulthandler.enable(file=_CRASH_LOG_HANDLE, all_threads=True)


def 例外ログを有効化() -> None:
    logger = get_logger("frontend_gui")

    def _handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.exception("未処理例外が発生しました", exc_info=(exc_type, exc_value, exc_traceback))

    def _handle_thread_exception(args):
        logger.exception(
            "スレッド例外が発生しました",
            exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
        )

    sys.excepthook = _handle_exception
    if hasattr(__import__("threading"), "excepthook"):
        __import__("threading").excepthook = _handle_thread_exception


def 起動() -> int:
    args = 引数を解析()
    script_dir = Path(__file__).resolve().parent
    setup_logging("frontend_gui")
    例外ログを有効化()
    ネイティブクラッシュログを有効化(script_dir)
    logger = get_logger("frontend_gui.main")
    logger.info("frontend_gui を起動します")
    settings = GuiSettings.読み込み(args.settings)

    if args.check_assets:
        logger.info("アセット確認モードで起動しました")
        print(f"settings={args.settings}")
        return 0

    if args.skip_login:
        auth_session = AuthSession(user_id="skip-login", access_token="", token_type="bearer")
        logger.info("ログインスキップで起動します")
    else:
        auth_session = LoginDialog(settings).表示()
        if auth_session is None:
            logger.info("ログインがキャンセルされました")
            return 1

    try:
        app = DesktopGuiApp(
            settings=settings,
            auth_session=auth_session,
            demo_seconds=args.demo_seconds,
            skip_core_connect=args.skip_core_connect,
        )
    except FileNotFoundError as exc:
        logger.error("起動に必要なファイルが見つかりません: %s", exc)
        print(str(exc), file=sys.stderr)
        return 1
    app.実行()
    logger.info("frontend_gui は正常終了しました")
    return 0


if __name__ == "__main__":
    raise SystemExit(起動())
