# M系マスタカラム追加手順

> 文書: `backend_server,M系マスタカラム追加手順.md` | 実装: `backend_server/apps_models/M商品.py`, `backend_server/apps_schema/M商品.py`, `backend_server/apps_crud/M商品.py`, `backend_server/apps_crud/init.py`

## このメモを使う場面

- 既存の M系マスタに新しいカラムを追加する（例: M商品に標準単価を追加）
- カラム追加後の新規 DB スキーマと初期データを確認する
- Optional なカラムを追加する

## 関連ファイル

- `backend_server/apps_models/M<名称>.py` — SQLAlchemy Model
- `backend_server/apps_schema/M<名称>.py` — Pydantic Schema（Base / Create / Update）
- `backend_server/apps_crud/M<名称>.py` — CRUD 関数
- `backend_server/apps_crud/init.py` — 新規 DB への初期データ投入

## 実装手順

### 1. Model にカラム定義を追加

```python
# apps_models/M商品.py
from sqlalchemy import Column, Boolean, Text, Float  # Float を追加
from database import Base

class M商品(Base):
    __tablename__ = "M商品"

    商品ID = Column(Text, primary_key=True)
    商品名 = Column(Text, nullable=False)
    単位 = Column(Text, nullable=False)
    商品分類ID = Column(Text, nullable=False)
    標準単価 = Column(Float)  # 追加（NULL許容）
    商品備考 = Column(Text)
    # ... 監査項目
```

- 型に応じた import を追加する（`Float`, `Integer`, `DateTime` など）
- Optional なカラムは `Column(型)` のみ、必須なら `nullable=False` を指定

### 2. Schema にフィールドを追加

```python
# apps_schema/M商品.py
from pydantic import BaseModel
from typing import Optional

class M商品Base(BaseModel):
    商品名: str
    単位: str
    商品分類ID: str
    標準単価: Optional[float] = None  # 追加
    商品備考: Optional[str] = None
    有効: bool = True

class M商品Update(BaseModel):
    商品ID: str
    商品名: Optional[str] = None
    単位: Optional[str] = None
    商品分類ID: Optional[str] = None
    標準単価: Optional[float] = None  # 追加
    商品備考: Optional[str] = None
    有効: Optional[bool] = None
```

- `Base` クラスに追加すると `Create` / `Response` にも継承される
- `Update` は個別定義のため手動で追加が必要

### 3. CRUD の create 関数を更新

```python
# apps_crud/M商品.py
def create_M商品(db: Session, 商品: schemas.M商品Create, 認証情報: Optional[Dict] = None):
    audit = create_audit_fields(認証情報)
    db_商品 = models.M商品(
        商品ID=商品.商品ID,
        商品名=商品.商品名,
        単位=商品.単位,
        商品分類ID=商品.商品分類ID,
        標準単価=商品.標準単価,  # 追加
        商品備考=商品.商品備考,
        有効=True,
        **audit
    )
    db.add(db_商品)
    db.commit()
    db.refresh(db_商品)
    return db_商品
```

### 4. 新規 DB の定義と初期データを確認

- `create_all()` は既存テーブルの列を更新しない。現行 Model から作成した一時 DB で、新しいカラムの型・NULL 許容・既定値を確認する。
- 初期データで新項目を使う場合は `init_M<名称>_data()` の投入値も調整する。
- `init.py` へ旧列検出や `ALTER TABLE` を追加しない。スキーマ変更後の利用は利用者による手動 DB 再作成を前提とする。
- 詳細は [`backend_server,スキーマ変更手順.md`](./backend_server,スキーマ変更手順.md) を参照する。

## 型の対応表

| Python / Pydantic | SQLAlchemy | SQLite |
|-------------------|------------|--------|
| `float` | `Float` | `REAL` |
| `int` | `Integer` | `INTEGER` |
| `str` | `Text` | `TEXT` |
| `bool` | `Boolean` | `INTEGER` |
| `datetime` | `DateTime` | `TEXT` |

## 注意点

- **関連レイヤーを揃える**: Model / Schema(Base, Update) / CRUD を変更し、必要なら初期データも更新する
- **旧 DB は自動変換しない**: カラム不足を旧スキーマへのフォールバックで隠さず、手動再作成が必要な定義差分として扱う
- **Update schema は Base を継承していない**: 個別に追加が必要
- **Router の変更は不要**: Schema 経由で自動的に API に反映される

## 確認方法

```powershell
cd backend_server
.venv\Scripts\python.exe -m py_compile apps_models\M商品.py apps_schema\M商品.py apps_crud\M商品.py apps_crud\init.py
```

DB 検証は `:memory:` または専用の一時ディレクトリへ接続先を固定し、現行 Model から作成した `M商品` の列定義と初期投入・CRUD を確認する。`apps_main` の import は実 DB を作成・接続するため、構文確認の代わりに実行しない。
