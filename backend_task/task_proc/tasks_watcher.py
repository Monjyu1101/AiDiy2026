# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""AIタスクの監視ループとプロセス管理。

- 5秒間隔でタスク要求を確認し、PID未設定の仮登録（準備開始）を見つけたら
  temp/input/<利用者ID>.<タスクID>.json を出力して sub_init.py を subprocess 起動する。
  起動時に準備中へ進め、PID・開始日時・実行回数を記録する。
- システム開始時（再起動含む）は、テーブルに残った PID のプロセスを強制停止して
  PID をクリアする（クリア後は監視ループが自動で再実行する）。
"""

from __future__ import annotations

import asyncio
import calendar
import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timedelta

from . import tasks_db

監視間隔秒 = 5
実行条件監視間隔秒 = 10
実行回数上限 = 3
実行タイムアウト分 = 30

# 実行開始条件は hh:mm が変わった確認回だけ処理する（毎分 1 回）
_前回確認分 = ""
_曜日番号 = {"月": 0, "火": 1, "水": 2, "木": 3, "金": 4, "土": 5, "日": 6}

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


def _時刻適用(基準日: datetime, 時刻: str) -> datetime | None:
    """datetime に 'HH:MM' を適用する。形式不正は None。"""
    try:
        h, m = 時刻.split(":")
        return 基準日.replace(hour=int(h), minute=int(m), second=0, microsecond=0)
    except (ValueError, AttributeError):
        return None


def _次回実行日時計算(条件: dict, 基準: datetime) -> str:
    """実行開始条件から基準より後の次回実行日時を求める（計算不能は空文字）。"""
    区分 = str(条件.get("実行区分", ""))
    開始時刻 = str(条件.get("開始時刻", ""))
    try:
        if 区分 == "時間指定":
            候補 = _時刻適用(基準, 開始時刻)
            if 候補 is None:
                return ""
            if 候補 <= 基準:
                候補 += timedelta(days=1)
            return 候補.strftime("%Y-%m-%d %H:%M:%S")
        if 区分 == "間隔実行":
            値 = max(1, int(条件.get("間隔値", 0) or 0))
            単位 = str(条件.get("間隔区分", ""))
            if 単位 == "分":
                候補 = 基準 + timedelta(minutes=値)
            elif 単位 == "時":
                候補 = 基準 + timedelta(hours=値)
            elif 単位 == "日":
                日候補 = _時刻適用(基準 + timedelta(days=値), 開始時刻)
                if 日候補 is None:
                    return ""
                候補 = 日候補
            else:
                return ""
            return 候補.replace(second=0, microsecond=0).strftime("%Y-%m-%d %H:%M:%S")
        if 区分 == "定時実行":
            定時 = str(条件.get("定時区分", ""))
            if 定時 == "毎日":
                候補 = _時刻適用(基準, 開始時刻)
                if 候補 is None:
                    return ""
                if 候補 <= 基準:
                    候補 += timedelta(days=1)
            elif 定時 == "毎週":
                番号 = _曜日番号.get(str(条件.get("実行曜日", "")))
                候補 = _時刻適用(基準, 開始時刻)
                if 番号 is None or 候補 is None:
                    return ""
                候補 += timedelta(days=(番号 - 候補.weekday()) % 7)
                if 候補 <= 基準:
                    候補 += timedelta(days=7)
            elif 定時 == "毎月":
                日 = int(条件.get("実行日", 0) or 0)
                if not (1 <= 日 <= 31):
                    return ""

                def 月内(y: int, m: int) -> datetime | None:
                    末日 = calendar.monthrange(y, m)[1]
                    return _時刻適用(datetime(y, m, min(日, 末日)), 開始時刻)

                月候補 = 月内(基準.year, 基準.month)
                if 月候補 is None:
                    return ""
                if 月候補 <= 基準:
                    y, m = (基準.year + 1, 1) if 基準.month == 12 else (基準.year, 基準.month + 1)
                    月候補 = 月内(y, m)
                    if 月候補 is None:
                        return ""
                候補 = 月候補
            else:
                return ""
            return 候補.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return ""
    return ""


def _次回繰り越し(条件: dict, 基準: datetime) -> str:
    """発火せずに次周期へ送るときの次回実行日時（時間指定は一回限りなので空にする）。"""
    if str(条件.get("実行区分", "")) == "時間指定":
        return ""
    return _次回実行日時計算(条件, 基準)


def _発火可能状態(条件: dict) -> bool:
    """発火してよい状態（実行有効 かつ 要求が 準備完了 / 完了）かを返す。"""
    try:
        有効 = int(条件.get("要求実行有効") or 0) == 1
    except (TypeError, ValueError):
        有効 = False
    return 有効 and str(条件.get("要求状態", "")) in ("準備完了", "完了")


def _保持可能状態(条件: dict) -> bool:
    """次回実行日時を保持してよい状態（実行有効 かつ 要求が 待機/実行中/準備完了/完了）かを返す。

    待機・実行中は自タスクの実行サイクル途中なので次回実行日時は消さない
    （期限が到来しても発火せず次周期へスキップする）。クリアするのは
    無効・準備開始・準備中・エラー・中止などの発火対象外だけ。
    """
    try:
        有効 = int(条件.get("要求実行有効") or 0) == 1
    except (TypeError, ValueError):
        有効 = False
    return 有効 and str(条件.get("要求状態", "")) in ("待機", "実行中", "準備完了", "完了")


def 実行条件再計算(利用者ID: str, タスクID: str) -> str:
    """実行条件の編集・実行有効切替・状態変更時に次回実行日時を計算し直す。

    保持可能状態（実行有効 かつ 要求が 待機/実行中/準備完了/完了）の時間駆動条件だけ
    次回を計算し、それ以外（無効・準備開始・準備中・エラー・中止や即時など）は空に戻す。
    """
    条件 = tasks_db.実行条件監視取得(利用者ID, タスクID)
    if 条件 is None:
        return ""
    時間駆動 = str(条件.get("実行区分", "")) in ("時間指定", "間隔実行", "定時実行")
    新次回 = _次回実行日時計算(条件, datetime.now()) if 時間駆動 and _保持可能状態(条件) else ""
    if 新次回 != str(条件.get("次回実行日時", "")):
        tasks_db.次回実行日時更新(利用者ID, タスクID, 新次回)
    return 新次回


def 起動時実行条件初期化(logger: logging.Logger) -> None:
    """PG 起動時（タイマー起動前）の実行条件初期化。

    発火対象外（時間駆動でない・保持可能状態でない）の条件は次回実行日時を一括で空にする。
    停止中に期限が到来した条件（次回実行日時 <= now）は発火させずに次周期へ更新し、
    起動直後のまとめて発火を防ぐ。未計算（空）の時間駆動条件はここで初回計算する。
    """
    try:
        クリア件数 = tasks_db.発火対象外次回実行日時クリア()
        if クリア件数:
            logger.info(f"発火対象外の次回実行日時をクリアしました: {クリア件数} 件")
    except Exception:
        logger.exception("発火対象外の次回実行日時クリアでエラーが発生しました")
    now = datetime.now()
    now文字 = now.strftime("%Y-%m-%d %H:%M:%S")
    for 条件 in tasks_db.実行条件監視一覧():
        利用者ID = str(条件["利用者ID"])
        タスクID = str(条件["タスクID"])
        try:
            if str(条件.get("実行区分", "")) not in ("時間指定", "間隔実行", "定時実行"):
                continue
            if not _保持可能状態(条件):
                continue  # 次回実行日時は一括クリア済み
            次回 = str(条件.get("次回実行日時", ""))
            if 次回 == "":
                初回 = _次回実行日時計算(条件, now)
                if 初回:
                    tasks_db.次回実行日時更新(利用者ID, タスクID, 初回)
                continue
            if 次回 <= now文字:
                新次回 = _次回繰り越し(条件, now)
                tasks_db.次回実行日時更新(利用者ID, タスクID, 新次回)
                logger.info(
                    f"起動時に期限切れの次回実行日時を更新しました: {利用者ID}/{タスクID} {次回} -> {新次回 or 'なし'}"
                )
        except Exception:
            logger.exception(f"起動時実行条件初期化でエラーが発生しました: {利用者ID}/{タスクID}")


def _フォルダ状態取得(パス: str) -> tuple[int, str] | None:
    """監視フォルダ直下のファイル数と最新更新日時を返す。参照不能は None。"""
    try:
        件数 = 0
        最終 = 0.0
        with os.scandir(パス) as it:
            for entry in it:
                if entry.is_file():
                    件数 += 1
                    最終 = max(最終, entry.stat().st_mtime)
        最終日時 = datetime.fromtimestamp(最終).strftime("%Y-%m-%d %H:%M:%S") if 件数 else ""
        return 件数, 最終日時
    except OSError:
        return None


def _即時実行条件確認(logger: logging.Logger) -> None:
    """即時実行（実行区分='即時'）かつ実行有効・準備完了の要求を待機に戻す。

    時間駆動条件が無い即時実行は _実行条件確認 の対象外（1 分ゲートの対象にもならない）ため、
    実行条件監視ループの先頭で毎回（10 秒ごとに）確認し、他の処理より先に待機へ戻す。
    """
    for 行 in tasks_db.即時発火対象一覧():
        利用者ID = str(行["利用者ID"])
        タスクID = str(行["タスクID"])
        try:
            if tasks_db.タスク発火(利用者ID, タスクID):
                logger.info(f"即時実行のため待機に戻しました: {利用者ID}/{タスクID}")
        except Exception:
            logger.exception(f"即時実行の待機化でエラーが発生しました: {利用者ID}/{タスクID}")


def _実行条件確認(logger: logging.Logger) -> None:
    """hh:mm が変わった監視回だけ、次回実行日時と実行条件を確認して発火する。

    発火条件: 要求が 準備完了 / 完了 かつ実行有効で、明細が全件待機または全件完了。
    保持可能状態でない条件（無効・準備開始・準備中・エラー・中止など）は次回実行日時を空にする。
    自タスクの実行サイクル途中（待機/実行中）や条件不成立の回（フォルダ変化なし等）は
    発火せず次回実行日時だけ次周期へ更新する（スキップ。消さない）。
    発火時は 明細 → 要求 の順で 待機 に戻し、次回実行日時を更新する。
    """
    global _前回確認分
    now = datetime.now()
    現在分 = now.strftime("%Y-%m-%d %H:%M")
    if 現在分 == _前回確認分:
        return
    _前回確認分 = 現在分
    now文字 = now.strftime("%Y-%m-%d %H:%M:%S")

    for 条件 in tasks_db.実行条件監視一覧():
        利用者ID = str(条件["利用者ID"])
        タスクID = str(条件["タスクID"])
        try:
            区分 = str(条件.get("実行区分", ""))
            時間駆動 = 区分 in ("時間指定", "間隔実行", "定時実行")

            if not _保持可能状態(条件):
                # 発火対象外（無効・準備開始・準備中・エラー・中止など）は次回実行日時を空にする
                if 時間駆動 and str(条件.get("次回実行日時", "")):
                    tasks_db.次回実行日時更新(利用者ID, タスクID, "")
                    logger.info(
                        f"発火対象外のため次回実行日時をクリアしました: {利用者ID}/{タスクID} "
                        f"状態={条件.get('要求状態', '')} 実行有効={条件.get('要求実行有効', '')}"
                    )
                continue

            def 次回送り() -> None:
                """発火せずに次周期へ進める（時間指定は一回限りなので空にする）。"""
                if 時間駆動:
                    tasks_db.次回実行日時更新(利用者ID, タスクID, _次回繰り越し(条件, now))

            if 時間駆動:
                次回 = str(条件.get("次回実行日時", ""))
                if 次回 == "":
                    # 初回は次回実行日時の計算だけ行う
                    初回次回 = _次回実行日時計算(条件, now)
                    if 初回次回:
                        tasks_db.次回実行日時更新(利用者ID, タスクID, 初回次回)
                    continue
                if 次回 > now文字:
                    continue

            if not _発火可能状態(条件):
                # 自タスクが待機/実行中（実行サイクル途中）: 発火せず次周期へスキップ
                次回送り()
                continue

            # フォルダ変化条件の確認（実行区分=即時 + フォルダ変化 は毎分確認）
            スナップショット: tuple[int, str] | None = None
            if str(条件.get("実行条件", "")) == "フォルダ変化":
                スナップショット = _フォルダ状態取得(str(条件.get("監視フォルダ", "")))
                if スナップショット is None:
                    logger.warning(
                        f"監視フォルダを確認できません: {利用者ID}/{タスクID} {条件.get('監視フォルダ', '')}"
                    )
                    次回送り()
                    continue
                try:
                    保存ファイル数 = int(条件.get("フォルダ内ファイル数"))
                except (TypeError, ValueError):
                    保存ファイル数 = -1
                if 保存ファイル数 < 0:
                    # 初回はスナップショット取得のみ（登録直後の誤発火防止）
                    tasks_db.フォルダ状態記録(利用者ID, タスクID, スナップショット[0], スナップショット[1])
                    次回送り()
                    continue
                if スナップショット == (保存ファイル数, str(条件.get("フォルダ内最終日時", ""))):
                    次回送り()  # 変化なし: 発火せず次周期へ
                    continue

            if not tasks_db.タスク発火(利用者ID, タスクID):
                # 明細が実行途中など: 発火せずに次周期へスキップ（消さない）
                次回送り()
                continue

            if スナップショット is not None:
                tasks_db.フォルダ状態記録(利用者ID, タスクID, スナップショット[0], スナップショット[1])
            次回 = _次回実行日時計算(条件, now) if 時間駆動 and 区分 != "時間指定" else ""
            tasks_db.次回実行日時更新(利用者ID, タスクID, 次回, 前回実行日時=now文字)
            logger.info(
                f"実行開始条件により再実行します: {利用者ID}/{タスクID} 区分={区分} 次回={次回 or 'なし'}"
            )
        except Exception:
            logger.exception(f"実行条件確認でエラーが発生しました: {利用者ID}/{タスクID}")


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

    # --- 仮登録（準備開始・PIDなし）→ 準備中 + sub_init.pyでAIタスク分解 ---
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
    # code agent 系はタスク単位で 1 明細まで（タスク間は並行実行する）。
    # 通知音などの軽量明細は依存関係が許せば同時起動する。
    code_agent実行中タスク = {
        (str(行["利用者ID"]), str(行["タスクID"]))
        for 行 in tasks_db.実行中明細一覧()
        if not _軽量並行明細か(行)
    }
    for 行 in tasks_db.実行待ち明細一覧():
        利用者ID = str(行["利用者ID"])
        タスクID = str(行["タスクID"])
        明細SEQ = int(行["明細SEQ"])
        出力JSONパス = os.path.join(_出力DIR, _タスクファイル名(利用者ID, タスクID))
        if not os.path.isfile(出力JSONパス):
            continue  # AI 生成タスク以外（出力 JSON なし）は自動実行の対象外
        軽量並行明細 = _軽量並行明細か(行)
        if (利用者ID, タスクID) in code_agent実行中タスク and not 軽量並行明細:
            continue
        try:
            if int(行.get("実行回数", 0) or 0) >= 実行回数上限:
                tasks_db.明細失敗(利用者ID, タスクID, 明細SEQ, f"実行回数が上限({実行回数上限}回)に達しました")
                logger.warning(f"実行回数上限のため失敗にしました: {利用者ID}/{タスクID} SEQ={明細SEQ}")
                continue
            _明細実行開始(行, 出力JSONパス, logger)
            if not 軽量並行明細:
                code_agent実行中タスク.add((利用者ID, タスクID))
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


async def 実行条件監視ループ(logger: logging.Logger) -> None:
    """実行開始条件の確認ループ。

    明細起動（5 秒間隔の 監視ループ）とは分離して 10 秒間隔で回し、フォルダ走査などで
    時間がかかっても明細起動を遅らせない。実際の発火確認は hh:mm 変化時（毎分 1 回）。
    """
    logger.info(f"実行開始条件の監視ループを開始しました (interval={実行条件監視間隔秒}s)")
    while True:
        try:
            await asyncio.to_thread(_即時実行条件確認, logger)
            await asyncio.to_thread(_実行条件確認, logger)
        except Exception:
            logger.exception("実行開始条件の監視ループでエラーが発生しました")
        await asyncio.sleep(実行条件監視間隔秒)
