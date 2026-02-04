# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
# This software is licensed under the MIT License.
# https://github.com/monjyu1101
# Thank you for keeping the rules.
# ------------------------------------------------

from sqlalchemy.orm import Session
from typing import Optional, Dict
import core_models as models, core_schema as schemas
from core_crud.utils import create_audit_fields

def get_C利用者_by_利用者ID(db: Session, 利用者ID: str):
    """利用者IDで利用者を取得"""
    return db.query(models.C利用者).filter(models.C利用者.利用者ID == 利用者ID).first()

def get_C利用者_by_利用者名(db: Session, 利用者名: str):
    """利用者名で利用者を取得"""
    return db.query(models.C利用者).filter(models.C利用者.利用者名 == 利用者名).first()

def create_C利用者(db: Session, 利用者情報: schemas.C利用者Create, 認証情報: Optional[Dict] = None):
    """利用者を作成"""
    audit = create_audit_fields(認証情報)

    db_利用者 = models.C利用者(
        利用者ID=利用者情報.利用者ID,
        利用者名=利用者情報.利用者名,
        パスワード=利用者情報.パスワード,  # 平文パスワード（参照モデルに合わせる）
        権限ID=利用者情報.権限ID,
        利用者備考=利用者情報.利用者備考,
        **audit
    )
    db.add(db_利用者)
    db.commit()
    db.refresh(db_利用者)
    return db_利用者

def authenticate_C利用者(db: Session, 利用者ID: str, パスワード: str):
    """利用者認証"""
    利用者 = get_C利用者_by_利用者ID(db, 利用者ID)
    if not 利用者:
        return None
    if 利用者.パスワード != パスワード:  # 平文パスワード比較
        return None
    return 利用者
