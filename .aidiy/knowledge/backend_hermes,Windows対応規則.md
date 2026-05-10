# Windows 対応規則（aidiy_hermes）

> 文書: `backend_hermes,Windows対応規則.md` | 実装: `backend_hermes/base/hermes_constants.py`, `backend_hermes/tools/environments/local.py`, `backend_hermes/tools/environments/base.py`, `backend_hermes/tools/file_operations.py`, `backend_hermes/tools/file_operations_linux.py`, `backend_hermes/tools/file_operations_win.py`, `backend_hermes/tools/file_tools.py`, `backend_hermes/tools/file_tools_linux.py`, `backend_hermes/tools/file_tools_win.py`, `backend_hermes/tools/terminal_tool.py`, `backend_hermes/tools/terminal_tool_linux.py`, `backend_hermes/tools/terminal_tool_win.py`, `backend_hermes/tools/process_registry.py`, `backend_hermes/tools/process_registry_linux.py`, `backend_hermes/tools/process_registry_win.py`

## このメモを使う場面

- aidiy_hermes の terminal / file 操作系コードへ修正を入れるとき
- Windows ネイティブ実行（cmd / PowerShell）で `[exit -1]` や 14 秒タイムアウト等が再発したとき
- POSIX 依存（`wc`、`sed`、`find`、`bash -l`、`preexec_fn` 等）を新規に追加してしまわないか確認したいとき
- 新たに OS 依存処理を `if os.name != 'nt':` で分岐するとき

## アーキテクチャ: platform selector + 純化された `*_linux.py` / `*_win.py`

下記 4 ファイルは **薄い selector** として動作する。Windows なら `*_win.py`、非 Windows なら `*_linux.py` のどちらか一方だけを import する。両側を同時に import しない。

| selector | Linux 実装 | Windows 実装 |
|----------|-----------|--------------|
| `tools/file_operations.py` | `file_operations_linux.py` | `file_operations_win.py` |
| `tools/file_tools.py` | `file_tools_linux.py` | `file_tools_win.py` |
| `tools/terminal_tool.py` | `terminal_tool_linux.py` | `terminal_tool_win.py` |
| `tools/process_registry.py` | `process_registry_linux.py` | `process_registry_win.py` |

純化の方針:

- `*_linux.py` は POSIX 前提の直線的な実装。`_IS_WINDOWS` 参照、`msvcrt`、`winpty`、Windows 分岐を **一切持たない**。
- `*_win.py` は Windows 前提の実装。`ptyprocess`、`fcntl`、`termios`、process group 処理を **一切持たない**。
- `*_linux.py` / `*_win.py` は selector 経由でのみ import する（discovery 対象から除外）。

`tools/environments/` 配下は selector 化されておらず、同一ファイル内で `if os.name != 'nt':` 分岐を残す（`local.py`、`base.py`）。Windows 分岐は POSIX 経路を改変せず `else:` 側へ追記する。

## OS 分岐コーディング規則

1. **既存 POSIX 経路を温存** — `if os.name != 'nt':` で囲み、ロジックは触らない（インデント追加のみ）。Windows 経路は `else:` 側に追記。
2. **判定式は `os.name == 'nt'` に統一** — 新規コードで `sys.platform.startswith('win')` や `platform.system() == 'Windows'` を混ぜない。既存の `_IS_WINDOWS = platform.system() == "Windows"` はそのまま残す（改変禁止）。
3. **戻り値・副作用の互換性を厳守** — Windows 経路でも `{"output": str, "returncode": int}` 形式、`self.cwd` 更新、ログ・activity_callback の呼び出しタイミングは Linux 経路と同じにする。
4. **例外は同じ型・メッセージ形式で raise** — silent fail で謎の `exit -1` を返さない。
5. **Windows 経路のログには `[winnt]` 識別子** を入れて grep 可能にする。
6. **判定ヘルパーは `backend_hermes/base/hermes_constants.py` の `is_windows_native()`** を使う。

## Windows 実装の落とし穴と対処

