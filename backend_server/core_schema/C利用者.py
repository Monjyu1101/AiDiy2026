# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
# This software is licensed under the MIT License.
# https://github.com/monjyu1101
# Thank you for keeping the rules.
# ------------------------------------------------

from pydantic import BaseModel
from typing import Optional

# --- 利用者 (C利用者) ---

class C利用者Base(BaseModel):
    利用者名: str
    権限ID: str
    利用者備考: Optional[str] = None


class C利用者Create(C利用者Base):
    利用者ID: str
    パスワード: str


class C利用者Update(BaseModel):
    利用者ID: str
    利用者名: Optional[str] = None
    パスワード: Optional[str] = None
    権限ID: Optional[str] = None
    利用者備考: Optional[str] = None


class C利用者Delete(BaseModel):
    利用者ID: str


class C利用者Get(BaseModel):
    利用者ID: str


class C利用者(C利用者Base):
    利用者ID: str
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
