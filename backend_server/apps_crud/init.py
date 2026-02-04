# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
# This software is licensed under the MIT License.
# https://github.com/monjyu1101
# Thank you for keeping the rules.
# ------------------------------------------------

from sqlalchemy.orm import Session
import apps_models as models, apps_schema as schemas
from apps_crud.M配車区分 import create_M配車区分
from apps_crud.M車両 import create_M車両
from apps_crud.M商品 import create_M商品
from apps_crud.T配車 import init_T配車_data
from apps_crud.T商品出庫 import init_T商品出庫_data
from apps_crud.T商品棚卸 import init_T商品棚卸_data
from apps_crud.T商品入庫 import init_T商品入庫_data
from log_config import get_logger

logger = get_logger(__name__)


def init_db_data(db: Session):
    """apps系の初期データを投入"""
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
        商品一覧 = [
            ('H001', '牛飼料', 'Kg', ''),
            ('H002', '豚飼料', 'Kg', ''),
            ('H003', '鶏飼料', 'Kg', ''),
            ('H004', '魚飼料', 'Kg', ''),
            ('H099', 'その他', 'Kg', ''),
        ]
        for 商品ID, 商品名, 単位, 商品備考 in 商品一覧:
            商品 = schemas.M商品Create(
                商品ID=商品ID,
                商品名=商品名,
                単位=単位,
                商品備考=商品備考
            )
            create_M商品(db, 商品)
        logger.info("Initialized M商品")

    # T配車の初期化
    init_T配車_data(db)

    # T商品出庫の初期化
    init_T商品出庫_data(db)

    # T商品棚卸の初期化
    init_T商品棚卸_data(db)

    # T商品入庫の初期化
    init_T商品入庫_data(db)
