# Service層は AiDiy2026 では未実装です
#
# このプロジェクトでは、Service層を省略し、
# RouterからCRUDを直接呼び出す構成になっています。
#
# Service層相当の処理（ビジネスロジック、権限チェック等）は
# Router層に直接記述しています。
#
# 【参考】Service層を導入する場合の実装例
# ============================================================

"""
from sqlalchemy.orm import Session
from core_models import C利用者
import apps_crud.M商品


class M商品Service:
 def __init__(self, db: Session, 現在利用者: C利用者):
 self.db = db
 self.現在利用者 = 現在利用者

 def 登録(self, 商品データ: M商品Create):
 # 権限チェック
 if self.現在利用者.権限ID not in ['1', '2']:
 raise HTTPException(403, "登録権限がありません")

 # ビジネスロジック
 existing = apps_crud.M商品.get_商品_by_code(
 self.db, 商品データ.商品コード
 )
 if existing:
 raise HTTPException(400, "商品コードが重複しています")

 # CRUD呼び出し
 認証情報 = {"ログインID": self.現在利用者.ログインID}
 return apps_crud.M商品.create_商品(
 self.db, 商品データ, 認証情報
 )
"""

# ============================================================
# 現在のプロジェクトでは、上記のようなService層は未実装です。
# Router層で直接ビジネスロジックを実装しています。
# 詳細は apps_router/M商品.py を参照してください。
# ============================================================
