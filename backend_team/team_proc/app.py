# -*- coding: utf-8 -*-

from fastapi import FastAPI

from log_config import get_logger

from .routes import router
from .runtime import lifespan, setup_reboot_watcher


def create_app() -> FastAPI:
    logger = get_logger("team_main")
    app = FastAPI(
        title="AiDiy Backend Team",
        description="複数AIエージェントのチーム活動を表現する仮実装API",
        version="0.1.0-mock",
        lifespan=lifespan,
        openapi_tags=[
            {"name": "default", "description": "backend_team の稼働確認"},
            {"name": "AIチーム", "description": "エージェントの状態、召喚、活動履歴のモックAPI"},
            {"name": "チーム要員", "description": "Aチーム要員の保守API"},
            {"name": "チーム作業", "description": "Aチーム作業の保守API"},
        ],
    )
    app.include_router(router)
    setup_reboot_watcher(logger)
    return app
