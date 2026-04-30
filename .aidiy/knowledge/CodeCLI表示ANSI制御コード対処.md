# CodeCLI表示ANSI制御コード対処

## このメモを使う場面

- AIコードパネルやチャット表示に `?[36m`、`?[0m`、`\x1b[36m` のような色制御コードが見える
- Hermes / Codex / Claude など CLI 系 CodeAI の出力を AiDiy の WebSocket 表示へ流す処理を調整したい
- 過去履歴やストリーム出力に混ざった ANSI エスケープを表示直前で無害化したい

## 関連ファイル

- `backend_server/AIコア/AIコード_cli.py` — CLI subprocess 出力の取得・WebSocket送信
- `frontend_avatar/src/components/AIコード.vue` — コードパネルの出力表示
- `frontend_avatar/src/components/AIチャット.vue` — チャットパネルの出力表示
- `backend_hermes/tools/code_execution_tool.py` — Hermes `execute_code` の subprocess 出力取得
- `backend_hermes/tools/ansi_strip.py` — Hermes 側の ANSI 除去実装例

## 実装方針

- CLI subprocess の stdout / stderr は、WebSocket へ送る前に `AIコード_cli.py` で ANSI 制御コードを除去する
- subprocess 環境変数には `NO_COLOR=1`、`FORCE_COLOR=0`、`CLICOLOR=0`、`TERM=dumb` を渡し、CLI 側にもプレーン出力を促す
- 実際の ESC 文字が壊れて `?[36m` のように保存・表示されるケースがあるため、通常の ANSI 正規表現に加えて `?\[[0-9;:]*[A-Za-z]` 形式も除去対象にする
- フロント側でも `受信内容文字列()` で同じ除去を行い、既存履歴や別経路から混入した制御コードを表示直前に落とす
- Windows 上の subprocess 出力は既定の `cp932` に任せず、`encoding="utf-8"` と `errors="replace"` を明示する。子 Python には `PYTHONIOENCODING=utf-8:replace` を渡し、UTF-8 出力を正として扱う。
- stdout / stderr は `None` や `bytes` になる経路（timeout の部分出力など）を考慮し、JSON 化前に文字列へ正規化してから末尾制限・ANSI 除去を行う。

## 確認方法

```powershell
backend_server\.venv\Scripts\python.exe -m py_compile backend_server\AIコア\AIコード_cli.py
backend_hermes\.venv\Scripts\python.exe -m py_compile backend_hermes\tools\code_execution_tool.py
cd frontend_avatar
npm run type-check
```

小確認では、以下の両方が `--- Hermes ---` に戻ることを確認する。

```text
\x1b[36m--- Hermes ---\x1b[0m
?[36m--- Hermes ---?[0m
```

## 次回の注意点

- CLI ごとに色を止めるオプション名が違うため、個別オプション追加より共通の環境変数と表示側サニタイズを優先する
- `output_stream` と最終 `output_text` の両方に出るため、ストリーム送信前・戻り値作成前の共通箇所で除去する
- フロントの `textContent` は HTML としては安全だが、制御コード自体は見えることがあるため、表示直前の文字列正規化は残す
- `execute_code` で `UnicodeDecodeError` 後に `proc.stdout is None` となる二次エラーが出た場合は、`subprocess.run(text=True)` のエンコーディング未指定をまず疑う。
