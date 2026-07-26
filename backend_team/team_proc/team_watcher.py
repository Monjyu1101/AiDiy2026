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
- 開始してから無進捗タイムアウト分（既定30分）以上ひとつも進捗が無い作業は、hh:mm が
  変わった監視回だけ（毎分1回）強制停止してエラーにする。状態='準備中'（sub_init.py に
  よる担当選択とAIタスク投入）だけは準備無進捗タイムアウト分（既定10分）で見る。
- 毎分1回、終わった Aチーム作業に対応する未終了の改善レコードを回収する
  （改善ループのオン・オフに関わらず行う）。
- 毎分1回、Aチーム目標の改善ループ（PDCA）も確認する。実行中の要員がいない空き時間で、
  前の段が終わっていれば次の段を対応する sub_pdca_*.py で投入する。
- システム開始時（再起動含む）は、テーブルに残った未投入の作業をエラーとして記録しクリアする
  （PID は再利用され得るため、プロセスの強制停止はしない）。
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from . import team_exp_db, team_goal_db, team_pdca_db, team_status_db, team_work_db

監視間隔秒 = 5
実行回数上限 = 3

_BASE_DIR = Path(__file__).resolve().parents[1]
_SUB_INITパス = _BASE_DIR / "team_sub" / "sub_init.py"
_入力DIR = _BASE_DIR / "temp" / "input"
_SUB_EXPパス = _BASE_DIR / "team_sub" / "sub_exp.py"
_経験入力DIR = _BASE_DIR / "temp" / "exp"
_SUB_PDCAパス = {
    "S": _BASE_DIR / "team_sub" / "sub_pdca_soudan.py",
    "P": _BASE_DIR / "team_sub" / "sub_pdca_plan.py",
    "D": _BASE_DIR / "team_sub" / "sub_pdca_do.py",
    "C": _BASE_DIR / "team_sub" / "sub_pdca_check.py",
    "A": _BASE_DIR / "team_sub" / "sub_pdca_action.py",
}
_改善入力DIR = _BASE_DIR / "temp" / "pdca"

# 無進捗タイムアウトの確認は hh:mm が変わった監視回だけ処理する（毎分 1 回）
_前回確認分 = ""
# 起動中の改善ループ投入プロセス（前回分が動いている間は次を投入しない）
_改善プロセス: subprocess.Popen | None = None
# 未実装区分の案内は毎分繰り返さず、プロジェクト×区分ごとに1回だけ出す
_改善未実装通知済み: set[tuple[str, str]] = set()


def _サブプロセス環境() -> dict:
    """サブプロセスの標準出力を UTF-8 にする環境変数を足して返す。

    Windows では既定が cp932 になり、AI応答に含まれる — や絵文字を print した時点で
    UnicodeEncodeError になって処理が失敗するため（変換できない文字は置換する）。
    """
    return {**os.environ, "PYTHONIOENCODING": "utf-8:replace"}


def _安全ファイル名部品(値: str) -> str:
    return re.sub(r"[^0-9A-Za-z_.\-぀-ヿ㐀-鿿]", "_", 値)


def _入力パス(作業ID: str) -> Path:
    return _入力DIR / f"{_安全ファイル名部品(作業ID)}.json"


def _経験入力パス(経験ID: str) -> Path:
    return _経験入力DIR / f"{_安全ファイル名部品(経験ID)}.json"


def _改善入力パス(プロジェクト: str, 区分: str) -> Path:
    時刻 = datetime.now().strftime("%Y%m%d_%H%M%S")
    return _改善入力DIR / f"{_安全ファイル名部品(プロジェクト)}_{_安全ファイル名部品(区分)}_{時刻}.json"


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
    """システム開始時: 未投入のまま残った作業をエラーとして記録しクリアする。

    PID は OS に再利用され得るため、別プロセスを誤って停止する恐れがあり強制停止はしない。
    """
    try:
        残存 = team_work_db.残存PID一覧()
        for 行 in 残存:
            logger.info(f"起動時クリーンアップ: 作業ID={行.get('作業ID', '')} PID={行.get('PID', '')}")
        更新件数 = team_work_db.PID全クリア()
        if 更新件数:
            logger.info(f"残存作業を{更新件数}件エラーにしてクリアしました")
    except Exception:
        logger.exception("チーム作業の起動時クリーンアップに失敗しました")
    try:
        for 行 in team_exp_db.生成中一覧():
            logger.info(f"起動時クリーンアップ: 経験ID={行.get('経験ID', '')} PID={行.get('PID', '')}")
        経験件数 = team_exp_db.生成中をエラー化("システム再起動のため中断しました")
        if 経験件数:
            logger.info(f"生成中の経験を{経験件数}件エラーにしてクリアしました")
    except Exception:
        logger.exception("Aチーム経験の起動時クリーンアップに失敗しました")
    try:
        改善件数 = team_pdca_db.取り残し終了()
        if 改善件数:
            logger.info(f"終了済み作業に対応する改善レコードを{改善件数}件回収しました")
    except Exception:
        logger.exception("Aチーム改善の起動時クリーンアップに失敗しました")


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
            env=_サブプロセス環境(),
        )
        team_work_db.実行開始記録(作業ID, proc.pid)
        logger.info(f"チーム作業のタスク投入を開始しました: {作業ID} PID={proc.pid}")
    except Exception as e:
        team_work_db.投入失敗記録(作業ID, f"sub_init起動エラー: {e}")
        logger.exception(f"チーム作業sub_initの起動に失敗しました: {作業ID}")


