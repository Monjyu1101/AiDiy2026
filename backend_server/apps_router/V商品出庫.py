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
from typing import Optional
import apps_schema as schemas, deps, apps_models as models
from list_controls import append_active_condition, get_limit_clause

router = APIRouter(prefix="/apps/V商品出庫", tags=["V商品出庫"])

@router.post("/一覧", response_model=schemas.ResponseBase)
def list_V商品出庫(
    request: Optional[schemas.ListRequest] = None,
    db: Session = Depends(deps.get_db),
    現在利用者: models.C利用者 = Depends(deps.get_現在利用者)
):
    filter_params = {}
    conditions = []
    append_active_condition(conditions, request, "T.有効")

    if request and request.開始日付:
        conditions.append("date(T.出庫日) >= :start_date")
        filter_params["start_date"] = request.開始日付

    if request and request.終了日付:
        conditions.append("date(T.出庫日) <= :end_date")
        filter_params["end_date"] = request.終了日付

    where_sql = ""
    if conditions:
        where_sql = "WHERE " + " AND ".join(conditions)

    limit_sql, limit_value = get_limit_clause(request)
    sql = f"""
    SELECT
        T.出庫伝票ID,
        T.出庫日,
        T.商品ID,
        T.出庫数量,
        T.出庫備考,
        T.有効,
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
    FROM T商品出庫 T
    LEFT JOIN M商品 M ON T.商品ID = M.商品ID
    {where_sql}
    ORDER BY T.出庫日 DESC
    {limit_sql}
    """

    params = {**filter_params}
    if limit_value is not None:
        params["limit"] = limit_value
    result = db.execute(text(sql), params).fetchall()

    items = []
    for row in result:
        items.append({
            "出庫伝票ID": row.出庫伝票ID,
            "出庫日": row.出庫日,
            "商品ID": row.商品ID,
            "出庫数量": row.出庫数量,
            "出庫備考": row.出庫備考,
            "有効": bool(row.有効) if row.有効 is not None else True,
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
    FROM T商品出庫 T
    LEFT JOIN M商品 M ON T.商品ID = M.商品ID
    {where_sql}
    """
    total = db.execute(text(count_sql), filter_params).scalar()

    return schemas.ResponseBase(
        status="OK",
        message="V商品出庫一覧を取得しました",
        data={
            "items": items,
            "total": total,
            "limit": limit_value
        }
    )
