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
MAX_ITEMS = 10000

router = APIRouter(prefix="/apps/V生産", tags=["V生産"])

@router.post("/一覧", response_model=schemas.ResponseBase)
def list_V生産(
    request: Optional[schemas.ListRequest] = None,
    db: Session = Depends(deps.get_db),
    現在利用者: models.C利用者 = Depends(deps.get_現在利用者)
):
    filter_params = {}
    conditions = []

    if request and request.開始日付:
        conditions.append("""
        (
            date(T.生産開始日時) >= :start_date
            OR date(T.生産終了日時) >= :start_date
        )
        """)
        filter_params["start_date"] = request.開始日付

    if request and request.終了日付:
        conditions.append("""
        (
            date(T.生産開始日時) <= :end_date
            OR date(T.生産終了日時) <= :end_date
        )
        """)
        filter_params["end_date"] = request.終了日付

    where_sql = ""
    if conditions:
        where_sql = "WHERE " + " AND ".join(conditions)

    sql = f"""
    SELECT
        T.生産伝票ID,
        T.生産開始日時,
        T.生産終了日時,
        T.生産区分ID,
        T.工程ID,
        T.生産内容,
        T.生産備考,
        T.登録日時,
        T.登録利用者ID,
        T.登録利用者名,
        T.登録端末ID,
        T.更新日時,
        T.更新利用者ID,
        T.更新利用者名,
        T.更新端末ID,
        M2.生産区分名,
        M2.生産区分備考,
        M2.配色枠,
        M2.配色背景,
        M2.配色前景,
        M1.工程名,
        M1.工程備考
    FROM T生産 T
    LEFT JOIN M工程 M1 ON T.工程ID = M1.工程ID
    LEFT JOIN M生産区分 M2 ON T.生産区分ID = M2.生産区分ID
    {where_sql}
    ORDER BY T.生産開始日時 DESC
    LIMIT :limit
    """

    params = {"limit": MAX_ITEMS, **filter_params}
    result = db.execute(text(sql), params).fetchall()

    items = []
    for row in result:
        items.append({
            "生産伝票ID": row.生産伝票ID,
            "生産開始日時": row.生産開始日時,
            "生産終了日時": row.生産終了日時,
            "生産区分ID": row.生産区分ID,
            "工程ID": row.工程ID,
            "生産内容": row.生産内容,
            "生産備考": row.生産備考,
            "登録日時": row.登録日時,
            "登録利用者ID": row.登録利用者ID,
            "登録利用者名": row.登録利用者名,
            "登録端末ID": row.登録端末ID,
            "更新日時": row.更新日時,
            "更新利用者ID": row.更新利用者ID,
            "更新利用者名": row.更新利用者名,
            "更新端末ID": row.更新端末ID,
            "生産区分名": row.生産区分名,
            "生産区分備考": row.生産区分備考,
            "配色枠": row.配色枠,
            "配色背景": row.配色背景,
            "配色前景": row.配色前景,
            "工程名": row.工程名,
            "工程備考": row.工程備考
        })

    count_sql = f"""
    SELECT count(*)
    FROM T生産 T
    LEFT JOIN M工程 M1 ON T.工程ID = M1.工程ID
    LEFT JOIN M生産区分 M2 ON T.生産区分ID = M2.生産区分ID
    {where_sql}
    """
    total = db.execute(text(count_sql), filter_params).scalar()

    return schemas.ResponseBase(
        status="OK",
        message="V生産一覧を取得しました",
        data={
            "items": items,
            "total": total,
            "limit": MAX_ITEMS
        }
    )
