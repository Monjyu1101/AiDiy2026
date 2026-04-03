# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101
# -------------------------------------------------------------------------

from sqlalchemy.orm import Session
import apps_models as models, apps_schema as schemas
from apps_crud.M配車区分 import create_M配車区分
from apps_crud.M生産区分 import create_M生産区分
from apps_crud.M工程 import create_M工程
from apps_crud.M車両 import create_M車両
from apps_crud.M商品 import create_M商品
from apps_crud.M商品構成 import create_M商品構成
from apps_crud.T配車 import init_T配車_data
from apps_crud.T生産 import init_T生産_data
from apps_crud.T商品出庫 import init_T商品出庫_data
from apps_crud.T商品棚卸 import init_T商品棚卸_data
from apps_crud.T商品入庫 import init_T商品入庫_data
from apps_crud.seed_data import INITIAL_PRODUCTS, INITIAL_PRODUCT_COMPOSITIONS
from log_config import get_logger

logger = get_logger(__name__)


def init_db_data(db: Session):
    """apps系の初期データを投入"""
    # 有効カラムの追加（既存DBマイグレーション）
    from sqlalchemy import text, inspect
    inspector = inspect(db.bind)

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
            "明細番号" not in columns
            or columns.get("構成商品ID", {}).get("nullable") is False
            or columns.get("構成数量分子", {}).get("nullable") is False
            or columns.get("構成数量分母", {}).get("nullable") is False
        )
        if requires_recreate:
            db.execute(text('DROP TABLE IF EXISTS "M商品構成"'))
            db.commit()
            models.M商品構成.__table__.create(bind=db.bind, checkfirst=True)
            db.commit()
            inspector = inspect(db.bind)

    for テーブル名 in ["M配車区分", "M生産区分", "M工程", "M車両", "M商品", "M商品構成"]:
        if not inspector.has_table(テーブル名):
            continue
        columns = [col['name'] for col in inspector.get_columns(テーブル名)]
        if "有効" not in columns:
            db.execute(text(f'ALTER TABLE "{テーブル名}" ADD COLUMN "有効" INTEGER NOT NULL DEFAULT 1'))
    db.commit()

    # 配車区分の初期化
    if not db.query(models.M配車区分).first():
        配車区分一覧 = [
            ('1', '通常', '青', '#001f3f', '#cce6ff', '#000000'),
            ('2', '定期', '緑', '#003300', '#ccffcc', '#000000'),
            ('3', '予備', '黄', '#4d3300', '#ffffcc', '#000000'),
            ('4', '緊急', '赤', '#660000', '#ffcccc', '#000000'),
            ('5', '特別', '紫', '#330044', '#e6ccff', '#000000'),
            ('6', '巡回', '水', '#004444', '#ccffff', '#000000'),
            ('7', '回送', '黒', '#000000', '#e6e6e6', '#000000'),
            ('8', '予備', '灰', '#1a1a1a', '#f0f0f0', '#000000'),
        ]
        for 配車区分ID, 配車区分名, 配車区分備考, 配色枠, 配色背景, 配色前景 in 配車区分一覧:
            配車区分 = schemas.M配車区分Create(
                配車区分ID=配車区分ID,
                配車区分名=配車区分名,
                配車区分備考=配車区分備考,
                配色枠=配色枠,
                配色背景=配色背景,
                配色前景=配色前景
            )
            create_M配車区分(db, 配車区分)
        logger.info("Initialized M配車区分")

    # 生産区分の初期化
    if not db.query(models.M生産区分).first():
        生産区分一覧 = [
            ('1', '牛飼料', '', '#001f3f', '#cce6ff', '#000000'),
            ('2', '豚飼料', '', '#003300', '#ccffcc', '#000000'),
            ('3', '鶏飼料', '', '#4d3300', '#ffffcc', '#000000'),
            ('4', '魚飼料', '', '#660000', '#ffcccc', '#000000'),
            ('9', 'その他', '', '#1a1a1a', '#f0f0f0', '#000000'),
        ]
        for 生産区分ID, 生産区分名, 生産区分備考, 配色枠, 配色背景, 配色前景 in 生産区分一覧:
            生産区分 = schemas.M生産区分Create(
                生産区分ID=生産区分ID,
                生産区分名=生産区分名,
                生産区分備考=生産区分備考,
                配色枠=配色枠,
                配色背景=配色背景,
                配色前景=配色前景
            )
            create_M生産区分(db, 生産区分)
        logger.info("Initialized M生産区分")

    # 工程の初期化
    if not db.query(models.M工程).first():
        工程一覧 = [
            ('L01', 'ライン１', ''),
            ('L02', 'ライン２', ''),
            ('L03', 'ライン３', ''),
            ('L04', 'ライン４', ''),
            ('L05', 'ライン５', ''),
            ('L06', 'ライン６', ''),
            ('L07', 'ライン７', ''),
            ('L99', '未定', ''),
        ]
        for 工程ID, 工程名, 工程備考 in 工程一覧:
            工程 = schemas.M工程Create(
                工程ID=工程ID,
                工程名=工程名,
                工程備考=工程備考
            )
            create_M工程(db, 工程)
        logger.info("Initialized M工程")

    # 車両の初期化
    if not db.query(models.M車両).first():
        車両一覧 = [
            ('1001', '１号車', '近藤'),
            ('1002', '２号車', '藤原'),
            ('1003', '３号車', '津村'),
            ('1004', '４号車', '鈴木'),
            ('1005', '５号車', '高松'),
            ('1006', '６号車', '藤井'),
            ('1007', '７号車', '山田'),
            ('1099', '未定', ''),
        ]
        for 車両ID, 車両名, 車両備考 in 車両一覧:
            車両 = schemas.M車両Create(
                車両ID=車両ID,
                車両名=車両名,
                車両備考=車両備考
            )
            create_M車両(db, 車両)
        logger.info("Initialized M車両")

    # 商品の初期化
    if not db.query(models.M商品).first():
        for 商品ID, 商品名, 単位, 商品備考 in INITIAL_PRODUCTS:
            商品 = schemas.M商品Create(
                商品ID=商品ID,
                商品名=商品名,
                単位=単位,
                商品備考=商品備考
            )
            create_M商品(db, 商品)
        logger.info("Initialized M商品")

    # 商品構成の初期化
    if not db.query(models.M商品構成).first():
        for item in INITIAL_PRODUCT_COMPOSITIONS:
            商品構成 = schemas.M商品構成Create(
                商品ID=item["商品ID"],
                生産ロット=item["生産ロット"],
                商品構成備考=item["商品構成備考"],
                有効=True,
                明細一覧=[
                    schemas.M商品構成明細Base(**明細)
                    for 明細 in item["明細一覧"]
                ],
            )
            create_M商品構成(db, 商品構成)
        logger.info("Initialized M商品構成")

    # T生産採番の追加（既存DB対応）
    from sqlalchemy import inspect as sa_inspect
    from core_models.C採番 import C採番 as C採番Model
    from apps_crud.utils import create_audit_fields
    inspector2 = sa_inspect(db.bind)
    if inspector2.has_table("C採番"):
        if not db.query(C採番Model).filter(C採番Model.採番ID == "T生産").first():
            登録項目 = create_audit_fields({"利用者ID": "system", "利用者名": "system"})
            db.add(C採番Model(
                採番ID="T生産",
                最終採番値=10000,
                採番備考="生産の採番",
                有効=True,
                **登録項目
            ))
            db.commit()
            logger.info("Initialized C採番 for T生産")

    # T配車の初期化
    init_T配車_data(db)

    # T生産の初期化
    init_T生産_data(db)

    # T商品出庫の初期化
    init_T商品出庫_data(db)

    # T商品棚卸の初期化
    init_T商品棚卸_data(db)

    # T商品入庫の初期化
    init_T商品入庫_data(db)
