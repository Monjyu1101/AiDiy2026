# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""backend_team の AIチーム業務 API ルーター（エージェント、要員、作業）。"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from log_config import get_logger

from . import persona_catalog, team_db, team_status_db, team_work_db
from .config import 設定読込
from .store import ストア

logger = get_logger("team_api")

router = APIRouter(prefix="/team")


def ok(message: str, data=None) -> dict:
    return {"status": "OK", "message": message, "data": data if data is not None else {}}


def ng(message: str) -> dict:
    return {"status": "NG", "message": message, "data": {}}


class 召喚要求(BaseModel):
    要員ID: str = ""
    エージェント名: str = ""
    役割: str = ""


class 状態変更要求(BaseModel):
    エージェントID: str
    状態: str
    作業内容: str = ""
    ひとこと: str = ""


class 排除要求(BaseModel):
    要員ID: str


class 活動一覧要求(BaseModel):
    limit: int = Field(default=20, ge=1, le=50)


class シミュレーション切替要求(BaseModel):
    有効: bool


class 操作情報(BaseModel):
    操作利用者ID: str = "admin"
    操作利用者名: str = "admin"
    操作端末ID: str = "frontend_web"

    def 操作者(self) -> dict[str, str]:
        return {
            "利用者ID": self.操作利用者ID.strip() or "admin",
            "利用者名": self.操作利用者名.strip() or "admin",
            "端末ID": self.操作端末ID.strip() or "frontend_web",
        }


class 要員一覧要求(BaseModel):
    無効も表示: bool = False


class 要員取得要求(BaseModel):
    要員ID: str


class 要員保存要求(操作情報):
    要員ID: str
    要員名: str
    役割: str = ""
    人格情報: str = ""
    有効: bool = True


class 要員削除要求(操作情報):
    要員ID: str


class チーム作業一覧要求(BaseModel):
    要員ID: str = "admin"


class チーム作業取得要求(チーム作業一覧要求):
    作業ID: str


class チーム作業保存要求(操作情報):
    要員ID: str = ""
    作業ID: str = ""
    プロジェクト: str = ""
    要求内容: str
    TEAM_AI_NAME: str = "claude_cli"
    TEAM_AI_MODEL: str = "auto"
    TASK_AI_NAME: str = "claude_cli"
    TASK_AI_MODEL: str = "auto"
    実行有効: bool = True
    状態: str = "準備開始"


@router.post("/状態/取得", tags=["AIチーム"])
async def 状態取得() -> dict:
    try:
        return ok("チーム状態を取得しました", ストア.スナップショット())
    except Exception as e:
        logger.error(f"チーム状態の取得に失敗: {e}")
        return ng(f"チーム状態の取得に失敗しました: {e}")


@router.post("/設定/取得", tags=["AIチーム"])
async def チーム設定取得() -> dict:
    try:
        config = 設定読込()
        return ok("チーム設定を取得しました", {
            "CODE_BASE_PATH": str(config.CODE_BASE_PATH),
            "TEAM_AI_NAME": str(config.TEAM_AI_NAME),
            "TEAM_AI_MODEL": str(config.TEAM_AI_MODEL),
            "TASK_AI_NAME": str(config.TASK_AI_NAME),
            "TASK_AI_MODEL": str(config.TASK_AI_MODEL),
        })
    except Exception as e:
        logger.error(f"チーム設定の取得に失敗: {e}")
        return ng(f"チーム設定の取得に失敗しました: {e}")


@router.post("/エージェント/一覧", tags=["AIチーム"])
async def エージェント一覧() -> dict:
    try:
        items = ストア.エージェント一覧()
        return ok(f"{len(items)}件取得しました", {"items": items, "total": len(items)})
    except Exception as e:
        logger.error(f"エージェント一覧の取得に失敗: {e}")
        return ng(f"エージェント一覧の取得に失敗しました: {e}")


@router.post("/エージェント/召喚", tags=["AIチーム"])
async def エージェント召喚(request: 召喚要求) -> dict:
    try:
        要員ID = request.要員ID.strip() or request.エージェント名.strip()
        item = ストア.召喚(要員ID, request.役割)
        return ok("エージェントを召喚しました", item)
    except ValueError as exc:
        return ng(str(exc))
    except Exception as e:
        logger.error(f"エージェントの召喚に失敗: {e}")
        return ng(f"エージェントの召喚に失敗しました: {e}")


@router.post("/エージェント/状態変更", tags=["AIチーム"])
async def エージェント状態変更(request: 状態変更要求) -> dict:
    try:
        item = ストア.状態変更(
            request.エージェントID,
            request.状態,
            request.作業内容,
            request.ひとこと,
        )
        return ok("エージェント状態を変更しました", item)
    except KeyError:
        return ng("対象エージェントが見つかりません")
    except ValueError as exc:
        return ng(str(exc))
    except Exception as e:
        logger.error(f"エージェント状態の変更に失敗: {e}")
        return ng(f"エージェント状態の変更に失敗しました: {e}")


