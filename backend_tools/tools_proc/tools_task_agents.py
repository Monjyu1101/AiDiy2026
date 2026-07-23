# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""aidiy_task_agents MCP ツール登録 + HTTP ルート"""

import asyncio
import json
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from log_config import get_logger

logger = get_logger(__name__)


class TaskAgentsRequest(BaseModel):
    prompt: str = ""
    project_path: Optional[str] = None
    ai_name: str = "claude_cli"
    ai_model: str = "auto"
    user_id: str = "admin"
    task_id: str = ""
    利用者ID: str = ""
    タスクID: str = ""
    enabled: bool = True
    return_task_id: bool = True
    request_timeout_sec: int = 15


def register_tools(mcp_ta, task_agents):
    """aidiy_task_agents MCP ツールを登録する。"""

    @mcp_ta.tool()
    async def task_agents_config() -> str:
        """backend_task API の接続先と疎通状態を返す。"""
        info = await asyncio.to_thread(task_agents.get_config)
        return json.dumps(info, ensure_ascii=False)

    @mcp_ta.tool()
    async def task_agents_submit(
        prompt: str,
        project_path: Optional[str] = None,
        ai_name: str = "claude_cli",
        ai_model: str = "auto",
        user_id: str = "admin",
        task_id: str = "",
        enabled: bool = True,
        return_task_id: bool = True,
        request_timeout_sec: int = 15,
    ) -> str:
        """
        backend_task の AIタスク要求へ非同期タスクを投入する。
        登録だけを行い、タスク分解や実行完了は待たない。
        task_id は通常指定不要。外部システムのIDを引き継ぐ場合だけ指定する。
        """
        result = await asyncio.to_thread(
            task_agents.submit,
            prompt=prompt,
            project_path=project_path,
            ai_name=ai_name,
            ai_model=ai_model,
            user_id=user_id,
            enabled=enabled,
            return_task_id=return_task_id,
            request_timeout_sec=request_timeout_sec,
            task_id=task_id,
        )
        return json.dumps(result, ensure_ascii=False)

    @mcp_ta.tool()
    async def task_agents_get_request_status(
        user_id: str,
        task_id: str,
        request_timeout_sec: int = 15,
    ) -> str:
        """利用者IDとタスクIDで AIタスク要求 1 件の状態を取得する。"""
        result = await asyncio.to_thread(
            task_agents.get_request_status,
            user_id,
            task_id,
            request_timeout_sec,
        )
        return json.dumps(result, ensure_ascii=False)

    @mcp_ta.tool()
    async def task_agents_get_detail_status(
        user_id: str,
        task_id: str,
        request_timeout_sec: int = 15,
    ) -> str:
        """利用者IDとタスクIDで AIタスク明細一覧の状態を取得する。"""
        result = await asyncio.to_thread(
            task_agents.get_detail_status,
            user_id,
            task_id,
            request_timeout_sec,
        )
        return json.dumps(result, ensure_ascii=False)


