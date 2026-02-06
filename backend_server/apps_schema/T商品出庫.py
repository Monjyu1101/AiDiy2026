# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
# This software is licensed under the MIT License.
# https://github.com/monjyu1101
# Thank you for keeping the rules.
# ------------------------------------------------

from pydantic import BaseModel
from typing import Optional

# --- 商品出庫 (T商品出庫) ---

class T商品出庫Base(BaseModel):
    出庫日: str
    商品ID: str
    出庫数量: int
    出庫備考: Optional[str] = None


class T商品出庫Create(T商品出庫Base):
    出庫伝票ID: Optional[str] = None  # 自動採番の場合は省略可能


class T商品出庫Update(BaseModel):
    出庫日: Optional[str] = None
    商品ID: Optional[str] = None
    出庫数量: Optional[int] = None
    出庫備考: Optional[str] = None


class T商品出庫Delete(BaseModel):
    出庫伝票ID: str


class T商品出庫Get(BaseModel):
    出庫伝票ID: str


class T商品出庫(T商品出庫Base):
    出庫伝票ID: str
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
