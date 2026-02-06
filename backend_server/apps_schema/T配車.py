# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
# This software is licensed under the MIT License.
# https://github.com/monjyu1101
# Thank you for keeping the rules.
# ------------------------------------------------

from pydantic import BaseModel
from typing import Optional

# --- 配車 (T配車) ---

class T配車Base(BaseModel):
    配車開始日時: str
    配車終了日時: str
    配車区分ID: Optional[str] = None
    車両ID: str
    配車内容: Optional[str] = None
    配車備考: Optional[str] = None


class T配車Create(T配車Base):
    配車伝票ID: Optional[str] = None  # 自動採番の場合は省略可能


class T配車Update(BaseModel):
    配車開始日時: Optional[str] = None
    配車終了日時: Optional[str] = None
    配車区分ID: Optional[str] = None
    車両ID: Optional[str] = None
    配車内容: Optional[str] = None
    配車備考: Optional[str] = None


class T配車Delete(BaseModel):
    配車伝票ID: str


class T配車Get(BaseModel):
    配車伝票ID: str


class T配車(T配車Base):
    配車伝票ID: str
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
