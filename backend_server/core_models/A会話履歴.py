# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101
# -------------------------------------------------------------------------

from sqlalchemy import Column, Integer, Text
from database import Base


class A会話履歴(Base):
    """
    A会話履歴テーブル
    WebSocketセッションの会話履歴を保存
    """
    __tablename__ = "A会話履歴"
    __table_args__ = {'extend_existing': True}

    # 複合主キー
    セッションID = Column(Text, primary_key=True)
    シーケンス = Column(Integer, primary_key=True)

    # 会話データ
    チャンネル = Column(Text, nullable=False)
    メッセージ識別 = Column(Text, nullable=False)
    メッセージ内容 = Column(Text)
    ファイル名 = Column(Text)
    サムネイル画像 = Column(Text)

    # 監査フィールド
    登録日時 = Column(Text, nullable=False)
    登録利用者ID = Column(Text, nullable=False)
    登録利用者名 = Column(Text)
    登録端末ID = Column(Text, nullable=False)
    更新日時 = Column(Text, nullable=False)
    更新利用者ID = Column(Text, nullable=False)
    更新利用者名 = Column(Text)
    更新端末ID = Column(Text, nullable=False)
