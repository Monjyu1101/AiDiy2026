# Markdown現状追従チェック

## 参照する場面

`.md` 全体を現行実装へ追従させるときに参照する。

## 今回確認した主なズレ

- `docs/開発ガイド/**/code_samples` の M商品サンプルは現行実装から遅れやすい。
  - 同期元: `backend_server/apps_models/M商品.py`, `apps_schema/M商品.py`, `apps_crud/M商品.py`, `apps_router/M商品.py`, `apps_router/V商品.py`
  - 同期元: `frontend_web/src/components/Mマスタ/M商品/M商品一覧.vue`, `M商品編集.vue`, `components/M商品一覧テーブル.vue`
  - 現行サンプルは `商品分類ID`、`有効`、`件数制限`、`無効も表示`、`qBooleanCheckbox`、`ListRequest` を含む。
- `backend_mcp` は 6 ではなく 8 MCP サーバー構成。
  - 追加済み: `aidiy_backup_check`, `aidiy_backup_save`
  - 関連: `backend_mcp/mcp_main.py`, `backend_mcp/mcp_proc/backup_check.py`, `backend_mcp/mcp_proc/backup_save.py`
- M系マスタには `M取引先分類` / `M取引先` が存在する。
  - V系も `V取引先分類` / `V取引先` を持つ。
  - 機能一覧、router 一覧、初期データ一覧、frontend ルート一覧に反映が必要。
- 認証時間延長の現行ルールは以下。
  - 延長対象: C/M/T操作系API、S/V更新日監視、AI非音声入力、AIファイル `files_temp`
  - 延長対象外: メニュー遷移、X系、ログアウト、認証API、`input_audio`、`operations`、`cancel_run`、`cancel_audio`、`files_backup`、`files_save`、`file_select`、`file_deselect`
- `CHAT_AI_NAME` の OpenRouter 系キーは `openrt_chat`。`openai_chat` ではない。
- `frontend_avatar` は HTTP 認証Storageが Electron=`localStorage`、Web=`sessionStorage`。
- MCP 実装詳細は `backend_server/AGENTS.md` ではなく `backend_mcp/AGENTS.md` に分離済み。

## 最低限の確認方法

```powershell
$files = rg --files -g '*.md' -g '!**/node_modules/**' -g '!**/.venv/**' -g '!**/dist/**' -g '!**/backup/**'
rg -n '6 サーバー|6 MCP|6 SSE|2 つの MCP|MCP サーバーも同居|openai_chat' $files
rg -n 'aidiy_backup_check|aidiy_backup_save|M取引先|V取引先|トークン更新|files_temp' $files
rg -n 'includeInactive|無効も検索|router/index\.ts へのルート追加|商品コードが重複|get_商品_by_code|DELETE文でデータを完全に削除' docs
```

## 注意点

- サンプル設計書内の「JWT 60分」はバックエンドの有効期限として正しいため、認証延長を必ず併記する必要はない。
- `frontend_avatar/src/api/config.ts` の `defaultModelSettings()` は backend から設定取得前のフォールバック。実行時の正は backend の `/core/AIコア/モデル情報/取得` と `backend_server/_config/AiDiy_key.json`。
- `backend_server/_config/` 配下の設定ファイル内容は Git 同期対象外。キー名やファイル名など仕様説明に必要な範囲だけ記載し、実ファイル内容・値は docs/code_samples へもコピーしない。
