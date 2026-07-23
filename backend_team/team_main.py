# -*- coding: utf-8 -*-

"""バックエンド(team) FastAPI エントリポイント。"""

from log_config import setup_logging
from team_proc.app import create_app
from team_proc.config import get_team_port

setup_logging("team_main")

app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("team_main:app", host="0.0.0.0", port=get_team_port())