def _タイムアウト確認(logger: logging.Logger) -> None:
    """開始してから無進捗タイムアウト分以上ひとつも進捗が無い作業を強制停止してエラーにする。

    監視ループ（5秒間隔）から、hh:mm が変わった回だけ（毎分1回）呼ばれる。
    """
    try:
        タイムアウト対象 = team_work_db.作業タイムアウト対象一覧(
            team_work_db.無進捗タイムアウト分, team_work_db.準備無進捗タイムアウト分
        )
        for 行 in タイムアウト対象:
            pid = str(行.get("PID", "")).strip()
            状態 = str(行.get("状態", ""))
            制限分 = (
                team_work_db.準備無進捗タイムアウト分
                if 状態 == "準備中"
                else team_work_db.無進捗タイムアウト分
            )
            logger.warning(
                f"無進捗タイムアウト({制限分}分)のためキャンセルします: "
                f"{行.get('作業ID', '')} (要員ID={行.get('要員ID', '')} 状態={状態}) "
                f"開始日時={行.get('開始日時', '')} 最終進捗={行.get('最終進捗日時', '')} PID={pid}"
            )
            if pid.isdigit():
                _プロセス強制停止(int(pid), logger)
        if タイムアウト対象:
            更新件数 = team_work_db.作業タイムアウト対象エラー化(タイムアウト対象)
            logger.warning(f"無進捗タイムアウト対象をエラーにしました: {更新件数} 件")
    except Exception:
        logger.exception("無進捗タイムアウト処理でエラーが発生しました")


