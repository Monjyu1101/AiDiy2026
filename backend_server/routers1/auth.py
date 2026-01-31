# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
# This software is licensed under the MIT License.
# https://github.com/monjyu1101
# Thank you for keeping the rules.
# ------------------------------------------------

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
import schemas, auth, crud1 as crud, deps
from models1 import C利用者

router = APIRouter(prefix="/core/auth", tags=["auth"])

def issue_token(利用者: C利用者):
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": 利用者.利用者ID}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/ログイン", response_model=schemas.ResponseBase)
def login(request: schemas.LoginRequest, db: Session = Depends(deps.get_db)):
    利用者 = crud.authenticate_C利用者(db, 利用者ID=request.利用者ID, パスワード=request.パスワード)
    if not 利用者:
        return schemas.ResponseBase(
            status="NG",
            message="利用者IDまたはパスワードが間違っています",
            data={"error": {"code": "AUTH_FAILED"}}
        )

    return schemas.ResponseBase(
        status="OK",
        message="ログインしました",
        data=issue_token(利用者)
    )

@router.post("/token", response_model=schemas.Token)
def token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(deps.get_db)):
    利用者 = crud.authenticate_C利用者(db, 利用者ID=form_data.username, パスワード=form_data.password)
    if not 利用者:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return issue_token(利用者)

@router.post("/ログアウト", response_model=schemas.ResponseBase)
def logout(現在利用者: C利用者 = Depends(deps.get_現在利用者)):
    # JWTはステートレスなのでサーバー側での無効化はブラックリスト等が必要だが
    # 今回はクライアント側でトークン破棄を想定し、レスポンスのみ返す
    return schemas.ResponseBase(
        status="OK",
        message="ログアウトしました"
    )

@router.post("/現在利用者", response_model=schemas.ResponseBase)
def read_現在利用者(現在利用者: C利用者 = Depends(deps.get_現在利用者)):
    return schemas.ResponseBase(
        status="OK",
        message="利用者情報を取得しました",
        data=schemas.C利用者.model_validate(現在利用者)
    )


