# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
# This software is licensed under the MIT License.
# https://github.com/monjyu1101
# Thank you for keeping the rules.
# ------------------------------------------------

from pydantic import BaseModel
from typing import Optional

# --- 商品 (M商品) ---

class M商品Base(BaseModel):
    商品名: str
    単位: str
    商品備考: Optional[str] = None


class M商品Create(M商品Base):
    商品ID: str


class M商品Update(BaseModel):
    商品ID: str
    商品名: Optional[str] = None
    単位: Optional[str] = None
    商品備考: Optional[str] = None


class M商品Delete(BaseModel):
    商品ID: str


class M商品Get(BaseModel):
    商品ID: str


class M商品(M商品Base):
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
