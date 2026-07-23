# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel, Field

from .store import store
from . import persona_catalog, team_db, team_work_db
from .config import load_config

router = APIRouter()


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

    def operator(self) -> dict[str, str]:
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
    利用者ID: str = "admin"


class チーム作業取得要求(チーム作業一覧要求):
    作業ID: str


class チーム作業保存要求(操作情報):
    利用者ID: str = "admin"
    作業ID: str = ""
    プロジェクト: str = ""
    要求内容: str
    TEAM_AI_NAME: str = "claude_cli"
    TEAM_AI_MODEL: str = "auto"
    TASK_AI_NAME: str = "claude_cli"
    TASK_AI_MODEL: str = "auto"
    実行有効: bool = True
    状態: str = "準備開始"


@router.get("/")
async def root() -> dict:
    return ok("backend_team is running", {
        "service": "backend_team",
        "time": datetime.now().astimezone().isoformat(timespec="seconds"),
    })


@router.get("/health")
async def health() -> dict:
    return ok("healthy", {"service": "backend_team"})


@router.post("/team/状態/取得")
async def 状態取得() -> dict:
    return ok("チーム状態を取得しました", store.snapshot())


@router.post("/team/設定/取得")
async def チーム設定取得() -> dict:
    config = load_config()
    return ok("チーム設定を取得しました", {
        "CODE_BASE_PATH": str(config.CODE_BASE_PATH),
        "TEAM_AI_NAME": str(config.TEAM_AI_NAME),
        "TEAM_AI_MODEL": str(config.TEAM_AI_MODEL),
        "TASK_AI_NAME": str(config.TASK_AI_NAME),
        "TASK_AI_MODEL": str(config.TASK_AI_MODEL),
    })


@router.post("/team/エージェント/一覧")
async def エージェント一覧() -> dict:
    agents = store.list_agents()
    return ok(f"{len(agents)}件取得しました", {"items": agents, "total": len(agents)})


@router.post("/team/エージェント/召喚")
async def エージェント召喚(request: 召喚要求) -> dict:
    try:
        member_id = request.要員ID.strip() or request.エージェント名.strip()
        agent = store.summon(member_id, request.役割)
        return ok("エージェントを召喚しました", agent)
    except ValueError as exc:
        return ng(str(exc))


@router.post("/team/エージェント/状態変更")
async def エージェント状態変更(request: 状態変更要求) -> dict:
    try:
        agent = store.update_state(
            request.エージェントID,
            request.状態,
            request.作業内容,
            request.ひとこと,
        )
        return ok("エージェント状態を変更しました", agent)
    except KeyError:
        return ng("対象エージェントが見つかりません")
    except ValueError as exc:
        return ng(str(exc))


@router.post("/team/エージェント/排除")
async def エージェント排除(request: 排除要求) -> dict:
    try:
        item = store.expel(request.要員ID)
        return ok("エージェントを排除しました", item)
    except KeyError:
        return ng("対象エージェントが見つかりません")
    except ValueError as exc:
        return ng(str(exc))


@router.post("/team/活動/一覧")
async def 活動一覧(request: 活動一覧要求) -> dict:
    activities = store.list_activities(request.limit)
    return ok(f"{len(activities)}件取得しました", {"items": activities, "total": len(activities)})


@router.post("/team/シミュレーション/切替")
async def シミュレーション切替(request: シミュレーション切替要求) -> dict:
    enabled = store.set_simulation(request.有効)
    return ok("シミュレーション状態を変更しました", {"有効": enabled})


@router.post("/team/召喚要員/一覧")
async def 召喚要員一覧() -> dict:
    try:
        items = persona_catalog.list_personas()
        return ok(f"{len(items)}件取得しました", {"items": items, "total": len(items)})
    except ValueError as exc:
        return ng(str(exc))


@router.post("/team/要員/一覧")
async def 要員一覧(request: 要員一覧要求) -> dict:
    items = team_db.list_members(include_disabled=request.無効も表示)
    return ok(f"{len(items)}件取得しました", {"items": items, "total": len(items)})


@router.post("/team/要員/取得")
async def 要員取得(request: 要員取得要求) -> dict:
    item = team_db.get_member(request.要員ID.strip())
    return ok("要員を取得しました", item) if item else ng("対象要員が見つかりません")


