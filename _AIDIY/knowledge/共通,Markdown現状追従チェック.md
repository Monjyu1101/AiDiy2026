# Markdown 現状追従チェック

> 文書: `共通,Markdown現状追従チェック.md` | 実装: `_AIDIY/knowledge/`, `docs/`

## このメモを使う場面
- `.md` を現行実装へまとめて追従させる
- docs と実装の食い違いを確認する
- `_AIDIY/knowledge` の整理後にリンク、BOM、旧表現を確認する

## 優先する同期元

1. 実装ファイルを最優先する。
   - 認証: `backend_server/auth.py`, `backend_server/core_router/auth.py`, `frontend_web/src/api/client.ts`, `frontend_web/src/stores/auth.ts`, `frontend_avatar/src/api/client.ts`
   - Hermes: `command_hermes/cli_main.py`, `backend_server/AIコア/AIコード_cli.py`, `backend_server/conf/conf_model.py`, `backend_server/conf/conf_json.py`
   - MCP: `backend_tools/tools_main.py`, `backend_tools/mcp_stdio.py`, `backend_tools/tools_proc/`
   - Task / Team: `backend_taskteam/taskteam_main.py`, `backend_taskteam/taskteam_proc/app.py`, `backend_taskteam/_start.py`
   - 起動・環境: `_setup.py`, `_start.py`, `CLAUDE.md`, 各 `AGENTS.md`
2. 方針は `AGENTS.md` / `CLAUDE.md` を確認する。
3. `docs/開発ガイド/` は HTML が主。検索は `rg -n '<語句>' docs/開発ガイド -g '*.html'` を使う。

docs と実装が食い違う場合は、実装を確認したうえで「現行実装では」と明記する。

## 実装追従チェックリスト

- [ ] MCP は 19 サーバー構成として記載している。
  - 同期元: `backend_tools/tools_main.py`, `backend_tools/tools_proc/`
  - 含める: `aidiy_backup`（旧表現: `aidiy_backup_check` / `aidiy_backup_save`）、`aidiy_task_agents`、`aidiy_team_agents`、`aidiy_windows_control`
- [ ] 常駐バックエンドは 5 サーバー構成（core 8091 / apps 8098 / tools 8095 / local 8096 / task・team 8093）として記載している。
- [ ] Vite proxy は `/core` → 8091、`/apps` → 8098、`/task` → 8093、`/team` → 8093 の 4 経路で記載している。
- [ ] `backend_taskteam` は「AIタスク実行 + 定期タスク + 複数AIエージェントのチーム活動」として記載している。
  - 同期元: `backend_taskteam/task_proc/tasks_api.py`, `backend_taskteam/task_proc/tasks_watcher.py`, `backend_taskteam/team_proc/team_api.py`, `backend_taskteam/team_proc/team_watcher.py`
  - AIタスクとAIチームは `backend_taskteam` の単一サービスとして記載する。
- [ ] 移動済みフォルダを旧パスで書いていない。
  - AI コア実装: `backend_server/AIコア/`（旧: `backend_server/core_router/AIコア/`）。`core_router/AIコア.py` は Router 本体として現存する
  - 共通設定: プロジェクトルートの `_config/`（旧: `backend_server/_config/`）。`backend_server` からは `../_config` で参照する
  - MCP 個別設定: `_config/mcp_*.json`（旧: `_config/aidiy_*.json`）
  - ビデオ自動生成: `backend_tools/aidiy_automations/ビデオページ生成/`（旧: `aidiy_automations/` 直下）
  - CLI ランチャー: `scripts/cli_bat/_claude-code.bat` など（旧: `_*_AiDiy.bat`）
  - Xビデオの VRM: `frontend_web/public/Xビデオ/_vrm/` を `../_vrm/` で共有（旧: 各ビデオフォルダ内 `vrm/`）
- [ ] Docker 構成に `backend_tools` を含めていない。
  - MCP 検証はローカル起動を前提に書く。
- [ ] `command_hermes` は `_setup.py` / `_cleanup.py` に統合済み、`_start.py` の常駐起動対象外として書く。
- [ ] Code AI 名は `aidiy_hermes` として書く。
  - 旧表現: `hermes_cli`
- [ ] Code AI パネルは 6 枠として書く。
  - backend: `CODE_AI1_NAME`〜`CODE_AI6_NAME`
  - frontend: `code1`〜`code6`, `エージェント1`〜`エージェント6`
- [ ] `CHAT_AI_NAME` の OpenRouter 系キーは `openrt_chat` として書く。
  - 旧表現: `openai_chat`
- [ ] `_start.py` は対話形式、`--reload` なしとして書く。
  - コード変更反映は個別起動または `temp/reboot_*.txt`。
- [ ] `_stop.py` を前提にしない。
- [ ] `npm run build` は明示依頼時または Docker 反映時に限定し、通常検証は `npm run type-check` を優先する。

## 認証チェックリスト

- [ ] JWT 有効期限は 600 分として書く。
  - 同期元: `backend_server/auth.py`
