# aidiy_hermes Windows ネイティブ対応 作業チェックシート

最終更新: 2026-05-09

## 0. 背景と目的

`aidiy_hermes` は元来 Linux/macOS 向けに設計されており、Windows ネイティブ
（cmd / PowerShell ホスト）では以下の症状が出る：

- `terminal` ツールで実行する単純コマンド（`pwd`、`ls`、`test -e`）が **14 秒前後で `[exit -1]`** に落ちる
- `read_file` ツールが `wc -c` 等の POSIX シェルコマンドに依存しており、Windows 標準環境だけでは動かない
- shell 探索が WSL bash（`C:\Windows\System32\bash.exe`）を拾うことがあり、Windows ホストパス（`D:/...`）を扱えず詰まる
- LLM が tool 呼び出し時に `timeout=14` のような短い値を渡してくることがあり、Hermes 側の bash 起動オーバーヘッドと相まって kill される

これらを「**Linux 経路を一切壊さず、Windows 経路を追加する**」方針で根本的に修正する。

---

## 1. コーディング規則（厳守）

破綻しにくい修正にするため、以下を絶対ルールとする。

### 1.1 OS 分岐のスケルトン

すべての修正箇所は **既存コードを `if os.name != 'nt':` ブロックに包んで温存** し、Windows 経路は `else:` ブランチに追記する。

```python
def some_function(...):
    if os.name != 'nt':
        # 旧コード（既存の POSIX 実装をそのまま残す。一切触らない）
        ...
    else:
        # Windows 専用コード（新規追加）
        ...
```

**やってはいけないこと**:

- 既存 POSIX コードの行を改変する（インデント追加だけにとどめる、ロジックは触らない）
- 共通ヘルパー関数のシグネチャ・戻り値を変更する
- "Windows ならこのフラグを立てる" のような条件を分岐の外に滲ませる
- `if sys.platform == "win32"` と `if os.name == 'nt'` を混在させる（**統一して `os.name == 'nt'`** とする）

### 1.2 破綻防止の原則

1. **戻り値の互換性**: Windows 経路でも `{"output": str, "returncode": int}` の dict 形式を厳守
2. **副作用の同期**: `self.cwd` の更新、ログ出力、活動コールバックは Linux 経路と同じタイミング・同じ呼び出し方で実施
3. **例外の伝播**: Windows 経路で発生した例外は Linux 経路と同じ型・同じメッセージ形式で raise する
4. **既存テストへの影響ゼロ**: Linux 上で実行される CI/テストには一切影響を与えない（`os.name == 'nt'` でガードしているので原理的に安全）
5. **ログメッセージは識別可能に**: Windows 経路から出るログには `[winnt]` 等の識別子を入れて、後で grep できるようにする

### 1.3 失敗時のフォールバック

Windows 経路の処理が想定外の例外を吐いた場合は、可能な限り **Linux 経路の挙動に巻き戻す** か、**明示的なエラーメッセージで失敗** させる。silent fail で謎の `exit -1` を返さない。

```python
else:  # Windows
    try:
        return _windows_specific_impl(...)
    except Exception as exc:
        logger.warning("[winnt] specialised path failed: %s — falling back to bash", exc)
        # 既存の bash 経路にフォールバック（Linux 経路と共通）
        return _bash_path(...)
```

### 1.4 検証ポイント

各フェーズの完了時に **以下の最小コマンドが 5 秒以内に成功する** ことを確認：

- `pwd`
- `ls -la`
- `test -e .` で exit 0
- `read_file` で `.aidiy/knowledge/_index.md` を読める
- `search_files(target='files', pattern='*.md')` で結果が返る

---

## 2. 作業フェーズと進め方

リスク順に小さい単位から積み上げる。各フェーズは **コミット可能な単位** とし、一つずつ動作確認する。

| フェーズ | 内容 | 想定行数 | リスク |
|---|---|---|---|
| A | 環境検出ヘルパーの整備 | ~80 | 低 |
| B | `LocalEnvironment` の Windows 経路（bash 起動の簡素化） | ~250 | 中 |
| C | `ShellFileOperations` の Windows ネイティブ実装 | ~600 | 高 |
| D | `terminal` ツールのヒント強化と timeout 下限引き上げ | ~50 | 低 |
| E | 動作確認・回帰テスト | - | - |

