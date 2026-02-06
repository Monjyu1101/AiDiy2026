# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
# This software is licensed under the MIT License.
# https://github.com/monjyu1101
# Thank you for keeping the rules.
# ------------------------------------------------

from pydantic import BaseModel
from typing import Optional

# --- 車両 (M車両) ---

class M車両Base(BaseModel):
    車両名: str
    車両備考: Optional[str] = None


class M車両Create(M車両Base):
    車両ID: str


class M車両Update(BaseModel):
    車両ID: str
    車両名: Optional[str] = None
    車両備考: Optional[str] = None


class M車両Delete(BaseModel):
    車両ID: str


class M車両Get(BaseModel):
    車両ID: str


class M車両(M車両Base):
    車両ID: str
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
