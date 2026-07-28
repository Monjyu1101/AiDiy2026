# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""aidiy_team_agents MCP ツール登録 + HTTP ルート"""

import asyncio
import json
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from log_config import get_logger

logger = get_logger(__name__)


class TeamAgentsRequest(BaseModel):
    prompt: str = ""
    # project_path / team_ai_* / task_ai_* は未指定（null）可。
    # backend_team が AIチーム_作業編集の新規時と同じ条件（更新最終レコード → 規定値）で補完する
    project_path: Optional[str] = None
    member_id: str = "admin"
    team_ai_name: Optional[str] = None
    team_ai_model: Optional[str] = None
    task_ai_name: Optional[str] = None
    task_ai_model: Optional[str] = None
    work_id: str = ""
    要員ID: str = ""
    作業ID: str = ""
    include_disabled: bool = False
    enabled: bool = True
    return_work_id: bool = True
    request_timeout_sec: int = 15


def register_tools(mcp_te, team_agents):
    """aidiy_team_agents MCP ツールを登録する。"""

    @mcp_te.tool()
    async def team_agents_config() -> str:
        """backend_team API の接続先と疎通状態を返す。"""
        info = await asyncio.to_thread(team_agents.get_config)
        return json.dumps(info, ensure_ascii=False)

    @mcp_te.tool()
    async def team_agents_submit(
        prompt: str,
        project_path: Optional[str] = None,
        member_id: str = "admin",
        team_ai_name: Optional[str] = None,
        team_ai_model: Optional[str] = None,
        task_ai_name: Optional[str] = None,
        task_ai_model: Optional[str] = None,
        enabled: bool = True,
        return_work_id: bool = True,
        request_timeout_sec: int = 15,
    ) -> str:
        """
        backend_team の Aチーム作業へ非同期作業を投入する。
        登録だけを行い、AIタスク要求への投入や実行完了は待たない
        （登録後は backend_team の起動監視ループが AIタスク要求へ投入する）。
        作業IDは backend_team が TW+8桁で自動採番する。
        project_path / team_ai_name / team_ai_model / task_ai_name / task_ai_model は通常指定不要。
        未指定なら AIチーム画面の新規時と同じ条件
        （要員IDの更新最終レコードの値、無ければ規定値）で補完される。
        """
        result = await asyncio.to_thread(
            team_agents.submit,
            prompt=prompt,
            project_path=project_path,
            member_id=member_id,
            team_ai_name=team_ai_name,
            team_ai_model=team_ai_model,
            task_ai_name=task_ai_name,
            task_ai_model=task_ai_model,
            enabled=enabled,
            return_work_id=return_work_id,
            request_timeout_sec=request_timeout_sec,
        )
        return json.dumps(result, ensure_ascii=False)

    @mcp_te.tool()
    async def team_agents_get_work_status(
        member_id: str,
        work_id: str,
        request_timeout_sec: int = 15,
    ) -> str:
        """要員IDと作業IDで Aチーム作業 1 件の状態を取得する。"""
        result = await asyncio.to_thread(
            team_agents.get_work_status,
            member_id,
            work_id,
            request_timeout_sec,
        )
        return json.dumps(result, ensure_ascii=False)

    @mcp_te.tool()
    async def team_agents_get_work_list(
        member_id: str,
        request_timeout_sec: int = 15,
    ) -> str:
        """要員IDで Aチーム作業一覧の状態を取得する。"""
        result = await asyncio.to_thread(
            team_agents.get_work_list,
            member_id,
            request_timeout_sec,
        )
        return json.dumps(result, ensure_ascii=False)

    @mcp_te.tool()
    async def team_agents_get_member_list(
        include_disabled: bool = False,
        request_timeout_sec: int = 15,
    ) -> str:
        """Aチーム要員の一覧を取得する。submit で指定できる要員IDの確認に使う。"""
        result = await asyncio.to_thread(
            team_agents.get_member_list,
            include_disabled,
            request_timeout_sec,
        )
        return json.dumps(result, ensure_ascii=False)


