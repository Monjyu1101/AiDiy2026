# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
# This software is licensed under the MIT License.
# https://github.com/monjyu1101
# Thank you for keeping the rules.
# ------------------------------------------------

from sqlalchemy import Column, Text
from database import Base

class M車両(Base):
    """M車両テーブル（車両マスタ）"""
    __tablename__ = "M車両"
    __table_args__ = {'extend_existing': True}

    車両ID = Column(Text, primary_key=True)
    車両名 = Column(Text, nullable=False)
    車両備考 = Column(Text)
    登録日時 = Column(Text, nullable=False)
    登録利用者ID = Column(Text, nullable=False)
    登録利用者名 = Column(Text)
    登録端末ID = Column(Text, nullable=False)
    更新日時 = Column(Text, nullable=False)
    更新利用者ID = Column(Text, nullable=False)
    更新利用者名 = Column(Text)
    更新端末ID = Column(Text, nullable=False)
