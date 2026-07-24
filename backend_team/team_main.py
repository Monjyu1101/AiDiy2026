# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス v1.1".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

"""バックエンド(team) FastAPI エントリポイント。"""

from log_config import setup_logging
from team_proc.app import create_app
from team_proc.config import チームポート取得

setup_logging("team_main")

app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("team_main:app", host="0.0.0.0", port=チームポート取得())
