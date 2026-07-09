# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""AIタスクの監視ループとプロセス管理。

- 5 秒間隔でタスク要求を確認し、PID 未設定の仮登録（準備中）を見つけたら
  temp/input/<利用者ID>.<タスクID>.json を出力して sub_init.py を subprocess 起動する。
  起動時に PID・開始日時・実行回数+1 を記録する。
- システム開始時（再起動含む）は、テーブルに残った PID のプロセスを強制停止して
  PID をクリアする（クリア後は監視ループが自動で再実行する）。
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
import sys

from . import tasks_db

監視間隔秒 = 5
実行回数上限 = 3
実行タイムアウト分 = 30

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SUB_INITパス = os.path.join(_BASE_DIR, "sub_init.py")
_SUB_STARTパス = os.path.join(_BASE_DIR, "sub_start.py")
_SUB_PROCパス = os.path.join(_BASE_DIR, "sub_proc.py")
_SUB_TERMINATEパス = os.path.join(_BASE_DIR, "sub_terminate.py")
_入力DIR = os.path.join(_BASE_DIR, "temp", "input")
_出力DIR = os.path.join(_BASE_DIR, "temp", "output")


def _タスクファイル名(利用者ID: str, タスクID: str) -> str:
    return f"{利用者ID}.{タスクID}.json"


def _プロセス強制停止(pid: int, logger: logging.Logger) -> None:
    """PID のプロセスを子プロセスごと強制停止する。python 以外は誤爆防止のため停止しない。"""
    try:
        if os.name == "nt":
            確認 = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                capture_output=True, text=True, timeout=15,
            )
            if f'"{pid}"' not in 確認.stdout:
                return  # 既に存在しない
            if "python" not in 確認.stdout.lower():
                logger.warning(f"PID {pid} は python プロセスではないため停止しません")
                return
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                           capture_output=True, timeout=15)
            logger.info(f"残存プロセスを強制停止しました: PID={pid}")
        else:
            import signal
            os.kill(pid, signal.SIGKILL)
            logger.info(f"残存プロセスを強制停止しました: PID={pid}")
    except ProcessLookupError:
        pass
    except Exception as e:
        logger.warning(f"PID {pid} の停止に失敗しました: {e}")


def 起動時クリーンアップ(logger: logging.Logger) -> None:
    """システム開始時: テーブルに残った PID を強制停止してクリアする。"""
    try:
        残存 = tasks_db.残存PID一覧()
        for 行 in 残存:
            pid = str(行.get("PID", "")).strip()
            if pid.isdigit():
                logger.info(f"起動時クリーンアップ: {行['テーブル']} {行.get('利用者ID', '')}/{行['タスクID']} PID={pid}")
                _プロセス強制停止(int(pid), logger)
        if 残存:
            tasks_db.PID全クリア()
            logger.info(f"PID を {len(残存)} 件クリアしました（監視ループが再実行します）")
    except Exception:
        logger.exception("起動時クリーンアップでエラーが発生しました")


def _タスク実行開始(行: dict, logger: logging.Logger) -> None:
    """仮登録 1 件について入力 JSON を出力し、sub_init.py を起動して PID を記録する。"""
    利用者ID = str(行["利用者ID"])
    タスクID = str(行["タスクID"])
    os.makedirs(_入力DIR, exist_ok=True)
    入力JSONパス = os.path.join(_入力DIR, _タスクファイル名(利用者ID, タスクID))
    with open(入力JSONパス, "w", encoding="utf-8") as f:
        json.dump({
            "利用者ID": 利用者ID,
            "タスクID": タスクID,
            "プロジェクト": str(行.get("プロジェクト", "")),
            "要求内容": str(行.get("要求内容", "")),
            "TASK_AI_NAME": str(行.get("TASK_AI_NAME", "claude_cli")),
            "TASK_AI_MODEL": str(行.get("TASK_AI_MODEL", "auto")),
        }, f, ensure_ascii=False, indent=2)

    creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    proc = subprocess.Popen(
        [sys.executable, _SUB_INITパス, 入力JSONパス],
        cwd=_BASE_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags,
    )
    tasks_db.実行開始記録(利用者ID, タスクID, proc.pid)
    logger.info(f"AIタスク生成を開始しました: {利用者ID}/{タスクID} PID={proc.pid}")


def _明細実行開始(行: dict, 出力JSONパス: str, logger: logging.Logger) -> None:
    """実行可能なタスク明細 1 件についてサブプロセスを起動して PID を記録する。"""
    利用者ID = str(行["利用者ID"])
    タスクID = str(行["タスクID"])
    明細SEQ = int(行["明細SEQ"])
    タイトル = str(行.get("タイトル", ""))
    if タイトル == "開始":
        サブプロセスパス = _SUB_STARTパス
    elif タイトル == "終了":
        サブプロセスパス = _SUB_TERMINATEパス
    else:
        サブプロセスパス = _SUB_PROCパス
    creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    proc = subprocess.Popen(
        [sys.executable, サブプロセスパス, 出力JSONパス, str(明細SEQ)],
        cwd=_BASE_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags,
    )
    tasks_db.明細実行開始記録(利用者ID, タスクID, 明細SEQ, proc.pid)
    logger.info(f"ステップ実行を開始しました: {利用者ID}/{タスクID} SEQ={明細SEQ} タイトル={タイトル} PID={proc.pid}")


