# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101
# -------------------------------------------------------------------------

from sqlalchemy.orm import Session
import apps_models as models
from apps_crud.M配車区分 import init_M配車区分_data
from apps_crud.M生産区分 import init_M生産区分_data
from apps_crud.M生産工程 import init_M生産工程_data
from apps_crud.M商品分類 import init_M商品分類_data
from apps_crud.M車両 import init_M車両_data
from apps_crud.M商品 import init_M商品_data
from apps_crud.M商品構成 import init_M商品構成_data
from apps_crud.T配車 import init_T配車_data
from apps_crud.T生産 import init_T生産_data
from apps_crud.T商品出庫 import init_T商品出庫_data
from apps_crud.T商品棚卸 import init_T商品棚卸_data
from apps_crud.T商品入庫 import init_T商品入庫_data
from log_config import get_logger

logger = get_logger(__name__)


def init_db_data(db: Session):
    """apps系の初期データを投入"""
    from sqlalchemy import text, inspect
    inspector = inspect(db.bind)

    # スキーママイグレーション（旧テーブル対応）
    if inspector.has_table("M商品構成明細"):
        db.execute(text('DROP TABLE IF EXISTS "M商品構成明細"'))
        db.commit()

    if inspector.has_table("M生産分類") and not inspector.has_table("M生産区分"):
        db.execute(text('ALTER TABLE "M生産分類" RENAME TO "M生産区分"'))
        db.commit()
        inspector = inspect(db.bind)

    if inspector.has_table("M商品構成"):
        columns = {col['name']: col for col in inspector.get_columns("M商品構成")}
        requires_recreate = (
            "明細SEQ" not in columns
            or columns.get("構成商品ID", {}).get("nullable") is False
            or columns.get("計算分子数量", {}).get("nullable") is False
            or columns.get("計算分母数量", {}).get("nullable") is False
        )
        if requires_recreate:
            db.execute(text('DROP TABLE IF EXISTS "M商品構成"'))
            db.commit()
            models.M商品構成.__table__.create(bind=db.bind, checkfirst=True)
            db.commit()
            inspector = inspect(db.bind)
        columns = [col['name'] for col in inspector.get_columns("M商品構成")]
        if "生産区分ID" not in columns:
            db.execute(text('ALTER TABLE "M商品構成" ADD COLUMN "生産区分ID" TEXT NOT NULL DEFAULT ""'))
            db.execute(text('UPDATE "M商品構成" SET "生産区分ID" = substr("商品ID", 1, 1) WHERE "生産区分ID" = "" OR "生産区分ID" IS NULL'))
        if "生産工程ID" not in columns:
            db.execute(text('ALTER TABLE "M商品構成" ADD COLUMN "生産工程ID" TEXT NOT NULL DEFAULT ""'))
            db.execute(text('UPDATE "M商品構成" SET "生産工程ID" = "L99" WHERE "生産工程ID" = "" OR "生産工程ID" IS NULL'))
        if "最小ロット構成数量" not in columns:
            db.execute(text('ALTER TABLE "M商品構成" ADD COLUMN "最小ロット構成数量" REAL'))
            db.execute(text('UPDATE "M商品構成" SET "最小ロット構成数量" = CASE WHEN "計算分母数量" IS NOT NULL AND CAST("計算分母数量" AS REAL) != 0 THEN (CAST("計算分子数量" AS REAL) / CAST("計算分母数量" AS REAL)) * CAST("最小ロット数量" AS REAL) ELSE 0 END WHERE "明細SEQ" > 0'))
            db.commit()

    # T生産: 明細SEQ追加対応（複合PK追加のためテーブル再作成）またはカラム名変更対応
    if inspector.has_table("T生産"):
        columns = [col['name'] for col in inspector.get_columns("T生産")]
        if "明細SEQ" not in columns or "受入商品ID" not in columns:
            db.execute(text('DROP TABLE IF EXISTS "T生産"'))
            db.commit()
            models.T生産.__table__.create(bind=db.bind, checkfirst=True)
            db.commit()
            inspector = inspect(db.bind)
        columns = [col['name'] for col in inspector.get_columns("T生産")]
        if "最小ロット構成数量" not in columns:
            db.execute(text('ALTER TABLE "T生産" ADD COLUMN "最小ロット構成数量" REAL'))
            db.execute(text('UPDATE "T生産" SET "最小ロット構成数量" = CASE WHEN "計算分母数量" IS NOT NULL AND CAST("計算分母数量" AS REAL) != 0 THEN (CAST("計算分子数量" AS REAL) / CAST("計算分母数量" AS REAL)) * COALESCE(CAST("最小ロット数量" AS REAL), 1) ELSE 0 END WHERE "明細SEQ" > 0'))
            db.commit()
        if "最小ロット所要数量" in columns:
            db.execute(text('ALTER TABLE "T生産" DROP COLUMN "最小ロット所要数量"'))
            db.commit()

    for テーブル名 in ["M配車区分", "M生産区分", "M生産工程", "M商品分類", "M車両", "M商品", "M商品構成"]:
        if not inspector.has_table(テーブル名):
            continue
        columns = [col['name'] for col in inspector.get_columns(テーブル名)]
        if "有効" not in columns:
            db.execute(text(f'ALTER TABLE "{テーブル名}" ADD COLUMN "有効" INTEGER NOT NULL DEFAULT 1'))
        if テーブル名 == "M商品" and "商品分類ID" not in columns:
            db.execute(text('ALTER TABLE "M商品" ADD COLUMN "商品分類ID" TEXT NOT NULL DEFAULT ""'))
            db.execute(text('UPDATE "M商品" SET "商品分類ID" = substr("商品ID", 1, 1) WHERE "商品分類ID" = "" OR "商品分類ID" IS NULL'))
    db.commit()

    初期認証情報 = {"利用者ID": "system", "利用者名": "system", "端末ID": "localhost"}

    # C採番: T生産採番の追加（既存DB対応）
    from sqlalchemy import inspect as sa_inspect
    from core_models.C採番 import C採番 as C採番Model
    from apps_crud.utils import create_audit_fields
    if sa_inspect(db.bind).has_table("C採番"):
        if not db.query(C採番Model).filter(C採番Model.採番ID == "T生産").first():
            登録項目 = create_audit_fields(初期認証情報)
            db.add(C採番Model(
                採番ID="T生産",
                最終採番値=10000,
                採番備考="生産の採番",
                有効=True,
                **登録項目
            ))
            db.commit()
            logger.info("Initialized C採番 for T生産")

    # 各モジュールの初期データ投入
    init_M配車区分_data(db, 認証情報=初期認証情報)
    init_M生産区分_data(db, 認証情報=初期認証情報)
    init_M生産工程_data(db, 認証情報=初期認証情報)
    init_M商品分類_data(db, 認証情報=初期認証情報)
    init_M車両_data(db, 認証情報=初期認証情報)
    init_M商品_data(db, 認証情報=初期認証情報)
    init_M商品構成_data(db, 認証情報=初期認証情報)
    init_T配車_data(db)
    init_T生産_data(db)
    init_T商品出庫_data(db)
    init_T商品棚卸_data(db)
    init_T商品入庫_data(db)
