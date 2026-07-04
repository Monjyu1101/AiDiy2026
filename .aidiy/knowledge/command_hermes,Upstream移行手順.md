# command_hermes Upstream 移行手順

> 文書: `command_hermes,Upstream移行手順.md` | 実装: `command_hermes/` (全ファイル)

## このメモを使う場面

- Nous Research の hermes-agent が新バージョン（v0.13 以降）をリリースした
- `command_hermes` を upstream の新バージョンへ追従させる必要がある
- コンフリクト解消や差分再適用の方針を確認したい

## 前提

- upstream: https://github.com/nousresearch/hermes-agent
- 現行ベース: v0.12.0 (`__version__ = "0.12.0"`, `__release_date__ = "2026.4.30"`)
- AiDiy 側は `command_hermes/` としてフォーク管理
- upstream / AiDiy ともに `pyproject.toml` ベース

---

## 1. 手順概要

| 工程 | 内容 | 想定時間 |
|------|------|---------|
| A. 事前準備 | upstream clone、現行バックアップ | 10分 |
| B. ファイル分類マップを参照 | 追加/削除/修正ファイルを把握 | 15分 |
| C. upstream ファイル反映 | 変更なしファイルは単純コピー、修正ファイルは差分再適用 | 2-4時間 |
| D. 動作確認 | コンパイル・起動・provider・MCP の確認 | 30分 |
| E. ナレッジ更新 | 移行後の差分テーブルを更新 | 15分 |

---

## 2. ファイル分類マップ（v0.12.0 時点）

upstream v0.12.0 と AiDiy の全ファイルを6分類しています。

凡例:
- **A** = AiDiy 追加（upstream に存在しない）
- **D** = AiDiy 削除（upstream にはあるが AiDiy にない）
- **M** = 修正あり（upstream と内容が異なる）
- **SAME** = 同一（上書きして問題ない）
- **MOVED** = 移動のみ（内容同一、パス変更）
- **STRIP** = 縮退（upstream の一部ファイルだけ残した）

### 2.1 root 直下

| ファイル | 状態 | 移行時の扱い |
|----------|------|-------------|
| `cli_main.py` | **M** | upstream `cli.py` をベースに AiDiy パッチを再適用 |
| `pyproject.toml` | **M** | 新バージョンの依存を調査し、必要な AiDiy 依存だけ残す |
| `AGENTS.md` | **A** | そのまま維持 |
| `NOTICE.md` | **A** | そのまま維持（バージョン表記を更新） |
| `AIDIY-HERMESロゴ.txt` | **A** | そのまま維持 |
| `tui画面出す.bat` | **A** | そのまま維持 |
| `_setup.py` | **A** | そのまま維持（`uv sync --upgrade` + ランチャ生成） |

### 2.2 `core/`（upstream `agent/`）

