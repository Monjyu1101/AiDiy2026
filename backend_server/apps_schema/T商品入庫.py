# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101
# -------------------------------------------------------------------------

from pydantic import BaseModel
from typing import Optional

# --- 商品入庫 (T商品入庫) ---

class T商品入庫Base(BaseModel):
    入庫日: str
    商品ID: str
    入庫数量: int
    入庫備考: Optional[str] = None


class T商品入庫Create(T商品入庫Base):
    入庫伝票ID: Optional[str] = None  # 自動採番の場合は省略可能


class T商品入庫Update(BaseModel):
    入庫日: Optional[str] = None
    商品ID: Optional[str] = None
    入庫数量: Optional[int] = None
    入庫備考: Optional[str] = None


class T商品入庫Delete(BaseModel):
    入庫伝票ID: str


class T商品入庫Get(BaseModel):
    入庫伝票ID: str


class T商品入庫(T商品入庫Base):
    入庫伝票ID: str
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
