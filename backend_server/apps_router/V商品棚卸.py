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
from typing import Optional
import apps_schema as schemas, deps, apps_models as models
MAX_ITEMS = 10000

router = APIRouter(prefix="/apps/V商品棚卸", tags=["V商品棚卸"])

@router.post("/一覧", response_model=schemas.ResponseBase)
def list_V商品棚卸(
    request: Optional[schemas.ListRequest] = None,
    db: Session = Depends(deps.get_db),
    現在利用者: models.C利用者 = Depends(deps.get_現在利用者)
):
    filter_params = {}
    conditions = []

    if request and request.開始日付:
        conditions.append("date(T.棚卸日) >= :start_date")
        filter_params["start_date"] = request.開始日付

    if request and request.終了日付:
        conditions.append("date(T.棚卸日) <= :end_date")
        filter_params["end_date"] = request.終了日付

    where_sql = ""
    if conditions:
        where_sql = "WHERE " + " AND ".join(conditions)

    sql = f"""
    SELECT
        T.棚卸伝票ID,
        T.棚卸日,
        T.商品ID,
        T.実棚数量,
        T.棚卸備考,
        T.登録日時,
        T.登録利用者ID,
        T.登録利用者名,
        T.登録端末ID,
        T.更新日時,
        T.更新利用者ID,
        T.更新利用者名,
        T.更新端末ID,
        M.商品名,
        M.単位,
        M.商品備考
    FROM T商品棚卸 T
    LEFT JOIN M商品 M ON T.商品ID = M.商品ID
    {where_sql}
    ORDER BY T.棚卸日 DESC
    LIMIT :limit
    """

    params = {"limit": MAX_ITEMS, **filter_params}
    result = db.execute(text(sql), params).fetchall()

    items = []
    for row in result:
        items.append({
            "棚卸伝票ID": row.棚卸伝票ID,
            "棚卸日": row.棚卸日,
            "商品ID": row.商品ID,
            "実棚数量": row.実棚数量,
            "棚卸備考": row.棚卸備考,
            "登録日時": row.登録日時,
            "登録利用者ID": row.登録利用者ID,
            "登録利用者名": row.登録利用者名,
            "登録端末ID": row.登録端末ID,
            "更新日時": row.更新日時,
            "更新利用者ID": row.更新利用者ID,
            "更新利用者名": row.更新利用者名,
            "更新端末ID": row.更新端末ID,
            "商品名": row.商品名,
            "単位": row.単位,
            "商品備考": row.商品備考
        })

    count_sql = f"""
    SELECT count(*)
    FROM T商品棚卸 T
    LEFT JOIN M商品 M ON T.商品ID = M.商品ID
    {where_sql}
    """
    total = db.execute(text(count_sql), filter_params).scalar()

    return schemas.ResponseBase(
        status="OK",
        message="V商品棚卸一覧を取得しました",
        data={
            "items": items,
            "total": total,
            "limit": MAX_ITEMS
        }
    )

