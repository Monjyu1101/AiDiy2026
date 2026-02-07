# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
# This software is licensed under the MIT License.
# https://github.com/monjyu1101
# Thank you for keeping the rules.
# ------------------------------------------------

import os
import sys

# UTF-8出力を強制（Windows文字化け対策）
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import database, apps_crud, apps_models
from conf import conf as app_conf
import os
import sys
import threading
import time
from log_config import setup_logging, get_logger
from AIコア.AIバックアップ import バックアップ実行

# ロガー取得
logger = get_logger(__name__)

from apps_router import M配車区分
from apps_router import V配車区分
from apps_router import M車両
from apps_router import V車両
from apps_router import M商品
from apps_router import V商品

from apps_router import T配車
from apps_router import V配車
from apps_router import T商品出庫
from apps_router import V商品出庫
from apps_router import T商品棚卸
from apps_router import V商品棚卸
from apps_router import T商品入庫
from apps_router import V商品入庫
from apps_router import V商品推移表
from apps_router import S配車_週表示
from apps_router import S配車_日表示

app = FastAPI(title="Welcome to AiDiy system")

# テーブル作成（apps系のみ）
database.Base.metadata.create_all(
    bind=database.engine,
    tables=[
        apps_models.M配車区分.__table__,
        apps_models.M車両.__table__,
        apps_models.M商品.__table__,
        apps_models.T配車.__table__,
        apps_models.T商品出庫.__table__,
        apps_models.T商品棚卸.__table__,
        apps_models.T商品入庫.__table__,
    ]
)

# CORS設定
origins = [
    "http://localhost:5173", # Vite default
    "http://localhost:3000",
    "http://localhost:8090", # New Port
    "https://localhost",     # Docker Nginx HTTPS
    "http://localhost",      # Docker Nginx HTTP
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
    reboot_self_path = os.path.join(temp_dir, "reboot_apps.txt")
    if os.path.isfile(reboot_self_path):
        try:
            os.remove(reboot_self_path)
        except Exception:
            pass
        raise SystemExit("reboot_apps.txt detected")
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
        apps_crud.init_db_data(db)
    finally:
        db.close()

    # バックアップ実行
    try:
        backend_dir = os.path.dirname(__file__)
        logger.info("バックアップ処理を開始します...")
        result = バックアップ実行(アプリ設定=app_conf, backend_dir=backend_dir)
        if result:
            最終時刻, ファイル一覧, バックアップファイル一覧, 全件フラグ, バックアップフォルダ = result
            if 全件フラグ:
                logger.info(f"バックアップ完了 最終更新時刻={最終時刻}, 総ファイル数={len(ファイル一覧)}, 保存先={バックアップフォルダ}")
            else:
                if バックアップファイル一覧:
                    logger.info(f"バックアップ完了 最終更新時刻={最終時刻}, 総ファイル数={len(ファイル一覧)}, 差分ファイル数={len(バックアップファイル一覧)}, 保存先={バックアップフォルダ}")
                    for file in バックアップファイル一覧[:10]:  # 最大10件表示
                        logger.info(f"・{file}")
                    if len(バックアップファイル一覧) > 10:
                        logger.info(f"... 他 {len(バックアップファイル一覧) - 10}件")
                else:
                    logger.info(f"バックアップ完了 最終更新時刻={最終時刻}, 総ファイル数={len(ファイル一覧)}, 差分ファイル=なし")
        else:
            logger.info("バックアップスキップ（更新ファイルなし）")
    except Exception as e:
        logger.error(f"バックアップ実行時エラー: {e}")

@app.get("/")
def read_root():
    return {"message": "FastAPI Server is running"}
