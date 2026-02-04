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

class LoginRequest(BaseModel):
    利用者ID: str
    パスワード: str


class Token(BaseModel):
    access_token: str
    token_type: str

# --- A会話履歴 ---

class A会話履歴Base(BaseModel):
    ソケットID: str
    シーケンス: int
    チャンネル: int
    メッセージ識別: str
    メッセージ内容: Optional[str] = None
    ファイル名: Optional[str] = None
    サムネイル画像: Optional[str] = None


class A会話履歴Create(A会話履歴Base):
    pass


class A会話履歴Update(BaseModel):
    ソケットID: str
    シーケンス: int
    メッセージ内容: Optional[str] = None
    ファイル名: Optional[str] = None
    サムネイル画像: Optional[str] = None


class A会話履歴Delete(BaseModel):
    ソケットID: str
    シーケンス: int


class A会話履歴Get(BaseModel):
    ソケットID: str
    シーケンス: int


class A会話履歴ListRequest(BaseModel):
    ソケットID: Optional[str] = None
    チャンネル: Optional[int] = None
    件数: Optional[int] = None


class A会話履歴Response(A会話履歴Base):
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

# --- 権限 (C権限) ---

class C権限Base(BaseModel):
    権限名: str
    権限備考: Optional[str] = None


class C権限Create(C権限Base):
    権限ID: str


class C権限Update(BaseModel):
    権限ID: str
    権限名: Optional[str] = None
    権限備考: Optional[str] = None


class C権限Delete(BaseModel):
    権限ID: str


class C権限(C権限Base):
    権限ID: str
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

# --- 採番 (C採番) ---

class C採番Base(BaseModel):
    最終採番値: int
    採番備考: Optional[str] = None


class C採番Create(C採番Base):
    採番ID: str


class C採番Update(BaseModel):
    採番ID: str
    最終採番値: Optional[int] = None
    採番備考: Optional[str] = None


class C採番Delete(BaseModel):
    採番ID: str


class C採番Get(BaseModel):
    採番ID: str


class C採番(C採番Base):
    採番ID: str
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

# --- 配車区分 (M配車区分) ---