### subprocess / シェル
- **`bash -l` は使わない** — `.bashrc` 読み込みで起動が遅延し、14 秒タイムアウト問題の原因になる。Windows 経路では `bash -c '<cmd>'` 単体で起動する。
- **`creationflags=CREATE_NO_WINDOW` を付ける** — コンソールのちらつき抑止。
- **`encoding='utf-8', errors='replace'` を必ず指定** — Windows のデフォルトは cp932 のことがある。
- **`preexec_fn` は使えない** — Windows 非対応。Windows 経路では渡さない。
- **drain thread は使わず `proc.communicate(timeout=...)` を直接呼ぶ** — Windows での `_wait_for_process()` は drain thread 経由にしない。timeout 時は `_kill_process()` → `communicate(timeout=2)` → `returncode=124` で返す。
- **`_kill_process()` は `terminate()` 後に `wait(timeout=2)`** — returncode が None なら `-9` に正規化。

### shell 選択
- **Windows local shell は Git Bash 優先 → PowerShell fallback、WSL bash は除外** — `C:\Windows\System32\bash.exe` は Windows パス（`D:/...`）を扱えず詰まる。
- PowerShell 強制経路では `ls ... | head -N` のような POSIX パイプを変換するヘルパーが入っている。
- background process registry も同じ shell 選択を使う。

### file 操作（`WindowsFileOperations`）
- bash 経由ではなく **Python 直接実装**（`pathlib` / `subprocess`）。`wc`、`sed`、`find` 依存は持たせない。
- `read_file` は `Path.read_text(encoding='utf-8', errors='replace')`、改行は `newline=None` で読み込み LF に統一。
- `write_file` は **原子書き込み**（同ディレクトリに `.tmp` → `os.replace()`）。
- **OneDrive 配下のロック対策** — `os.replace()` は OneDrive 同期と競合し ACCESS DENIED になることがある。リトライ（最大 3 回・100ms 間隔）を入れる。
- `search_files(target='content')` は **`ripgrep` バイナリを `subprocess.run` で直接呼ぶ**。`rg` が無い場合は Python 正規表現でフォールバック。
- `search_files(target='files')` は `Path.rglob()`。
- patch 適用は `WindowsFileOperations.patch_replace()` / `patch_v4a()` を Python で再実装。
- 大小文字統一は `Path.resolve()`、長いパスは `\\?\` プレフィックスを検討。

### terminal_tool
- **Windows で `timeout < 30` のときは 30 に底上げ** — bash 起動オーバーヘッドで kill されないようにする safeguard。LLM が短い timeout を渡してきても落ちない。
- `TERMINAL_TOOL_DESCRIPTION` に Windows 注意書き（`timeout` を 60 以上推奨）が入っている。

### `LocalEnvironment.init_session()`
- Windows では **snapshot を作らない簡易セッション初期化** にする。`self._snapshot_ready = False` を立てるだけ。
- cwd 検証は `os.path.isdir()`、`pwd` 結果をそのまま `self.cwd` に格納。
- ログに `[winnt] init_session: snapshot disabled, fresh-bash mode` を出す。

### `_wrap_command()`
- Windows では `source <snapshot>` をスキップ。
- CWD ファイル更新は選択 shell に合わせる（Git Bash なら MSYS 形式、PowerShell なら Windows 形式）。
- CWD マーカー（`__HERMES_CWD_xxx__`）は Windows でも出力する。

## 動作確認コマンド

各修正後、以下が **5 秒以内** に成功すること。

```text
pwd
ls -la
ls -la D:/OneDrive/_sandbox/AiDiy2026
test -e D:/OneDrive/_sandbox/AiDiy2026 && echo OK
cat .aidiy/knowledge/_index.md
```

ツール経由:

- `read_file('.aidiy/knowledge/_index.md')` で読める
- `search_files(target='files', pattern='*.md', path='backend_hermes')` で結果が返る
- `search_files(target='content', pattern='def is_wsl', path='backend_hermes')` で結果が返る
- `write_file` で一時ファイル作成・削除できる
- `patch` で 1 行置換できる

統合確認:

- `uv run python cli_main.py --list-tools` が成功する
- 「`.aidiy/knowledge/_index.md` を読んで要約して」が 30 秒以内に応答する

## Linux/macOS 回帰テスト

Linux/WSL で `aidiy_hermes` を起動し、`pwd`、`ls`、`read_file` が従来通り動くこと。`if os.name != 'nt':` で囲っただけなら原理的に影響ゼロだが、インデント変更でシンタックスエラーが入っていないか目視確認する。
