# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
# This software is licensed under the MIT License.
# https://github.com/monjyu1101
# Thank you for keeping the rules.
# ------------------------------------------------

from sqlalchemy.orm import Session
from typing import Optional, Dict
import models1 as models, schemas
from crud1.utils import create_audit_fields

def get_C権限(db: Session, 権限ID: str):
    """権限IDで権限を取得"""
    return db.query(models.C権限).filter(models.C権限.権限ID == 権限ID).first()

def get_C権限一覧(db: Session):
    """全権限を取得"""
    return db.query(models.C権限).order_by(models.C権限.権限ID).all()

def create_C権限(db: Session, 権限: schemas.C権限Create, 認証情報: Optional[Dict] = None):
    """権限を作成"""
    audit = create_audit_fields(認証情報)

    db_権限 = models.C権限(
        権限ID=権限.権限ID,
        権限名=権限.権限名,
        権限備考=権限.権限備考,
        **audit
    )
    db.add(db_権限)
    db.commit()
    db.refresh(db_権限)
    return db_権限
