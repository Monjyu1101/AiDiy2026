# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
# This software is licensed under the MIT License.
# https://github.com/monjyu1101
# Thank you for keeping the rules.
# ------------------------------------------------

from sqlalchemy.orm import Session
from typing import Optional, Dict
import apps_models as models, apps_schema as schemas
from apps_crud.utils import create_audit_fields, update_audit_fields
from log_config import get_logger
import datetime

logger = get_logger(__name__)

def get_T商品棚卸(db: Session, 棚卸伝票ID: str):
    """棚卸伝票IDで商品棚卸データを取得"""
    return db.query(models.T商品棚卸).filter(models.T商品棚卸.棚卸伝票ID == 棚卸伝票ID).first()

def get_T商品棚卸一覧(db: Session):
    """全商品棚卸データを取得"""
    return db.query(models.T商品棚卸).order_by(models.T商品棚卸.棚卸日.desc()).all()

def create_T商品棚卸(db: Session, 商品棚卸: schemas.T商品棚卸Create, 認証情報: Optional[Dict] = None):
    """商品棚卸データを作成（棚卸伝票IDは必須、ルーター側で採番済み）"""
    if not 商品棚卸.棚卸伝票ID:
        raise ValueError("棚卸伝票IDが指定されていません")

    audit = create_audit_fields(認証情報)

    db_商品棚卸 = models.T商品棚卸(
        棚卸伝票ID=商品棚卸.棚卸伝票ID,
        棚卸日=商品棚卸.棚卸日,
        商品ID=商品棚卸.商品ID,
        実棚数量=商品棚卸.実棚数量,
        棚卸備考=商品棚卸.棚卸備考,
        **audit
    )
    db.add(db_商品棚卸)
    db.commit()
    db.refresh(db_商品棚卸)
    return db_商品棚卸

def update_T商品棚卸(db: Session, 棚卸伝票ID: str, 商品棚卸: schemas.T商品棚卸Update, 認証情報: Optional[Dict] = None):
    """商品棚卸データを更新"""
    db_商品棚卸 = get_T商品棚卸(db, 棚卸伝票ID)
    if not db_商品棚卸:
        return None

    update_data = 商品棚卸.model_dump(exclude_unset=True)
    audit = update_audit_fields(認証情報)

    for key, value in update_data.items():
        setattr(db_商品棚卸, key, value)

    for key, value in audit.items():
        setattr(db_商品棚卸, key, value)

    db.commit()
    db.refresh(db_商品棚卸)
    return db_商品棚卸

def delete_T商品棚卸(db: Session, 棚卸伝票ID: str):
    """商品棚卸データを削除"""
    db_商品棚卸 = get_T商品棚卸(db, 棚卸伝票ID)
    if not db_商品棚卸:
        return False

    db.delete(db_商品棚卸)
    db.commit()
    return True

def init_T商品棚卸_data(db: Session, 認証情報: Optional[Dict] = None):
    """T商品棚卸の初期データを作成"""
    if db.query(models.T商品棚卸).first():
        return  # 既にデータがある場合はスキップ

    # 初期データ用の日時取得
    audit = create_audit_fields(認証情報)

    now = datetime.datetime.now()
    today = now.date()

    # T商品棚卸の初期データ作成（本日のH001商品、実棚数量200の1件のみ）
    棚卸日 = today
    商品ID = "H001"
    実棚数量 = 200
    伝票番号 = "HT00000001"
    備考 = ""

    # SQLAlchemyモデルでINSERT
    棚卸データ = models.T商品棚卸(
        棚卸伝票ID=伝票番号,
        棚卸日=棚卸日.isoformat(),
        商品ID=商品ID,
        実棚数量=実棚数量,
        棚卸備考=備考,
        **audit
    )
    db.add(棚卸データ)

    db.commit()
    logger.info("Initialized T商品棚卸")