def _経験生成開始(対象: dict, logger: logging.Logger) -> None:
    """完了した作業 1 件を経験化する。仮登録 → sub_exp.py 起動まで行う。"""
    作業ID = str(対象["作業ID"])
    経験 = team_exp_db.経験仮登録(対象)
    if not 経験:
        # 同時実行などで既に登録済み
        return
    経験ID = str(経験["経験ID"])
    try:
        _経験入力DIR.mkdir(parents=True, exist_ok=True)
        入力パス = _経験入力パス(経験ID)
        with 入力パス.open("w", encoding="utf-8") as f:
            json.dump(
                {
                    "経験ID": 経験ID,
                    "作業ID": 作業ID,
                    "タスクID": str(対象.get("タスクID", "")),
                    "要員ID": str(対象.get("要員ID", "")),
                    "プロジェクト": str(対象.get("プロジェクト", "")),
                    "要求内容": str(対象.get("要求内容", "")),
                    "TEAM_AI_NAME": str(対象.get("TEAM_AI_NAME", "claude_cli")),
                    "TEAM_AI_MODEL": str(対象.get("TEAM_AI_MODEL", "auto")),
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        proc = subprocess.Popen(
            [sys.executable, str(_SUB_EXPパス), str(入力パス)],
            cwd=str(_BASE_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
            env=_サブプロセス環境(),
        )
        team_exp_db.生成開始記録(経験ID, proc.pid)
        logger.info(f"Aチーム経験の生成を開始しました: {経験ID} (作業={作業ID}) PID={proc.pid}")
    except Exception as e:
        team_exp_db.経験失敗記録(経験ID, f"sub_exp起動エラー: {e}")
        logger.exception(f"Aチーム経験のsub_exp起動に失敗しました: {経験ID}")


def _経験生成確認(logger: logging.Logger) -> None:
    """完了から1時間以内で経験未登録の作業を経験化する（1分ごと）。"""
    try:
        # 生成が長引いたものはエラーにして次回に持ち越さない
        for 行 in team_exp_db.生成タイムアウト対象一覧():
            pid = str(行.get("PID", "")).strip()
            logger.warning(
                f"経験生成タイムアウト({team_exp_db.生成タイムアウト分}分): "
                f"{行.get('経験ID', '')} 開始日時={行.get('開始日時', '')} PID={pid}"
            )
            if pid.isdigit():
                _プロセス強制停止(int(pid), logger)
            team_exp_db.経験失敗記録(
                str(行["経験ID"]), f"生成が{team_exp_db.生成タイムアウト分}分を超えたため中断しました"
            )
        for 対象 in team_exp_db.経験対象一覧():
            _経験生成開始(対象, logger)
    except Exception:
        logger.exception("Aチーム経験の生成確認でエラーが発生しました")


def _改善実行開始(目標: dict, 区分: str, logger: logging.Logger) -> subprocess.Popen | None:
    """PDCA 1段分の入力 JSON を出力し、区分に対応する sub_pdca_*.py を起動する。"""
    プロジェクト = str(目標.get("CODE_BASE_PATH", ""))
    スクリプト = _SUB_PDCAパス[区分]
    try:
        _改善入力DIR.mkdir(parents=True, exist_ok=True)
        入力パス = _改善入力パス(プロジェクト, 区分)
        with 入力パス.open("w", encoding="utf-8") as f:
            json.dump(
                {
                    "プロジェクト": プロジェクト,
                    "チーム目標": str(目標.get("チーム目標", "")),
                    "PDCA区分": 区分,
                    "最大ループ回数": max(1, min(99, int(目標.get("最大ループ回数", 1) or 1))),
                    "動員要員数": max(
                        1,
                        min(
                            team_goal_db.動員要員数上限,
                            int(目標.get("動員要員数", team_goal_db.既定動員要員数)
                                or team_goal_db.既定動員要員数),
                        ),
                    ),
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        proc = subprocess.Popen(
            [sys.executable, str(スクリプト), str(入力パス)],
            cwd=str(_BASE_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
            env=_サブプロセス環境(),
        )
        logger.info(
            f"改善ループ({区分})の投入を開始しました: プロジェクト={プロジェクト} PID={proc.pid}"
        )
        return proc
    except Exception:
        logger.exception(f"改善ループ({区分})の起動に失敗しました: プロジェクト={プロジェクト}")
        return None


def _改善回収(logger: logging.Logger) -> None:
    """Aチーム作業が終わっているのに未終了で残った改善レコードを回収する（1分ごと）。

    改善ループのオン・オフや空き時間の有無とは無関係に毎分行う。改善ループがオンの
    プロジェクトだけを対象にしていると、起動時のオフ解除（team_goal_db.起動時改善ループをオフ）
    直後にタイムアウトやエラーで確定した作業を誰も回収できず、改善レコードが未終了のまま
    固着してしまうため。
    """
    try:
        回収件数 = team_pdca_db.取り残し終了()
        if 回収件数:
            logger.info(f"終了済みのAチーム作業に対応する改善レコードを{回収件数}件回収しました")
    except Exception:
        logger.exception("Aチーム改善の回収でエラーが発生しました")


def _改善ループ確認(logger: logging.Logger) -> None:
    """改善ループがオンの目標について、空き時間なら次の PDCA 段を投入する（1分ごと）。

    投入するのは次のすべてを満たすときだけ。
    - 前回の投入プロセスが残っていない
    - Aチーム状況で実行中（準備中・実行中）の要員が 1 人もいない＝空き時間
    - そのプロジェクトの Aチーム改善に未終了レコードが無く、次の区分が実装済み

    未終了レコードの回収は _改善回収() が毎分行うため、ここでは行わない。
    """
    global _改善プロセス
    try:
        if _改善プロセス is not None and _改善プロセス.poll() is None:
            return
        _改善プロセス = None
        対象一覧 = team_goal_db.改善ループ対象一覧()
        if not 対象一覧:
            return
        実行中人数 = team_status_db.実行中要員数()
        if 実行中人数 > 0:
            return
        for 目標 in 対象一覧:
            プロジェクト = str(目標.get("CODE_BASE_PATH", ""))
            区分 = team_pdca_db.次のPDCA区分(プロジェクト)
            if not 区分:
                continue
            最大ループ回数 = max(1, min(99, int(目標.get("最大ループ回数", 1) or 1)))
            現在ループ = team_pdca_db.ループ最大値(プロジェクト)
            if 区分 == "S" and 最大ループ回数 != 99 and 現在ループ >= 最大ループ回数:
                # 止まったのか、やり切って終わったのかを区別できるよう1回だけ記録する
                if (プロジェクト, "完了") not in _改善未実装通知済み:
                    _改善未実装通知済み.add((プロジェクト, "完了"))
                    logger.info(
                        f"改善ループは最大ループ回数に達したため終了しました: "
                        f"プロジェクト={プロジェクト} 完了={現在ループ}周 最大={最大ループ回数}周"
                    )
                continue
            _改善未実装通知済み.discard((プロジェクト, "完了"))
            if 区分 not in team_pdca_db.実装済みPDCA区分 or 区分 not in _SUB_PDCAパス:
                if (プロジェクト, 区分) not in _改善未実装通知済み:
                    _改善未実装通知済み.add((プロジェクト, 区分))
                    logger.info(
                        f"改善ループの次の区分({区分})は未実装のため投入しません: プロジェクト={プロジェクト}"
                    )
                continue
            _改善未実装通知済み.discard((プロジェクト, 区分))
            _改善プロセス = _改善実行開始(目標, 区分, logger)
            # 空き時間を埋めるのは1サイクルにつき1プロジェクトだけにする
            break
    except Exception:
        logger.exception("改善ループの確認でエラーが発生しました")


def _監視1回(logger: logging.Logger) -> None:
    global _前回確認分
    現在分 = datetime.now().strftime("%Y-%m-%d %H:%M")
    if 現在分 != _前回確認分:
        _前回確認分 = 現在分
        _タイムアウト確認(logger)
        _経験生成確認(logger)
        # 回収は改善ループのオン・オフに関わらず行い、そのうえで次の段の投入を判断する
        _改善回収(logger)
        _改善ループ確認(logger)

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
