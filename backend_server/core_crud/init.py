# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101
# -------------------------------------------------------------------------

from sqlalchemy.orm import Session
from core_crud.C権限 import init_C権限_data
from core_crud.C利用者 import init_C利用者_data
from core_crud.C採番 import init_C採番_data

def init_db_data(db: Session):
    """初期データを投入"""
    # 有効カラムの追加（既存DBマイグレーション）
    from sqlalchemy import text, inspect
    inspector = inspect(db.bind)
    for テーブル名 in ["C権限", "C利用者", "C採番"]:
        columns = [col['name'] for col in inspector.get_columns(テーブル名)]
        if "有効" not in columns:
            db.execute(text(f'ALTER TABLE "{テーブル名}" ADD COLUMN "有効" INTEGER NOT NULL DEFAULT 1'))
    db.commit()

    初期認証情報 = {"利用者ID": "system", "利用者名": "system", "端末ID": "localhost"}

    init_C権限_data(db, 認証情報=初期認証情報)
    init_C利用者_data(db, 認証情報=初期認証情報)
    init_C採番_data(db, 認証情報=初期認証情報)
