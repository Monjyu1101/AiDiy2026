# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
# This software is licensed under the MIT License.
# https://github.com/monjyu1101
# Thank you for keeping the rules.
# ------------------------------------------------

from sqlalchemy import Column, Text
from database import Base

class C利用者(Base):
    """C利用者テーブル（利用者マスタ）"""
    __tablename__ = "C利用者"
    __table_args__ = {'extend_existing': True}

    利用者ID = Column(Text, primary_key=True)
    利用者名 = Column(Text, nullable=False)
    パスワード = Column(Text, nullable=False)
    権限ID = Column(Text, nullable=False)
    利用者備考 = Column(Text)
    登録日時 = Column(Text, nullable=False)
    登録利用者ID = Column(Text, nullable=False)
    登録利用者名 = Column(Text)
    登録端末ID = Column(Text, nullable=False)
    更新日時 = Column(Text, nullable=False)
    更新利用者ID = Column(Text, nullable=False)
    更新利用者名 = Column(Text)
    更新端末ID = Column(Text, nullable=False)
