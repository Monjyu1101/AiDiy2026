# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""backend_task の FastAPI アプリ生成。"""

from __future__ import annotations

from fastapi import FastAPI

from log_config import get_logger

from .routes import router
from .runtime import build_lifespan, setup_reboot_watcher
from .tasks_api import router as tasks_router


def create_app() -> FastAPI:
    logger = get_logger("task_main")
    task_app = FastAPI(
        title="AiDiy Backend Task",
        version="0.1.0",
        openapi_tags=[
            {"name": "default", "description": "backend_task の稼働確認 API"},
            {"name": "タスク要求", "description": "AIタスク要求の一覧、登録、更新 API"},
            {"name": "タスク明細", "description": "AIタスク明細の一覧、更新、実行結果登録 API"},
        ],
        lifespan=build_lifespan(logger),
    )
    task_app.include_router(router)
    task_app.include_router(tasks_router)
    setup_reboot_watcher(logger)
    return task_app
