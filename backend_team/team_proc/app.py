# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""backend_team の FastAPI アプリ生成。"""

from __future__ import annotations

from fastapi import FastAPI

from log_config import get_logger

from .routes import router
from .runtime import build_lifespan, setup_reboot_watcher
from .team_api import router as team_router


def create_app() -> FastAPI:
    logger = get_logger("team_main")
    team_app = FastAPI(
        title="AiDiy Backend Team",
        version="0.1.0",
        openapi_tags=[
            {"name": "default", "description": "backend_team の稼働確認 API"},
            {"name": "AIチーム", "description": "エージェントの状態、召喚、活動履歴 API"},
            {"name": "チーム要員", "description": "Aチーム要員の保守 API"},
            {"name": "チーム作業", "description": "Aチーム作業の保守 API"},
        ],
        lifespan=build_lifespan(logger),
    )
    team_app.include_router(router)
    team_app.include_router(team_router)
    setup_reboot_watcher(logger)
    return team_app
