# CodeCLI プロンプト整形と履歴保持

## このメモを使う場面
- `backend_server/AIコア/AIコード_cli.py` の system prompt や送信プロンプトの整形ロジックを修正するとき
- 履歴表示では改行を残したいが、CLI 引数へ渡す直前には 1 行化したいとき
- `None` と非文字列入力を同じ扱いにしてよいか判断するとき

## 実装の結論（関数と呼び出しパターン）

### `_CLI送信用テキスト正規化()`

```python
def _CLI送信用テキスト正規化(self, text: Optional[str]) -> str:
    if text is None:
        return ""
    if not isinstance(text, str):
        raise TypeError(f"CLI送信用テキストは文字列である必要があります: {type(text).__name__}")
    return text.replace('\n', ' ').replace('\r', ' ').strip()
```

- `None` は未設定値として空文字へ変換する（呼び出し元の省略を許容）
- `int`, `list` など非文字列は `TypeError` — 呼び出し元の不整合として扱う
- 改行・復帰を空白に変換して `strip()` するだけ。CLIの引数に渡せる 1 行になる

### `_コマンド構築()` での呼び出し箇所

```python
def _コマンド構築(self, プロンプト: str, 初回: bool = False, repo_path: str = None, 読取専用: bool = False) -> list:
    # ← ここで 1 行化する（システムプロンプト構築時には 1 行化しない）
    プロンプト = self._CLI送信用テキスト正規化(プロンプト)

    if self.code_ai == "claude_cli":
        common = [cmd, "--allow-dangerously-skip-permissions", "--permission-mode", "bypassPermissions", "--chrome"]
        if 初回:
            return common + ["-p", プロンプト]
        else:
            return common + ["--continue", "-p", プロンプト]
    # copilot_cli / gemini_cli / codex_cli / hermes_cli も同様のパターン
```

### `_システムプロンプト構築()`

```python
def _システムプロンプト構築(self) -> str:
    # 複数行のまま返す（1行化しない）
    base_prompt = self.system_instruction.strip() if self.system_instruction else "あなたは賢いコードエージェントです。"
    # OS に応じた補足を末尾に付加（hermes_cli は WSL 向け文言）
    # suffix は OS 判定後に設定される文字列変数（例: "WSL2 環境で実行..." など）
    return f"{base_prompt}\n{suffix}" if suffix else base_prompt
```

システムプロンプトは履歴やデバッグ表示で読む機会があるため、構築時点では改行を保持する。

## 修正内容
- `_CLI送信用テキスト正規化()` は `None` のときだけ空文字を返し、`int` や `list` など文字列以外は `TypeError` にする方針へ変更した
- `_システムプロンプト構築()` は system prompt をその場で 1 行化せず、複数行のまま返すように変更した
- 実際の CLI 送信時は `_コマンド構築()` 冒頭で `_CLI送信用テキスト正規化()` を通すため、送信前にだけ 1 行化される

## 関連ファイル
- `backend_server/AIコア/AIコード_cli.py`

## 関連箇所
- `_CLI送信用テキスト正規化()`
- `_システムプロンプト構築()`
- `_コマンド構築()`
- system prompt を履歴へ追加する箇所

## 実装や運用の結論
- 保持用テキストと送信用テキストは分けて考える
- 履歴やデバッグ表示で読みやすさが必要な情報は、構築時点では改行を保持してよい
- CLI 引数へ渡す直前だけ改行・復帰を空白へ置換して 1 行化する
- 入力が `None` なのか、想定外型なのかは切り分ける。前者は未設定値、後者は呼び出し側の不整合として扱う

## 次回の注意点
- `_システムプロンプト構築()` で早期に 1 行化すると、履歴表示やデバッグ出力が読みにくくなりやすい
- `_CLI送信用テキスト正規化()` を厳格化した場合、既存呼び出し側で非文字列を渡していないか確認する
- 例外化した場合は、呼び出し元が握りつぶして空文字化していないかも確認する
- system prompt を変更したときは、初回送信・継続送信・履歴再利用の 3 経路で整合が取れているかを見る

## 最低限の確認方法
- `python3 -m py_compile backend_server/AIコア/AIコード_cli.py` が通る
- 初回送信時に `self.system_prompt` が複数行のまま保持されることを確認する
- `_コマンド構築()` に渡る直前のプロンプトが 1 行化されることを確認する
- `None` は空文字、非文字列は例外になることをテストで確認する
