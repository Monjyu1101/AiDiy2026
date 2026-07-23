# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""
Task Agents モジュール

backend_task の HTTP API に疎結合で接続し、AIタスク要求を非同期投入する。
DB 直書きや backend_task の import は行わない。
"""

from __future__ import annotations

import os
from typing import Optional

import requests


class TaskAgents:
    """backend_task API へ AIタスク要求を投入する薄いクライアント"""

    def __init__(self, task_api_base: Optional[str] = None):
        self.task_api_base = (task_api_base or os.environ.get("AIDIY_TASK_API_BASE") or "http://localhost:8093").rstrip("/")

    def get_config(self) -> dict:
        """接続先と疎通状態を返す。backend_task 未起動でも例外にしない。"""
        health_url = f"{self.task_api_base}/health"
        info = {
            "task_api_base": self.task_api_base,
            "submit_endpoint": f"{self.task_api_base}/task/タスク要求/AI登録",
            "health": {"ok": False, "url": health_url, "message": ""},
        }
        try:
            res = requests.get(health_url, timeout=3)
            info["health"] = {
                "ok": res.ok,
                "url": health_url,
                "status_code": res.status_code,
                "message": res.text[:300],
            }
        except requests.RequestException as e:
            info["health"]["message"] = f"backend_task に接続できません: {e}"
        return info

    def _post_task_api(self, path: str, payload: dict, request_timeout_sec: int) -> dict:
        """backend_task の API を POST で呼び出す。接続不能時も dict で返す。"""
        url = f"{self.task_api_base}{path}"
        try:
            res = requests.post(url, json=payload, timeout=max(1, int(request_timeout_sec)))
            res.raise_for_status()
            return res.json()
        except requests.RequestException as e:
            return {
                "status": "NG",
                "message": (
                    f"backend_task ({self.task_api_base}) に接続できません。"
                    f"backend_task を起動してから再実行してください。"
                ),
                "error": str(e),
            }
        except ValueError as e:
            return {
                "status": "NG",
                "message": "backend_task から JSON ではない応答が返りました。",
                "error": str(e),
            }

    def submit(
        self,
        prompt: str,
        project_path: Optional[str] = None,
        ai_name: str = "claude_cli",
        ai_model: str = "auto",
        user_id: str = "admin",
        enabled: bool = True,
        return_task_id: bool = True,
        request_timeout_sec: int = 15,
        task_id: Optional[str] = None,
    ) -> dict:
        """AIタスク要求を登録する。task_idは通常省略し、外部IDを引き継ぐ場合だけ指定する。"""
        prompt = (prompt or "").strip()
        user_id = (user_id or "").strip() or "admin"
        task_id = (task_id or "").strip()
        if not prompt:
            return {"status": "NG", "message": "prompt を指定してください。"}

        payload = {
            "利用者ID": user_id,
            "プロジェクト": (project_path or "").strip(),
            "要求内容": prompt,
            "TASK_AI_NAME": (ai_name or "").strip() or "claude_cli",
            "TASK_AI_MODEL": (ai_model or "").strip() or "auto",
            "実行有効": bool(enabled),
        }
        if task_id:
            payload["タスクID"] = task_id
        data = self._post_task_api("/task/タスク要求/AI登録", payload, request_timeout_sec)

        if data.get("status") != "OK":
            return {
                "status": "NG",
                "message": str(data.get("message") or "backend_task へのタスク投入に失敗しました。"),
                "利用者ID": user_id,
            }

        item = data.get("data", {}).get("item", {})
        task_id = str(item.get("タスクID", ""))
        result = {
            "status": "OK",
            "message": "タスクを投入しました。",
            "利用者ID": str(item.get("利用者ID") or user_id),
            "タスクID": task_id,
        }
        if return_task_id:
            result["task_id"] = task_id
        return result

    def get_request_status(self, user_id: str, task_id: str, request_timeout_sec: int = 15) -> dict:
        """AIタスク要求 1 件の状態を backend_task API から取得する。"""
        user_id = (user_id or "").strip()
        task_id = (task_id or "").strip()
        if not user_id or not task_id:
            return {"status": "NG", "message": "利用者IDとタスクIDを指定してください。"}
        data = self._post_task_api(
            "/task/タスク要求/取得",
            {"利用者ID": user_id, "タスクID": task_id},
            request_timeout_sec,
        )
        if data.get("status") != "OK":
            return {
                "status": "NG",
                "message": str(data.get("message") or "タスク要求の取得に失敗しました。"),
                "利用者ID": user_id,
                "タスクID": task_id,
            }
        return {
            "status": "OK",
            "message": str(data.get("message") or ""),
            "利用者ID": user_id,
            "タスクID": task_id,
            "item": data.get("data", {}).get("item", {}),
        }

    def get_detail_status(self, user_id: str, task_id: str, request_timeout_sec: int = 15) -> dict:
        """AIタスク明細一覧の状態を backend_task API から取得する。"""
        user_id = (user_id or "").strip()
        task_id = (task_id or "").strip()
        if not user_id or not task_id:
            return {"status": "NG", "message": "利用者IDとタスクIDを指定してください。"}
        data = self._post_task_api(
            "/task/タスク明細/一覧",
            {"利用者ID": user_id, "タスクID": task_id},
            request_timeout_sec,
        )
        if data.get("status") != "OK":
            return {
                "status": "NG",
                "message": str(data.get("message") or "タスク明細の取得に失敗しました。"),
                "利用者ID": user_id,
                "タスクID": task_id,
            }
        body = data.get("data", {})
        items = body.get("items", [])
        return {
            "status": "OK",
            "message": str(data.get("message") or ""),
            "利用者ID": user_id,
            "タスクID": task_id,
            "items": items,
            "total": body.get("total", len(items) if isinstance(items, list) else 0),
        }
