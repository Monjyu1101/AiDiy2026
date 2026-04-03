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
from log_config import get_logger
import datetime
import random

logger = get_logger(__name__)

def get_T生産(db: Session, 生産伝票ID: str):
    """生産伝票IDで生産データを取得"""
    return db.query(models.T生産).filter(models.T生産.生産伝票ID == 生産伝票ID).first()

def get_T生産一覧(db: Session):
    """全生産データを取得"""
    return db.query(models.T生産).order_by(models.T生産.生産開始日時.desc()).all()

def create_T生産(db: Session, 生産: schemas.T生産Create, 認証情報: Optional[Dict] = None):
    """生産データを作成（生産伝票IDは必須、ルーター側で採番済み）"""
    if not 生産.生産伝票ID:
        raise ValueError("生産伝票IDが指定されていません")

    audit = create_audit_fields(認証情報)

    db_生産 = models.T生産(
        生産伝票ID=生産.生産伝票ID,
        生産開始日時=生産.生産開始日時,
        生産終了日時=生産.生産終了日時,
        生産区分ID=生産.生産区分ID,
        工程ID=生産.工程ID,
        生産内容=生産.生産内容,
        生産備考=生産.生産備考,
        **audit
    )
    db.add(db_生産)
    db.commit()
    db.refresh(db_生産)
    return db_生産

def update_T生産(db: Session, 生産伝票ID: str, 生産: schemas.T生産Update, 認証情報: Optional[Dict] = None):
    """生産データを更新"""
    db_生産 = get_T生産(db, 生産伝票ID)
    if not db_生産:
        return None

    update_data = 生産.model_dump(exclude_unset=True)
    audit = update_audit_fields(認証情報)

    for key, value in update_data.items():
        setattr(db_生産, key, value)

    for key, value in audit.items():
        setattr(db_生産, key, value)

    db.commit()
    db.refresh(db_生産)
    return db_生産

def delete_T生産(db: Session, 生産伝票ID: str):
    """生産データを削除"""
    db_生産 = get_T生産(db, 生産伝票ID)
    if not db_生産:
        return False

    db.delete(db_生産)
    db.commit()
    return True

def init_T生産_data(db: Session, 認証情報: Optional[Dict] = None):
    """T生産の初期データを作成"""
    if db.query(models.T生産).first():
        return  # 既にデータがある場合はスキップ

    # 初期データ用の日時取得
    audit = create_audit_fields(認証情報)

    now = datetime.datetime.now()
    today = now.date()

    # ランダムな開始日（今日から7日先まで）を8件作成
    start_dates = [today + datetime.timedelta(days=random.randint(0, 7)) for _ in range(8)]

    # 終了日は開始日に3〜7日足した日
    end_dates = [start + datetime.timedelta(days=random.randint(3, 7)) for start in start_dates]

    # 各日付に時刻を追加
    start_datetimes = [datetime.datetime.combine(d, datetime.time(8, 0)) for d in start_dates]
    end_datetimes = [datetime.datetime.combine(d, datetime.time(17, 0)) for d in end_dates]

    # 生産区分IDリスト：'1'〜'4','9'からランダムに8件
    生産区分IDs = ['1', '2', '3', '4', '9']
    生産区分IDs = random.choices(生産区分IDs, k=8)

    # 工程IDリスト：'L01'〜'L07'と'L99'をランダムシャッフル
    工程IDs = [f"L0{i}" for i in range(1, 8)] + ['L99']
    random.shuffle(工程IDs)

    for i in range(8):
        伝票番号 = f"SE{str(i+1).zfill(8)}"  # SE00000001〜SE00000008
        start_dt = start_datetimes[i]
        end_dt = end_datetimes[i]
        category_id = 生産区分IDs[i]
        工程ID = 工程IDs[i]
        content = f"サンプルデータ{i+1}"
        remarks = ""

        # SQLAlchemyモデルでINSERT
        生産データ = models.T生産(
            生産伝票ID=伝票番号,
            生産開始日時=start_dt.isoformat(),
            生産終了日時=end_dt.isoformat(),
            生産区分ID=category_id,
            工程ID=工程ID,
            生産内容=content,
            生産備考=remarks,
            **audit
        )
        db.add(生産データ)

    db.commit()
    logger.info("Initialized T生産")
