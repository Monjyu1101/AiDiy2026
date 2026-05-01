# スキーマ変更手順

> 文書: `backend_server,スキーマ変更手順.md` | 実装: `backend_server/apps_crud/init.py`, `backend_server/core_crud/init.py`

## このメモを使う場面
- SQLite の既存DBへカラム追加・削除・型変更を適用する
- 不要テーブルを削除する
- サーバー起動時に既存DBとのスキーマ差分を補正する

## 関連ファイル
- `backend_server/apps_crud/init.py`
- `backend_server/core_crud/init.py`
- `backend_server/apps_models/`
- `backend_server/core_models/`

## 実装手順

### 1. 差分を確認する

既存DBが残る運用では `create_all()` だけでは既存テーブルの列追加・PK変更・列削除は反映されない。変更前に `PRAGMA table_info()` または SQLAlchemy inspector で現行スキーマを確認する。

```python
result = db.execute(text('PRAGMA table_info("テーブル名")')).fetchall()
existing_columns = [row[1] for row in result]
```

```python
from sqlalchemy import inspect

inspector = inspect(db.bind)
if inspector.has_table("テーブル名"):
    columns = [column["name"] for column in inspector.get_columns("テーブル名")]
```

### 2. カラム追加

```python
def apply_schema_migrations(db: Session):
    result = db.execute(text('PRAGMA table_info("テーブル名")')).fetchall()
    existing = [row[1] for row in result]
    if "新カラム名" not in existing:
        db.execute(text('ALTER TABLE "テーブル名" ADD COLUMN "新カラム名" TEXT'))
        db.execute(text('UPDATE "テーブル名" SET "新カラム名" = :value WHERE "新カラム名" IS NULL'), {"value": "デフォルト値"})
        db.commit()
```

- NULL許容カラムは `ALTER TABLE ADD COLUMN` で追加する。
- NOT NULL相当のカラムは `DEFAULT` 付き追加、または追加直後の `UPDATE` で既存行を埋める。
- 日本語カラム名はダブルクォートで囲む。

### 3. カラム削除・型変更・PK変更

SQLite の `DROP COLUMN`、型変更、主キー変更は制約が多い。互換性を優先し、原則としてテーブル再作成方式にする。

1. 旧テーブルをリネームする。
2. Model 定義から新テーブルを作成する。
3. 必要な列だけを `INSERT INTO ... SELECT ...` で移行する。
4. 旧テーブルを削除する。
5. `db.commit()` する。

```python
db.execute(text('ALTER TABLE "テーブル名" RENAME TO "テーブル名_old"'))
models.M対象.__table__.create(bind=db.bind, checkfirst=True)
db.execute(text("""
    INSERT INTO "テーブル名" ("ID", "名称", "有効")
    SELECT "ID", "名称", 1
    FROM "テーブル名_old"
"""))
db.execute(text('DROP TABLE IF EXISTS "テーブル名_old"'))
db.commit()
```

開発用の空テーブルや再投入可能なサンプルデータなら `DROP TABLE` 後に `models.<Model>.__table__.create(bind=db.bind, checkfirst=True)` で再作成してよい。実データがある場合は、移行SQLを明示してから削除する。

### 4. テーブル削除

```python
db.execute(text('DROP TABLE IF EXISTS "旧テーブル名"'))
db.commit()
```

## 注意点

- `apply_schema_migrations()` は `init_db_data()` の前に呼ぶ。構造が揃っていないと初期データ投入が失敗する。
- `ALTER TABLE` / `DROP TABLE` / `CREATE TABLE` 後に続けて列確認する場合は、`inspector = inspect(db.bind)` を作り直す。
- 複合PKを追加する変更（例: `明細SEQ` 追加）は SQLite の `ALTER TABLE ADD PRIMARY KEY` では対応できない。旧テーブルをリネーム、新テーブルを Model から作成、必要なデータを INSERT、旧テーブルを DROP する。
- 互換救済コードは永続化しすぎない。既存ユーザーDBを壊さない範囲で削除可否を判断する。
- DBファイルの場所や初期化順は現行実装を確認してから作業する。

## 判断基準

| 変更内容 | 推奨対応 |
|---------|----------|
| NULL許容カラム追加 | `ALTER TABLE ADD COLUMN` |
| NOT NULLカラム追加 | `DEFAULT` 付きで追加し、必要なら既存行を `UPDATE` |
| 表示用/任意項目追加 | 起動時補正で追加してよい |
| PK構成変更 | テーブル再作成 |
| カラム名変更 | テーブル再作成、または新列追加＋データコピー＋旧列は互換残し |
| 不要テーブル削除 | `DROP TABLE IF EXISTS` |

## 確認方法

```powershell
sqlite3 backend_server/_data/AiDiy/database.db ".schema テーブル名"
```

```powershell
cd backend_server
.venv\Scripts\python.exe -m py_compile apps_crud\init.py
.venv\Scripts\python.exe -c "import apps_main"
```
