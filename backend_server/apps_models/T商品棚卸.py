# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
# This software is licensed under the MIT License.
# https://github.com/monjyu1101
# Thank you for keeping the rules.
# ------------------------------------------------

from sqlalchemy import Column, Text, Integer
from database import Base

class T商品棚卸(Base):
    """T商品棚卸テーブル（商品棚卸伝票トランザクション）"""
    __tablename__ = "T商品棚卸"
    __table_args__ = {'extend_existing': True}

    棚卸伝票ID = Column(Text, primary_key=True)
    棚卸日 = Column(Text, nullable=False)
    商品ID = Column(Text, nullable=False)
    実棚数量 = Column(Integer, nullable=False)
    棚卸備考 = Column(Text)
    登録日時 = Column(Text, nullable=False)
    登録利用者ID = Column(Text, nullable=False)
    登録利用者名 = Column(Text)
    登録端末ID = Column(Text, nullable=False)
    更新日時 = Column(Text, nullable=False)
    更新利用者ID = Column(Text, nullable=False)
    更新利用者名 = Column(Text)
    更新端末ID = Column(Text, nullable=False)
