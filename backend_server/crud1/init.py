# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
# This software is licensed under the MIT License.
# https://github.com/monjyu1101
# Thank you for keeping the rules.
# ------------------------------------------------

from sqlalchemy.orm import Session
import models1, schemas
from crud1.utils import create_audit_fields, get_current_datetime
from crud1.C利用者 import get_C利用者_by_利用者ID, create_C利用者
from crud1.C権限 import create_C権限
from log_config import get_logger

logger = get_logger(__name__)

def init_db_data(db: Session):
    """初期データを投入"""
    # 権限の初期化
    if not db.query(models1.C権限).first():
        初期日時 = get_current_datetime()
        権限一覧 = [
            ('1', 'システム管理者', ''),
            ('2', '管理者', ''),
            ('3', '利用者', ''),
            ('4', '閲覧者', ''),
            ('9', 'その他', '')
        ]
        for 権限ID, 権限名, 権限備考 in 権限一覧:
            権限 = schemas.C権限Create(権限ID=権限ID, 権限名=権限名, 権限備考=権限備考)
            create_C権限(db, 権限)
        logger.info("Initialized C権限")

    # 利用者の初期化
    if not get_C利用者_by_利用者ID(db, "admin"):
        利用者一覧 = [
            ('admin', 'Administrator', '********', '1', 'システム管理者'),
            ('leader', '管理者', 'secret', '2', '管理者'),
            ('user', '利用者', 'user', '3', '利用者'),
            ('guest', '閲覧者', 'guest', '4', '閲覧者'),
            ('other', 'その他', 'other', '9', 'その他')
        ]
        for 利用者ID, 利用者名, パスワード, 権限ID, 利用者備考 in 利用者一覧:
            利用者 = schemas.C利用者Create(
                利用者ID=利用者ID,
                利用者名=利用者名,
                パスワード=パスワード,
                権限ID=権限ID,
                利用者備考=利用者備考
            )
            create_C利用者(db, 利用者)
        logger.info("Initialized C利用者")

    # 採番の初期化
    if not db.query(models1.C採番).first():
        初期値 = [
            ("T配車", 10000, "配車の採番"),
            ("T商品棚卸", 10000, "商品棚卸の採番"),
            ("T商品入庫", 10000, "商品入庫の採番"),
            ("T商品出庫", 10000, "商品出庫の採番")
        ]
        認証情報 = {"利用者ID": "system", "利用者名": "system"}
        登録項目 = create_audit_fields(認証情報)
        for 採番ID, 最終採番値, 採番備考 in 初期値:
            db.add(models1.C採番(
                採番ID=採番ID,
                最終採番値=最終採番値,
                採番備考=採番備考,
                **登録項目
            ))
        db.commit()
        logger.info("Initialized C採番")

