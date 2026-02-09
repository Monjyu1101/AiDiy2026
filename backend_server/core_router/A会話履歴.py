# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
# This software is licensed under the MIT License.
# https://github.com/monjyu1101
# Thank you for keeping the rules.
# ------------------------------------------------

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
import core_schema as schemas, core_crud as crud, deps, core_models as models
MAX_ITEMS = 10000

router = APIRouter(prefix="/core/A会話履歴", tags=["A会話履歴"])


@router.post("/一覧", response_model=schemas.ResponseBase)
def list_A会話履歴(
    request: Optional[schemas.A会話履歴ListRequest] = None,
    db: Session = Depends(deps.get_db),
    現在利用者: models.C利用者 = Depends(deps.get_現在利用者)
):
    query = db.query(models.A会話履歴)

    if request and request.セッションID:
        query = query.filter(models.A会話履歴.セッションID == request.セッションID)
    if request and request.チャンネル is not None:
        query = query.filter(models.A会話履歴.チャンネル == request.チャンネル)

    total = query.count()

    limit = MAX_ITEMS
    if request and request.件数:
        limit = min(request.件数, MAX_ITEMS) if request.件数 > 0 else MAX_ITEMS

    items = query.order_by(
        models.A会話履歴.セッションID,
        models.A会話履歴.シーケンス.desc()
    ).limit(limit).all()

    return schemas.ResponseBase(
        status="OK",
        message="会話履歴一覧を取得しました",
        data={
            "items": [schemas.A会話履歴Response.from_orm(item) for item in items],
            "total": total,
            "limit": limit
        }
    )


@router.post("/取得", response_model=schemas.ResponseBase)
def get_A会話履歴(
    request: schemas.A会話履歴Get,
    db: Session = Depends(deps.get_db),
    現在利用者: models.C利用者 = Depends(deps.get_現在利用者)
):
    item = crud.get_会話履歴(db, request.セッションID, request.シーケンス)
    if not item:
        return schemas.ResponseBase(status="NG", message="指定された会話履歴が見つかりません", error={"code": "NOT_FOUND"})

    return schemas.ResponseBase(
        status="OK",
        message="会話履歴を取得しました",
        data=schemas.A会話履歴Response.from_orm(item)
    )


@router.post("/登録", response_model=schemas.ResponseBase)
def create_A会話履歴(
    request: schemas.A会話履歴Create,
    db: Session = Depends(deps.get_db),
    現在利用者: models.C利用者 = Depends(deps.get_現在利用者)
):
    existing = crud.get_会話履歴(db, request.セッションID, request.シーケンス)
    if existing:
        return schemas.ResponseBase(status="NG", message="この会話履歴は既に登録されています", error={"code": "DUPLICATE"})

    認証情報 = {"利用者ID": 現在利用者.利用者ID, "利用者名": 現在利用者.利用者名}
    item = crud.create_会話履歴(
        db,
        セッションID=request.セッションID,
        シーケンス=request.シーケンス,
        チャンネル=request.チャンネル,
        メッセージ識別=request.メッセージ識別,
        メッセージ内容=request.メッセージ内容,
        ファイル名=request.ファイル名,
        サムネイル画像=request.サムネイル画像,
        認証情報=認証情報
    )

    return schemas.ResponseBase(
        status="OK",
        message="会話履歴を作成しました",
        data=schemas.A会話履歴Response.from_orm(item)
    )


@router.post("/変更", response_model=schemas.ResponseBase)
def update_A会話履歴(
    request: schemas.A会話履歴Update,
    db: Session = Depends(deps.get_db),
    現在利用者: models.C利用者 = Depends(deps.get_現在利用者)
):
    認証情報 = {"利用者ID": 現在利用者.利用者ID, "利用者名": 現在利用者.利用者名}
    item = crud.update_会話履歴(
        db,
        セッションID=request.セッションID,
        シーケンス=request.シーケンス,
        メッセージ内容=request.メッセージ内容,
        ファイル名=request.ファイル名,
        サムネイル画像=request.サムネイル画像,
        認証情報=認証情報
    )

    if not item:
        return schemas.ResponseBase(status="NG", message="指定された会話履歴が見つかりません", error={"code": "NOT_FOUND"})

    return schemas.ResponseBase(
        status="OK",
        message="会話履歴を更新しました",
        data=schemas.A会話履歴Response.from_orm(item)
    )


@router.post("/削除", response_model=schemas.ResponseBase)
def delete_A会話履歴(
    request: schemas.A会話履歴Delete,
    db: Session = Depends(deps.get_db),
    現在利用者: models.C利用者 = Depends(deps.get_現在利用者)
):
    success = crud.delete_会話履歴(db, request.セッションID, request.シーケンス)
    if not success:
        return schemas.ResponseBase(status="NG", message="削除対象が見つかりません", error={"code": "NOT_FOUND"})

    return schemas.ResponseBase(
        status="OK",
        message="会話履歴を削除しました",
        data={"セッションID": request.セッションID, "シーケンス": request.シーケンス}
    )

