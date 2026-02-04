# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
# This software is licensed under the MIT License.
# https://github.com/monjyu1101
# Thank you for keeping the rules.
# ------------------------------------------------

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import apps_schema as schemas, deps, apps_models as models
MAX_ITEMS = 10000

router = APIRouter(prefix="/apps/V配車区分", tags=["V配車区分"])

@router.post("/一覧", response_model=schemas.ResponseBase)
def list_V配車区分(
    db: Session = Depends(deps.get_db),
    現在利用者: models.C利用者 = Depends(deps.get_現在利用者)
):
    params = {"limit": MAX_ITEMS}

    sql = f"""
    SELECT 配車区分ID, 配車区分名, 配車区分備考, 配色枠, 配色背景, 配色前景,
           登録日時, 登録利用者ID, 登録利用者名, 登録端末ID,
           更新日時, 更新利用者ID, 更新利用者名, 更新端末ID
    FROM M配車区分
    LIMIT :limit
    """

    result = db.execute(text(sql), params).fetchall()

    items = []
    for row in result:
        items.append({
            "配車区分ID": row.配車区分ID,
            "配車区分名": row.配車区分名,
            "配車区分備考": row.配車区分備考,
            "配色枠": row.配色枠,
            "配色背景": row.配色背景,
            "配色前景": row.配色前景,
            "登録日時": row.登録日時,
            "登録利用者ID": row.登録利用者ID,
            "登録利用者名": row.登録利用者名,
            "登録端末ID": row.登録端末ID,
            "更新日時": row.更新日時,
            "更新利用者ID": row.更新利用者ID,
            "更新利用者名": row.更新利用者名,
            "更新端末ID": row.更新端末ID
        })

    count_sql = "SELECT count(*) FROM M配車区分"
    total = db.execute(text(count_sql)).scalar()

    return schemas.ResponseBase(
        status="OK",
        message="V配車区分一覧を取得しました",
        data={
            "items": items,
            "total": total,
            "limit": MAX_ITEMS
        }
    )