---

## 3. チェックリスト

### フェーズ A: 環境検出ヘルパーの整備

- [ ] **A-1** `backend_hermes/base/hermes_constants.py` の `is_windows_native()` が正しく動くことを確認（既に追加済み）
- [x] **A-2** `backend_hermes/tools/environments/local.py` の Windows shell 探索が Git Bash または PowerShell を返すことを確認
- [ ] **A-3** `_IS_WINDOWS = (os.name == 'nt')` を新規モジュールで使う場合は **常に `os.name == 'nt'`** を直接参照する。`platform.system() == 'Windows'` や `sys.platform.startswith('win')` は新規コードに書かない
- [ ] **A-4** `tools/environments/local.py` の既存 `_IS_WINDOWS = platform.system() == "Windows"` はそのまま残す（既存ロジック改変禁止）。新規追加箇所は `os.name == 'nt'` で書く（混ぜない）
- [x] **A-5** Windows 用パスフォーマッタを `tools/environments/local.py` に追加：
  ```python
  if os.name == 'nt':
      def _to_msys_path(path: str) -> str:
          """Convert 'D:\\foo\\bar' or 'D:/foo/bar' to '/d/foo/bar' for MSYS-compatible shells."""
          ...
  ```

### フェーズ B: `LocalEnvironment` の Windows 経路（最重要）

#### B-1. `init_session()` の Windows 分岐

- [x] **B-1-1** `backend_hermes/tools/environments/base.py` の `init_session()` 全体を `if os.name != 'nt':` ブロックに包む
- [x] **B-1-2** `else:` ブロックに **snapshot を作らない簡易セッション初期化** を実装：
  - `self._snapshot_ready = False` を立てるだけ
  - cwd の検証は Python の `os.path.isdir()` で行う
  - `pwd` 結果はそのまま `self.cwd` に格納
- [x] **B-1-3** ログに `[winnt] init_session: snapshot disabled, fresh-bash mode` を出力

#### B-2. `_run_bash()` の Windows 分岐

- [x] **B-2-1** `tools/environments/local.py` の `_run_bash()` を `if os.name != 'nt':` で包み、Windows では shell 選択経路へ分岐する
- [x] **B-2-2** Windows 経路では：
  - `bash -l` を使わない（login shell の `.bashrc` が遅延の原因のため）
  - `bash -c '<cmd>'` 単体で起動
  - `subprocess.Popen(..., creationflags=CREATE_NO_WINDOW)` でコンソール抑止
  - `cwd` は Windows 形式（`D:/foo/bar`）のまま渡す（Git Bash / PowerShell の双方で扱える形式）
- [x] **B-2-3** `preexec_fn` は使わない（Windows 非対応のため。既に `None if _IS_WINDOWS else os.setsid` で対処済みだが、Windows 経路全体を囲うことで明示化）

#### B-3. `_wait_for_process()` の Windows 分岐（**14秒問題の本丸**）

- [x] **B-3-1** `tools/environments/base.py` の `_wait_for_process()` を `if os.name != 'nt':` で包む
- [x] **B-3-2** Windows 経路では **drain thread を使わず `proc.communicate(timeout=...)` を直接呼ぶ**：
  ```python
  else:  # os.name == 'nt'
      try:
          stdout, _ = proc.communicate(timeout=timeout)
          return {"output": stdout or "", "returncode": proc.returncode}
      except subprocess.TimeoutExpired:
          self._kill_process(proc)
          try:
              proc.communicate(timeout=2)
          except Exception:
              pass
          return {"output": "", "returncode": 124}
  ```
- [x] **B-3-3** Interrupt 検出は Windows 経路にも入れる（KeyboardInterrupt で kill）
- [x] **B-3-4** `activity_callback` の touch は維持（10s 間隔）

#### B-4. `_kill_process()` の Windows 分岐の見直し

