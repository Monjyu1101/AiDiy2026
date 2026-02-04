from sqlalchemy.orm import Session
from typing import Optional, Dict
import models, apps_schema as schemas
from crud.utils import create_audit_fields

def get_M配車区分(db: Session, 配車区分ID: str):
    """配車区分IDで配車区分を取得"""
    return db.query(models.M配車区分).filter(models.M配車区分.配車区分ID == 配車区分ID).first()

def get_M配車区分一覧(db: Session):
    """全配車区分を取得"""
    return db.query(models.M配車区分).order_by(models.M配車区分.配車区分ID).all()

def create_M配車区分(db: Session, 配車区分: schemas.M配車区分Create, 認証情報: Optional[Dict] = None):
    """配車区分を作成"""
    audit = create_audit_fields(認証情報)

    db_配車区分 = models.M配車区分(
        配車区分ID=配車区分.配車区分ID,
        配車区分名=配車区分.配車区分名,
        配車区分備考=配車区分.配車区分備考,
        配色枠=配車区分.配色枠,
        配色背景=配車区分.配色背景,
        配色前景=配車区分.配色前景,
        **audit
    )
    db.add(db_配車区分)
    db.commit()
    db.refresh(db_配車区分)
    return db_配車区分