def _軽量並行明細か(行: dict) -> bool:
    """code agent を使わず短時間で完了する明細は並行起動を許可する。"""
    タイトル = str(行.get("タイトル", ""))
    return "通知音" in タイトル


def _監視1回(logger: logging.Logger) -> None:
    # --- 開始日時だけが入ったまま実行タイムアウト分以上経過 → 状態=エラー・実行有効=0 ---
    try:
        タイムアウト対象 = tasks_db.タイムアウト対象一覧(実行タイムアウト分)
        for 行 in タイムアウト対象:
            pid = str(行.get("PID", "")).strip()
            logger.warning(
                f"実行タイムアウト({実行タイムアウト分}分)のためキャンセルします: "
                f"{行['テーブル']} {行.get('利用者ID', '')}/{行.get('タスクID', '')} "
                f"SEQ={行.get('明細SEQ', '')} 開始日時={行.get('開始日時', '')} PID={pid}"
            )
            if pid.isdigit():
                _プロセス強制停止(int(pid), logger)
        if タイムアウト対象:
            更新件数 = tasks_db.タイムアウト対象エラー化(タイムアウト対象)
            logger.warning(f"実行タイムアウト対象をエラーにしました: {更新件数} 件")
    except Exception:
        logger.exception("実行タイムアウト処理でエラーが発生しました")

    # --- 仮登録（準備中・PID なし）→ sub_init.py で AI タスク分解 ---
    for 行 in tasks_db.実行待ち一覧():
        利用者ID = str(行["利用者ID"])
        タスクID = str(行["タスクID"])
        try:
            if int(行.get("実行回数", 0) or 0) >= 実行回数上限:
                tasks_db.タスク失敗(利用者ID, タスクID, f"実行回数が上限({実行回数上限}回)に達しました")
                logger.warning(f"実行回数上限のため失敗にしました: {利用者ID}/{タスクID}")
                continue
            _タスク実行開始(行, logger)
        except Exception as e:
            logger.exception(f"タスク実行開始に失敗しました: {利用者ID}/{タスクID}")
            try:
                tasks_db.タスク失敗(利用者ID, タスクID, f"実行開始エラー: {e}")
            except Exception:
                logger.exception(f"失敗登録もエラー: {利用者ID}/{タスクID}")

    # --- 未実行のタスク明細（先行完了済み）→ sub_proc.py で 1 ステップ実行 ---
    # code agent 系は 1 明細まで。通知音などの軽量明細は依存関係が許せば同時起動する。
    code_agent実行中 = any(not _軽量並行明細か(行) for 行 in tasks_db.実行中明細一覧())
    for 行 in tasks_db.実行待ち明細一覧():
        利用者ID = str(行["利用者ID"])
        タスクID = str(行["タスクID"])
        明細SEQ = int(行["明細SEQ"])
        出力JSONパス = os.path.join(_出力DIR, _タスクファイル名(利用者ID, タスクID))
        if not os.path.isfile(出力JSONパス):
            continue  # AI 生成タスク以外（出力 JSON なし）は自動実行の対象外
        軽量並行明細 = _軽量並行明細か(行)
        if code_agent実行中 and not 軽量並行明細:
            continue
        try:
            if int(行.get("実行回数", 0) or 0) >= 実行回数上限:
                tasks_db.明細失敗(利用者ID, タスクID, 明細SEQ, f"実行回数が上限({実行回数上限}回)に達しました")
                logger.warning(f"実行回数上限のため失敗にしました: {利用者ID}/{タスクID} SEQ={明細SEQ}")
                continue
            _明細実行開始(行, 出力JSONパス, logger)
            if not 軽量並行明細:
                code_agent実行中 = True
        except Exception as e:
            logger.exception(f"ステップ実行開始に失敗しました: {利用者ID}/{タスクID} SEQ={明細SEQ}")
            try:
                tasks_db.明細失敗(利用者ID, タスクID, 明細SEQ, f"実行開始エラー: {e}")
            except Exception:
                logger.exception(f"失敗登録もエラー: {利用者ID}/{タスクID} SEQ={明細SEQ}")


async def 監視ループ(logger: logging.Logger) -> None:
    logger.info(f"AIタスク監視ループを開始しました (interval={監視間隔秒}s)")
    while True:
        try:
            await asyncio.to_thread(_監視1回, logger)
        except Exception:
            logger.exception("AIタスク監視ループでエラーが発生しました")
        await asyncio.sleep(監視間隔秒)
