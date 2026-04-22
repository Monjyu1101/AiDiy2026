# M系マスタ追加チェック

## 参照する場面
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

## 実装の結論
- backend は Model / Schema / CRUD / Router / V系Router を揃え、`apps_main.py` へ import と `include_router` を追加する。
- 新テーブルは `apps_models/__init__.py`、`apps_schema/__init__.py`、`apps_crud/__init__.py` へ必ず登録する。特に `apps_crud/__init__.py` の import / `__all__` は漏れやすい。
- 初期データが必要な場合は `apps_crud/init.py` へ init 関数 import、テーブル作成、初期投入呼び出しを追加する。
- V系一覧で分類条件を使う場合は `apps_schema/common.py` の `ListRequest` に分類IDを追加し、frontend の一覧テーブル prop から `/apps/V.../一覧` へ渡す。
- frontend は一覧画面、編集画面、qTubler 一覧テーブル、型定義、ルート、メニューを一式で追加する。

## 再発しやすい注意点
- `Mマスタ.vue` と `メインメニュー.vue` の両方に導線を追加する。片方だけだと画面へ到達しづらい。
- 分類プルダウンを親画面に作っただけでは絞り込みは効かない。一覧テーブル側で prop を定義し、API payload へ分類IDを入れる。
- 既に同名テーブルがあるがカラムが古い場合は、`inspect(...).get_columns()` で必要カラムを確認する。開発用初期テーブルなら `DROP TABLE` → 再作成も選択肢だが、実データがある場合は `ALTER TABLE` を優先する。
- 画面のカード追加時は重複カードを残さない。既存の仮実装や過去追加分がないか `rg` で確認する。

## 最低限の確認方法
- backend: `python -m py_compile` で新規/更新 Python ファイルを確認する。
- backend: `python -c "import apps_main"` で router / schema / crud import の破綻を確認する。
- DB: SQLite で新テーブルの存在、件数、分類IDカラム、JOIN件数を確認する。
- frontend: `npm run type-check` を通す。
- 画面: 分類選択後に再検索し、V系一覧の絞り込みが効くことを確認する。
