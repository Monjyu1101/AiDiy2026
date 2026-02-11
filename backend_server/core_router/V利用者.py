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
import core_schema as schemas, deps, core_models as models
MAX_ITEMS = 10000

router = APIRouter(prefix="/core/V利用者", tags=["V利用者"])

@router.post("/一覧", response_model=schemas.ResponseBase)
def list_V利用者(
    db: Session = Depends(deps.get_db),
    現在利用者: models.C利用者 = Depends(deps.get_現在利用者)
):
    # Viewのクエリ (SQLAlchemyのモデルとしてViewを定義していないため直接SQLか、モデル定義が必要)
    # 今回はmodels.pyにはView定義がないため、生SQLで取得して辞書にマッピングするか、Viewモデルを追加定義する。
    # ここではシンプルにJOINクエリを自分で構築するか、Viewを使う。Viewを定義したとしてSQLを投げる。
    
    params = {"limit": MAX_ITEMS}

    sql = f"""
    SELECT
        u."利用者ID",
        u."利用者名",
        u."権限ID",
        COALESCE(u."利用者備考", '') AS "利用者備考",
        u."登録日時",
        u."登録利用者ID",
        COALESCE(u."登録利用者名", '') AS "登録利用者名",
        u."登録端末ID",
        u."更新日時",
        u."更新利用者ID",
        COALESCE(u."更新利用者名", '') AS "更新利用者名",
        u."更新端末ID",
        COALESCE(p."権限名", '') AS "権限名",
        COALESCE(p."権限備考", '') AS "権限備考"
    FROM "C利用者" u
    LEFT JOIN "C権限" p ON u."権限ID" = p."権限ID"
    LIMIT :limit
    """
    
    result = db.execute(text(sql), params).fetchall()
    
    # 辞書リストに変換
    items = []
    for row in result:
        # rowはタプルまたはRowオブジェクト。カラム名でアクセス可能。
        item = {
            "利用者ID": row.利用者ID,
            "利用者名": row.利用者名,
            "権限ID": row.権限ID,
            "利用者備考": row.利用者備考,
            "登録日時": row.登録日時,
            "登録利用者ID": row.登録利用者ID,
            "登録利用者名": row.登録利用者名,
            "登録端末ID": row.登録端末ID,
            "更新日時": row.更新日時,
            "更新利用者ID": row.更新利用者ID,
            "更新利用者名": row.更新利用者名,
            "更新端末ID": row.更新端末ID,
            "権限名": row.権限名,
            "権限備考": row.権限備考
        }
        items.append(item)
        
    # トータル件数
    count_sql = """
    SELECT count(*)
    FROM "C利用者" u
    LEFT JOIN "C権限" p ON u."権限ID" = p."権限ID"
    """
    total = db.execute(text(count_sql)).scalar()

    return schemas.ResponseBase(
        status="OK",
        message="V利用者一覧を取得しました",
        data={
            "items": items,
            "total": total,
            "limit": MAX_ITEMS
        }
    )



