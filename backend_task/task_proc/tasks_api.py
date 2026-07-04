# -*- coding: utf-8 -*-

"""AIタスクの HTTP API ルーター。

フロントエンドの AIタスク画面から Vite proxy 経由（/task/*）で呼ばれる。
レスポンスは status / message / data の統一形式。
"""

from __future__ import annotations

import json
import os

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


class タスク明細一覧リクエスト(BaseModel):
    利用者ID: str
    タスクID: str


class タスク要求AI登録リクエスト(BaseModel):
    利用者ID: str
    プロジェクト: str = ""
    要求内容: str
    TASK_AI_NAME: str = "claude_cli"
    TASK_AI_MODEL: str = "auto"
    有効: bool = True


class タスク要求更新登録リクエスト(BaseModel):
    利用者ID: str
    タスクID: str
    プロジェクト: str = ""
    要求内容: str
    TASK_AI_NAME: str = "claude_cli"
    TASK_AI_MODEL: str = "auto"
    有効: bool = True
    状況: str = "準備開始"  # 準備開始 / 中止


class タスク明細全消去リクエスト(BaseModel):
    利用者ID: str
    タスクID: str


class タスク有効切替リクエスト(BaseModel):
    利用者ID: str
    タスクID: str
    有効: bool


class タスク明細有効切替リクエスト(BaseModel):
    利用者ID: str
    タスクID: str
    明細SEQ: int
    有効: bool


class タスク明細更新登録リクエスト(BaseModel):
    利用者ID: str
    タスクID: str
    明細SEQ: int
    タイトル: str
    要求内容: str = ""
    先行SEQ: str = ""
    TASK_AI_NAME: str = "claude_cli"
    TASK_AI_MODEL: str = "auto"
    有効: bool = True
    状態: str = "待機"


class タスク要求本登録リクエスト(BaseModel):
    利用者ID: str
    タスクID: str
    タイトル: str
    要求内容: str = ""
    マーメイド記号: str = ""
    明細: list[dict]


class タスク要求AI失敗リクエスト(BaseModel):
    利用者ID: str
    タスクID: str
    メッセージ: str = ""


class タスク明細完了リクエスト(BaseModel):
    利用者ID: str
    タスクID: str
    明細SEQ: int
    応答内容: str = ""


class タスク明細失敗リクエスト(BaseModel):
    利用者ID: str
    タスクID: str
    明細SEQ: int
    メッセージ: str = ""


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
            request.有効,
        )
        return _OK({"item": item}, f"タスク {タスクID} を準備中として登録しました。")
    except Exception as e:
        logger.error(f"タスク要求のAI登録に失敗: {e}")
        return _NG(f"タスク要求のAI登録に失敗しました: {e}")


@router.post("/タスク要求/更新登録", tags=["タスク要求"])
async def タスク要求更新登録(request: タスク要求更新登録リクエスト) -> dict:
    """修正ダイアログからの更新。実行中プロセス（要求側・明細側）を全て停止してから更新する。

    状況=準備開始 は 状態=準備中 で再分解（明細の消去は sub_init.py が行う）、
    状況=中止 は 状態=中止 で停止したままにする。
    """
    利用者ID = request.利用者ID.strip()
    タスクID = request.タスクID.strip()
    要求内容 = request.要求内容.strip()
    if not 利用者ID or not タスクID:
        return _NG("利用者IDとタスクIDを指定してください。")
    if not 要求内容:
        return _NG("要求内容を入力してください。")
    try:
        for pid in tasks_db.タスクPID一覧(利用者ID, タスクID):
            tasks_watcher._プロセス強制停止(pid, logger)
        tasks_db.タスクPIDクリア(利用者ID, タスクID)
        状態 = "準備中" if request.状況.strip() == "準備開始" else "中止"
        item = tasks_db.タスク要求更新登録(
            利用者ID,
            タスクID,
            request.プロジェクト.strip(),
            要求内容,
            request.TASK_AI_NAME.strip() or "claude_cli",
            request.TASK_AI_MODEL.strip() or "auto",
            request.有効,
            状態,
        )
        if not item:
            return _NG(f"タスク {タスクID} が見つかりません。")
        return _OK({"item": item}, f"タスク {タスクID} を {状態} として更新しました。")
    except Exception as e:
        logger.error(f"タスク要求の更新登録に失敗: {e}")
        return _NG(f"タスク要求の更新登録に失敗しました: {e}")


@router.post("/タスク要求/有効切替", tags=["タスク要求"])
async def タスク要求有効切替(request: タスク有効切替リクエスト) -> dict:
    """タスク要求と全タスク明細の有効フラグをまとめて更新する。"""
    利用者ID = request.利用者ID.strip()
    タスクID = request.タスクID.strip()
    if not 利用者ID or not タスクID:
        return _NG("利用者IDとタスクIDを指定してください。")
    try:
        item = tasks_db.タスク有効更新(利用者ID, タスクID, request.有効)
        if not item:
            return _NG(f"タスク {タスクID} が見つかりません。")
        表示 = "有効" if request.有効 else "無効"
        return _OK({"item": item}, f"タスク {タスクID} を {表示} に変更しました。")
    except Exception as e:
        logger.error(f"タスク有効切替に失敗: {e}")
        return _NG(f"タスク有効切替に失敗しました: {e}")


@router.post("/タスク明細/有効切替", tags=["タスク明細"])
async def タスク明細有効切替(request: タスク明細有効切替リクエスト) -> dict:
    """タスク明細 1 行の有効フラグを更新する。"""
    利用者ID = request.利用者ID.strip()
    タスクID = request.タスクID.strip()
    if not 利用者ID or not タスクID:
        return _NG("利用者IDとタスクIDを指定してください。")
    try:
        if not tasks_db.明細有効更新(利用者ID, タスクID, request.明細SEQ, request.有効):
            return _NG(f"タスク明細 {タスクID} SEQ={request.明細SEQ} が見つかりません。")
        表示 = "有効" if request.有効 else "無効"
        return _OK({}, f"タスク明細 SEQ={request.明細SEQ} を {表示} に変更しました。")
    except Exception as e:
        logger.error(f"タスク明細有効切替に失敗: {e}")
        return _NG(f"タスク明細有効切替に失敗しました: {e}")


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
    if 状態 not in {"待機", "完了", "失敗"}:
        return _NG("状態は 待機 / 完了 / 失敗 から選択してください。")
    for seq in [s.strip() for s in 先行SEQ.split(",") if s.strip()]:
        if not seq.isdigit():
            return _NG("先行SEQは数値のカンマ区切りで入力してください。")
        if int(seq) == request.明細SEQ:
            return _NG("先行SEQに自分自身は指定できません。")
    try:
        現行 = tasks_db.タスク明細取得(利用者ID, タスクID, request.明細SEQ)
        if not 現行:
            return _NG(f"タスク明細 {タスクID} SEQ={request.明細SEQ} が見つかりません。")
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
            request.有効,
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
