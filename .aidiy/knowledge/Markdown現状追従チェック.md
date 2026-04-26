# Markdown現状追従チェック

## 参照する場面

`.md` 全体を現行実装へ追従させるときに参照する。

## 優先する同期元

1. 実装ファイルを最優先する。
   - 認証: `backend_server/auth.py`, `backend_server/core_router/auth.py`, `frontend_web/src/api/client.ts`, `frontend_web/src/stores/auth.ts`, `frontend_avatar/src/api/client.ts`
   - MCP: `backend_mcp/mcp_main.py`, `backend_mcp/mcp_stdio.py`, `backend_mcp/mcp_proc/`
   - 起動・環境: `_setup.py`, `_start.py`, `CLAUDE.md`, 各 `AGENTS.md`
2. 次に AGENTS/CLAUDE の方針を確認する。
   - 全体方針は `AGENTS.md`
   - MCP 詳細は `backend_mcp/AGENTS.md`
   - クイックコマンドと注意点は `CLAUDE.md`
3. `docs/開発ガイド/` はHTML資料として確認する。
   - `.md` ではなく `.html` が主なので、検索は `rg -n '<語句>' docs/開発ガイド -g '*.html'` を使う。
   - docs と実装が食い違う場合は、実装を確認したうえで「現行実装では」と明記する。

## 追従チェックで見つかりやすいズレ

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
- `frontend_web` の認証Storageは `localStorage`。`frontend_avatar` は HTTP 認証Storageが Electron=`localStorage`、Web=`sessionStorage`。
- MCP 実装詳細は `backend_server/AGENTS.md` ではなく `backend_mcp/AGENTS.md` に分離済み。
- `_start.py` は対話形式で、`--reload` は付かない。コード変更反映は個別起動または `temp/reboot_*.txt` を使う。
- Docker 構成は `backend_mcp` を含まない。MCP 検証手順ではローカル起動を前提にする。
- `npm run build` は明示依頼時のみ。通常の検証記述は `npm run type-check` を優先する。

## X系 / Avatar 表示まわりの確認観点

- X系ゲーム一覧: `X立体リバーシ`（Three.js 6面立体）と `Xハローワールド`（Leaflet + OSM 絶景巡回）が追加済み。
  - 関連: `frontend_web/src/components/Xその他/X立体リバーシ.vue`, `Xハローワールド.vue`
  - 関連: `frontend_web/public/X立体リバーシ/`, `frontend_web/public/Xハローワールド/`
- `frontend_avatar` の表示コンポーネント: `AIコア_xneko.vue`（旧 AIコア_ネコ.vue）/ `AIコア_xeyes.vue` / `AIコア_アナログ時計.vue` / `AIコア_デジタル時計.vue` / `AIコア_カレンダー.vue` が追加済み。
- `AIコア.vue` の `アバター表示` チェックボックスは廃止。`表示選択` select（`アバター` / `xneko(猫)` / `xeyes(目)` / `アナログ時計` / `デジタル時計` / `カレンダー` / `無し`）に変更済み。
- Electron IPC: `window:get-pointer-snapshot` と `system:get-cpu-usage` が追加済み（xeyes 用）。

## 最低限の確認方法

```powershell
$files = rg --files -g '*.md' -g '!**/node_modules/**' -g '!**/.venv/**' -g '!**/dist/**' -g '!**/backup/**'
rg -n '6 サーバー|6 MCP|6 SSE|2 つの MCP|MCP サーバーも同居|openai_chat' $files
rg -n 'aidiy_backup_check|aidiy_backup_save|M取引先|V取引先|トークン更新|files_temp|reboot_mcp' $files
rg -n 'includeInactive|無効も検索|router/index\.ts へのルート追加|商品コードが重複|get_商品_by_code|DELETE文でデータを完全に削除' docs
rg -n 'start\.py|_stop\.py|8095.*Docker|npm run build' $files
```

## Markdown 一斉更新後の横断チェック

`.aidiy/knowledge` 配下の Markdown をまとめて更新した後は、内容の新旧だけでなくリンク・文字コード・未整理表現を確認する。

```powershell
$knowledgeFiles = rg --files .aidiy/knowledge -g '*.md'

# ローカル Markdown リンク切れ確認（http/https とアンカーのみのリンクは除外）
$root = Resolve-Path .
$missingLinks = foreach ($file in $knowledgeFiles) {
  $dir = Split-Path $file
  Select-String -Path $file -Pattern '\]\(([^)]+)\)' -AllMatches | ForEach-Object {
    foreach ($match in $_.Matches) {
      $link = $match.Groups[1].Value -replace '#.*$', ''
      if ($link -and $link -notmatch '^(https?://|#)') {
        $target = Join-Path $dir $link
        if (-not (Test-Path $target)) { "${file}:$($_.LineNumber) -> $link" }
      }
    }
  }
}
$missingLinks

# BOM 混入確認（結果が空なら OK）
foreach ($file in $knowledgeFiles) {
  $bytes = [System.IO.File]::ReadAllBytes((Resolve-Path $file))
  if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) { $file }
}

# 未整理・古い表現の残存確認
rg -n '準備中|追加チェック|追加パターン|構成整理|^## 場面' $knowledgeFiles
```

- リンク切れは相対パスの移動・ファイル名変更後に発生しやすい。ファイル名規則に合わせてリンク先を直す。
- BOM が見つかった場合は [`UTF8BOM問題対処.md`](./UTF8BOM問題対処.md) の手順で除去する。
- `準備中`、`追加チェック`、`追加パターン`、`構成整理`、`## 場面` は作業途中の見出しや旧テンプレート由来の可能性が高い。残す場合も、再利用できる具体的な観点へ言い換える。

## 注意点

- サンプル設計書内の「JWT 60分」はバックエンドの有効期限として正しいため、認証延長を必ず併記する必要はない。
- `frontend_avatar/src/api/config.ts` の `defaultModelSettings()` は backend から設定取得前のフォールバック。実行時の正は backend の `/core/AIコア/モデル情報/取得` と `backend_server/_config/AiDiy_key.json`。
- `backend_server/_config/` 配下の設定ファイル内容は Git 同期対象外。キー名やファイル名など仕様説明に必要な範囲だけ記載し、実ファイル内容・値は docs/code_samples へもコピーしない。
- Markdown のリンクは、`.aidiy/knowledge` 内では同階層ファイルへの相対リンクかコード表記のパスにする。docs のHTMLへ深いリンクを張る場合は、実在確認できない限りコード表記に留める。
