# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
# This software is licensed under the MIT License.
# https://github.com/monjyu1101
# Thank you for keeping the rules.
# ------------------------------------------------

from pydantic import BaseModel
from typing import Optional

# --- A会話履歴 ---

class A会話履歴Base(BaseModel):
    セッションID: str
    シーケンス: int
    チャンネル: int
    メッセージ識別: str
    メッセージ内容: Optional[str] = None
    ファイル名: Optional[str] = None
    サムネイル画像: Optional[str] = None


class A会話履歴Create(A会話履歴Base):
    pass


class A会話履歴Update(BaseModel):
    セッションID: str
    シーケンス: int
    メッセージ内容: Optional[str] = None
    ファイル名: Optional[str] = None
    サムネイル画像: Optional[str] = None


class A会話履歴Delete(BaseModel):
    セッションID: str
    シーケンス: int


class A会話履歴Get(BaseModel):
    セッションID: str
    シーケンス: int


class A会話履歴ListRequest(BaseModel):
    セッションID: Optional[str] = None
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