- [x] **B-4-1** 既に Windows 分岐は存在 (`tools/environments/local.py`)。`proc.terminate()` 後に `proc.wait(timeout=2)` を追加して returncode を確実に取得する
- [x] **B-4-2** kill 後の returncode が None なら `-9`（SIGKILL 相当）に正規化して返す

#### B-5. `_wrap_command()` の Windows 適応

- [x] **B-5-1** `tools/environments/base.py` の `_wrap_command()` の `parts.append(f"source {self._snapshot_path} ...")` を `if os.name != 'nt': ... else: pass` でスキップ可能に
- [x] **B-5-2** CWD ファイル更新は Windows の選択 shell に合わせて扱う（Git Bash は MSYS 形式、PowerShell は Windows 形式）
- [x] **B-5-3** Windows 経路でも CWD マーカー (`__HERMES_CWD_xxx__`) は出力する（後段の cwd 抽出と整合させる）

### フェーズ C: `ShellFileOperations` の Windows ネイティブ実装

bash 経由ではなく Python 直接実装に切り替える。

- [x] **C-1** `tools/file_operations_win.py` に `WindowsFileOperations(ShellFileOperations)` クラスを配置
  - `read_file()` は `pathlib.Path.read_text(encoding='utf-8', errors='replace')`
  - `write_file()` は `pathlib.Path.write_text(...)`
  - `_is_likely_binary()` は既存ロジックそのまま流用可
  - `_expand_path()` は `os.path.expanduser()` で十分
- [x] **C-2** `_get_file_ops()` の生成ロジックを変更：
  ```python
  if os.name != 'nt':
      file_ops = ShellFileOperations(terminal_env)  # 既存
  elif getattr(terminal_env, "_winnt_native_local", False):
      from tools.file_tools_win import create_file_ops
      file_ops = create_file_ops(terminal_env)
  else:
      file_ops = ShellFileOperations(terminal_env)
  ```
- [x] **C-3** `WindowsFileOperations.read_file()`：
  - `path` 解決は `Path(path).expanduser().resolve()`
  - サイズチェックは `Path.stat().st_size`
  - 行範囲は Python の `splitlines()` でスライス
  - 戻り値の `ReadResult` 構造は Linux 経路と同一にする
- [x] **C-4** `WindowsFileOperations.write_file()`：
  - 親ディレクトリ作成は `Path.mkdir(parents=True, exist_ok=True)`
  - 書き込みは原子操作（同ディレクトリに `.tmp` を作って `os.replace()`）
- [x] **C-5** `WindowsFileOperations.search_files()`：
  - `target='files'` は `pathlib.Path.rglob()` で実装
  - `target='content'` は **既存の `ripgrep` バイナリを `subprocess.run` で直接呼ぶ**（bash 経由しない）
  - `rg` が見つからない場合は Python の正規表現フォールバック
- [x] **C-6** `WindowsFileOperations._unified_diff()`：既存の Linux 実装と同じく `difflib.unified_diff()` を使うのでそのまま
- [x] **C-7** patch 適用：既存ロジックに依存しているので、Windows 用は `WindowsFileOperations.patch_replace()` / `patch_v4a()` を Python 直接実装で再実装

### フェーズ D: `terminal` ツール周りの細部調整

- [x] **D-1** `terminal_tool.py` の `TERMINAL_TOOL_DESCRIPTION` の Windows 注意書きを更に強化（既に一行入れているが、`timeout` を 60 以上にするよう促す追記）
- [x] **D-2** `terminal_tool()` 関数本体で **`os.name == 'nt'` かつ `timeout < 30` のときは `timeout = 30` に底上げ** する safeguard を追加（LLM が短すぎる timeout を渡してきても bash 起動オーバーヘッドで kill されないようにする）
- [x] **D-3** `init_session()` を Windows でスキップした影響で `bash -l` 経由で取れていた環境変数が落ちる場合、`os.environ` をそのまま `_make_run_env()` に渡すパスでカバー（既存実装で対応済みか確認）
- [x] **D-4** Windows でのシェル選択：Git Bash が無ければ PowerShell へフォールバックし、`aidiy_hermes` 起動時に選択シェルを検証する

