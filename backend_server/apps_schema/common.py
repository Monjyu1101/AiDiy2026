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

# --- 共通リクエスト ---

class ListRequest(BaseModel):
    開始日付: Optional[str] = None
    終了日付: Optional[str] = None
