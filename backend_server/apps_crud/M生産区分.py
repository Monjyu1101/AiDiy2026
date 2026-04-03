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


def get_M生産区分(db: Session, 生産区分ID: str):
    """生産区分IDで生産区分を取得"""
    return db.query(models.M生産区分).filter(models.M生産区分.生産区分ID == 生産区分ID).first()


def get_M生産区分一覧(db: Session):
    """全生産区分を取得"""
    return db.query(models.M生産区分).order_by(models.M生産区分.生産区分ID).all()


def create_M生産区分(db: Session, 生産区分: schemas.M生産区分Create, 認証情報: Optional[Dict] = None):
    """生産区分を作成"""
    audit = create_audit_fields(認証情報)

    db_生産区分 = models.M生産区分(
        生産区分ID=生産区分.生産区分ID,
        生産区分名=生産区分.生産区分名,
        生産区分備考=生産区分.生産区分備考,
        配色枠=生産区分.配色枠,
        配色背景=生産区分.配色背景,
        配色前景=生産区分.配色前景,
        有効=True,
        **audit
    )
    db.add(db_生産区分)
    db.commit()
    db.refresh(db_生産区分)
    return db_生産区分