def create_router(team_agents) -> APIRouter:
    """aidiy_team_agents HTTP APIRouter を作成して返す。"""
    router = APIRouter(tags=["aidiy_team_agents"])

    @router.get("/aidiy_team_agents/docs", summary="aidiy_team_agents ドキュメント")
    async def http_team_agents_docs() -> dict:
        return {
            "service": "aidiy_team_agents",
            "description": "backend_team API に疎結合で接続し、Aチーム作業を非同期投入する。登録後のAIタスク投入・実行完了は待たない。",
            "endpoint": "POST /aidiy_team_agents/{method_name}",
            "content_type": "application/json",
            "methods": {
                "config": {
                    "summary": "接続設定取得",
                    "description": "backend_team API の接続先と /health の疎通状態を返す。backend_team 未起動でも error ではなく health.ok=false を返す。",
                    "example_request": {},
                },
                "submit": {
                    "summary": "チーム作業投入",
                    "description": "指定promptをbackend_teamの/team/作業/登録へ渡し、Aチーム作業を準備開始として登録する。作業IDはbackend_teamがTW+8桁で自動採番する。project_path / team_ai_* / task_ai_* は通常指定不要で、省略（null）時は AIチーム_作業編集の新規時と同じ条件（要員IDの更新最終レコードの値、無ければ規定値）で補完する。8094未起動時はstatus=NGで理由を返す。",
                    "parameters": {
                        "prompt": {"type": "string", "required": True, "description": "作業化したい依頼内容"},
                        "project_path": {"type": "string", "required": False, "default": None, "description": "対象プロジェクトのパス。backend_team の プロジェクト に対応。null なら更新最終レコードの値、無ければ規定値（CODE_BASE_PATH）。空文字は明示的な空欄指定"},
                        "member_id": {"type": "string", "required": False, "default": "admin", "description": "要員ID。Aチーム要員の要員ID（get_member_list で確認できる）"},
                        "team_ai_name": {"type": "string", "required": False, "default": None, "description": "TEAM_AI_NAME。null なら更新最終レコードの値、無ければ規定値"},
                        "team_ai_model": {"type": "string", "required": False, "default": None, "description": "TEAM_AI_MODEL。null なら更新最終レコードの値、無ければ規定値"},
                        "task_ai_name": {"type": "string", "required": False, "default": None, "description": "TASK_AI_NAME。null なら更新最終レコードの値、無ければ規定値"},
                        "task_ai_model": {"type": "string", "required": False, "default": None, "description": "TASK_AI_MODEL。null なら更新最終レコードの値、無ければ規定値"},
                        "enabled": {"type": "boolean", "required": False, "default": True, "description": "実行有効。true なら backend_team の watcher が処理対象にする"},
                        "return_work_id": {"type": "boolean", "required": False, "default": True, "description": "応答に work_id を含める"},
                        "request_timeout_sec": {"type": "integer", "required": False, "default": 15, "description": "登録 API 呼び出しのタイムアウト秒"},
                    },
                    "example_request": {
                        "prompt": "frontend_web の AIチーム画面に作業件数の表示を追加してください",
                    },
                    "response_fields": {
                        "status": "OK / NG",
                        "message": "投入結果の短いメッセージ",
                        "要員ID": "登録時に使った要員ID",
                        "作業ID": "登録された Aチーム作業の作業ID",
                        "プロジェクト": "登録に使われたプロジェクト（未指定時は補完後の値）",
                        "TEAM_AI_NAME": "登録に使われた TEAM_AI_NAME（未指定時は補完後の値）",
                        "TEAM_AI_MODEL": "登録に使われた TEAM_AI_MODEL（未指定時は補完後の値）",
                        "TASK_AI_NAME": "登録に使われた TASK_AI_NAME（未指定時は補完後の値）",
                        "TASK_AI_MODEL": "登録に使われた TASK_AI_MODEL（未指定時は補完後の値）",
                        "状態": "登録直後の状態（準備開始）",
                        "work_id": "登録された Aチーム作業の作業ID。return_work_id=true のときだけ返す互換フィールド",
                    },
                },
                "get_work_status": {
                    "summary": "チーム作業状態取得",
                    "description": "要員IDと作業IDで /team/作業/取得 を呼び出し、画面表示で使う作業 1 件の item を返す。",
                    "parameters": {
                        "member_id": {"type": "string", "required": True, "description": "要員ID"},
                        "work_id": {"type": "string", "required": True, "description": "作業ID"},
                        "request_timeout_sec": {"type": "integer", "required": False, "default": 15},
                    },
                    "example_request": {"member_id": "admin", "work_id": "TW00001001"},
                },
                "get_work_list": {
                    "summary": "チーム作業一覧取得",
                    "description": "要員IDで /team/作業/一覧 を呼び出し、画面表示で使う作業一覧相当の items と total を返す。",
                    "parameters": {
                        "member_id": {"type": "string", "required": True, "description": "要員ID"},
                        "request_timeout_sec": {"type": "integer", "required": False, "default": 15},
                    },
                    "example_request": {"member_id": "admin"},
                },
                "get_member_list": {
                    "summary": "チーム要員一覧取得",
                    "description": "/team/要員/一覧 を呼び出し、submit で指定できる要員IDを確認する。",
                    "parameters": {
                        "include_disabled": {"type": "boolean", "required": False, "default": False, "description": "無効な要員も含める"},
                        "request_timeout_sec": {"type": "integer", "required": False, "default": 15},
                    },
                    "example_request": {},
                },
                "run": {
                    "summary": "チーム作業投入（submit の別名）",
                    "description": "aidiy_code_agents / aidiy_task_agents 互換の呼び出し名として用意した submit の別名。実行完了は待たない。",
                },
            },
        }

    @router.post("/aidiy_team_agents/{method_name}", summary="チーム作業投入")
    async def http_team_agents(method_name: str, req: TeamAgentsRequest = TeamAgentsRequest()) -> dict:
        try:
            if method_name == "config":
                return await asyncio.to_thread(team_agents.get_config)
            if method_name in {"submit", "run"}:
                return await asyncio.to_thread(
                    team_agents.submit,
                    prompt=req.prompt,
                    project_path=req.project_path,
                    # 要員ID は補完時の参照キーになるため、日本語キーでの指定も受け付ける
                    member_id=req.要員ID or req.member_id,
                    team_ai_name=req.team_ai_name,
                    team_ai_model=req.team_ai_model,
                    task_ai_name=req.task_ai_name,
                    task_ai_model=req.task_ai_model,
                    enabled=req.enabled,
                    return_work_id=req.return_work_id,
                    request_timeout_sec=req.request_timeout_sec,
                )
            if method_name == "get_work_status":
                member_id = req.要員ID or req.member_id
                work_id = req.作業ID or req.work_id
                return await asyncio.to_thread(
                    team_agents.get_work_status,
                    member_id,
                    work_id,
                    req.request_timeout_sec,
                )
            if method_name == "get_work_list":
                member_id = req.要員ID or req.member_id
                return await asyncio.to_thread(
                    team_agents.get_work_list,
                    member_id,
                    req.request_timeout_sec,
                )
            if method_name == "get_member_list":
                return await asyncio.to_thread(
                    team_agents.get_member_list,
                    req.include_disabled,
                    req.request_timeout_sec,
                )
            return {"status": "NG", "message": f"未知のメソッド: {method_name}"}
        except Exception as e:
            logger.warning(f"http_team_agents [{method_name}] error: {e}")
            return {"status": "NG", "message": str(e)}

    return router
