# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
# This software is licensed under the MIT License.
# https://github.com/monjyu1101
# Thank you for keeping the rules.
# ------------------------------------------------

from pydantic import BaseModel
from typing import Optional, Any

# --- 共通レスポンス ---

class ResponseBase(BaseModel):
    status: str = "OK"
    message: str
    data: Optional[Any] = None
    error: Optional[dict] = None


class ErrorResponse(BaseModel):
    status: str = "NG"
    message: str
    error: Optional[dict] = None

# --- 認証 ---

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

# --- V配車区分 (View) ---

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

# --- V車両 (View) ---

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

# --- V商品 (View) ---

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

# --- V配車ビュー ---

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

# --- V商品出庫ビュー ---

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

# --- V商品棚卸ビュー ---

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

# --- V商品入庫ビュー ---

class ListRequest(BaseModel):
    開始日付: Optional[str] = None
    終了日付: Optional[str] = None
