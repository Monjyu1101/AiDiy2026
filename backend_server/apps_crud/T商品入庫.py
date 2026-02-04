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
from datetime import timedelta

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

def delete_T商品入庫(db: Session, 入庫伝票ID: str):
    """T商品入庫を削除"""
    db_商品入庫 = get_T商品入庫(db, 入庫伝票ID)
    if not db_商品入庫:
        return False

    db.delete(db_商品入庫)
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

    # 明日から2週間以内で3件の入庫日を設定 (3日後、8日後、13日後)
    tomorrow = today + timedelta(days=1)

    入庫日一覧 = [
        tomorrow + timedelta(days=2),   # 3日後
        tomorrow + timedelta(days=7),   # 8日後
        tomorrow + timedelta(days=12)   # 13日後
    ]

    for i, 入庫日 in enumerate(入庫日一覧):
        伝票番号 = f"HI{str(i+1).zfill(8)}"  # HI00000001〜HI00000003
        商品ID = "H001"
        入庫数量 = 500
        備考 = ""

        # SQLAlchemyモデルでINSERT
        入庫データ = models.T商品入庫(
            入庫伝票ID=伝票番号,
            入庫日=入庫日.isoformat(),
            商品ID=商品ID,
            入庫数量=入庫数量,
            入庫備考=備考,
            **audit
        )
        db.add(入庫データ)

    db.commit()
    logger.info("Initialized T商品入庫")
