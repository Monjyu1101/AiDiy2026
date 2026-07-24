# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""backend_team の HTTP API ルーター（稼働確認）。"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def root() -> dict:
    return {
        "status": "OK",
        "message": "backend_team is running",
        "data": {
            "service": "backend_team",
            "time": datetime.now().astimezone().isoformat(timespec="seconds"),
        },
    }


@router.get("/health")
async def health() -> dict:
    return {
        "status": "OK",
        "message": "healthy",
        "data": {"service": "backend_team"},
    }
