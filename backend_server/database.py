# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
# This software is licensed under the MIT License.
# https://github.com/monjyu1101
# Thank you for keeping the rules.
# ------------------------------------------------

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# データベースファイルのパス
DB_DIR = os.path.join(os.path.dirname(__file__), "_data", "AiDiy")
DB_PATH = os.path.join(DB_DIR, "database.db")

# ディレクトリが存在しない場合は作成
os.makedirs(DB_DIR, exist_ok=True)

# SQLiteデータベースのURL
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# データベースエンジンの作成
# check_same_thread=False はSQLiteのみで必要
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# セッションローカルクラスの作成
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ベースクラスの作成
Base = declarative_base()

# DBセッション取得用の依存関係関数
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
