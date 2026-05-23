# antigravity_cli タイムアウトと継続オプション

> 文書: `backend_server,antigravity_cliタイムアウトと継続オプション.md` | 実装: `backend_server/AIコア/AIコード_cli.py`

## このメモを使う場面

- `antigravity_cli` (agy) のコマンドライン引数やパス解決を変更・修正する
- `antigravity_cli` のタイムアウト延長や継続フラグの動作を理解する
- Code AI 設定で `antigravity_cli` を選んだときの挙動を調整する

## パス解決

`_コマンドパス取得()` 内の `antigravity_cli` 専用分岐:

```python
if self.code_ai == "antigravity_cli":
    if os.name == 'nt':
        userprofile = os.environ.get('USERPROFILE', os.path.expanduser('~'))
        candidate = os.path.join(userprofile, 'AppData', 'Local', 'agy', 'bin', 'agy.exe')
        if os.path.isfile(candidate):
            return candidate
    return "agy"
```

探索順:
1. `%USERPROFILE%\AppData\Local\agy\bin\agy.exe` (Windows ローカルインストール)
2. `agy` (PATH 依存フォールバック)

## コマンド構築パターン

`_コマンド構築()` 内の `antigravity_cli` 専用分岐:

```python
elif self.code_ai == "antigravity_cli":
    # Antigravity CLI (agy) — claude 互換インターフェース
    common = list(base)
    if self.code_permissions != "none":
        common.append("--dangerously-skip-permissions")
    if repo_path:
        common.extend(["--add-dir", repo_path])
    # --print-timeout: デフォルト5分を20分に延長
    common.extend(["--print-timeout", "20m"])
    if 初回:
        return common + ["-p", プロンプト]
    else:
        # -c (--continue) は -p の後ろに付ける（opencode_cli と同様）
        return common + ["-p", プロンプト, "-c"]
```

### タイムアウトの延長
デフォルトのタイムアウト時間 `5m0s`（5分）から `--print-timeout 20m` を指定して20分に延長しています。これは、大規模なファイル変更や複雑な処理を伴う場合にタイムアウトが発生するのを防ぐためです。

### 継続会話（-c フラグ）の位置
`agy` の引数解析において、継続会話を示す `-c` フラグは `-p`（およびプロンプト）の後に付与する必要があります。
- 初回: `agy -p "プロンプト"`
- 継続: `agy -p "プロンプト" -c`

## 注意点

- `agy` は Go の標準フラグ解析機能を使用しており、オプションフラグの解析が厳密です。位置引数やフラグの指定順序が正しくない場合、引数解析エラー (`flag provided but not defined` 等) になる可能性があるため注意が必要です。
- `-c`（または `--continue`）フラグは `-p`（プロンプト）の後方に付与することで、前回の会話コンテキストを正しく引き継ぎます。
- タイムアウト値 `"20m"` は Go の duration 形式であり、正しく解釈されます。
