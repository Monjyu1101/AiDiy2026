# M系マスタカラム追加手順

> 文書: `backend_server,M系マスタカラム追加手順.md` | 実装: `backend_server/apps_models/M商品.py`, `backend_server/apps_schema/M商品.py`, `backend_server/apps_crud/M商品.py`, `backend_server/apps_crud/init.py`

## このメモを使う場面

- 既存の M系マスタに新しいカラムを追加する（例: M商品に標準単価を追加）
- 既存DBのマイグレーション対応が必要なカラム追加
- Optional なカラムを追加する

## 関連ファイル

- `backend_server/apps_models/M<名称>.py` — SQLAlchemy Model
- `backend_server/apps_schema/M<名称>.py` — Pydantic Schema（Base / Create / Update）
- `backend_server/apps_crud/M<名称>.py` — CRUD 関数
- `backend_server/apps_crud/init.py` — 既存DBマイグレーション処理

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

### 4. init.py にマイグレーション処理を追加

```python
# apps_crud/init.py
for テーブル名 in ["M配車区分", "M生産区分", "M生産工程", "M商品分類", "M車両", "M商品", "M商品構成"]:
    if not inspector.has_table(テーブル名):
        continue
    columns = [col['name'] for col in inspector.get_columns(テーブル名)]
    if "有効" not in columns:
        db.execute(text(f'ALTER TABLE "{テーブル名}" ADD COLUMN "有効" INTEGER NOT NULL DEFAULT 1'))
    if テーブル名 == "M商品" and "商品分類ID" not in columns:
        db.execute(text('ALTER TABLE "M商品" ADD COLUMN "商品分類ID" TEXT NOT NULL DEFAULT ""'))
        db.execute(text('UPDATE "M商品" SET "商品分類ID" = substr("商品ID", 1, 1) WHERE "商品分類ID" = "" OR "商品分類ID" IS NULL'))
    if テーブル名 == "M商品" and "標準単価" not in columns:  # 追加
        db.execute(text('ALTER TABLE "M商品" ADD COLUMN "標準単価" REAL'))
db.commit()
```

- 既存DBでカラムが存在しない場合のみ `ALTER TABLE ADD COLUMN` を実行
- NULL許容カラムは `DEFAULT` 句不要
- NOT NULL カラムは `DEFAULT` 付きで追加し、必要なら既存行を `UPDATE`

## 型の対応表

| Python / Pydantic | SQLAlchemy | SQLite |
|-------------------|------------|--------|
| `float` | `Float` | `REAL` |
| `int` | `Integer` | `INTEGER` |
| `str` | `Text` | `TEXT` |
| `bool` | `Boolean` | `INTEGER` |
| `datetime` | `DateTime` | `TEXT` |

## 注意点

- **4箇所すべてを変更する**: Model / Schema(Base, Update) / CRUD / init.py のいずれかが漏れると動作しない
- **init.py のマイグレーションは `init_M<名称>_data()` より前に実行される**: カラムが存在しないと初期データ投入が失敗する
- **Update schema は Base を継承していない**: 個別に追加が必要
- **Router の変更は不要**: Schema 経由で自動的に API に反映される

## 確認方法

```powershell
cd backend_server
.venv\Scripts\python.exe -m py_compile apps_models\M商品.py apps_schema\M商品.py apps_crud\M商品.py apps_crud\init.py
.venv\Scripts\python.exe -c "import apps_main"
```

```powershell
sqlite3 backend_server/_data/AiDiy/database.db "PRAGMA table_info('M商品')"
```