- [ ] 認証 Storage を対象別に分けて書く。
  - `frontend_web`: `localStorage`
  - `frontend_avatar` Electron: `localStorage`
  - `frontend_avatar` Web: `sessionStorage`
- [ ] 認証延長対象を現行ルールに合わせる。
  - 延長対象: C/M/T 操作系 API、S/V 更新日監視、AI 非音声入力、AI ファイル `files_temp`
  - 延長対象外: メニュー遷移、X系、ログアウト、認証 API、`input_audio`, `operations`, `cancel_run`, `cancel_audio`, `files_backup`, `files_save`, `file_select`, `file_deselect`

## 画面・機能チェックリスト

- [ ] M系マスタに `M取引先分類` / `M取引先` を含める。
  - V系も `V取引先分類` / `V取引先` を含める。
- [ ] M商品サンプルは現行項目に合わせる。
  - 同期元: `backend_server/apps_models/M商品.py`, `apps_schema/M商品.py`, `apps_crud/M商品.py`, `apps_router/M商品.py`, `apps_router/V商品.py`
  - 同期元: `frontend_web/src/components/Mマスタ/M商品/M商品一覧.vue`, `M商品編集.vue`, `components/M商品一覧テーブル.vue`
  - 確認項目: `商品分類ID`, `有効`, `件数制限`, `無効も表示`, `qBooleanCheckbox`, `ListRequest`
- [ ] X系に `X立体リバーシ` と `X世界の絶景` を含める。
- [ ] `frontend_avatar` の表示選択は現行コンポーネント名で書く。
  - `AIコア_xneko.vue`, `AIコア_xeyes.vue`, `AIコア_アナログ時計.vue`, `AIコア_デジタル時計.vue`, `AIコア_カレンダー.vue`
  - `AIコア.vue` は `アバター表示` チェックボックスではなく `表示選択` select。

## 横断検索

```powershell
$files = rg --files -g '*.md' -g '!**/node_modules/**' -g '!**/.venv/**' -g '!**/dist/**' -g '!**/backup/**'

rg -n '6 サーバー|6 MCP|6 SSE|2 つの MCP|MCP サーバーも同居|openai_chat|16 サーバー|16 個の MCP|17 サーバー|17 個の MCP' $files
rg -n 'hermes_cli|aidiy_hermes|3サーバー構成|_start\.py.*command_hermes|AiDiy_code_hermes_cli' $files
rg -n 'aidiy_backup|M取引先|V取引先|トークン更新|files_temp|reboot_tools|backend_taskteam|8093' $files
rg -n '6 サーバー|旧分離バックエンド' $files
rg -n 'includeInactive|無効も検索|router/index\.ts へのルート追加|商品コードが重複|get_商品_by_code|DELETE文でデータを完全に削除' docs
rg -n 'start\.py|_stop\.py|8095.*Docker|npm run build' $files

# 旧フォルダ構成の残骸（ヒットしたら現行パスへ直す）
rg -n 'core_router/AIコア/|backend_server/_config|_config/aidiy_|aidiy_automations/ビデオページ生成_|_AiDiy\.bat|src/stores/AIモデル設定|components/Avatar\.vue|13 MCP|14 個の MCP' $files
```

## `_AIDIY/knowledge` 整理後の確認

```powershell
$knowledgeFiles = rg --files _AIDIY/knowledge -g '*.md'

# ローカル Markdown リンク切れ確認（http/https とアンカーのみのリンクは除外）
$missingLinks = foreach ($file in $knowledgeFiles) {
  $dir = Split-Path $file
  # () を含むパスは Markdown の <...> 形式も認識する
  Select-String -LiteralPath $file -Encoding UTF8 -Pattern '\]\((?:<([^>]+)>|([^)]+))\)' -AllMatches | ForEach-Object {
    foreach ($match in $_.Matches) {
      $rawLink = if ($match.Groups[1].Success) { $match.Groups[1].Value } else { $match.Groups[2].Value }
      $link = ([System.Uri]::UnescapeDataString($rawLink)) -replace '#.*$', ''
      if ($link -and $link -notmatch '^(https?://|#)') {
        $target = Join-Path $dir $link
        if (-not (Test-Path $target)) { "${file}:$($_.LineNumber) -> $link" }
      }
    }
  }
}
$missingLinks

# BOM 混入確認（出力なしなら OK）
foreach ($file in $knowledgeFiles) {
  $bytes = [System.IO.File]::ReadAllBytes((Resolve-Path $file))
  if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) { $file }
}

# 未整理表現は、仮置き見出し・旧テンプレート由来の見出し・一時的な説明が残っていないか本文を確認する
```

## 注意点

- 仕様値を書くときは同期元を併記する。
- `_config/` 配下の実ファイル内容や API キー値は docs/code_samples へコピーしない。
- Markdown のリンクは、`_AIDIY/knowledge` 内では同階層ファイルへの相対リンクかコード表記のパスにする。
- docs の HTML へ深いリンクを張る場合は、実在確認できない限りコード表記に留める。
