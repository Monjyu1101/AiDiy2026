# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
# This software is licensed under the MIT License.
# https://github.com/monjyu1101
# Thank you for keeping the rules.
# ------------------------------------------------

from pydantic import BaseModel
from typing import Optional

# --- 商品棚卸 (T商品棚卸) ---

class T商品棚卸Base(BaseModel):
    棚卸日: str
    商品ID: str
    実棚数量: int
    棚卸備考: Optional[str] = None


class T商品棚卸Create(T商品棚卸Base):
    棚卸伝票ID: Optional[str] = None  # 自動採番の場合は省略可能


class T商品棚卸Update(BaseModel):
    棚卸日: Optional[str] = None
    商品ID: Optional[str] = None
    実棚数量: Optional[int] = None
    棚卸備考: Optional[str] = None


class T商品棚卸Delete(BaseModel):
    棚卸伝票ID: str


class T商品棚卸Get(BaseModel):
    棚卸伝票ID: str


class T商品棚卸(T商品棚卸Base):
    棚卸伝票ID: str
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
