from sqlalchemy import Column, Text
from database import Base

class M配車区分(Base):
    """M配車区分テーブル（配車区分マスタ）"""
    __tablename__ = "M配車区分"
    __table_args__ = {'extend_existing': True}

    配車区分ID = Column(Text, primary_key=True)
    配車区分名 = Column(Text, nullable=False)
    配車区分備考 = Column(Text)
    配色枠 = Column(Text)
    配色背景 = Column(Text)
    配色前景 = Column(Text)
    登録日時 = Column(Text, nullable=False)
    登録利用者ID = Column(Text, nullable=False)
    登録利用者名 = Column(Text)
    登録端末ID = Column(Text, nullable=False)
    更新日時 = Column(Text, nullable=False)
    更新利用者ID = Column(Text, nullable=False)
    更新利用者名 = Column(Text)
    更新端末ID = Column(Text, nullable=False)

