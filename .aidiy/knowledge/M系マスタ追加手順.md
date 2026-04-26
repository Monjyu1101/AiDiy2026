# M系マスタ追加手順

## このメモを使う場面
M商品分類 / M商品 と同じ型の M系マスタを追加するときに参照する。
分類マスタと本体マスタを対で追加し、V系一覧で分類名をJOIN表示するケースを想定する。

## 関連ファイル
- `backend_server/apps_models/`
- `backend_server/apps_schema/`
- `backend_server/apps_crud/`
- `backend_server/apps_router/`
- `backend_server/apps_main.py`
- `backend_server/apps_crud/init.py`
- `frontend_web/src/types/entities.ts`
- `frontend_web/src/types/api.ts`
- `frontend_web/src/router/appsRouter.ts`
- `frontend_web/src/components/メインメニュー.vue`
- `frontend_web/src/components/Mマスタ.vue`
- `frontend_web/src/components/Mマスタ/<機能名>/`

## 実装手順
- backend は Model / Schema / CRUD / Router / V系Router を揃え、`apps_main.py` へ import と `include_router` を追加する。
- 新テーブルは `apps_models/__init__.py`、`apps_schema/__init__.py`、`apps_crud/__init__.py` へ必ず登録する。特に `apps_crud/__init__.py` の import / `__all__` は漏れやすい。
- 初期データが必要な場合は `apps_crud/init.py` へ init 関数 import、テーブル作成、初期投入呼び出しを追加する。
- 追加直後の新規 M系マスタは `apps_main.py` の `create_all()` で作成する。既存DB移行が不要な場合、`apps_crud/init.py` に個別の `DROP TABLE` / `ALTER TABLE` / 手動 `__table__.create()` を入れない。
- 初期データ関数は、既存データが1件でもあれば即 `return` する。起動のたびに upsert して監査項目を更新しない。
- V系一覧で分類条件を使う場合は `apps_schema/common.py` の `ListRequest` に分類IDを追加し、frontend の一覧テーブル prop から `/apps/V.../一覧` へ渡す。
- frontend は一覧画面、編集画面、qTubler 一覧テーブル、型定義、ルート、メニューを一式で追加する。

## Backend 登録チェックリスト

- `apps_models/M<名称>.py` に Model を作る。全テーブル共通の監査8項目と `有効` を含める。
- `apps_models/__init__.py` に import を追加する。ここが漏れると `create_all()` の対象にならない。
- `apps_schema/M<名称>.py` に Base / Create / Update / Get / Delete / Response 用 schema を作る。
- `apps_schema/__init__.py` に import を追加する。Router が `apps_schema as schemas` 経由で参照するため必須。
- `apps_crud/M<名称>.py` に get / list / create / update / delete / init 関数を作る。
- `apps_crud/__init__.py` に import と `__all__` を追加する。Router が `apps_crud as crud` 経由で呼ぶ場合に必須。
- `apps_router/M<名称>.py` に `/一覧` `/取得` `/登録` `/変更` `/削除` を POST で作る。
- `apps_router/V<名称>.py` に一覧表示用 JOIN を作る。画面一覧は原則 V 系を使う。
- `apps_main.py` に `from apps_router import M<名称>` / `V<名称>` と `app.include_router(...)` を追加する。
- `apps_main.py` の `create_all(tables=[...])` に新 Model の `.__table__` を追加する。

## 一覧件数と有効フラグ

- M系の直接 `/apps/M.../一覧` は既存パターンに合わせて固定上限でよい。
- V系一覧は `request: Optional[schemas.ListRequest] = None` を受け取り、`list_controls.py` の `append_active_condition()` / `get_limit_clause()` を使う。
- `無効も表示=False` の既定動作では `有効=1` のみ返す。新規 V 系でこの条件が抜けると、削除済みデータが一覧に出る。
- `件数制限=True` の既定動作では LIMIT 1000。V系で手書きの固定 LIMIT を入れず、`get_limit_clause()` の返り値を使う。

## 注意点
- `Mマスタ.vue` と `メインメニュー.vue` の両方に導線を追加する。片方だけだと画面へ到達しづらい。
- 分類プルダウンを親画面に作っただけでは絞り込みは効かない。一覧テーブル側で prop を定義し、API payload へ分類IDを入れる。
- 既に同名テーブルがあるがカラムが古い場合は、`inspect(...).get_columns()` で必要カラムを確認する。開発用初期テーブルなら `DROP TABLE` → 再作成も選択肢だが、実データがある場合は `ALTER TABLE` を優先する。
- ユーザーが「マイグレーション不要」とした追加テーブルでは、旧スキーマ救済コードを残さない。`create_all()` と空テーブル時の seed だけにする。
- 画面のカード追加時は重複カードを残さない。既存の仮実装や過去追加分がないか `rg` で確認する。

## 最低限の確認方法
- backend: `python -m py_compile` で新規/更新 Python ファイルを確認する。
- backend: `python -c "import apps_main"` で router / schema / crud import の破綻を確認する。
- DB: SQLite で新テーブルの存在、件数、分類IDカラム、JOIN件数を確認する。
- frontend: `npm run type-check` を通す。
- 画面: 分類選択後に再検索し、V系一覧の絞り込みが効くことを確認する。