| ファイル | 状態 | 移行時の扱い |
|----------|------|-------------|
| `__init__.py` | **SAME** | upstream `agent/__init__.py` で上書き |
| `account_usage.py` | **SAME** | upstream で上書き |
| `anthropic_adapter.py` | **SAME** | upstream で上書き |
| `auxiliary_client.py` | **SAME** | upstream で上書き |
| `bedrock_adapter.py` | **SAME** | upstream で上書き |
| `codex_responses_adapter.py` | **SAME** | upstream で上書き |
| `context_compressor.py` | **M** | upstream ベース + AiDiy パッチ再適用 |
| `context_engine.py` | **SAME** | upstream で上書き |
| `context_references.py` | **SAME** | upstream で上書き |
| `copilot_acp_client.py` | **SAME** | upstream で上書き |
| `credential_pool.py` | **M** | upstream ベース + AiDiy パッチ再適用 |
| `credential_sources.py` | **SAME** | upstream で上書き |
| `curator.py` | **M** | upstream ベース + AiDiy パッチ再適用 |
| `display.py` | **M** | upstream ベース + AiDiy パッチ再適用 |
| `error_classifier.py` | **M** | upstream ベース + AiDiy パッチ再適用 |
| `file_safety.py` | **SAME** | upstream で上書き |
| `gemini_cloudcode_adapter.py` | **SAME** | upstream で上書き |
| `gemini_native_adapter.py` | **SAME** | upstream で上書き |
| `gemini_schema.py` | **SAME** | upstream で上書き |
| `google_code_assist.py` | **SAME** | upstream で上書き |
| `google_oauth.py` | **SAME** | upstream で上書き |
| `image_gen_provider.py` | **SAME** | upstream で上書き |
| `image_gen_registry.py` | **SAME** | upstream で上書き |
| `image_routing.py` | **SAME** | upstream で上書き |
| `insights.py` | **SAME** | upstream で上書き |
| `lmstudio_reasoning.py` | **SAME** | upstream で上書き |
| `manual_compression_feedback.py` | **SAME** | upstream で上書き |
| `memory_manager.py` | **SAME** | upstream で上書き |
| `memory_provider.py` | **SAME** | upstream で上書き |
| `model_metadata.py` | **SAME** | upstream で上書き |
| `models_dev.py` | **SAME** | upstream で上書き |
| `moonshot_schema.py` | **SAME** | upstream で上書き |
| `nous_rate_guard.py` | **SAME** | upstream で上書き |
| `onboarding.py` | **SAME** | upstream で上書き |
| `prompt_builder.py` | **M** | upstream ベース + AiDiy パッチ再適用 |
| `prompt_caching.py` | **SAME** | upstream で上書き |
| `rate_limit_tracker.py` | **SAME** | upstream で上書き |
| `redact.py` | **SAME** | upstream で上書き |
| `retry_utils.py` | **SAME** | upstream で上書き |
| `shell_hooks.py` | **SAME** | upstream で上書き |
| `skill_commands.py` | **SAME** | upstream で上書き |
| `skill_preprocessing.py` | **SAME** | upstream で上書き |
| `skill_utils.py` | **SAME** | upstream で上書き |
| `subdirectory_hints.py` | **SAME** | upstream で上書き |
| `title_generator.py` | **SAME** | upstream で上書き |
| `tool_guardrails.py` | **SAME** | upstream で上書き |
| `trajectory.py` | **SAME** | upstream で上書き |
| `usage_pricing.py` | **SAME** | upstream で上書き |
| `transports/` (全ファイル) | **SAME** | upstream `agent/transports/` で上書き |
| `curator_backup.py` | **D** | upstream にあっても無視（AiDiy では使わない） |
| `think_scrubber.py` | **D** | upstream にあっても無視（AiDiy では使わない） |

### 2.3 `base/`（upstream ルートから移動）

| ファイル | 状態 | 移行時の扱い |
|----------|------|-------------|
| `hermes_constants.py` | **MOVED** | upstream ルート版を `base/` へコピー |
| `utils.py` | **MOVED** | upstream ルート版を `base/` へコピー |
| `model_tools.py` | **MOVED** | upstream ルート版を `base/` へコピー |
| `toolsets.py` | **MOVED** | upstream ルート版を `base/` へコピー |
| `toolset_distributions.py` | **MOVED** | upstream ルート版を `base/` へコピー |
| `batch_runner.py` | **MOVED** | upstream ルート版を `base/` へコピー |
| `run_agent.py` | **MOVED** | upstream ルート版を `base/` へコピー |

### 2.4 `tools/`

| ファイル | 状態 | 移行時の扱い |
|----------|------|-------------|
| `__init__.py` | **SAME** | upstream で上書き |
| `registry.py` | **SAME** | upstream で上書き |
| `terminal_tool.py` | **SAME** | upstream で上書き |
| `web_tools.py` | **SAME** | upstream で上書き |
| `image_generation_tool.py` | **SAME** | upstream で上書き |
| `todo_tool.py` | **SAME** | upstream で上書き |
| `clarify_tool.py` | **SAME** | upstream で上書き |
| `code_execution_tool.py` | **SAME** | upstream で上書き |
| `memory_tool.py` | **SAME** | upstream で上書き |
| `discord_tool.py` | **SAME** | upstream で上書き |
| `neutts_synth.py` | **SAME** | upstream で上書き |
| `homeassistant_tool.py` | **SAME** | upstream で上書き |
| `feishu_doc_tool.py` | **SAME** | upstream で上書き |
| `feishu_drive_tool.py` | **SAME** | upstream で上書き |
| `browser_providers/` (全5ファイル) | **SAME** | upstream で上書き |
| `environments/` (全ファイル) | **SAME** | upstream で上書き |
| `mcp_tool.py` | **M** | upstream ベース + AiDiy SSE/AiDiy_mcp.json パッチ再適用 |
| `file_operations.py` | **M** | upstream ベース + AiDiy パッチ再適用 |
| `file_tools.py` | **M** | upstream ベース + AiDiy パッチ再適用 |
| `vision_tools.py` | **M** | upstream ベース + AiDiy パッチ再適用（動画解析削除） |
| `approval.py` | **M** | upstream ベース + AiDiy パッチ再適用 |
| `delegate_tool.py` | **M** | upstream ベース + AiDiy パッチ再適用 |
| `schema_sanitizer.py` | **M** | upstream ベース + AiDiy パッチ再適用 |
| `cronjob_tools.py` | **M** | upstream ベース + AiDiy パッチ再適用 |
| `send_message_tool.py` | **M** | upstream ベース + AiDiy パッチ再適用 |
| `skill_manager_tool.py` | **M** | upstream ベース + AiDiy パッチ再適用 |
| `session_search_tool.py` | **M** | upstream ベース + AiDiy パッチ再適用 |
| `tts_tool.py` | **M** | upstream ベース + AiDiy パッチ再適用 |
| `skills_hub.py` | **M** | upstream ベース + AiDiy パッチ再適用 |
| `skill_provenance.py` | **D** | upstream にあっても無視 |
| (その他未記載の`.py`ファイル) | **SAME** | ファイル単位で確認 |

