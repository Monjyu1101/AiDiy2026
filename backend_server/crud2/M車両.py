# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
# This software is licensed under the MIT License.
# https://github.com/monjyu1101
# Thank you for keeping the rules.
# ------------------------------------------------

from sqlalchemy.orm import Session
from typing import Optional, Dict
import models2 as models, schemas
from crud2.utils import create_audit_fields

def get_M車両(db: Session, 車両ID: str):
    """車両IDで車両を取得"""
    return db.query(models.M車両).filter(models.M車両.車両ID == 車両ID).first()

def get_M車両一覧(db: Session):
    """全車両を取得"""
    return db.query(models.M車両).order_by(models.M車両.車両ID).all()

def create_M車両(db: Session, 車両: schemas.M車両Create, 認証情報: Optional[Dict] = None):
    """車両を作成"""
    audit = create_audit_fields(認証情報)

    db_車両 = models.M車両(
        車両ID=車両.車両ID,
        車両名=車両.車両名,
        車両備考=車両.車両備考,
        **audit
    )
    db.add(db_車両)
    db.commit()
    db.refresh(db_車両)
    return db_車両
