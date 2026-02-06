# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
# This software is licensed under the MIT License.
# https://github.com/monjyu1101
# Thank you for keeping the rules.
# ------------------------------------------------

from pydantic import BaseModel
from typing import Optional

# --- 配車区分 (M配車区分) ---

class M配車区分Base(BaseModel):
    配車区分名: str
    配車区分備考: Optional[str] = None
    配色枠: str
    配色背景: str
    配色前景: str


class M配車区分Create(M配車区分Base):
    配車区分ID: str


class M配車区分Update(BaseModel):
    配車区分ID: str
    配車区分名: Optional[str] = None
    配車区分備考: Optional[str] = None
    配色枠: str
    配色背景: str
    配色前景: str


class M配車区分Delete(BaseModel):
    配車区分ID: str


class M配車区分Get(BaseModel):
    配車区分ID: str


class M配車区分(M配車区分Base):
    配車区分ID: str
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