def _member_data(request: 要員保存要求) -> dict:
    member_id = request.要員ID.strip()
    member_name = request.要員名.strip()
    if not member_id:
        raise ValueError("要員IDを指定してください")
    if not member_name:
        raise ValueError("要員名を指定してください")
    return {
        "要員ID": member_id,
        "要員名": member_name,
        "役割": request.役割.strip(),
        "人格情報": request.人格情報.strip(),
        "有効": request.有効,
    }


@router.post("/team/要員/登録")
async def 要員登録(request: 要員保存要求) -> dict:
    try:
        item = team_db.create_member(_member_data(request), request.operator())
        store.reload_members()
        return ok("要員を登録しました", item)
    except ValueError as exc:
        return ng(str(exc))


@router.post("/team/要員/変更")
async def 要員変更(request: 要員保存要求) -> dict:
    try:
        item = team_db.update_member(_member_data(request), request.operator())
        store.reload_members()
        return ok("要員を変更しました", item)
    except KeyError:
        return ng("対象要員が見つかりません")
    except ValueError as exc:
        return ng(str(exc))


@router.post("/team/要員/削除")
async def 要員削除(request: 要員削除要求) -> dict:
    try:
        team_db.delete_member(request.要員ID.strip())
        store.reload_members()
        return ok("要員を削除しました")
    except KeyError:
        return ng("対象要員が見つかりません")
    except ValueError as exc:
        return ng(str(exc))


@router.post("/team/作業/一覧")
async def チーム作業一覧(request: チーム作業一覧要求) -> dict:
    user_id = request.利用者ID.strip()
    if not user_id:
        return ng("利用者IDを指定してください")
    items = team_work_db.list_works(user_id)
    return ok(f"{len(items)}件取得しました", {"items": items, "total": len(items)})


@router.post("/team/作業/最大更新日時")
async def チーム作業最大更新日時(request: チーム作業一覧要求) -> dict:
    user_id = request.利用者ID.strip()
    if not user_id:
        return ng("利用者IDを指定してください")
    return ok(
        "最大更新日時を取得しました",
        {"最大更新日時": team_work_db.max_updated_at(user_id)},
    )


@router.post("/team/作業/取得")
async def チーム作業取得(request: チーム作業取得要求) -> dict:
    user_id = request.利用者ID.strip()
    work_id = request.作業ID.strip()
    if not user_id or not work_id:
        return ng("利用者IDと作業IDを指定してください")
    item = team_work_db.get_work(user_id, work_id)
    return ok("作業を取得しました", {"item": item}) if item else ng("対象作業が見つかりません")


def _work_data(request: チーム作業保存要求, editing: bool) -> dict:
    user_id = request.利用者ID.strip()
    work_id = request.作業ID.strip()
    request_content = request.要求内容.strip()
    if not user_id:
        raise ValueError("利用者IDを指定してください")
    if editing and not work_id:
        raise ValueError("作業IDを指定してください")
    if not request_content:
        raise ValueError("要求内容を入力してください")
    if request.状態 not in team_work_db.状態入力一覧:
        raise ValueError("状態が正しくありません")
    return {
        "利用者ID": user_id,
        "作業ID": work_id,
        "プロジェクト": request.プロジェクト.strip(),
        "要求内容": request_content,
        "TEAM_AI_NAME": request.TEAM_AI_NAME.strip() or "claude_cli",
        "TEAM_AI_MODEL": request.TEAM_AI_MODEL.strip() or "auto",
        "TASK_AI_NAME": request.TASK_AI_NAME.strip() or "claude_cli",
        "TASK_AI_MODEL": request.TASK_AI_MODEL.strip() or "auto",
        "実行有効": request.実行有効,
        "状態": request.状態,
    }


@router.post("/team/作業/登録")
async def チーム作業登録(request: チーム作業保存要求) -> dict:
    try:
        item = team_work_db.create_work(_work_data(request, editing=False), request.operator())
        return ok(f"作業 {item['作業ID']} を登録しました", {"item": item})
    except ValueError as exc:
        return ng(str(exc))


@router.post("/team/作業/変更")
async def チーム作業変更(request: チーム作業保存要求) -> dict:
    try:
        item = team_work_db.update_work(_work_data(request, editing=True), request.operator())
        return ok(f"作業 {item['作業ID']} を変更しました", {"item": item})
    except KeyError:
        return ng("対象作業が見つかりません")
    except ValueError as exc:
        return ng(str(exc))
