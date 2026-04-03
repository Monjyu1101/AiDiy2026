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


class M工程Base(BaseModel):
    工程名: str
    工程備考: Optional[str] = None
    有効: bool = True


class M工程Create(M工程Base):
    工程ID: str


class M工程Update(BaseModel):
    工程ID: str
    工程名: Optional[str] = None
    工程備考: Optional[str] = None
    有効: Optional[bool] = None


class M工程Delete(BaseModel):
    工程ID: str


class M工程Get(BaseModel):
    工程ID: str


class M工程(M工程Base):
    工程ID: str
    有効: bool
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
