# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101
# -------------------------------------------------------------------------

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import apps_schema as schemas, deps, apps_models as models
MAX_ITEMS = 10000

router = APIRouter(prefix="/apps/V工程", tags=["V工程"])


@router.post("/一覧", response_model=schemas.ResponseBase)
def list_V工程(
    db: Session = Depends(deps.get_db),
    現在利用者: models.C利用者 = Depends(deps.get_現在利用者)
):
    params = {"limit": MAX_ITEMS}

    sql = f"""
    SELECT 工程ID, 工程名, 工程備考,
           有効,
           登録日時, 登録利用者ID, 登録利用者名, 登録端末ID,
           更新日時, 更新利用者ID, 更新利用者名, 更新端末ID
    FROM M工程
    ORDER BY 工程ID
    LIMIT :limit
    """

    result = db.execute(text(sql), params).fetchall()

    items = []
    for row in result:
        items.append({
            "工程ID": row.工程ID,
            "工程名": row.工程名,
            "工程備考": row.工程備考,
            "有効": bool(row.有効) if row.有効 is not None else True,
            "登録日時": row.登録日時,
            "登録利用者ID": row.登録利用者ID,
            "登録利用者名": row.登録利用者名,
            "登録端末ID": row.登録端末ID,
            "更新日時": row.更新日時,
            "更新利用者ID": row.更新利用者ID,
            "更新利用者名": row.更新利用者名,
            "更新端末ID": row.更新端末ID
        })

    count_sql = "SELECT count(*) FROM M工程"
    total = db.execute(text(count_sql)).scalar()

    return schemas.ResponseBase(
        status="OK",
        message="V工程一覧を取得しました",
        data={
            "items": items,
            "total": total,
            "limit": MAX_ITEMS
        }
    )
