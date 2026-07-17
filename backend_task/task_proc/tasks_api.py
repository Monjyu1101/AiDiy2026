# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""AIタスクの HTTP API ルーター。

フロントエンドの AIタスク画面から Vite proxy 経由（/task/*）で呼ばれる。
レスポンスは status / message / data の統一形式。
"""

from __future__ import annotations

import json
import os
import re

from fastapi import APIRouter
from pydantic import BaseModel

from log_config import get_logger

from . import tasks_db
from . import tasks_watcher

logger = get_logger("tasks_api")

router = APIRouter(prefix="/task")

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_出力DIR = os.path.join(_BASE_DIR, "temp", "output")


class タスク要求登録リクエスト(BaseModel):
    利用者ID: str
    タイトル: str
    要求内容: str = ""


class タスク要求一覧リクエスト(BaseModel):
    利用者ID: str


class タスク要求取得リクエスト(BaseModel):
    利用者ID: str
    タスクID: str


class タスク明細一覧リクエスト(BaseModel):
    利用者ID: str
    タスクID: str


class タスク実行条件入力(BaseModel):
    """タスク要求ダイアログ右側の実行開始条件（区分は文字値）。"""
    実行区分: str = "即時"
    間隔区分: str = ""
    間隔値: int = 0
    定時区分: str = ""
    実行曜日: str = ""
    実行日: int = 0
    開始時刻: str = ""
    実行条件: str = "無し"
    監視フォルダ: str = ""


class タスク要求AI登録リクエスト(BaseModel):
    利用者ID: str
    プロジェクト: str = ""
    要求内容: str
    TASK_AI_NAME: str = "claude_cli"
    TASK_AI_MODEL: str = "auto"
    実行有効: bool = True
    実行条件: タスク実行条件入力 | None = None


class タスク要求更新登録リクエスト(BaseModel):
    利用者ID: str
    タスクID: str
    プロジェクト: str = ""
    要求内容: str
    TASK_AI_NAME: str = "claude_cli"
    TASK_AI_MODEL: str = "auto"
    実行有効: bool = True
    状況: str = "準備開始"  # 準備開始 / 準備完了 / 中止 / 更新前の状態
    実行条件: タスク実行条件入力 | None = None


class タスク明細全消去リクエスト(BaseModel):
    利用者ID: str
    タスクID: str


class タスク実行有効切替リクエスト(BaseModel):
    利用者ID: str
    タスクID: str
    実行有効: bool


class タスク明細実行有効切替リクエスト(BaseModel):
    利用者ID: str
    タスクID: str
    明細SEQ: int
    実行有効: bool


class タスク明細更新登録リクエスト(BaseModel):
    利用者ID: str
    タスクID: str
    明細SEQ: int
    タイトル: str
    要求内容: str = ""
    先行SEQ: str = ""
    TASK_AI_NAME: str = "claude_cli"
    TASK_AI_MODEL: str = "auto"
    実行有効: bool = True
    状態: str = "待機"


class タスク要求本登録リクエスト(BaseModel):
    利用者ID: str
    タスクID: str
    タイトル: str
    要求内容: str = ""
    マーメイド記号: str = ""
    明細: list[dict]
    応答内容: str = ""


class タスク要求AI失敗リクエスト(BaseModel):
    利用者ID: str
    タスクID: str
    メッセージ: str = ""


class タスク明細完了リクエスト(BaseModel):
    利用者ID: str
    タスクID: str
    明細SEQ: int
    応答内容: str = ""


class タスク明細開始完了リクエスト(BaseModel):
    利用者ID: str
    タスクID: str
    明細SEQ: int
    応答内容: str = ""


class タスク明細終了完了リクエスト(BaseModel):
    利用者ID: str
    タスクID: str
    明細SEQ: int
    応答内容: str = ""


class タスク明細失敗リクエスト(BaseModel):
    利用者ID: str
    タスクID: str
    明細SEQ: int
    メッセージ: str = ""


_時刻形式 = re.compile(r"^([01][0-9]|2[0-3]):[0-5][0-9]$")
_間隔上限 = {"分": 600, "時": 24, "日": 7}


def _実行条件検証(条件: タスク実行条件入力) -> str:
    """実行条件の入力値を検証し、問題があればエラーメッセージを返す（正常は空文字）。"""
    if 条件.実行区分 not in tasks_db.実行区分値:
        return f"実行区分は {' / '.join(tasks_db.実行区分値)} から選択してください。"
    if 条件.実行区分 == "時間指定":
        if not _時刻形式.match(条件.開始時刻):
            return "時間指定の開始時刻は HH:MM 形式で入力してください。"
    if 条件.実行区分 == "間隔実行":
        if 条件.間隔区分 not in tasks_db.間隔区分値:
            return f"間隔区分は {' / '.join(tasks_db.間隔区分値)} から選択してください。"
        上限 = _間隔上限[条件.間隔区分]
        if not (1 <= 条件.間隔値 <= 上限):
            return f"間隔値（{条件.間隔区分}）は 1〜{上限} で入力してください。"
        if 条件.間隔区分 == "日" and not _時刻形式.match(条件.開始時刻):
            return "日間隔の開始時刻は HH:MM 形式で入力してください。"
    if 条件.実行区分 == "定時実行":
        if 条件.定時区分 not in tasks_db.定時区分値:
            return f"定時区分は {' / '.join(tasks_db.定時区分値)} から選択してください。"
        if 条件.定時区分 == "毎週" and 条件.実行曜日 not in tasks_db.実行曜日値:
            return "毎週の実行曜日を選択してください。"
        if 条件.定時区分 == "毎月" and not (1 <= 条件.実行日 <= 31):
            return "毎月の実行日は 1〜31 で入力してください。"
        if not _時刻形式.match(条件.開始時刻):
            return "定時実行の開始時刻は HH:MM 形式で入力してください。"
    if 条件.実行条件 not in tasks_db.実行条件値:
        return f"実行条件は {' / '.join(tasks_db.実行条件値)} から選択してください。"
    if 条件.実行条件 == "フォルダ変化" and not 条件.監視フォルダ.strip():
        return "フォルダ変化の監視フォルダを指定してください。"
    return ""


def _OK(data: dict, message: str = "") -> dict:
    return {"status": "OK", "message": message, "data": data}


def _NG(message: str) -> dict:
    return {"status": "NG", "message": message, "data": {}}


def _出力JSON明細更新(利用者ID: str, タスクID: str, item: dict) -> bool:
    """sub_proc.py が参照する出力 JSON の明細内容も DB 更新に合わせる。"""
    path = os.path.join(_出力DIR, f"{利用者ID}.{タスクID}.json")
    if not os.path.isfile(path):
        return False
    with open(path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    明細 = data.get("明細")
    if not isinstance(明細, list):
        return False
    対象SEQ = int(item.get("明細SEQ", -1))
    更新済み = False
    for row in 明細:
        if not isinstance(row, dict):
            continue
        try:
            if int(row.get("明細SEQ", -1)) != 対象SEQ:
                continue
        except (TypeError, ValueError):
            continue
        row["タイトル"] = str(item.get("タイトル", ""))
        row["要求内容"] = str(item.get("要求内容", ""))
        row["先行SEQ"] = str(item.get("先行SEQ", ""))
        row["TASK_AI_NAME"] = str(item.get("TASK_AI_NAME", "claude_cli"))
        row["TASK_AI_MODEL"] = str(item.get("TASK_AI_MODEL", "auto"))
        更新済み = True
        break
    if not 更新済み:
        return False
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return True


@router.post("/タスク要求/一覧", tags=["タスク要求"])
async def タスク要求一覧(request: タスク要求一覧リクエスト) -> dict:
    try:
        利用者ID = request.利用者ID.strip()
        if not 利用者ID:
            return _NG("利用者IDを指定してください。")
        items = tasks_db.タスク要求一覧(利用者ID)
        return _OK({"items": items, "total": len(items)})
    except Exception as e:
        logger.error(f"タスク要求一覧の取得に失敗: {e}")
        return _NG(f"タスク要求一覧の取得に失敗しました: {e}")


@router.post("/タスク要求/取得", tags=["タスク要求"])
async def タスク要求取得(request: タスク要求取得リクエスト) -> dict:
    try:
        利用者ID = request.利用者ID.strip()
        タスクID = request.タスクID.strip()
        if not 利用者ID or not タスクID:
            return _NG("利用者IDとタスクIDを指定してください。")
        item = tasks_db.タスク要求取得(利用者ID, タスクID)
        if not item:
            return _NG(f"タスク {タスクID} が見つかりません。")
        return _OK({"item": item})
    except Exception as e:
        logger.error(f"タスク要求の取得に失敗: {e}")
        return _NG(f"タスク要求の取得に失敗しました: {e}")


@router.post("/タスク実行条件/取得", tags=["タスク要求"])
async def タスク実行条件取得(request: タスク要求取得リクエスト) -> dict:
    """タスク要求に紐づく実行開始条件を返す。未設定なら空 item（即時扱い）。"""
    try:
        利用者ID = request.利用者ID.strip()
        タスクID = request.タスクID.strip()
        if not 利用者ID or not タスクID:
            return _NG("利用者IDとタスクIDを指定してください。")
        return _OK({"item": tasks_db.実行条件取得(利用者ID, タスクID)})
    except Exception as e:
        logger.error(f"タスク実行条件の取得に失敗: {e}")
        return _NG(f"タスク実行条件の取得に失敗しました: {e}")


@router.post("/タスク要求/最大更新日時", tags=["タスク要求"])
async def タスク要求最大更新日時(request: タスク要求一覧リクエスト) -> dict:
    try:
        利用者ID = request.利用者ID.strip()
        if not 利用者ID:
            return _NG("利用者IDを指定してください。")
        return _OK({"最大更新日時": tasks_db.タスク要求最大更新日時(利用者ID)})
    except Exception as e:
        logger.error(f"タスク要求最大更新日時の取得に失敗: {e}")
        return _NG(f"タスク要求最大更新日時の取得に失敗しました: {e}")


@router.post("/タスク要求/登録", tags=["タスク要求"])
async def タスク要求登録(request: タスク要求登録リクエスト) -> dict:
    タイトル = request.タイトル.strip()
    利用者ID = request.利用者ID.strip()
    if not 利用者ID:
        return _NG("利用者IDを指定してください。")
    if not タイトル:
        return _NG("タイトルを入力してください。")
    try:
        item = tasks_db.タスク要求登録(利用者ID, タイトル, request.要求内容.strip())
        return _OK({"item": item}, f"タスク {item['タスクID']} を登録しました。")
    except Exception as e:
        logger.error(f"タスク要求の登録に失敗: {e}")
        return _NG(f"タスク要求の登録に失敗しました: {e}")


@router.post("/タスク明細/一覧", tags=["タスク明細"])
async def タスク明細一覧(request: タスク明細一覧リクエスト) -> dict:
    try:
        利用者ID = request.利用者ID.strip()
        if not 利用者ID:
            return _NG("利用者IDを指定してください。")
        items = tasks_db.タスク明細一覧(利用者ID, request.タスクID)
        return _OK({"items": items, "total": len(items)})
    except Exception as e:
        logger.error(f"タスク明細一覧の取得に失敗: {e}")
        return _NG(f"タスク明細一覧の取得に失敗しました: {e}")


@router.post("/タスク明細/最大更新日時", tags=["タスク明細"])
async def タスク明細最大更新日時(request: タスク明細一覧リクエスト) -> dict:
    try:
        利用者ID = request.利用者ID.strip()
        if not 利用者ID:
            return _NG("利用者IDを指定してください。")
        return _OK({"最大更新日時": tasks_db.タスク明細最大更新日時(利用者ID, request.タスクID)})
    except Exception as e:
        logger.error(f"タスク明細最大更新日時の取得に失敗: {e}")
        return _NG(f"タスク明細最大更新日時の取得に失敗しました: {e}")


# ==================================================
# プロジェクト選択肢（backend_server の外部プロジェクト探索と同等）
# ==================================================

def _プロジェクト選択肢取得() -> dict[str, str]:
    """AiDiy 実行ルートと、2 階層上から探索した _AIDIY.md 保有フォルダを返す。"""
    選択肢: dict[str, str] = {"../": "AiDiy 実行ルート"}
    探索ルート = os.path.abspath(os.path.join(_BASE_DIR, "..", ".."))

    def 追加(パス: str) -> None:
        if os.path.isfile(os.path.join(パス, "_AIDIY.md")):
            正規パス = os.path.abspath(パス).replace("\\", "/")
            if not 正規パス.endswith("/"):
                正規パス += "/"
            選択肢.setdefault(正規パス, os.path.basename(os.path.abspath(パス)))

    try:
        for entry in os.scandir(探索ルート):
            if not entry.is_dir():
                continue
            追加(entry.path)
            try:
                for sub in os.scandir(entry.path):
                    if sub.is_dir():
                        追加(sub.path)
            except (PermissionError, OSError):
                continue
    except (PermissionError, OSError) as e:
        logger.warning(f"プロジェクト探索エラー: {e}")
    return 選択肢


@router.post("/プロジェクト選択肢", tags=["タスク要求"])
async def プロジェクト選択肢() -> dict:
    try:
        return _OK({"選択肢": _プロジェクト選択肢取得()})
    except Exception as e:
        logger.error(f"プロジェクト選択肢の取得に失敗: {e}")
        return _NG(f"プロジェクト選択肢の取得に失敗しました: {e}")


# ==================================================
# AI タスク登録（仮登録 → 定型 python 生成 → subprocess 起動）
# ==================================================

@router.post("/タスク要求/AI登録", tags=["タスク要求"])
async def タスク要求AI登録(request: タスク要求AI登録リクエスト) -> dict:
    要求内容 = request.要求内容.strip()
    利用者ID = request.利用者ID.strip()
    if not 利用者ID:
        return _NG("利用者IDを指定してください。")
    if not 要求内容:
        return _NG("要求内容を入力してください。")
    実行条件 = request.実行条件 or タスク実行条件入力()
    エラー = _実行条件検証(実行条件)
    if エラー:
        return _NG(エラー)
    try:
        # 仮登録のみ行う（タスクID: yyyymmdd.hhmmss、状態: 準備中）。
        # 実行は監視ループが 5 秒間隔で PID 未設定の仮登録を拾って開始する。
        タスクID = tasks_db.新規タスクID()
        タイトル = 要求内容.splitlines()[0][:40]
        item = tasks_db.仮タスク登録(
            タスクID,
            タイトル,
            要求内容,
            利用者ID,
            request.プロジェクト.strip(),
            request.TASK_AI_NAME.strip() or "claude_cli",
            request.TASK_AI_MODEL.strip() or "auto",
            request.実行有効,
        )
        tasks_db.実行条件登録(利用者ID, タスクID, 実行条件.model_dump())
        tasks_watcher.実行条件再計算(利用者ID, タスクID)
        return _OK({"item": item}, f"タスク {タスクID} を準備中として登録しました。")
    except Exception as e:
        logger.error(f"タスク要求のAI登録に失敗: {e}")
        return _NG(f"タスク要求のAI登録に失敗しました: {e}")


@router.post("/タスク要求/更新登録", tags=["タスク要求"])
async def タスク要求更新登録(request: タスク要求更新登録リクエスト) -> dict:
    """修正ダイアログからの更新。実行中プロセス（要求側・明細側）を全て停止してから更新する。

    状況=準備開始 は 状態=準備中 で再分解（明細の消去は sub_init.py が行う）、
    状況=中止 は 状態=中止 で停止したままにする。
    状況=準備完了 はタスク明細がある場合だけ許可し、実行有効なら全明細を
    実行有効・待機に戻して再起動可能（実行開始条件の充足待ち）にする。
    状況=それ以外（更新前の状態など）は最新の状態を保持して内容だけ更新する
    （ダイアログ表示中に状態が変わっていても NG にしない）。
    """
    利用者ID = request.利用者ID.strip()
    タスクID = request.タスクID.strip()
    要求内容 = request.要求内容.strip()
    if not 利用者ID or not タスクID:
        return _NG("利用者IDとタスクIDを指定してください。")
    if not 要求内容:
        return _NG("要求内容を入力してください。")
    実行条件 = request.実行条件
    if 実行条件 is not None:
        エラー = _実行条件検証(実行条件)
        if エラー:
            return _NG(エラー)
    try:
        現行 = tasks_db.タスク要求取得(利用者ID, タスクID)
        if not 現行:
            return _NG(f"タスク {タスクID} が見つかりません。")
        状況 = request.状況.strip()
        明細再開 = False
        if 状況 == "準備開始":
            状態 = "準備中"
        elif 状況 == "中止":
            状態 = "中止"
        elif 状況 == "準備完了":
            if not tasks_db.タスク明細一覧(利用者ID, タスクID):
                return _NG("タスク明細が無いため 準備完了 には戻せません。準備開始で再分解してください。")
            状態 = "準備完了"
            明細再開 = bool(request.実行有効)
        else:
            # 更新前の状態を保持（内容だけ更新）。ダイアログ表示中に状態が
            # 変わっていた場合も NG にせず、最新の状態を採用する
            状態 = str(現行.get("状態", ""))
        for pid in tasks_db.タスクPID一覧(利用者ID, タスクID):
            tasks_watcher._プロセス強制停止(pid, logger)
        tasks_db.タスクPIDクリア(利用者ID, タスクID)
        item = tasks_db.タスク要求更新登録(
            利用者ID,
            タスクID,
            request.プロジェクト.strip(),
            要求内容,
            request.TASK_AI_NAME.strip() or "claude_cli",
            request.TASK_AI_MODEL.strip() or "auto",
            request.実行有効,
            状態,
        )
        if not item:
            return _NG(f"タスク {タスクID} が見つかりません。")
        if 明細再開:
            # 有効な準備完了: 全明細を 実行有効・待機 に戻して再起動可能にする
            tasks_db.明細全件有効待機化(利用者ID, タスクID)
        if 実行条件 is not None:
            tasks_db.実行条件登録(利用者ID, タスクID, 実行条件.model_dump())
        # 実行条件・状態・実行有効のどれが変わっても次回実行日時を計算し直す
        tasks_watcher.実行条件再計算(利用者ID, タスクID)
        return _OK({"item": item}, f"タスク {タスクID} を {状態} として更新しました。")
    except Exception as e:
        logger.error(f"タスク要求の更新登録に失敗: {e}")
        return _NG(f"タスク要求の更新登録に失敗しました: {e}")


@router.post("/タスク要求/実行有効切替", tags=["タスク要求"])
async def タスク要求実行有効切替(request: タスク実行有効切替リクエスト) -> dict:
    """タスク要求と全タスク明細の実行有効フラグをまとめて更新する。"""
    利用者ID = request.利用者ID.strip()
    タスクID = request.タスクID.strip()
    if not 利用者ID or not タスクID:
        return _NG("利用者IDとタスクIDを指定してください。")
    try:
        item = tasks_db.タスク実行有効更新(利用者ID, タスクID, request.実行有効)
        if not item:
            return _NG(f"タスク {タスクID} が見つかりません。")
        tasks_watcher.実行条件再計算(利用者ID, タスクID)
        表示 = "有効化" if request.実行有効 else "無効化"
        return _OK({"item": item}, f"タスク {タスクID} を{表示}しました。")
    except Exception as e:
        logger.error(f"タスク実行有効切替に失敗: {e}")
        return _NG(f"タスク実行有効切替に失敗しました: {e}")


@router.post("/タスク明細/実行有効切替", tags=["タスク明細"])
async def タスク明細実行有効切替(request: タスク明細実行有効切替リクエスト) -> dict:
    """タスク明細 1 行の実行有効フラグを更新する。"""
    利用者ID = request.利用者ID.strip()
    タスクID = request.タスクID.strip()
    if not 利用者ID or not タスクID:
        return _NG("利用者IDとタスクIDを指定してください。")
    try:
        if not tasks_db.明細実行有効更新(利用者ID, タスクID, request.明細SEQ, request.実行有効):
            return _NG(f"タスク明細 {タスクID} SEQ={request.明細SEQ} が見つかりません。")
        表示 = "有効化" if request.実行有効 else "無効化"
        return _OK({}, f"タスク明細 SEQ={request.明細SEQ} を{表示}しました。")
    except Exception as e:
        logger.error(f"タスク明細実行有効切替に失敗: {e}")
        return _NG(f"タスク明細実行有効切替に失敗しました: {e}")


@router.post("/タスク明細/更新登録", tags=["タスク明細"])
async def タスク明細更新登録(request: タスク明細更新登録リクエスト) -> dict:
    """明細編集ダイアログからの更新。実行中なら該当明細のプロセスを停止してから更新する。"""
    利用者ID = request.利用者ID.strip()
    タスクID = request.タスクID.strip()
    タイトル = request.タイトル.strip()
    要求内容 = request.要求内容.strip()
    先行SEQ = request.先行SEQ.strip()
    状態 = request.状態.strip() or "待機"
    if not 利用者ID or not タスクID:
        return _NG("利用者IDとタスクIDを指定してください。")
    if not タイトル:
        return _NG("タイトルを入力してください。")
    for seq in [s.strip() for s in 先行SEQ.split(",") if s.strip()]:
        if not seq.isdigit():
            return _NG("先行SEQは数値のカンマ区切りで入力してください。")
        if int(seq) == request.明細SEQ:
            return _NG("先行SEQに自分自身は指定できません。")
    try:
        現行 = tasks_db.タスク明細取得(利用者ID, タスクID, request.明細SEQ)
        if not 現行:
            return _NG(f"タスク明細 {タスクID} SEQ={request.明細SEQ} が見つかりません。")
        # 更新前の状態（実行中など）はそのまま維持できる。ダイアログ表示中に
        # 状態が変わっていた場合も NG にせず、最新の状態を採用して内容だけ更新する
        if 状態 not in {"待機", "完了", "エラー", "中止"} and 状態 != str(現行.get("状態", "")):
            状態 = str(現行.get("状態", "")) or "待機"
        pid = str(現行.get("PID", "")).strip()
        if pid.isdigit():
            tasks_watcher._プロセス強制停止(int(pid), logger)
        item = tasks_db.明細更新登録(
            利用者ID,
            タスクID,
            request.明細SEQ,
            タイトル,
            要求内容,
            先行SEQ,
            request.TASK_AI_NAME.strip() or "claude_cli",
            request.TASK_AI_MODEL.strip() or "auto",
            request.実行有効,
            状態,
        )
        if not item:
            return _NG(f"タスク明細 {タスクID} SEQ={request.明細SEQ} が見つかりません。")
        JSON同期 = _出力JSON明細更新(利用者ID, タスクID, item)
        message = f"タスク明細 SEQ={request.明細SEQ} を更新しました。"
        if not JSON同期:
            message += " 出力JSONは未更新です。"
        return _OK({"item": item, "JSON同期": JSON同期}, message)
    except Exception as e:
        logger.error(f"タスク明細更新登録に失敗: {e}")
        return _NG(f"タスク明細更新登録に失敗しました: {e}")


@router.post("/タスク明細/全消去", tags=["タスク明細"])
async def タスク明細全消去(request: タスク明細全消去リクエスト) -> dict:
    """指定タスクの AIタスク明細を全消去する（sub_init.py の再生成前クリア用）。

    明細に PID が残っていれば処理を停止してから消去する。
    """
    利用者ID = request.利用者ID.strip()
    タスクID = request.タスクID.strip()
    if not 利用者ID or not タスクID:
        return _NG("利用者IDとタスクIDを指定してください。")
    try:
        for 行 in tasks_db.タスク明細一覧(利用者ID, タスクID):
            pid = str(行.get("PID", "")).strip()
            if pid.isdigit():
                tasks_watcher._プロセス強制停止(int(pid), logger)
        件数 = tasks_db.タスク明細全削除(利用者ID, タスクID)
        return _OK({"削除件数": 件数}, f"タスク {タスクID} の明細を {件数} 件消去しました。")
    except Exception as e:
        logger.error(f"タスク明細の全消去に失敗: {e}")
        return _NG(f"タスク明細の全消去に失敗しました: {e}")


@router.post("/タスク要求/本登録", tags=["タスク要求"])
async def タスク要求本登録(request: タスク要求本登録リクエスト) -> dict:
    try:
        利用者ID = request.利用者ID.strip()
        if not 利用者ID:
            return _NG("利用者IDを指定してください。")
        item = tasks_db.タスク本登録(
            利用者ID,
            request.タスクID,
            request.タイトル.strip(),
            request.要求内容.strip(),
            request.マーメイド記号.strip(),
            request.明細,
            request.応答内容.strip(),
        )
        return _OK({"item": item}, f"タスク {request.タスクID} を本登録しました。")
    except Exception as e:
        logger.error(f"タスク要求の本登録に失敗: {e}")
        return _NG(f"タスク要求の本登録に失敗しました: {e}")


@router.post("/タスク要求/AI失敗", tags=["タスク要求"])
async def タスク要求AI失敗(request: タスク要求AI失敗リクエスト) -> dict:
    try:
        利用者ID = request.利用者ID.strip()
        if not 利用者ID:
            return _NG("利用者IDを指定してください。")
        item = tasks_db.タスク失敗(利用者ID, request.タスクID, request.メッセージ)
        return _OK({"item": item}, f"タスク {request.タスクID} を失敗として登録しました。")
    except Exception as e:
        logger.error(f"タスク要求のAI失敗登録に失敗: {e}")
        return _NG(f"タスク要求のAI失敗登録に失敗しました: {e}")


@router.post("/タスク明細/完了", tags=["タスク明細"])
async def タスク明細完了(request: タスク明細完了リクエスト) -> dict:
    try:
        利用者ID = request.利用者ID.strip()
        if not 利用者ID:
            return _NG("利用者IDを指定してください。")
        item = tasks_db.明細完了(利用者ID, request.タスクID, request.明細SEQ, request.応答内容)
        return _OK({"item": item}, f"タスク {request.タスクID} SEQ{request.明細SEQ} を完了しました。")
    except Exception as e:
        logger.error(f"タスク明細の完了登録に失敗: {e}")
        return _NG(f"タスク明細の完了登録に失敗しました: {e}")


@router.post("/タスク明細/開始完了", tags=["タスク明細"])
async def タスク明細開始完了(request: タスク明細開始完了リクエスト) -> dict:
    """開始明細を完了し、AIタスク要求を実行中にする（sub_start.py 用）。"""
    try:
        利用者ID = request.利用者ID.strip()
        if not 利用者ID:
            return _NG("利用者IDを指定してください。")
        応答内容 = request.応答内容 or "開始処理を完了しました。"
        item = tasks_db.開始明細完了(利用者ID, request.タスクID, request.明細SEQ, 応答内容)
        return _OK({"item": item}, f"タスク {request.タスクID} SEQ{request.明細SEQ} の開始処理を完了しました。")
    except Exception as e:
        logger.error(f"タスク明細の開始完了登録に失敗: {e}")
        return _NG(f"タスク明細の開始完了登録に失敗しました: {e}")


@router.post("/タスク明細/終了完了", tags=["タスク明細"])
async def タスク明細終了完了(request: タスク明細終了完了リクエスト) -> dict:
    """終了明細を完了し、AIタスク要求を完了にする（sub_terminate.py 用）。"""
    try:
        利用者ID = request.利用者ID.strip()
        if not 利用者ID:
            return _NG("利用者IDを指定してください。")
        応答内容 = request.応答内容 or "終了処理を完了しました。"
        item = tasks_db.終了明細完了(利用者ID, request.タスクID, request.明細SEQ, 応答内容)
        return _OK({"item": item}, f"タスク {request.タスクID} SEQ{request.明細SEQ} の終了処理を完了しました。")
    except Exception as e:
        logger.error(f"タスク明細の終了完了登録に失敗: {e}")
        return _NG(f"タスク明細の終了完了登録に失敗しました: {e}")


@router.post("/タスク明細/失敗", tags=["タスク明細"])
async def タスク明細失敗(request: タスク明細失敗リクエスト) -> dict:
    try:
        利用者ID = request.利用者ID.strip()
        if not 利用者ID:
            return _NG("利用者IDを指定してください。")
        item = tasks_db.明細失敗(利用者ID, request.タスクID, request.明細SEQ, request.メッセージ)
        return _OK({"item": item}, f"タスク {request.タスクID} SEQ{request.明細SEQ} を失敗として登録しました。")
    except Exception as e:
        logger.error(f"タスク明細の失敗登録に失敗: {e}")
        return _NG(f"タスク明細の失敗登録に失敗しました: {e}")
