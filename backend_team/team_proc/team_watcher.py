# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""Aチーム作業の監視ループとプロセス管理。

- 5秒間隔でチーム作業を確認し、投入待ち（準備開始・未投入）を見つけたら
  temp/input/<作業ID>.json を出力して sub_init.py を subprocess 起動する。
  起動時に準備中へ進め、PID・開始日時・実行回数を記録する。
- 開始日時だけが入ったまま実行タイムアウト分以上経過した作業は、プロセスを
  強制停止してエラーにする。
- システム開始時（再起動含む）は、テーブルに残った PID のプロセスを強制停止して
  未投入の作業を準備開始へ戻す。
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path

from . import team_work_db

監視間隔秒 = 5
実行回数上限 = 3

_BASE_DIR = Path(__file__).resolve().parents[1]
_SUB_INITパス = _BASE_DIR / "sub_init.py"
_入力DIR = _BASE_DIR / "temp" / "input"


def _安全ファイル名部品(値: str) -> str:
    return re.sub(r"[^0-9A-Za-z_.\-぀-ヿ㐀-鿿]", "_", 値)


def _入力パス(作業ID: str) -> Path:
    return _入力DIR / f"{_安全ファイル名部品(作業ID)}.json"


def _プロセス強制停止(pid: int, logger: logging.Logger) -> None:
    """PID のプロセスを強制停止する。python 以外は誤爆防止のため停止しない。"""
    try:
        if os.name == "nt":
            確認 = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if f'"{pid}"' not in 確認.stdout:
                return
            if "python" not in 確認.stdout.lower():
                logger.warning(f"PID {pid} はpythonプロセスではないため停止しません")
                return
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                capture_output=True,
                timeout=15,
            )
        else:
            import signal

            os.kill(pid, signal.SIGKILL)
        logger.info(f"残存sub_initを停止しました: PID={pid}")
    except ProcessLookupError:
        pass
    except Exception as e:
        logger.warning(f"PID {pid} の停止に失敗しました: {e}")


def 起動時クリーンアップ(logger: logging.Logger) -> None:
    """再起動前から残るsub_initを停止し、未投入作業を準備開始へ戻す。"""
    try:
        残存 = team_work_db.残存PID一覧()
        for 行 in 残存:
            pid = str(行.get("PID", "")).strip()
            if pid.isdigit():
                _プロセス強制停止(int(pid), logger)
        更新件数 = team_work_db.PID全クリア()
        if 更新件数:
            logger.info(f"残存作業プロセスを{更新件数}件準備開始へ戻しました")
    except Exception:
        logger.exception("チーム作業の起動時クリーンアップに失敗しました")


def _作業実行開始(行: dict, logger: logging.Logger) -> None:
    """投入待ち作業 1 件について入力 JSON を出力し、sub_init.py を起動して PID を記録する。"""
    作業ID = str(行["作業ID"])
    if not team_work_db.作業確保(作業ID):
        return
    if int(行.get("実行回数", 0) or 0) >= 実行回数上限:
        team_work_db.投入失敗記録(作業ID, f"実行回数が上限({実行回数上限}回)に達しました")
        logger.warning(f"実行回数上限のため失敗にしました: {作業ID}")
        return

    try:
        _入力DIR.mkdir(parents=True, exist_ok=True)
        入力パス = _入力パス(作業ID)
        with 入力パス.open("w", encoding="utf-8") as f:
            json.dump(
                {
                    "要員ID": str(行.get("要員ID", "")),
                    "作業ID": 作業ID,
                    "プロジェクト": str(行.get("プロジェクト", "")),
                    "要求内容": str(行.get("要求内容", "")),
                    "TASK_AI_NAME": str(行.get("TASK_AI_NAME", "claude_cli")),
                    "TASK_AI_MODEL": str(行.get("TASK_AI_MODEL", "auto")),
                    "実行有効": int(行.get("実行有効", 1) or 0),
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        proc = subprocess.Popen(
            [sys.executable, str(_SUB_INITパス), str(入力パス)],
            cwd=str(_BASE_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
        )
        team_work_db.実行開始記録(作業ID, proc.pid)
        logger.info(f"チーム作業のタスク投入を開始しました: {作業ID} PID={proc.pid}")
    except Exception as e:
        team_work_db.投入失敗記録(作業ID, f"sub_init起動エラー: {e}")
        logger.exception(f"チーム作業sub_initの起動に失敗しました: {作業ID}")


def _監視1回(logger: logging.Logger) -> None:
    # --- 開始日時だけが入ったまま実行タイムアウト分以上経過 → 状態=エラー・実行有効=0 ---
    try:
        タイムアウト対象 = team_work_db.作業タイムアウト対象一覧(team_work_db.実行タイムアウト分)
        for 行 in タイムアウト対象:
            pid = str(行.get("PID", "")).strip()
            logger.warning(
                f"実行タイムアウト({team_work_db.実行タイムアウト分}分)のためキャンセルします: "
                f"{行.get('作業ID', '')} (要員ID={行.get('要員ID', '')}) "
                f"開始日時={行.get('開始日時', '')} PID={pid}"
            )
            if pid.isdigit():
                _プロセス強制停止(int(pid), logger)
        if タイムアウト対象:
            更新件数 = team_work_db.作業タイムアウト対象エラー化(タイムアウト対象)
            logger.warning(f"実行タイムアウト対象をエラーにしました: {更新件数} 件")
    except Exception:
        logger.exception("実行タイムアウト処理でエラーが発生しました")

    # --- 投入待ち（準備開始・未投入）→ 準備中 + sub_init.pyでAIタスク投入 ---
    for 行 in team_work_db.投入待ち一覧():
        _作業実行開始(行, logger)


async def 監視ループ(logger: logging.Logger) -> None:
    logger.info(f"チーム作業監視ループを開始しました (interval={監視間隔秒}s)")
    while True:
        try:
            await asyncio.to_thread(_監視1回, logger)
        except Exception:
            logger.exception("チーム作業監視ループでエラーが発生しました")
        await asyncio.sleep(監視間隔秒)
