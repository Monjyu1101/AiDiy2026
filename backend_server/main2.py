# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
# This software is licensed under the MIT License.
# https://github.com/monjyu1101
# Thank you for keeping the rules.
# ------------------------------------------------

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import database, crud2, models2
from conf import conf as app_conf
import os
import sys
import threading
import time
from log_config import setup_logging, get_logger

# ロガー取得
logger = get_logger(__name__)

from routers2 import M配車区分
from routers2 import V配車区分
from routers2 import M車両
from routers2 import V車両
from routers2 import M商品
from routers2 import V商品

from routers2 import T配車
from routers2 import V配車
from routers2 import T商品出庫
from routers2 import V商品出庫
from routers2 import T商品棚卸
from routers2 import V商品棚卸
from routers2 import T商品入庫
from routers2 import V商品入庫
from routers2 import V商品推移表
from routers2 import S配車_週表示
from routers2 import S配車_日表示

app = FastAPI(title="Welcome to AiDiy system")

# テーブル作成（apps系のみ）
database.Base.metadata.create_all(
    bind=database.engine,
    tables=[
        models2.M配車区分.__table__,
        models2.M車両.__table__,
        models2.M商品.__table__,
        models2.T配車.__table__,
        models2.T商品出庫.__table__,
        models2.T商品棚卸.__table__,
        models2.T商品入庫.__table__,
    ]
)

# CORS設定
origins = [
    "http://localhost:5173", # Vite default
    "http://localhost:3000",
    "http://localhost:8090", # New Port
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(M配車区分.router)
app.include_router(V配車区分.router)
app.include_router(M車両.router)
app.include_router(V車両.router)
app.include_router(M商品.router)
app.include_router(V商品.router)

app.include_router(T配車.router)
app.include_router(V配車.router)
app.include_router(T商品出庫.router)
app.include_router(V商品出庫.router)
app.include_router(T商品棚卸.router)
app.include_router(V商品棚卸.router)
app.include_router(T商品入庫.router)
app.include_router(V商品入庫.router)
app.include_router(V商品推移表.router)
app.include_router(S配車_週表示.router)
app.include_router(S配車_日表示.router)

@app.on_event("startup")
def startup_event():
    # tempフォルダ準備 & 再起動フラグ処理
    temp_dir = os.path.join(os.path.dirname(__file__), "temp")
    os.makedirs(temp_dir, exist_ok=True)
    reboot_self_path = os.path.join(temp_dir, "reboot2.txt")
    if os.path.isfile(reboot_self_path):
        try:
            os.remove(reboot_self_path)
        except Exception:
            pass
        raise SystemExit("reboot2.txt detected")
    def reboot_watcher() -> None:
        while True:
            try:
                if os.path.isfile(reboot_self_path):
                    try:
                        os.remove(reboot_self_path)
                    except Exception:
                        pass
                    os._exit(0)
            except Exception:
                pass
            time.sleep(1)
    threading.Thread(target=reboot_watcher, daemon=True).start()

    # ログ設定
    setup_logging()

    # 構成情報を初期化（config.jsonは読むが、path/modelsは無効化）
    if not app_conf.init(conf_path_enabled=False, conf_models_enabled=False):
        logger.warning("構成情報の初期化に失敗しました")
    else:
        app.conf = app_conf

    # apps系の初期データ投入
    db = database.SessionLocal()
    try:
        crud2.init_db_data(db)
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "FastAPI Server is running"}
