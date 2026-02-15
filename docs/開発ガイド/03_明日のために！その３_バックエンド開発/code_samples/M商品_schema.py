# backend_server/apps_schema/M商品.py

from pydantic import BaseModel
from typing import Optional


# --- 商品 (M商品) ---

class M商品Base(BaseModel):
 """M商品の基本Schema"""
 商品名: str
 単位: str
 商品備考: Optional[str] = None


class M商品Create(M商品Base):
 """M商品新規作成用Schema"""
 商品ID: str


class M商品Update(BaseModel):
 """M商品更新用Schema（すべてOptional）"""
 商品ID: str
 商品名: Optional[str] = None
 単位: Optional[str] = None
 商品備考: Optional[str] = None


class M商品Delete(BaseModel):
 """M商品削除用Schema"""
 商品ID: str


class M商品Get(BaseModel):
 """M商品取得用Schema"""
 商品ID: str


class M商品(M商品Base):
 """M商品レスポンス用Schema（監査フィールド含む）"""
 商品ID: str
 登録日時: str
 登録利用者ID: str
 登録利用者名: Optional[str]
 登録端末ID: str
 更新日時: str
 更新利用者ID: str
 更新利用者名: Optional[str]
 更新端末ID: str

 class Config:
 from_attributes = True
