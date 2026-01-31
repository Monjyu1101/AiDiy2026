# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
# This software is licensed under the MIT License.
# https://github.com/monjyu1101
# Thank you for keeping the rules.
# ------------------------------------------------

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import schemas, crud2 as crud, deps, models2 as models
MAX_ITEMS = 10000

router = APIRouter(prefix="/apps/M車両", tags=["M車両"])

@router.post("/一覧", response_model=schemas.ResponseBase)
def list_M車両(
    db: Session = Depends(deps.get_db),
    現在利用者: models.C利用者 = Depends(deps.get_現在利用者)
):
    query = db.query(models.M車両)
    total = query.count()
    items = query.order_by(models.M車両.車両ID).limit(MAX_ITEMS).all()

    return schemas.ResponseBase(
        status="OK",
        message="車両一覧を取得しました",
        data={
            "items": [schemas.M車両.from_orm(item) for item in items],
            "total": total,
            "limit": MAX_ITEMS
        }
    )

@router.post("/取得", response_model=schemas.ResponseBase)
def get_M車両(
    request: schemas.M車両Get,
    db: Session = Depends(deps.get_db),
    現在利用者: models.C利用者 = Depends(deps.get_現在利用者)
):
    item = crud.get_M車両(db, request.車両ID)
    if not item:
        return schemas.ResponseBase(status="NG", message="指定された車両が見つかりません", error={"code": "NOT_FOUND"})

    return schemas.ResponseBase(
        status="OK",
        message="車両情報を取得しました",
        data=schemas.M車両.from_orm(item)
    )

@router.post("/登録", response_model=schemas.ResponseBase)
def create_M車両(
    request: schemas.M車両Create,
    db: Session = Depends(deps.get_db),
    現在利用者: models.C利用者 = Depends(deps.get_現在利用者)
):
    existing = crud.get_M車両(db, request.車両ID)
    if existing:
        return schemas.ResponseBase(status="NG", message="この車両IDは既に登録されています", error={"code": "DUPLICATE"})

    認証情報 = {"利用者ID": 現在利用者.利用者ID, "利用者名": 現在利用者.利用者名}
    item = crud.create_M車両(db, request, 認証情報=認証情報)
    return schemas.ResponseBase(
        status="OK",
        message="車両を作成しました",
        data=schemas.M車両.from_orm(item)
    )

@router.post("/変更", response_model=schemas.ResponseBase)
def update_M車両(
    request: schemas.M車両Update,
    db: Session = Depends(deps.get_db),
    現在利用者: models.C利用者 = Depends(deps.get_現在利用者)
):
    item = crud.get_M車両(db, request.車両ID)
    if not item:
        return schemas.ResponseBase(status="NG", message="指定された車両が見つかりません", error={"code": "NOT_FOUND"})

    認証情報 = {"利用者ID": 現在利用者.利用者ID, "利用者名": 現在利用者.利用者名}
    更新項目 = crud.create_audit_fields(認証情報, is_update=True)

    if request.車両名 is not None:
        item.車両名 = request.車両名
    if request.車両備考 is not None:
        item.車両備考 = request.車両備考

    for key, value in 更新項目.items():
        setattr(item, key, value)

    db.commit()
    db.refresh(item)

    return schemas.ResponseBase(
        status="OK",
        message="車両を更新しました",
        data=schemas.M車両.from_orm(item)
    )

@router.post("/削除", response_model=schemas.ResponseBase)
def delete_M車両(
    request: schemas.M車両Delete,
    db: Session = Depends(deps.get_db),
    現在利用者: models.C利用者 = Depends(deps.get_現在利用者)
):
    item = crud.get_M車両(db, request.車両ID)
    if not item:
        return schemas.ResponseBase(status="NG", message="指定された車両が見つかりません", error={"code": "NOT_FOUND"})

    db.delete(item)
    db.commit()

    return schemas.ResponseBase(
        status="OK",
        message="車両を削除しました",
        data={"車両ID": request.車両ID}
    )