### 2.5 `hermes_cli/`

| ファイル | 状態 | 移行時の扱い |
|----------|------|-------------|
| `banner.py` | **SAME** | upstream で上書き |
| `setup.py` | **D** | upstream にあっても無視 |
| `main.py` | **M** | upstream ベース + AiDiy パス注入 + TUI routing 再適用 |
| `_parser.py` | **M** | upstream ベース + `--dev` help 文言変更を再適用 |
| (その他共通ファイル) | **要確認** | v0.13 の変更差分に応じて対応 |

### 2.6 `gateway/` / `environments/` / `skills/` / `plugins/` / `optional-skills/`

| ディレクトリ | 状態 | 移行時の扱い |
|-------------|------|-------------|
| `gateway/` | **STRIP** | `__init__.py` + `session_context.py` のみ残す。他は削除 |
| `environments/` | **SAME** | upstream で上書き |
| `skills/` | **SAME** | upstream で上書き |
| `plugins/` | **SAME** | upstream で上書き |
| `optional-skills/` | **SAME** | upstream で上書き |

---

## 3. 修正ファイルのパッチ詳細（v0.12.0 ベース）

各修正ファイルについて、upstream からの差分内容と再適用方法を記載します。

### 3.1 `cli_main.py` — 最大の改変ファイル

upstream `cli.py` をコピーし、以下の変更を加える:

```
変更1: 冒頭の sys.path 追加 + utf-8 reconfigure + sys.modules alias
変更2: cron import を try/except でラップ
変更3: cli_entry() 関数追加 (argparse エントリ)
変更4: _load_aidiy_hermes_defaults() 追加
変更5: _resolve_aidiy_ollama_model() 追加
変更6: _aidiy_provider_* メソッド群追加 (L5655-5925)
変更7: quiet/oneshot 出力分離 (L12485-12543)
変更8: main() 末尾の fire.Fire() 維持
```

**再適用方法**:
1. upstream `cli.py` を `cli_main.py` としてコピー
2. 以下のキーワードで patch 箇所を検索して再適用:
   - `_aidiy_` — provider system 全メソッド
   - `AiDiy_key.json` — config 読込
   - `aidiy_hermes` — prog 名
   - `redirect_stdout` — 出力分離

### 3.2 `mcp_tool.py` — SSE transport

```
変更1: _MCP_SSE_AVAILABLE フラグ + sse_client import 確認
変更2: _is_sse() メソッド追加
変更3: _is_http() の条件を "not self._is_sse()" に変更
変更4: _run_sse() メソッド追加
変更5: run() の分岐に SSE 追加
変更6: _load_aidiy_mcp_servers() 関数追加
変更7: get_mcp_servers_config() に AiDiy_mcp.json マージ
変更8: transport type 表示に "SSE" 追加
```

**再適用方法**: `grep -n "sse\|SSE\|aidiy_mcp\|AiDiy_mcp"` で全該当箇所を抽出。

### 3.3 `core/display.py` — 日本語対応

