# -*- coding: utf-8 -*-

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
