# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101
# -------------------------------------------------------------------------

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

import apps_models as models
import apps_schema as schemas
import deps

MAX_ITEMS = 10000

router = APIRouter(prefix="/apps/V商品構成", tags=["V商品構成"])


@router.post("/一覧", response_model=schemas.ResponseBase)
def list_V商品構成(
    db: Session = Depends(deps.get_db),
    現在利用者: models.C利用者 = Depends(deps.get_現在利用者),
):
    params = {"limit": MAX_ITEMS}

    sql = """
    SELECT
        C.商品ID,
        P.商品名,
        P.単位,
        C.生産ロット,
        C.商品構成備考,
        C.有効,
        (
            SELECT COUNT(*)
            FROM M商品構成 D
            WHERE D.商品ID = C.商品ID AND D.明細番号 > 0
        ) AS 構成商品件数,
        C.登録日時,
        C.登録利用者ID,
        C.登録利用者名,
        C.登録端末ID,
        C.更新日時,
        C.更新利用者ID,
        C.更新利用者名,
        C.更新端末ID
    FROM M商品構成 C
    LEFT JOIN M商品 P ON C.商品ID = P.商品ID
    WHERE C.明細番号 = 0
    ORDER BY C.商品ID
    LIMIT :limit
    """

    result = db.execute(text(sql), params).fetchall()
    items = []
    for row in result:
        items.append({
            "商品ID": row.商品ID,
            "商品名": row.商品名,
            "単位": row.単位,
            "生産ロット": float(row.生産ロット) if row.生産ロット is not None else 0,
            "商品構成備考": row.商品構成備考,
            "有効": bool(row.有効) if row.有効 is not None else True,
            "構成商品件数": row.構成商品件数,
            "登録日時": row.登録日時,
            "登録利用者ID": row.登録利用者ID,
            "登録利用者名": row.登録利用者名,
            "登録端末ID": row.登録端末ID,
            "更新日時": row.更新日時,
            "更新利用者ID": row.更新利用者ID,
            "更新利用者名": row.更新利用者名,
            "更新端末ID": row.更新端末ID,
        })

    total = db.execute(text("SELECT count(*) FROM M商品構成 WHERE 明細番号 = 0")).scalar()

    return schemas.ResponseBase(
        status="OK",
        message="V商品構成一覧を取得しました",
        data={
            "items": items,
            "total": total,
            "limit": MAX_ITEMS,
        },
    )
