# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101
# -------------------------------------------------------------------------

from sqlalchemy import Column, Text, Integer
from database import Base

class T商品出庫(Base):
    """T商品出庫テーブル（商品出庫伝票トランザクション）"""
    __tablename__ = "T商品出庫"
    __table_args__ = {'extend_existing': True}

    出庫伝票ID = Column(Text, primary_key=True)
    出庫日 = Column(Text, nullable=False)
    商品ID = Column(Text, nullable=False)
    出庫数量 = Column(Integer, nullable=False)
    出庫備考 = Column(Text)
    登録日時 = Column(Text, nullable=False)
    登録利用者ID = Column(Text, nullable=False)
    登録利用者名 = Column(Text)
    登録端末ID = Column(Text, nullable=False)
    更新日時 = Column(Text, nullable=False)
    更新利用者ID = Column(Text, nullable=False)
    更新利用者名 = Column(Text)
    更新端末ID = Column(Text, nullable=False)
