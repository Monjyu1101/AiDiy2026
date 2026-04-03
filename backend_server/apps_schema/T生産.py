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

# --- 生産 (T生産) ---

class T生産Base(BaseModel):
    生産開始日時: str
    生産終了日時: str
    生産区分ID: Optional[str] = None
    工程ID: str
    生産内容: Optional[str] = None
    生産備考: Optional[str] = None


class T生産Create(T生産Base):
    生産伝票ID: Optional[str] = None  # 自動採番の場合は省略可能


class T生産Update(BaseModel):
    生産開始日時: Optional[str] = None
    生産終了日時: Optional[str] = None
    生産区分ID: Optional[str] = None
    工程ID: Optional[str] = None
    生産内容: Optional[str] = None
    生産備考: Optional[str] = None


class T生産Delete(BaseModel):
    生産伝票ID: str


class T生産Get(BaseModel):
    生産伝票ID: str


class T生産(T生産Base):
    生産伝票ID: str
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
