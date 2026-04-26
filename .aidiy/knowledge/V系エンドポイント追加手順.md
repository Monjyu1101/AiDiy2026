# V系エンドポイント追加手順

## このメモを使う場面
- M系テーブルや T系テーブルを JOIN して一覧表示するエンドポイントを追加したい
- DB VIEW を使わずに生 SQL で JOIN 集計をしたい

## 関連ファイル
- `backend_server/apps_router/V*.py` — V系ルーター群（既存を参照して作る）
- `backend_server/apps_main.py` — Router 登録
- `backend_server/apps_crud/__init__.py` — 必要なら CRUD 関数を登録

## 実装手順

### V系エンドポイントの基本構造

V系はすべて **POST メソッド**。DB VIEW オブジェクトは使わず、生 SQL（`text()`）で実装する。

```python
# backend_server/apps_router/V商品一覧.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
import apps_schema as schemas, deps, apps_models as models
from list_controls import append_active_condition, get_limit_clause

router = APIRouter(prefix="/apps/V商品一覧", tags=["V商品一覧"])

@router.post("/一覧", response_model=schemas.ResponseBase)
def 商品一覧(request: Optional[schemas.ListRequest] = None,
             db: Session = Depends(deps.get_db),
             現在利用者: models.C利用者 = Depends(deps.get_現在利用者)):
    sql = text("""
        SELECT
            m.商品ID,
            m.商品名,
            c.分類名
        FROM M商品 m
        LEFT JOIN M商品分類 c ON m.分類ID = c.分類ID
        WHERE 1=1
        -- 条件を動的に追加する場合は params dict を使う
    """)
    rows = db.execute(sql).fetchall()
    items = [dict(row._mapping) for row in rows]
    return {"status": "OK", "data": {"items": items, "total": len(items)}}
```

### 動的条件の追加

```python
conditions = ["1=1"]
params = {}
if request.商品名:
    conditions.append("m.商品名 LIKE :商品名")
    params["商品名"] = f"%{request.商品名}%"

sql = text(f"SELECT ... FROM M商品 m WHERE {' AND '.join(conditions)}")
rows = db.execute(sql, params).fetchall()
```

### 件数制限・有効フィルターの標準形

V系の一覧は `list_controls.py` を使う。`request=None` でも既定で「件数制限あり・有効のみ」になる。

`list_controls.py` の場所: `backend_server/list_controls.py`（`apps_crud/` 配下ではなく `backend_server/` 直下）

```python
# backend_server/ を cwd にして uvicorn を起動するため、パスプレフィックスなしで import できる
from list_controls import append_active_condition, get_limit_clause

conditions = []
append_active_condition(conditions, request, "M.有効")
limit_sql, limit_value = get_limit_clause(request)
params = {}
if limit_value is not None:
    params["limit"] = limit_value

where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""
sql = f"""
SELECT ...
FROM M商品 M
{where_sql}
ORDER BY M.商品ID
{limit_sql}
"""
rows = db.execute(text(sql), params).fetchall()
total = db.execute(text(f"SELECT count(*) FROM M商品 M {where_sql}"), params).scalar()
```

`conditions` を後から追加した場合は `where_sql` を作り直す。`V商品.py` の分類絞り込みが参考になる。

### 最終更新日時エンドポイント（監視用）

フロントが変更を検知するために使う軽量エンドポイント。

```python
@router.post("/apps/V商品一覧/最終更新日時")
def 最終更新日時(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    row = db.execute(text("SELECT MAX(更新日時) as 最終更新日時 FROM M商品")).fetchone()
    return {"status": "OK", "data": {"最終更新日時": row[0]}}
```

### apps_main.py への登録

```python
from apps_router import V商品一覧
app.include_router(V商品一覧.router)
```

## list_controls の関数シグネチャ

```python
# backend_server/list_controls.py
LIMITED_MAX_ITEMS = 1000

def get_limit_clause(request) -> tuple[str, Optional[int]]:
    # → ("LIMIT :limit", 1000)  または ("", None)（件数制限なし時）

def append_active_condition(conditions: list[str], request, column_name: str) -> None:
    # request.無効も表示=False（既定）なら conditions に "{column_name} = 1" を追加

def apply_active_filter(query, model, request):
    # ORM クエリ用。生SQLなら append_active_condition を使う
```

`request` が `None` のときは `getattr(request, "件数制限", None)` → `None` → `True`（制限あり）、`getattr(request, "無効も表示", None)` → `None` → `False`（有効のみ）として動くため、`request=None` でも安全に使える。

## 注意点

- M系テーブルを追加したときは V系エンドポイントも**必ず**作成する（フロントの一覧画面は V系を使うため、M系エンドポイントだけでは画面が動かない）
- `dict(row._mapping)` で行を辞書化すること（`row._asdict()` は非推奨）
- 生 SQL のカラム名は DB のカラム名と完全一致が必要（日本語カラム名もそのまま使う）
- LIMIT は `get_limit_clause()` を使い、値は `params["limit"]` に渡す（SQL インジェクション防止）
- f-string は固定SQL断片（`where_sql` / `limit_sql` など）の組み立てに限定し、ユーザー入力値は直接埋め込まない
- テーブル名・カラム名のような識別子は bind parameter にできない。動的にする必要がある場合は、許可リストで選んだ固定文字列だけを SQL に埋め込む。
- `WHERE` 条件の値は必ず `params` に入れる。ユーザー入力を f-string で直接結合しない。
- 集計系 V（例: 商品推移表）は必ずしも生SQLだけに寄せなくてよい。期間前在庫や同日イベント優先度など、SQLだけだと読みにくい業務計算は Python 側で整形してよい。
- 最終更新日時は、一覧の元になる全テーブルの `MAX(更新日時)` を考慮する。JOIN先マスタ名だけが変わる機能なら、マスタ側更新も監視対象に含めるかを判断する。

## 確認方法

FastAPI Swagger UI `http://localhost:8092/docs` でエンドポイントを実行して確認。
