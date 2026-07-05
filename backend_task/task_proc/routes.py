# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""backend_task の HTTP API ルーター。"""

from __future__ import annotations

from fastapi import APIRouter

from .runtime import now_hms

router = APIRouter()


@router.get("/")
async def root() -> dict[str, str]:
    return {
        "status": "OK",
        "message": "halloworld",
        "time": now_hms(),
    }


@router.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "OK",
        "service": "backend_task",
        "time": now_hms(),
    }
