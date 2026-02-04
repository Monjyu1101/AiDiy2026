# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
# This software is licensed under the MIT License.
# https://github.com/monjyu1101
# Thank you for keeping the rules.
# ------------------------------------------------

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
import apps_schema as schemas, apps_crud as crud, deps, apps_models as models
MAX_ITEMS = 10000

router = APIRouter(prefix="/apps/T商品入庫", tags=["T商品入庫"])

@router.post("/一覧", response_model=schemas.ResponseBase)
def list_T商品入庫(
    request: Optional[schemas.ListRequest] = None,
    db: Session = Depends(deps.get_db),
    現在利用者: models.C利用者 = Depends(deps.get_現在利用者)
):
    query = db.query(models.T商品入庫)
    if request and request.開始日付:
        query = query.filter(func.date(models.T商品入庫.入庫日) >= request.開始日付)

    if request and request.終了日付:
        query = query.filter(func.date(models.T商品入庫.入庫日) <= request.終了日付)

    total = query.count()
    items = query.order_by(models.T商品入庫.入庫日.desc()).limit(MAX_ITEMS).all()

    return schemas.ResponseBase(
        status="OK",
        message="商品入庫一覧を取得しました",
        data={
            "items": [schemas.T商品入庫.from_orm(item) for item in items],
            "total": total,
            "limit": MAX_ITEMS
        }
    )

@router.post("/取得", response_model=schemas.ResponseBase)
def get_T商品入庫(
    request: schemas.T商品入庫Get,
    db: Session = Depends(deps.get_db),
    現在利用者: models.C利用者 = Depends(deps.get_現在利用者)
):
    item = crud.get_T商品入庫(db, request.入庫伝票ID)
    if not item:
        return schemas.ResponseBase(status="NG", message="指定された入庫伝票が見つかりません", error={"code": "NOT_FOUND"})

    return schemas.ResponseBase(
        status="OK",
        message="商品入庫情報を取得しました",
        data=schemas.T商品入庫.from_orm(item)
    )

@router.post("/登録", response_model=schemas.ResponseBase)
def create_T商品入庫(
    request: schemas.T商品入庫Create,
    db: Session = Depends(deps.get_db),
    現在利用者: models.C利用者 = Depends(deps.get_現在利用者)
):
    # 入庫伝票IDが指定されていない場合は自動採番
    if not request.入庫伝票ID:
        採番 = db.query(models.C採番).filter(models.C採番.採番ID == "T商品入庫").first()
        if not 採番:
            return schemas.ResponseBase(status="NG", message="採番設定が見つかりません", error={"code": "NUMBERING_NOT_FOUND"})

        # 次の番号を発番
        next_number = 採番.最終採番値 + 1
        入庫伝票ID = f"HI{str(next_number).zfill(8)}"  # HI00010001形式

        # 最終採番値を更新
        採番.最終採番値 = next_number
        採番.更新日時 = crud.get_current_datetime()
        採番.更新利用者ID = 現在利用者.利用者ID
        採番.更新利用者名 = 現在利用者.利用者名
        採番.更新端末ID = "localhost"

        # requestに採番したIDをセット
        request.入庫伝票ID = 入庫伝票ID

    # 重複チェック
    existing = crud.get_T商品入庫(db, request.入庫伝票ID)
    if existing:
        return schemas.ResponseBase(status="NG", message="この入庫伝票IDは既に登録されています", error={"code": "DUPLICATE"})

    認証情報 = {"利用者ID": 現在利用者.利用者ID, "利用者名": 現在利用者.利用者名}
    item = crud.create_T商品入庫(db, request, 認証情報=認証情報)
    return schemas.ResponseBase(
        status="OK",
        message=f"商品入庫を作成しました（伝票ID: {request.入庫伝票ID}）",
        data=schemas.T商品入庫.from_orm(item)
    )

@router.post("/変更", response_model=schemas.ResponseBase)
def update_T商品入庫(
    request: schemas.T商品入庫Update,
    入庫伝票ID: str,
    db: Session = Depends(deps.get_db),
    現在利用者: models.C利用者 = Depends(deps.get_現在利用者)
):
    item = crud.get_T商品入庫(db, 入庫伝票ID)
    if not item:
        return schemas.ResponseBase(status="NG", message="指定された入庫伝票が見つかりません", error={"code": "NOT_FOUND"})

    認証情報 = {"利用者ID": 現在利用者.利用者ID, "利用者名": 現在利用者.利用者名}
    updated_item = crud.update_T商品入庫(db, 入庫伝票ID, request, 認証情報=認証情報)

    return schemas.ResponseBase(
        status="OK",
        message="商品入庫を更新しました",
        data=schemas.T商品入庫.from_orm(updated_item)
    )

@router.post("/削除", response_model=schemas.ResponseBase)
def delete_T商品入庫(
    request: schemas.T商品入庫Delete,
    db: Session = Depends(deps.get_db),
    現在利用者: models.C利用者 = Depends(deps.get_現在利用者)
):
    item = crud.get_T商品入庫(db, request.入庫伝票ID)
    if not item:
        return schemas.ResponseBase(status="NG", message="指定された入庫伝票が見つかりません", error={"code": "NOT_FOUND"})

    success = crud.delete_T商品入庫(db, request.入庫伝票ID)
    if not success:
        return schemas.ResponseBase(status="NG", message="商品入庫の削除に失敗しました", error={"code": "DELETE_FAILED"})

    return schemas.ResponseBase(
        status="OK",
        message="商品入庫を削除しました",
        data={"入庫伝票ID": request.入庫伝票ID}
    )