```
変更1: _static_wait_message() メソッド追加 (日本語 static メッセージ)
変更2: _animate() 内で static spinner 分岐追加
```

**再適用方法**: `_static_wait_message` と `_static_spinner` で検索。

### 3.4 `core/credential_pool.py` — env 読込統一

```
変更1: _get_env_prefer_dotenv() → get_env_value() に置換
```

### 3.5 `core/context_compressor.py` — ロジック簡略化

```
変更1: _summary_failure_cooldown_until 削除
変更2: prune 境界計算の budget_protect_count 経路削除
変更3: timeout 再試行条件から timeout を除外
```

### 3.6 `core/curator.py` — 整理

```
変更1: _strip_aux_credential() 削除
変更2: _ReviewRuntimeBinding NamedTuple 削除
```

### 3.7 `tools/` 群 — 軽微な修正

全修正ファイル共通のパターン:
- vision_tools.py: 動画解析コードブロック削除
- approval.py: 危険パターンリスト短縮
- delegate_tool.py: heartbeat 間隔短縮 (15→5, 40→20)
- 他: 削除/短縮のみ

**再適用方法**: upstream ファイルをコピー後、`git diff` または `diff -u` で patch ファイルを適用。

---

## 4. 移行手順 (step-by-step)

### Step 1: 事前準備

```powershell
# upstream clone
cd C:\tmp
git clone --depth 1 https://github.com/nousresearch/hermes-agent.git hermes-agent-upstream

# command_hermes 全体をバックアップ
$bak = "command_hermes_bak_$(Get-Date -Format 'yyyyMMdd')"
Copy-Item D:\OneDrive\_sandbox\AiDiy2026\command_hermes D:\OneDrive\_sandbox\AiDiy2026\$bak

# アップストリームのバージョン確認
cd C:\tmp\hermes-agent-upstream
git log --oneline -3
Get-Content pyproject.toml | Select-String "version"
```

### Step 2: upstream ファイルリストを取得する

```powershell
cd C:\tmp\hermes-agent-upstream

# すべての .py ファイルを抽出
Get-ChildItem -Recurse -Filter *.py | ForEach-Object { $_.FullName.Replace("C:\tmp\hermes-agent-upstream\", "") } | Sort-Object > upstream_files.txt

# AiDiy 側のファイルリスト
Set-Location D:\OneDrive\_sandbox\AiDiy2026\command_hermes
Get-ChildItem -Recurse -Filter *.py | ForEach-Object { $_.FullName.Replace("D:\OneDrive\_sandbox\AiDiy2026\command_hermes\", "") } | Sort-Object > aidiy_files.txt
```

### Step 3: 変更なし (SAME) ファイルを上書きする

```powershell
$upstreamRoot = "C:\tmp\hermes-agent-upstream"
$aidiyRoot = "D:\OneDrive\_sandbox\AiDiy2026\command_hermes"

# SAME ファイル一覧に基づきコピー
$sameFiles = @(
    # core/ (agent/ → core/)
    "agent/__init__.py", "agent/account_usage.py", ...
)
foreach ($rel in $sameFiles) {
    $src = $rel -replace "^agent/", "$upstreamRoot/agent/"
    $dst = $rel -replace "^agent/", "$aidiyRoot/core/"
    Copy-Item $src $dst
}
```

実際のコピーは「2. ファイル分類マップ」の **SAME** ファイルを対象に行う。

### Step 4: MOVED ファイルを base/ へコピー

```powershell
# upstream ルート → AiDiy base/
$movedFiles = @("hermes_constants.py","utils.py","model_tools.py","toolsets.py",
                "toolset_distributions.py","batch_runner.py","run_agent.py")
foreach ($f in $movedFiles) {
    Copy-Item "$upstreamRoot/$f" "$aidiyRoot/base/$f"
}
```

### Step 5: M ファイルに patch を再適用する

**推奨方式**: upstream 新ファイル + 事前にとっておいた patch ファイル

```powershell
# 事前に patch ファイルを作成しておく方法
cd D:\OneDrive\_sandbox\AiDiy2026\command_hermes

# 例: mcp_tool.py の場合
#  patch -p1 < patches/0001-mcp_tool-sse-support.patch

# または手動で各編集箇所を再適用
```

patch は初回移行時に `git diff` で採取しておくと良い。

### Step 6: 削除ファイルを反映

