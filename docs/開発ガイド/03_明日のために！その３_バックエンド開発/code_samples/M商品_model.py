# backend_server/apps_models/M商品.py

from sqlalchemy import Column, Text
from database import Base


class M商品(Base):
 """M商品マスタ"""
 __tablename__ = "M商品"

 # 主キー
 商品ID = Column(Text, primary_key=True)

 # 業務フィールド
 商品名 = Column(Text, nullable=False)
 単位 = Column(Text, nullable=False)
 商品備考 = Column(Text)

 # 監査フィールド（登録）
 登録日時 = Column(Text, nullable=False)
 登録利用者ID = Column(Text, nullable=False)
 登録利用者名 = Column(Text)
 登録端末ID = Column(Text, nullable=False)

 # 監査フィールド（更新）
 更新日時 = Column(Text, nullable=False)
 更新利用者ID = Column(Text, nullable=False)
 更新利用者名 = Column(Text)
 更新端末ID = Column(Text, nullable=False)