@router.post("/エージェント/排除", tags=["AIチーム"])
async def エージェント排除(request: 排除要求) -> dict:
    try:
        item = ストア.排除(request.要員ID)
        return ok("エージェントを排除しました", item)
    except KeyError:
        return ng("対象エージェントが見つかりません")
    except ValueError as exc:
        return ng(str(exc))
    except Exception as e:
        logger.error(f"エージェントの排除に失敗: {e}")
        return ng(f"エージェントの排除に失敗しました: {e}")


@router.post("/活動/一覧", tags=["AIチーム"])
async def 活動一覧(request: 活動一覧要求) -> dict:
    try:
        items = ストア.活動一覧(request.limit)
        return ok(f"{len(items)}件取得しました", {"items": items, "total": len(items)})
    except Exception as e:
        logger.error(f"活動一覧の取得に失敗: {e}")
        return ng(f"活動一覧の取得に失敗しました: {e}")


@router.post("/シミュレーション/切替", tags=["AIチーム"])
async def シミュレーション切替(request: シミュレーション切替要求) -> dict:
    try:
        有効 = ストア.シミュレーション切替(request.有効)
        return ok("シミュレーション状態を変更しました", {"有効": 有効})
    except Exception as e:
        logger.error(f"シミュレーション状態の変更に失敗: {e}")
        return ng(f"シミュレーション状態の変更に失敗しました: {e}")


@router.post("/召喚要員/一覧", tags=["AIチーム"])
async def 召喚要員一覧() -> dict:
    try:
        items = persona_catalog.召喚要員一覧()
        return ok(f"{len(items)}件取得しました", {"items": items, "total": len(items)})
    except ValueError as exc:
        return ng(str(exc))
    except Exception as e:
        logger.error(f"召喚要員一覧の取得に失敗: {e}")
        return ng(f"召喚要員一覧の取得に失敗しました: {e}")


@router.post("/要員/一覧", tags=["チーム要員"])
async def 要員一覧(request: 要員一覧要求) -> dict:
    try:
        items = team_db.要員一覧(無効も表示=request.無効も表示)
        return ok(f"{len(items)}件取得しました", {"items": items, "total": len(items)})
    except Exception as e:
        logger.error(f"要員一覧の取得に失敗: {e}")
        return ng(f"要員一覧の取得に失敗しました: {e}")


@router.post("/要員/取得", tags=["チーム要員"])
async def 要員取得(request: 要員取得要求) -> dict:
    try:
        item = team_db.要員取得(request.要員ID.strip())
        return ok("要員を取得しました", item) if item else ng("対象要員が見つかりません")
    except Exception as e:
        logger.error(f"要員の取得に失敗: {e}")
        return ng(f"要員の取得に失敗しました: {e}")


def _要員データ(request: 要員保存要求) -> dict:
    要員ID = request.要員ID.strip()
    要員名 = request.要員名.strip()
    if not 要員ID:
        raise ValueError("要員IDを指定してください")
    if not 要員名:
        raise ValueError("要員名を指定してください")
    return {
        "要員ID": 要員ID,
        "要員名": 要員名,
        "役割": request.役割.strip(),
        "人格情報": request.人格情報.strip(),
        "有効": request.有効,
    }


@router.post("/要員/登録", tags=["チーム要員"])
async def 要員登録(request: 要員保存要求) -> dict:
    try:
        item = team_db.要員登録(_要員データ(request), request.操作者())
        ストア.要員再読込()
        return ok("要員を登録しました", item)
    except ValueError as exc:
        return ng(str(exc))
    except Exception as e:
        logger.error(f"要員の登録に失敗: {e}")
        return ng(f"要員の登録に失敗しました: {e}")


@router.post("/要員/変更", tags=["チーム要員"])
async def 要員変更(request: 要員保存要求) -> dict:
    try:
        item = team_db.要員変更(_要員データ(request), request.操作者())
        ストア.要員再読込()
        return ok("要員を変更しました", item)
    except KeyError:
        return ng("対象要員が見つかりません")
    except ValueError as exc:
        return ng(str(exc))
    except Exception as e:
        logger.error(f"要員の変更に失敗: {e}")
        return ng(f"要員の変更に失敗しました: {e}")


@router.post("/要員/削除", tags=["チーム要員"])
async def 要員削除(request: 要員削除要求) -> dict:
    try:
        team_db.要員削除(request.要員ID.strip())
        ストア.要員再読込()
        return ok("要員を削除しました")
    except KeyError:
        return ng("対象要員が見つかりません")
    except ValueError as exc:
        return ng(str(exc))
    except Exception as e:
        logger.error(f"要員の削除に失敗: {e}")
        return ng(f"要員の削除に失敗しました: {e}")


