# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101
# -------------------------------------------------------------------------

from sqlalchemy.orm import Session
from typing import Optional, Dict
import apps_models as models, apps_schema as schemas
from apps_crud.utils import create_audit_fields, update_audit_fields
from apps_crud.seed_data import INITIAL_PRODUCT_IDS
from log_config import get_logger
import datetime
import random

logger = get_logger(__name__)

def get_T商品出庫(db: Session, 出庫伝票ID: str):
    """出庫伝票IDで商品出庫データを取得"""
    return db.query(models.T商品出庫).filter(models.T商品出庫.出庫伝票ID == 出庫伝票ID).first()

def get_T商品出庫一覧(db: Session):
    """全商品出庫データを取得"""
    return db.query(models.T商品出庫).order_by(models.T商品出庫.出庫日.desc()).all()

def create_T商品出庫(db: Session, 商品出庫: schemas.T商品出庫Create, 認証情報: Optional[Dict] = None):
    """商品出庫データを作成（出庫伝票IDは必須、ルーター側で採番済み）"""
    if not 商品出庫.出庫伝票ID:
        raise ValueError("出庫伝票IDが指定されていません")

    audit = create_audit_fields(認証情報)

    db_商品出庫 = models.T商品出庫(
        出庫伝票ID=商品出庫.出庫伝票ID,
        出庫日=商品出庫.出庫日,
        商品ID=商品出庫.商品ID,
        出庫数量=商品出庫.出庫数量,
        出庫備考=商品出庫.出庫備考,
        **audit
    )
    db.add(db_商品出庫)
    db.commit()
    db.refresh(db_商品出庫)
    return db_商品出庫

def update_T商品出庫(db: Session, 出庫伝票ID: str, 商品出庫: schemas.T商品出庫Update, 認証情報: Optional[Dict] = None):
    """商品出庫データを更新"""
    db_商品出庫 = get_T商品出庫(db, 出庫伝票ID)
    if not db_商品出庫:
        return None

    update_data = 商品出庫.model_dump(exclude_unset=True)
    audit = update_audit_fields(認証情報)

    for key, value in update_data.items():
        setattr(db_商品出庫, key, value)

    for key, value in audit.items():
        setattr(db_商品出庫, key, value)

    db.commit()
    db.refresh(db_商品出庫)
    return db_商品出庫

def delete_T商品出庫(db: Session, 出庫伝票ID: str):
    """商品出庫データを削除"""
    db_商品出庫 = get_T商品出庫(db, 出庫伝票ID)
    if not db_商品出庫:
        return False

    db.delete(db_商品出庫)
    db.commit()
    return True

def init_T商品出庫_data(db: Session, 認証情報: Optional[Dict] = None):
    """T商品出庫の初期データを作成"""
    if db.query(models.T商品出庫).first():
        return  # 既にデータがある場合はスキップ

    # 初期データ用の日時取得
    audit = create_audit_fields(認証情報)

    now = datetime.datetime.now()
    today = now.date()

    rng = random.Random(20260404)
    商品ID一覧 = INITIAL_PRODUCT_IDS[:]
    rng.shuffle(商品ID一覧)
    出庫日リスト = sorted(today + datetime.timedelta(days=rng.randint(1, 14)) for _ in 商品ID一覧)

    for i, (商品ID, 出庫日) in enumerate(zip(商品ID一覧, 出庫日リスト), start=1):
        伝票番号 = f"HO{str(i).zfill(8)}"
        出庫数量 = rng.choice([100, 200, 300, 400, 500])
        備考 = ""

        出庫データ = models.T商品出庫(
            出庫伝票ID=伝票番号,
            出庫日=出庫日.isoformat(),
            商品ID=商品ID,
            出庫数量=出庫数量,
            出庫備考=備考,
            **audit
        )
        db.add(出庫データ)

    db.commit()
    logger.info("Initialized T商品出庫")