### フェーズ E: 動作確認・回帰テスト

各フェーズ完了時、および全フェーズ完了時に以下を実施。

#### E-1. 単体動作確認（Windows）

- [ ] `aidiy_hermes` を再起動して以下のコマンドが 5 秒以内に成功すること
  - [ ] `pwd`
  - [ ] `ls -la`
  - [ ] `ls -la D:/OneDrive/_sandbox/AiDiy2026`
  - [ ] `test -e D:/OneDrive/_sandbox/AiDiy2026 && echo OK`
  - [ ] `cat .aidiy/knowledge/_index.md`（最初の数行が出ること）
- [ ] `read_file` ツールで `.aidiy/knowledge/_index.md` を読めること
- [ ] `search_files(target='files', pattern='*.md', path='backend_hermes')` で結果が返ること
- [ ] `search_files(target='content', pattern='def is_wsl', path='backend_hermes')` で結果が返ること
- [ ] `write_file` で一時ファイルを作成・削除できること
- [ ] `patch` で 1 行置換ができること

#### E-2. 統合動作確認（Windows）

- [ ] aidiy_hermes に「作業フォルダの中身を見せて」と依頼 → AI が search_files / read_file を使って正常に応答すること
- [ ] 「`.aidiy/knowledge/_index.md` を読んで要約して」と依頼 → 30 秒以内に応答すること
- [ ] 「`backend_hermes/cli_main.py` の最初の 50 行を表示して」と依頼 → 即時応答すること

#### E-3. 回帰テスト（Linux/macOS - もし可能なら）

- [ ] Linux/WSL 上で `aidiy_hermes` を起動し、`pwd`、`ls`、`read_file` 等が従来通り動くこと
  - 既存コードを `if os.name != 'nt':` で囲っただけなので、原理的には影響ゼロのはず
  - ただしインデント変更でシンタックスエラーが入っていないか目視確認

#### E-4. ロールバック手順の確保

- [x] 各フェーズの開始前に該当ファイルの **タイムスタンプ付きバックアップ** を `.aidiy/backup/winnt-migration/` に取る
- [ ] git で作業する場合は **フェーズ単位でコミット**（`feat(hermes): winnt phase A — env detection helpers` など）

---

## 4. 想定外の落とし穴チェック

実装中に遭遇しそうな罠を事前に列挙。Windows 経路を書く際は都度確認。

