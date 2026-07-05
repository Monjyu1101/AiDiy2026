# -*- coding: utf-8 -*-
# ■ バックエンド（Python）の命名例

# 正解：ビジネスドメインは日本語（Column 型は Text を使用、String は使わない）
class C利用者(Base):
 __tablename__ = "C利用者"
 利用者ID = Column(Text, primary_key=True)
 利用者名 = Column(Text)
 パスワード = Column(Text)
 権限ID = Column(Text)

def get_C利用者_by_利用者ID(db: Session, 利用者ID: str):
 return db.query(models.C利用者).filter(
 models.C利用者.利用者ID == 利用者ID
 ).first()

# 正解：システム/フレームワーク用語は英語
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter(prefix="/core/C利用者", tags=["C利用者"])

def get_db():
 db = SessionLocal()
 try:
 yield db
 finally:
 db.close()
