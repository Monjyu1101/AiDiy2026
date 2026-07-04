# M系マスタ追加手順

> 文書: `backend_server,M系マスタ追加手順.md` | 実装: `backend_server/apps_models/`, `backend_server/apps_schema/`, `backend_server/apps_crud/`, `backend_server/apps_router/`

## このメモを使う場面
- M商品分類 / M商品 と同じ型の M系マスタを追加する
- 分類マスタと本体マスタを対で追加する
- V系一覧で分類名などを JOIN 表示する

## 関連ファイル
- `backend_server/apps_models/`
- `backend_server/apps_schema/`
- `backend_server/apps_crud/`
- `backend_server/apps_router/`
- `backend_server/apps_main.py`
- `backend_server/apps_crud/init.py`

## 実装手順

### 1. Model

- `apps_models/M<名称>.py` に SQLAlchemy Model を作る。
- 共通の監査8項目と `有効` を含める。
- `apps_models/__init__.py` に import を追加する。ここが漏れると `create_all()` の対象にならない。
- `apps_main.py` の `create_all(tables=[...])` に新 Model の `.__table__` を追加する。

### 2. Schema

- `apps_schema/M<名称>.py` に Base / Create / Update / Get / Delete / Response 用 schema を作る。
- `apps_schema/__init__.py` に import を追加する。Router が `apps_schema as schemas` 経由で参照するため必須。

### 3. CRUD

- `apps_crud/M<名称>.py` に get / list / create / update / delete / init 関数を作る。
- `apps_crud/__init__.py` に import と `__all__` を追加する。Router が `apps_crud as crud` 経由で呼ぶ場合に必須。
- 登録時は `create_audit_fields()`、更新時は `update_audit_fields()` を使う。
- 削除は既存パターンに合わせ、論理削除なら `有効=False` にする。

### 4. Router

- `apps_router/M<名称>.py` に `/一覧` `/取得` `/登録` `/変更` `/削除` を POST で作る。
- `apps_router/V<名称>.py` に一覧表示用 JOIN を作る。呼び出し側の一覧取得は原則 V 系を使う。
- `apps_main.py` に `from apps_router import M<名称>` / `V<名称>` と `app.include_router(...)` を追加する。

### 5. 初期データ

- 初期データが必要な場合は `apps_crud/init.py` へ init 関数 import、テーブル作成、初期投入呼び出しを追加する。
- 初期データ関数は、既存データが1件でもあれば `return` する形を基本にする。起動のたびに upsert して監査項目を更新しない。
- 新規テーブルは `create_all()` で作成する。既存DB移行が不要な場合、個別の `DROP TABLE` / `ALTER TABLE` / 手動 `__table__.create()` を入れない。

## 一覧件数と有効フラグ

- V系一覧は `request: Optional[schemas.ListRequest] = None` を受け取り、`list_controls.py` の `append_active_condition()` / `get_limit_clause()` を使う。
- `無効も表示=False` の既定動作では `有効=1` のみ返す。
- `件数制限=True` の既定動作では LIMIT 1000。V系で手書きの固定 LIMIT を入れず、`get_limit_clause()` の返り値を使う。
- 分類条件を使う場合は `apps_schema/common.py` の `ListRequest` に分類IDを追加し、V系 Router で params と WHERE 条件に反映する。

## 注意点

- `apps_crud/__init__.py` の import / `__all__` は漏れやすい。
- 既に同名テーブルがあるがカラムが古い場合は、`inspect(...).get_columns()` で必要カラムを確認する。開発用初期テーブルなら `DROP TABLE` → 再作成も選択肢だが、実データがある場合は `ALTER TABLE` を優先する。
- ユーザーが「マイグレーション不要」とした追加テーブルでは、旧スキーマ救済コードを残さない。`create_all()` と空テーブル時の seed だけにする。
- 呼び出し側が V系一覧を使う前提の場合、M系 Router だけでは一覧取得が動かない。

## 確認方法

```powershell
cd backend_server
.venv\Scripts\python.exe -m py_compile apps_models\M<名称>.py apps_schema\M<名称>.py apps_crud\M<名称>.py apps_router\M<名称>.py apps_router\V<名称>.py
.venv\Scripts\python.exe -c "import apps_main"
```

- SQLite で新テーブルの存在、件数、必要カラムを確認する。
- Swagger `http://localhost:9098/docs` で M系 / V系エンドポイントを確認する。
- V系一覧で有効フィルター、件数制限、分類条件が効くことを確認する。