@router.post("/作業/一覧", tags=["チーム作業"])
async def チーム作業一覧(request: チーム作業一覧要求) -> dict:
    try:
        要員ID = request.要員ID.strip()
        if not 要員ID:
            return ng("要員IDを指定してください")
        items = team_work_db.作業一覧(要員ID)
        return ok(f"{len(items)}件取得しました", {"items": items, "total": len(items)})
    except Exception as e:
        logger.error(f"チーム作業一覧の取得に失敗: {e}")
        return ng(f"チーム作業一覧の取得に失敗しました: {e}")


@router.post("/作業/最大更新日時", tags=["チーム作業"])
async def チーム作業最大更新日時(request: チーム作業一覧要求) -> dict:
    try:
        要員ID = request.要員ID.strip()
        if not 要員ID:
            return ng("要員IDを指定してください")
        return ok(
            "最大更新日時を取得しました",
            {"最大更新日時": team_work_db.作業最大更新日時(要員ID)},
        )
    except Exception as e:
        logger.error(f"チーム作業最大更新日時の取得に失敗: {e}")
        return ng(f"チーム作業最大更新日時の取得に失敗しました: {e}")


@router.post("/作業/取得", tags=["チーム作業"])
async def チーム作業取得(request: チーム作業取得要求) -> dict:
    try:
        要員ID = request.要員ID.strip()
        作業ID = request.作業ID.strip()
        if not 要員ID or not 作業ID:
            return ng("要員IDと作業IDを指定してください")
        item = team_work_db.作業取得(要員ID, 作業ID)
        return ok("作業を取得しました", {"item": item}) if item else ng("対象作業が見つかりません")
    except Exception as e:
        logger.error(f"チーム作業の取得に失敗: {e}")
        return ng(f"チーム作業の取得に失敗しました: {e}")


def _作業データ(request: チーム作業保存要求, 編集中: bool) -> dict:
    要員ID = request.要員ID.strip() or request.操作利用者ID.strip() or "admin"
    作業ID = request.作業ID.strip()
    要求内容 = request.要求内容.strip()
    if 編集中 and not 作業ID:
        raise ValueError("作業IDを指定してください")
    if not 要求内容:
        raise ValueError("要求内容を入力してください")
    if request.状態 not in team_work_db.状態入力一覧:
        raise ValueError("状態が正しくありません")
    return {
        "要員ID": 要員ID,
        "作業ID": 作業ID,
        "プロジェクト": request.プロジェクト.strip(),
        "要求内容": 要求内容,
        "TEAM_AI_NAME": request.TEAM_AI_NAME.strip() or "claude_cli",
        "TEAM_AI_MODEL": request.TEAM_AI_MODEL.strip() or "auto",
        "TASK_AI_NAME": request.TASK_AI_NAME.strip() or "claude_cli",
        "TASK_AI_MODEL": request.TASK_AI_MODEL.strip() or "auto",
        "実行有効": request.実行有効,
        "状態": request.状態,
    }


@router.post("/作業/登録", tags=["チーム作業"])
async def チーム作業登録(request: チーム作業保存要求) -> dict:
    try:
        item = team_work_db.作業登録(_作業データ(request, 編集中=False), request.操作者())
        return ok(f"作業 {item['作業ID']} を登録しました", {"item": item})
    except ValueError as exc:
        return ng(str(exc))
    except Exception as e:
        logger.error(f"チーム作業の登録に失敗: {e}")
        return ng(f"チーム作業の登録に失敗しました: {e}")


@router.post("/作業/変更", tags=["チーム作業"])
async def チーム作業変更(request: チーム作業保存要求) -> dict:
    try:
        item = team_work_db.作業変更(_作業データ(request, 編集中=True), request.操作者())
        return ok(f"作業 {item['作業ID']} を変更しました", {"item": item})
    except KeyError:
        return ng("対象作業が見つかりません")
    except ValueError as exc:
        return ng(str(exc))
    except Exception as e:
        logger.error(f"チーム作業の変更に失敗: {e}")
        return ng(f"チーム作業の変更に失敗しました: {e}")


@router.post("/状況/一覧", tags=["チーム状況"])
async def チーム状況一覧() -> dict:
    """要員ごとのAタスク要求集計（待機数・実行数・完了数・エラー数）を取得する。

    集計自体はbackend_task側（10秒間隔）が行い、Aチーム状況テーブルを作り直している。
    """
    try:
        items = team_status_db.状況一覧()
        return ok(f"{len(items)}件取得しました", {"items": items, "total": len(items)})
    except Exception as e:
        logger.error(f"チーム状況一覧の取得に失敗: {e}")
        return ng(f"チーム状況一覧の取得に失敗しました: {e}")
