# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
# This software is licensed under the MIT License.
# https://github.com/monjyu1101
# Thank you for keeping the rules.
# ------------------------------------------------

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
import auth, database, models1 as models

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/core/auth/token")

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_現在利用者(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        利用者ID: str = payload.get("sub")
        if 利用者ID is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    利用者 = db.query(models.C利用者).filter(models.C利用者.利用者ID == 利用者ID).first()
    if 利用者 is None:
        raise credentials_exception
    return 利用者

