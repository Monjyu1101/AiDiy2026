# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101
# -------------------------------------------------------------------------

from sqlalchemy import Column, Text
from database import Base

class T生産(Base):
    """T生産テーブル（生産伝票トランザクション）"""
    __tablename__ = "T生産"
    __table_args__ = {'extend_existing': True}

    生産伝票ID = Column(Text, primary_key=True)
    生産開始日時 = Column(Text, nullable=False)
    生産終了日時 = Column(Text, nullable=False)
    生産区分ID = Column(Text)
    工程ID = Column(Text, nullable=False)
    生産内容 = Column(Text)
    生産備考 = Column(Text)
    登録日時 = Column(Text, nullable=False)
    登録利用者ID = Column(Text, nullable=False)
    登録利用者名 = Column(Text)
    登録端末ID = Column(Text, nullable=False)
    更新日時 = Column(Text, nullable=False)
    更新利用者ID = Column(Text, nullable=False)
    更新利用者名 = Column(Text)
    更新端末ID = Column(Text, nullable=False)