- [ ] **OneDrive のファイルロック**: `D:\OneDrive\...` 配下のファイルを `os.replace()` で原子書き込みすると OneDrive 同期と競合してアクセス拒否になることがある。リトライロジック（最大 3 回、間隔 100ms）を入れる
- [ ] **パスの大文字小文字**: Windows は大小文字を区別しないが、Hermes 内部で path を辞書キーに使っている箇所が dedup に影響する可能性。`Path.resolve()` で統一して比較
- [ ] **改行コード**: `read_file` は LF/CRLF 混在のファイルでも読めるよう `Path.read_text()` の `newline=None` を使い、戻り値では LF に統一
- [ ] **マルチバイト文字 (utf-8)**: Windows のデフォルト encoding は cp932 のことがある。**必ず `encoding='utf-8'` を明示**
- [ ] **長いパス制限**: Windows MAX_PATH 260 文字制限。長いパスを扱うときは `\\?\` プレフィックスを `Path` に渡す前に検討
- [ ] **シンボリックリンク / ジャンクション**: `Path.resolve()` がリパースポイントを辿る挙動の違い。テスト時に確認
- [ ] **stdout の encoding**: `subprocess.Popen(..., encoding='utf-8', errors='replace')` を必ず指定
- [ ] **環境変数の継承**: bash の `_make_run_env()` で `HOME` を勝手に書き換える箇所があるが、Windows ではそれを `USERPROFILE` から導出する必要があるか確認

---

## 5. 進捗メモ欄

各フェーズ完了時に日付と所感を記入していく。

| 日付 | フェーズ | 状況 | メモ |
|---|---|---|---|
| 2026-05-09 | A-1, A-2 | 完了 | `is_windows_native()` 追加、Windows shell 探索で Git Bash 優先 + PowerShell fallback 済み |
| 2026-05-09 | A-5, B, C, D | 完了 | `py_compile` 成功。`LocalEnvironment` 直接検証で `pwd`、`ls -la`、`test -e .` が 5 秒以内に成功。`WindowsFileOperations` 直接検証で read/search/write/patch が成功。 |
| 2026-05-09 | Git Bash 前提解除 | 完了 | Windows local shell 選択を Git Bash 優先 + PowerShell fallback に変更。PowerShell 強制経路で `pwd`、`ls -la`、`test -e . && echo OK`、`python --version` が成功。background process registry も同じ shell 選択を使うよう修正。 |
| 2026-05-09 | 統合確認 | 完了 | `uv run python cli_main.py --list-tools` 成功。実ツール経由で terminal / read_file / search_files / write_file / patch / background を確認。PowerShell 強制経路でも同一確認が成功。 |
| 2026-05-09 | Windows import 分離 | 完了 | `file_operations_win.py` / `file_tools_win.py` / `terminal_tool_win.py` / `process_registry_win.py` を Windows 分岐からのみ import する構成へ整理。通常側に `WindowsFileOperations` 本体を残さないよう移動し、PowerShell fallback の `ls ... | head -N` 変換も追加。 |
| 2026-05-09 | platform import selector | 完了 | `file_operations.py` / `file_tools.py` / `terminal_tool.py` / `process_registry.py` を薄い selector にし、Windows では `*_win.py`、非 Windows では `*_linux.py` のどちらか一方だけを import する構成に変更。`*_win.py` と `*_linux.py` は discovery から除外し、selector 経由で登録する。 |
| 2026-05-09 | Linux 側 original 化 | 完了 | `*_linux.py` から Windows 分岐、`*_win.py` import、`msvcrt` / `winpty` / `_IS_WINDOWS` 参照を削除し、POSIX 前提の直線的な実装へ戻した。 |
| 2026-05-09 | Windows 側専用化 | 完了 | `*_win.py` から Linux/POSIX 分岐、`ptyprocess` / `fcntl` / `termios` / process group 処理を削除。`file_operations_win.py` は `ShellFileOperations` を含めず `WindowsFileOperations` 単体にした。 |
| 2026-05-09 | 要件差分の解消 | 完了 | `file_operations_win.py` の lint 対象を `.py/.js/.ts/.go/.rs` に拡張。`file_tools_win.py` は Windows native local では `WindowsFileOperations`、remote/container backend では `ShellFileOperations` を使い、Linux 側と同じ file tool 要件を満たすよう調整。 |
| | | | |

---

## 6. 完了条件

以下が全てクリアされたら本対応は「完了」とする。

- [ ] フェーズ A〜D の全チェックボックスが完了
- [ ] フェーズ E-1, E-2 の動作確認が全て成功
- [ ] フェーズ E-3 の Linux 回帰テストで既存挙動に影響がないことを確認
- [x] CLAUDE.md または `backend_hermes/AGENTS.md` に「Windows ホストでの動作」セクションを追記
- [ ] ロールバック手順が文書化されている

---

## 7. 参考: 既に実施済みの修正（2026-05-08〜09）

- `backend_server/AIコア/AIコード_cli.py`: aidiy_hermes コマンド探索パスに `~/.local/bin/aidiy_hermes.cmd` を追加
- `backend_hermes/tools/environments/local.py`: Windows shell 探索を Git for Windows 優先 + WSL bash 除外に変更。その後 Git Bash が無い場合は PowerShell へフォールバックするよう変更
- `backend_hermes/base/hermes_constants.py`: `is_windows_native()` を追加
- `backend_hermes/core/prompt_builder.py`: `WINDOWS_NATIVE_SHELL_HINT` を追加し system prompt に注入
- `backend_hermes/tools/terminal_tool.py`: `TERMINAL_TOOL_DESCRIPTION` の Windows 注意書きを追加

これらは本作業の **フェーズ A の前段** として完了済み。
