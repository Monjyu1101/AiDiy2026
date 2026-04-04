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
from datetime import timedelta
import random

logger = get_logger(__name__)

def get_T商品入庫(db: Session, 入庫伝票ID: str):
    """T商品入庫を取得"""
    return db.query(models.T商品入庫).filter(models.T商品入庫.入庫伝票ID == 入庫伝票ID).first()

def get_T商品入庫一覧(db: Session):
    """全商品入庫データを取得"""
    return db.query(models.T商品入庫).order_by(models.T商品入庫.入庫日.desc()).all()

def create_T商品入庫(db: Session, 商品入庫: schemas.T商品入庫Create, 認証情報: Optional[Dict] = None):
    """商品入庫データを作成（入庫伝票IDは必須、ルーター側で採番済み）"""
    if not 商品入庫.入庫伝票ID:
        raise ValueError("入庫伝票IDが指定されていません")

    audit = create_audit_fields(認証情報)

    db_商品入庫 = models.T商品入庫(
        入庫伝票ID=商品入庫.入庫伝票ID,
        入庫日=商品入庫.入庫日,
        商品ID=商品入庫.商品ID,
        入庫数量=商品入庫.入庫数量,
        入庫備考=商品入庫.入庫備考,
        有効=商品入庫.有効,
        **audit
    )
    db.add(db_商品入庫)
    db.commit()
    db.refresh(db_商品入庫)
    return db_商品入庫

def update_T商品入庫(db: Session, 入庫伝票ID: str, 商品入庫: schemas.T商品入庫Update, 認証情報: Optional[Dict] = None):
    """商品入庫データを更新"""
    db_商品入庫 = get_T商品入庫(db, 入庫伝票ID)
    if not db_商品入庫:
        return None

    update_data = 商品入庫.model_dump(exclude_unset=True)
    audit = update_audit_fields(認証情報)

    for key, value in update_data.items():
        setattr(db_商品入庫, key, value)

    for key, value in audit.items():
        setattr(db_商品入庫, key, value)

    db.commit()
    db.refresh(db_商品入庫)
    return db_商品入庫

def delete_T商品入庫(db: Session, 入庫伝票ID: str, 認証情報: Optional[Dict] = None):
    """T商品入庫を論理削除"""
    db_商品入庫 = get_T商品入庫(db, 入庫伝票ID)
    if not db_商品入庫:
        return False

    audit = update_audit_fields(認証情報)
    db_商品入庫.有効 = False
    for key, value in audit.items():
        setattr(db_商品入庫, key, value)
    db.commit()
    return True

def init_T商品入庫_data(db: Session, 認証情報: Optional[Dict] = None):
    """T商品入庫の初期データを作成"""
    if db.query(models.T商品入庫).first():
        return  # 既にデータがある場合はスキップ

    # 初期データ用の日時取得
    audit = create_audit_fields(認証情報)

    now = datetime.datetime.now()
    today = now.date()

    rng = random.Random(20260403)
    商品ID一覧 = INITIAL_PRODUCT_IDS[:]
    rng.shuffle(商品ID一覧)
    入庫日一覧 = sorted(today + timedelta(days=rng.randint(1, 14)) for _ in 商品ID一覧)

    for i, (商品ID, 入庫日) in enumerate(zip(商品ID一覧, 入庫日一覧), start=1):
        伝票番号 = f"HI{str(i).zfill(8)}"
        入庫数量 = rng.choice([100, 200, 300, 400, 500])
        備考 = ""

        入庫データ = models.T商品入庫(
            入庫伝票ID=伝票番号,
            入庫日=入庫日.isoformat(),
            商品ID=商品ID,
            入庫数量=入庫数量,
            入庫備考=備考,
            有効=True,
            **audit
        )
        db.add(入庫データ)

    db.commit()
    logger.info("Initialized T商品入庫")
