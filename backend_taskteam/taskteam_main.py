# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""バックエンド(task,team) FastAPI エントリポイント。"""

from __future__ import annotations

from log_config import setup_logging
from taskteam_proc.app import create_app

setup_logging("taskteam_main")

PORT_TASKTEAM = 8093

app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("taskteam_main:app", host="0.0.0.0", port=PORT_TASKTEAM)
