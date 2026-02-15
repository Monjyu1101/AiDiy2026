# backend_server/apps_crud/M商品.py

from sqlalchemy.orm import Session
from typing import Optional, Dict
import apps_models as models, apps_schema as schemas
from apps_crud.utils import create_audit_fields


def get_M商品(db: Session, 商品ID: str):
 """商品IDで商品を取得"""
 return db.query(models.M商品).filter(models.M商品.商品ID == 商品ID).first()


def get_M商品一覧(db: Session):
 """全商品を取得"""
 return db.query(models.M商品).order_by(models.M商品.商品ID).all()


def create_M商品(db: Session, 商品: schemas.M商品Create, 認証情報: Optional[Dict] = None):
 """商品を作成"""
 audit = create_audit_fields(認証情報)

 db_商品 = models.M商品(
 商品ID=商品.商品ID,
 商品名=商品.商品名,
 単位=商品.単位,
 商品備考=商品.商品備考,
 **audit
 )
 db.add(db_商品)
 db.commit()
 db.refresh(db_商品)
 return db_商品


# ============================================================
# 監査フィールドユーティリティ（apps_crud/utils.py）
# ============================================================
# def create_audit_fields(認証情報: Optional[Dict] = None, is_update: bool = False) -> Dict:
# """登録/更新項目を作成"""
# now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
# 利用者ID = 認証情報.get('利用者ID', 'system') if 認証情報 else 'system'
# 利用者名 = 認証情報.get('利用者名', 'system') if 認証情報 else 'system'
# 端末ID = 'localhost'
#
# if is_update:
# # 更新時は更新項目のみ
# return {
# '更新日時': now,
# '更新利用者ID': 利用者ID,
# '更新利用者名': 利用者名,
# '更新端末ID': 端末ID
# }
# else:
# # 登録時は登録・更新項目両方
# return {
# '登録日時': now,
# '登録利用者ID': 利用者ID,
# '登録利用者名': 利用者名,
# '登録端末ID': 端末ID,
# '更新日時': now,
# '更新利用者ID': 利用者ID,
# '更新利用者名': 利用者名,
# '更新端末ID': 端末ID
# }
