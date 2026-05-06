# Provider 一覧と選択ロジック

> 文書: `backend_hermes,Provider一覧と選択ロジック.md` | 実装: `backend_hermes/cli_main.py`, `backend_hermes/hermes_cli/providers.py`

## このメモを使う場面

- 新しい AI provider を追加するとき
- provider 選択の優先順位や自動検出ロジックを変更するとき
- `/model` コマンドの interactive picker を調整するとき
- 認証情報（API Key/OAuth）の解決方法を確認するとき

## Provider 解決優先順位

`cli_main.py` では以下の優先順位で provider を決定します。

```
1. --provider CLI フラグ
2. config.yaml の model.provider
3. HERMES_INFERENCE_PROVIDER 環境変数
4. "auto"（runtime 自動検出）
```

`auto` の場合、`_ensure_runtime_credentials()` が環境変数や設定ファイルから認証情報を検出し、利用可能な provider を自動選択します。

## Provider Overlay 一覧

`hermes_cli/providers.py` の `HERMES_OVERLAYS` で 31 の provider が定義されています。各 overlay は transport、auth type、env var を指定します。

| カテゴリ | Provider |
|---------|----------|
| 汎用 API | `openrouter`, `nous`, `openai-codex` |
| 中国系 | `qwen-oauth`, `stepfun`, `minimax`, `minimax-oauth`, `minimax-cn`, `deepseek`, `alibaba`, `alibaba-coding-plan`, `xiaomi`, `tencent-tokenhub` |
| Google | `google-gemini-cli` |
| Microsoft | `copilot-acp`, `github-copilot`, `azure-foundry` |
| Anthropic | `anthropic` |
| コミュニティ | `lmstudio`, `zai`, `kimi-for-coding`, `vercel`, `opencode`, `opencode-go`, `kilo`, `huggingface`, `xai`, `nvidia`, `arcee`, `gmi`, `ollama-cloud`, `bedrock` |

## Alias 解決

50 以上のエイリアスが `ALIASES` 辞書に定義されています。フレンドリ名（`claude`, `grok`, `qwen` など）を canonical ID にマッピングします。`cli_main.py` の `process_command()` で `/model claude` のように使えます。

## Interactive Picker（/model コマンド）

`/model` を引数なしで実行すると、2 段階の picker が起動します。

```
Step 1: Provider 選択
  → list_authenticated_providers() で認証済み provider のみ表示
  → キーボード上下 + Enter で選択

Step 2: Model 選択
  → 選択した provider の curated model 一覧から選択
```

`list_authenticated_providers()` は各 provider の認証情報（API Key の有無、OAuth トークン）をスキャンし、利用可能なものだけを表示対象とします。

## 新しい Provider 追加手順

1. `hermes_cli/providers.py` の `HERMES_OVERLAYS` にエントリ追加
2. 必要に応じて `ALIASES` にエイリアス追加
3. `cli_main.py` の `list_authenticated_providers()` で認証チェック処理を追加
4. `backend_server/conf/conf_model.py` でモデル一覧取得が必要なら追記

## 注意点

- **認証情報の優先順位**: 環境変数 > config.yaml > ハードコード。新規 provider 追加時は env var 名を統一すること
- **Aggregator provider**: `openrouter`, `nous`, `vercel`, `kilo`, `opencode` はマルチモデルルーター。`auto` 検出時はこれらの優先度が高い
- **auto 検出のタイミング**: `_ensure_runtime_credentials()` は初回推論時まで遅延される。起動時には実行されない