def create_router(task_agents) -> APIRouter:
    """aidiy_task_agents HTTP APIRouter を作成して返す。"""
    router = APIRouter(tags=["aidiy_task_agents"])

    @router.get("/aidiy_task_agents/docs", summary="aidiy_task_agents ドキュメント")
    async def http_task_agents_docs() -> dict:
        return {
            "service": "aidiy_task_agents",
            "description": "backend_task API に疎結合で接続し、AIタスク要求を非同期投入する。登録後の分解・実行完了は待たない。",
            "endpoint": "POST /aidiy_task_agents/{method_name}",
            "content_type": "application/json",
            "methods": {
                "config": {
                    "summary": "接続設定取得",
                    "description": "backend_task API の接続先と /health の疎通状態を返す。backend_task 未起動でも error ではなく health.ok=false を返す。",
                    "example_request": {},
                },
                "submit": {
                    "summary": "AIタスク投入",
                    "description": "指定promptをbackend_taskの/task/タスク要求/AI登録へ渡し、タスクを準備開始として登録する。task_idは通常指定不要で、省略時はbackend_taskが自動採番する。8093未起動時はstatus=NGで理由を返す。",
                    "parameters": {
                        "prompt": {"type": "string", "required": True, "description": "タスク化したい依頼内容"},
                        "project_path": {"type": "string", "required": False, "description": "対象プロジェクトのパス。backend_task の プロジェクト に対応"},
                        "ai_name": {"type": "string", "required": False, "default": "claude_cli", "description": "TASK_AI_NAME。claude_sdk / claude_cli / codex_cli / aidiy_hermes など"},
                        "ai_model": {"type": "string", "required": False, "default": "auto", "description": "TASK_AI_MODEL"},
                        "user_id": {"type": "string", "required": False, "default": "admin", "description": "利用者ID"},
                        "task_id": {"type": "string", "required": False, "default": "", "description": "任意のタスクID。通常は指定不要。外部IDを引き継ぐ場合だけ指定し、省略時はTASK.mmdd.hhmmssで自動採番"},
                        "enabled": {"type": "boolean", "required": False, "default": True, "description": "有効。true なら backend_task の watcher が処理対象にする"},
                        "return_task_id": {"type": "boolean", "required": False, "default": True, "description": "応答に task_id を含める"},
                        "request_timeout_sec": {"type": "integer", "required": False, "default": 15, "description": "登録 API 呼び出しのタイムアウト秒"},
                    },
                    "example_request": {
                        "prompt": "frontend_web の AIタスク画面にローディング表示を追加してください",
                        "project_path": "/workspaces/AiDiy2026",
                        "ai_name": "codex_cli",
                        "ai_model": "auto",
                    },
                    "response_fields": {
                        "status": "OK / NG",
                        "message": "投入結果の短いメッセージ",
                        "利用者ID": "登録時に使った利用者ID",
                        "タスクID": "登録された AIタスク要求のタスクID",
                        "task_id": "登録された AIタスク要求のタスクID。return_task_id=true のときだけ返す互換フィールド",
                    },
                },
                "get_request_status": {
                    "summary": "AIタスク要求状態取得",
                    "description": "利用者IDとタスクIDで /task/タスク要求/取得 を呼び出し、画面表示で使う要求ヘッダー相当の item を返す。",
                    "parameters": {
                        "user_id": {"type": "string", "required": True, "description": "利用者ID"},
                        "task_id": {"type": "string", "required": True, "description": "タスクID"},
                        "request_timeout_sec": {"type": "integer", "required": False, "default": 15},
                    },
                    "example_request": {"user_id": "admin", "task_id": "TASK.0709.123456"},
                },
                "get_detail_status": {
                    "summary": "AIタスク明細状態取得",
                    "description": "利用者IDとタスクIDで /task/タスク明細/一覧 を呼び出し、画面表示で使う明細一覧相当の items と total を返す。",
                    "parameters": {
                        "user_id": {"type": "string", "required": True, "description": "利用者ID"},
                        "task_id": {"type": "string", "required": True, "description": "タスクID"},
                        "request_timeout_sec": {"type": "integer", "required": False, "default": 15},
                    },
                    "example_request": {"user_id": "admin", "task_id": "TASK.0709.123456"},
                },
                "run": {
                    "summary": "AIタスク投入（submit の別名）",
                    "description": "aidiy_code_agents 互換の呼び出し名として用意した submit の別名。実行完了は待たない。",
                },
            },
        }

    @router.post("/aidiy_task_agents/{method_name}", summary="AIタスク投入")
    async def http_task_agents(method_name: str, req: TaskAgentsRequest = TaskAgentsRequest()) -> dict:
        try:
            if method_name == "config":
                return await asyncio.to_thread(task_agents.get_config)
            if method_name in {"submit", "run"}:
                return await asyncio.to_thread(
                    task_agents.submit,
                    prompt=req.prompt,
                    project_path=req.project_path,
                    ai_name=req.ai_name,
                    ai_model=req.ai_model,
                    user_id=req.user_id,
                    enabled=req.enabled,
                    return_task_id=req.return_task_id,
                    request_timeout_sec=req.request_timeout_sec,
                    task_id=req.task_id or req.タスクID,
                )
            if method_name == "get_request_status":
                user_id = req.利用者ID or req.user_id
                task_id = req.タスクID or req.task_id
                return await asyncio.to_thread(
                    task_agents.get_request_status,
                    user_id,
                    task_id,
                    req.request_timeout_sec,
                )
            if method_name == "get_detail_status":
                user_id = req.利用者ID or req.user_id
                task_id = req.タスクID or req.task_id
                return await asyncio.to_thread(
                    task_agents.get_detail_status,
                    user_id,
                    task_id,
                    req.request_timeout_sec,
                )
            return {"status": "NG", "message": f"未知のメソッド: {method_name}"}
        except Exception as e:
            logger.warning(f"http_task_agents [{method_name}] error: {e}")
            return {"status": "NG", "message": str(e)}

    return router
