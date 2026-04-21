# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101/AiDiy2026
# -------------------------------------------------------------------------

from sqlalchemy.orm import Session
from typing import Optional, Dict
import apps_models as models, apps_schema as schemas
from apps_crud.utils import create_audit_fields


def get_M取引先分類(db: Session, 取引先分類ID: str):
    """取引先分類IDで取引先分類を取得"""
    return db.query(models.M取引先分類).filter(models.M取引先分類.取引先分類ID == 取引先分類ID).first()


def get_M取引先分類一覧(db: Session):
    """全取引先分類を取得"""
    return db.query(models.M取引先分類).order_by(models.M取引先分類.取引先分類ID).all()


def create_M取引先分類(db: Session, 取引先分類: schemas.M取引先分類Create, 認証情報: Optional[Dict] = None):
    """取引先分類を作成"""
    audit = create_audit_fields(認証情報)

    db_取引先分類 = models.M取引先分類(
        取引先分類ID=取引先分類.取引先分類ID,
        取引先分類名=取引先分類.取引先分類名,
        取引先分類備考=取引先分類.取引先分類備考,
        有効=True,
        **audit
    )
    db.add(db_取引先分類)
    db.commit()
    db.refresh(db_取引先分類)
    return db_取引先分類


def init_M取引先分類_data(db: Session, 認証情報: Optional[Dict] = None):
    """M取引先分類の初期データを投入"""
    from log_config import get_logger
    logger = get_logger(__name__)
    初期データ = [
        ('1', '得意先', '販売先・納品先'),
        ('3', '委託先', '外注・加工などの委託先'),
        ('5', '仕入先', '商品・原材料などの仕入先'),
        ('9', 'その他', ''),
    ]
    初期データID = {取引先分類ID for 取引先分類ID, _, _ in 初期データ}
    旧サンプルID = {'S', 'C', 'P', 'O'}
    audit = create_audit_fields(認証情報, is_update=True)

    for 取引先分類ID, 取引先分類名, 取引先分類備考 in 初期データ:
        existing = get_M取引先分類(db, 取引先分類ID)
        if existing:
            existing.取引先分類名 = 取引先分類名
            existing.取引先分類備考 = 取引先分類備考
            existing.有効 = True
            for key, value in audit.items():
                setattr(existing, key, value)
            continue
        create_M取引先分類(
            db,
            schemas.M取引先分類Create(
                取引先分類ID=取引先分類ID,
                取引先分類名=取引先分類名,
                取引先分類備考=取引先分類備考
            ),
            認証情報=認証情報
        )

    for 旧ID in 旧サンプルID - 初期データID:
        existing = get_M取引先分類(db, 旧ID)
        if existing:
            db.delete(existing)
    db.commit()
    logger.info("Initialized M取引先分類")