```powershell
# D (削除) ファイルが upstream に追加されていたら無視
# AiDiy 側で維持すべき A (追加) ファイルはそのまま
```

### Step 7: cli_main.py を統合

```powershell
# 1. upstream cli.py → cli_main.py にコピー
Copy-Item "$upstreamRoot/cli.py" "$aidiyRoot/cli_main.py"

# 2. AiDiy パッチ適用
#   - cli_entry() 追加
#   - _load_aidiy_defaults() 追加
#   - _aidiy_provider_* 追加
#   - quiet/oneshot 出力分離
#   - cron import fallback
```

### Step 8: `gateway/` を縮退

```powershell
# gateway は __init__.py + session_context.py だけ維持
$upstreamGateway = "$upstreamRoot/gateway"
$aidiyGateway = "$aidiyRoot/gateway"

# session_context.py が upstream で変更されていたら update
if (-not (Compare-Object (Get-Content "$upstreamGateway/session_context.py") `
                         (Get-Content "$aidiyGateway/session_context.py"))) {
    Copy-Item "$upstreamGateway/session_context.py" "$aidiyGateway/session_context.py"
}

# __init__.py は AiDiy 版を維持（互換性スタブ）
# gateway の他のファイルはコピーしない
```

### Step 9: 削除ディレクトリを確認

```powershell
# 以下のディレクトリが upstream にあっても AiDiy にはコピーしない
$skipDirs = @("cron","web","website","ui-tui","tui_gateway","acp_adapter",
              "acp_registry","docs","tests","scripts","packaging","nix","docker")
```

---

## 5. 動作確認リスト

```powershell
# ========== 5.1 コンパイルチェック ==========
Set-Location command_hermes
.venv\Scripts\python.exe -m py_compile cli_main.py
.venv\Scripts\python.exe -m py_compile tools/mcp_tool.py

# ========== 5.2 import チェック ==========
.venv\Scripts\python.exe -c "
import openai; import anthropic; import google.genai
print('provider SDKs OK')
"

# ========== 5.3 CLI 基本動作 ==========
.venv\Scripts\python.exe cli_main.py --version
.venv\Scripts\python.exe cli_main.py --help
.venv\Scripts\python.exe cli_main.py --list-tools

# ========== 5.4 oneshot 実行 ==========
python ..\_setup.py
aidiy_hermes -z -Q "こんにちは"

# ========== 5.5 provider / model 切替 ==========
aidiy_hermes -z --provider ollama --model "deepseek-v4-flash:cloud" -Q "test"

# ========== 5.6 MCP サーバー認識 ==========
.venv\Scripts\python.exe -c "
from tools.mcp_tool import discover_mcp_tools, get_mcp_status
result = discover_mcp_tools()
for s in get_mcp_status():
    print(s)
"

# ========== 5.7 stdout/stderr 分離 ==========
$out = aidiy_hermes -z -Q "Hello" 2>$null
$err = aidiy_hermes -z -Q "Hello" >$null
Write-Host "stdout: $out"
Write-Host "stderr: $err"
```

## 6. 移行後に更新すべきファイル

| ファイル | 更新内容 |
|---------|---------|
| `.aidiy/knowledge/command_hermes,TUI調整手順.md` | Upstream からの調整点テーブルを v0.13 用に更新 |
| `.aidiy/knowledge/command_hermes,Upstream移行手順.md` | 本ファイルのファイル分類マップを更新 |
| `command_hermes/NOTICE.md` | バージョン表記を更新 |
| `command_hermes/hermes_cli/__init__.py` | `__version__` / `__release_date__` を更新 (該当する場合) |

## 7. 移行判断フローチャート

```
upstream v0.13 リリース
    │
    ├── CHANGELOG / Release Notes を確認
    │
    ├─┬ 互換性のある変更のみ？
    │ │   │ YES → SAME/MOVED ファイルだけ上書き (Step 3,4)
    │ │   │ NO  → 以下の影響範囲を特定
    │ │
    │ └── M ファイルの API 変更？
    │        │ YES → M ファイルの patch 再設計が必要
    │        │ NO  → 既存 patch がそのまま適用可能
    │
    ├─┬ AiDiy 追加機能 (oneshot/provider system) 破壊？
    │     │ YES → cli_main.py 統合に工数が必要
    │     │ NO  → cli_main.py の patch のみ更新
    │
    └── 確認完了 → Step 3 以降を実行
```
