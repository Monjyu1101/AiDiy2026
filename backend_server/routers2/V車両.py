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
import schemas, deps, models2 as models
MAX_ITEMS = 10000

router = APIRouter(prefix="/apps/V車両", tags=["V車両"])

@router.post("/一覧", response_model=schemas.ResponseBase)
def list_V車両(
    db: Session = Depends(deps.get_db),
    現在利用者: models.C利用者 = Depends(deps.get_現在利用者)
):
    params = {"limit": MAX_ITEMS}

    sql = f"""
    SELECT 車両ID, 車両名, 車両備考,
           登録日時, 登録利用者ID, 登録利用者名, 登録端末ID,
           更新日時, 更新利用者ID, 更新利用者名, 更新端末ID
    FROM M車両
    ORDER BY 車両ID
    LIMIT :limit
    """

    result = db.execute(text(sql), params).fetchall()

    items = []
    for row in result:
        items.append({
            "車両ID": row.車両ID,
            "車両名": row.車両名,
            "車両備考": row.車両備考,
            "登録日時": row.登録日時,
            "登録利用者ID": row.登録利用者ID,
            "登録利用者名": row.登録利用者名,
            "登録端末ID": row.登録端末ID,
            "更新日時": row.更新日時,
            "更新利用者ID": row.更新利用者ID,
            "更新利用者名": row.更新利用者名,
            "更新端末ID": row.更新端末ID
        })

    count_sql = "SELECT count(*) FROM M車両"
    total = db.execute(text(count_sql)).scalar()

    return schemas.ResponseBase(
        status="OK",
        message="V車両一覧を取得しました",
        data={
            "items": items,
            "total": total,
            "limit": MAX_ITEMS
        }
    )


