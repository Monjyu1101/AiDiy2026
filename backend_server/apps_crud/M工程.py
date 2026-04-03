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
from apps_crud.utils import create_audit_fields


def get_M工程(db: Session, 工程ID: str):
    """工程IDで工程を取得"""
    return db.query(models.M工程).filter(models.M工程.工程ID == 工程ID).first()


def get_M工程一覧(db: Session):
    """全工程を取得"""
    return db.query(models.M工程).order_by(models.M工程.工程ID).all()


def create_M工程(db: Session, 工程: schemas.M工程Create, 認証情報: Optional[Dict] = None):
    """工程を作成"""
    audit = create_audit_fields(認証情報)

    db_工程 = models.M工程(
        工程ID=工程.工程ID,
        工程名=工程.工程名,
        工程備考=工程.工程備考,
        有効=True,
        **audit
    )
    db.add(db_工程)
    db.commit()
    db.refresh(db_工程)
    return db_工程
