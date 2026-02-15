# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101
# -------------------------------------------------------------------------

from fastapi import APIRouter, Depends
from pydantic import BaseModel
import os
import base64
import core_schema as schemas
import deps
import core_models as models


router = APIRouter(prefix="/core/files", tags=["files"])


class ファイル内容取得Request(BaseModel):
    ファイル名: str


def _解決ファイルパス(ファイル名: str) -> str:
    if os.path.isabs(ファイル名):
        return os.path.normpath(ファイル名)

    バックエンドディレクトリ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.normpath(os.path.join(バックエンドディレクトリ, ファイル名))


@router.post("/内容取得", response_model=schemas.ResponseBase)
def get_ファイル内容(
    request: ファイル内容取得Request,
    現在利用者: models.C利用者 = Depends(deps.get_現在利用者),
):
    ファイル名 = (request.ファイル名 or "").strip()
    if not ファイル名:
        return schemas.ResponseBase(
            status="NG",
            message="ファイル名を指定してください",
            error={"code": "INVALID_FILE_NAME"},
        )

    解決パス = _解決ファイルパス(ファイル名)
    if not os.path.isfile(解決パス):
        return schemas.ResponseBase(
            status="NG",
            message="指定されたファイルが見つかりません",
            error={"code": "FILE_NOT_FOUND", "file_path": 解決パス},
        )

    try:
        with open(解決パス, "rb") as f:
            バイナリ = f.read()
        base64_data = base64.b64encode(バイナリ).decode("ascii")
    except Exception as e:
        return schemas.ResponseBase(
            status="NG",
            message=f"ファイルの読み込みに失敗しました: {str(e)}",
            error={"code": "FILE_READ_ERROR", "file_path": 解決パス},
        )

    return schemas.ResponseBase(
        status="OK",
        message="ファイル内容を取得しました",
        data={
            "ファイル名": ファイル名,
            "解決ファイルパス": 解決パス,
            "base64_data": base64_data,
        },
    )
