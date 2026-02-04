# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
# This software is licensed under the MIT License.
# https://github.com/monjyu1101
# Thank you for keeping the rules.
# ------------------------------------------------

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import database, core_crud, core_models
import os
import sys
import threading
import time
from conf import conf as app_conf
from log_config import setup_logging, get_logger
from AIコア.AIバックアップ import バックアップ実行

# ロガー取得
logger = get_logger(__name__)

from core_router import auth
from core_router import C権限
from core_router import V権限
from core_router import C利用者
from core_router import V利用者
from core_router import C採番
from core_router import V採番

from core_router import AIコア
from core_router import A会話履歴

# テーブル作成（core系のみ）
database.Base.metadata.create_all(
    bind=database.engine,
    tables=[
        core_models.C採番.__table__,
        core_models.C権限.__table__,
        core_models.C利用者.__table__,
        core_models.A会話履歴.__table__,
    ]
)

app = FastAPI(title="Welcome to AiDiy system")

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
app.include_router(auth.router)
app.include_router(C権限.router)
app.include_router(V権限.router)
app.include_router(C利用者.router)
app.include_router(V利用者.router)
app.include_router(C採番.router)
app.include_router(V採番.router)

app.include_router(AIコア.router)
app.include_router(A会話履歴.router)

@app.on_event("startup")
def startup_event():
    # tempフォルダ準備 & 再起動フラグ処理
    temp_dir = os.path.join(os.path.dirname(__file__), "temp")
    os.makedirs(temp_dir, exist_ok=True)
    reboot_self_path = os.path.join(temp_dir, "reboot1.txt")
    if os.path.isfile(reboot_self_path):
        try:
            os.remove(reboot_self_path)
        except Exception:
            pass
        raise SystemExit("reboot1.txt detected")
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

    # 構成情報を初期化
    if not app_conf.init():
        logger.warning("構成情報の初期化に失敗しました")
    # Shortcut for easy access (app.conf)
    app.conf = app_conf

    # DB初期化 & VIEW作成
    db = database.SessionLocal()
    try:
        core_crud.init_db_data(db)
    finally:
        db.close()

    # バックアップ実行
    try:
        backend_dir = os.path.dirname(__file__)
        logger.info("バックアップ処理を開始します...")
        result = バックアップ実行(アプリ設定=app_conf, backend_dir=backend_dir)
        if result:
            最終時刻, ファイル一覧, バックアップファイル一覧, 全件フラグ = result
            if 全件フラグ:
                logger.info(f"バックアップ完了 最終更新時刻={最終時刻}, 総ファイル数={len(ファイル一覧)},")
            else:
                if バックアップファイル一覧:
                    logger.info(f"バックアップ完了 最終更新時刻={最終時刻}, 総ファイル数={len(ファイル一覧)}, 差分ファイル数={len(バックアップファイル一覧)},")
                    for file in バックアップファイル一覧[:10]:  # 最大10件表示
                        logger.info(f"・{file}")
                    if len(バックアップファイル一覧) > 10:
                        logger.info(f"... 他 {len(バックアップファイル一覧) - 10}件")
                else:
                    logger.info(f"バックアップ完了 最終更新時刻={最終時刻}, 総ファイル数={len(ファイル一覧)}, 差分ファイル=なし,")
        else:
            logger.info("バックアップスキップ（更新ファイルなし）")
    except Exception as e:
        logger.error(f"バックアップ実行時エラー: {e}")

@app.get("/")
def read_root():
    return {"message": "FastAPI Server is running"}

@app.get("/core/サーバー状態")
def get_ready_count():
    """サーバー状態を返すエンドポイント（タイトルバーのアニメーション用）"""
    # 簡易実装: 常に処理可能状態を返す
    # 実際の実装では、タスクキューやワーカーの状態を確認する
    # ログ出力なし（頻繁に呼ばれるため）
    return {
        "ready_count": 1,  # 処理可能数
        "busy_count": 0    # 処理中数
    }
