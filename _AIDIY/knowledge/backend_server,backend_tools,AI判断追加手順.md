# AI判断の利用とプロバイダ追加

> 文書: `backend_server,backend_tools,AI判断追加手順.md` | 実装: `backend_server/AIコア/AI判断.py`, `backend_server/AIコア/AI判断共通.py`, `backend_server/AIコア/AI判断_openai_decisions.py`, `backend_server/AIコア/AI判断_openai_jsonchat.py`, `backend_tools/tools_proc/tools_decisions.py`

## このメモを使う場面

- 真偽の確率・選択・段階評価をMCPまたはHTTPから取得する。
- Decisions APIとOAuth Responsesの接続・応答形式を確認する。
- 判断用プロバイダやモデルを追加する。

## 構成と切り替え

判断ロジックと入力・応答検証は `backend_server/AIコア/AI判断*.py` に置く。`backend_tools/tools_proc/decisions_check.py` はインポートの接続、`tools_decisions.py` はMCP / HTTPの公開だけを担当する。会話履歴やツール呼び出しは持たない。

| model指定 | 実装 | 通信・認証 |
|---|---|---|
| `openai_decisions/gpt-6-luna` | `AI判断_openai_decisions.py` | `https://api.openai.com/v1/decisions`、`openai_key_id` |
| `openai_oauth/gpt-6-luna` | `AI判断_openai_jsonchat.py` | `https://chatgpt.com/backend-api/codex/responses`、Codex OAuth |

`openai_jsonchat` は `openai_oauth` の別名として受け付ける。`ai_name` / `ai_model` での個別指定も可能。結合形式との矛盾や未知のプロバイダはエラーにする。明示指定した方式から別方式へ自動フォールバックしない。

プロバイダ未指定（空欄 / `auto`）では、起動チェックに成功した `openai_oauth` を優先し、利用不可なら成功した `openai_decisions` を使う。利用可否未確認の直接利用時は `DECISION_AI_NAME` を参照する。実行中の通信エラーによる再送・方式変更は行わない。

モデルの `auto` は選択方式の設定済み既定モデルを使う。設定自体も空欄 / `auto` ならプロバイダ定義の既定値（現在は `gpt-6-luna`）を使う。CLIと異なりAPIにはモデル名が必須なので、省略せず具体名を送る。`decisions_config.default_model` で自動選択先を確認できる。

`AiDiy_key.json` の設定は `conf/conf_json.py` の既定値と同期する。

| キー | 既定値 |
|---|---|
| `DECISION_AI_NAME` | `openai_oauth` |
| `DECISION_OPENAI_MODEL` | `gpt-6-luna` |
| `DECISION_OAUTH_MODEL` | `gpt-6-luna` |

OAuthは既存の `AIチャット_openai._oauth_access_token` を呼び、Hermes / Codex共有ストアの更新処理・排他制御を共用する。トークンを独自保存しない。backend_server / backend_tools の環境には `httpx` と、Hermes設定読込用の `PyYAML` が必要。

## 起動時の利用可否チェック

`backend_tools/tools_main.py` のFastAPI lifespanで `Decision.check_availability()` を1回実行する。モジュールimport時やbackend_serverの起動時には重複実行しない。

- 各プロバイダの既定モデルに「おはよう」を渡し、`choice` で「挨拶 / その他」へ分類する。共通の応答検証を通過し「挨拶」が返れば利用可能とする。
- APIキーが空欄・空白・`<`始まりのひな形・空引用符（`""` / `“”`等）の場合は、通信せず利用不可にする。OAuthはキーの有無で判定せず実行確認する。
- 方式ごとに最大15秒、並行してチェックする。認証・課金・通信・JSON形式の失敗、回答拒否、期待結果の不一致は利用不可。失敗しても他MCPの起動を止めない。
- 起動ログに方式・モデル・利用可能/不可・理由を出す。`decisions_config` とHTTP `/config` の `availability` に `ok/model/reason/answer/checked_at/elapsed_ms`、`available_models` に成功したモデルを返す。未実行時は `availability_checked=false`。
- 結果は起動チェック時点のモデルについてのスナップショット。認証情報を返したり保存したりしない。設定変更後は再起動で再確認する。
- 1方式以上が成功した場合だけMCP実行ツール `decisions_check` を公開する。全方式が利用不可（または未確認）の場合は実行ツールを非公開とし、`decisions_config` だけを残す。設定JSON・MCP接続先は維持し、接続初期化の `instructions` と設定取得の `status=NG` / `available=false` / `message` で「現在利用不可」を返す。理由は `availability` で確認できる。
- 全方式が利用不可の場合、HTTP `/check` も503と `status=NG` を返し、判断APIを呼ばない。HTTP `/config` は200で診断結果を返す。再起動チェックで1方式以上が成功すると実行ツールを再公開する。

## 呼び出し方

- MCPサーバー: `aidiy_decisions_check`
- MCPツール: `decisions_check` / `decisions_config`
- HTTP実行: `POST /aidiy_decisions_check/check`
- 設定: `GET` または `POST /aidiy_decisions_check/config`
- 引数仕様: `GET /aidiy_decisions_check/docs` / `GET /aidiy_decisions_check/list`
- MCP接続: `/aidiy_decisions_check/sse` と `/aidiy_decisions_check/mcp`。stdioは既存の `mcp_stdio.py` を使用。

```python
import requests

response = requests.post(
    "http://127.0.0.1:8095/aidiy_decisions_check/check",
    json={
        "model": "openai_oauth/gpt-6-luna",
        "input": "商品の外箱が破損しています。",
        "questions": [
            {"type": "predicate", "name": "damage", "instructions": "破損の報告ですか？"}
        ],
        "timeout_sec": 60,
    },
    timeout=70,
)
response.raise_for_status()
answers = response.json()["data"]["answers"]
```

`model` を `openai_decisions/gpt-6-luna` に替えるだけでDecisions APIへ切り替わる。backend_server内では `from AIコア.AI判断 import Decision` として `await Decision().実行({...})` を呼ぶ。

## 共通契約

質問には一意の `name` と `instructions` を指定する。

| type | 追加の質問項目 | 回答 |
|---|---|---|
| `predicate` | なし | `probability`（0～1） |
| `choice` | `choices: [{value, description}]`（2件以上） | `choice`, `probabilities: [{value, probability}]`, `confidence` |
| `score` | `levels: [{label, description}]`（2件以上、低→高） | `score`, `probabilities: [{value, label, probability}]`, `confidence` |

`score` の `value` は0始まりの段階番号、`score` は確率加重平均。拒否は `type: refusal` として返す。`input` はテキスト、または `role: user` のメッセージ配列。画像は `input_image.image_url` にインラインbase64のdata URLを指定し、外部URL・ファイルIDは受け付けない。

成功レスポンスは `status/message/data`、`data` に `ai_name`, `ai_model`, `model`, `method`, `answers`, `usage`, `elapsed_ms` を持つ。`answers` は質問順へ整列する。

OAuth側は Responses の `text.format.type=json_schema`, `strict=true` を使う。両経路とも回答名・型・候補の一致、確率の範囲と合計、段階評価の加重平均を検証する。JSON不正・途中切断・タイムアウト・未完了は成功として返さない。HTTP入力不正は422、処理エラーは400と `status=NG`。MCPではToolErrorを返す。

互換なのは入出力形式である。OAuth側の確率・confidenceは生成モデルの推定値で、Decisions APIと同じ校正値や実測頻度を保証しない。方式別に閾値を評価する。`method` は `decisions_api` または `responses_json_schema`。

## プロバイダ・モデル追加

1. `AI判断_<方式>.py` に `DecisionAI` クラスを実装する。`method` と非同期 `実行(request, model, config, client)` を持ち、`answers` 配列を返す。
2. `AI判断.py` の `PROVIDERS` にモジュール、モデル設定キー、既定モデル、認証方式、必要な別名を追加する。APIキー方式は `api_key_field` に設定キー名を指定すると、起動時の未設定判定を共用できる。
3. `conf_json.DEFAULT_CONFIG` にモデルの既定値を追加する。モデル単体の追加は登録表を変更せず、`model` 指定または設定値の変更で利用できる（利用可否はプロバイダ側が判定）。
4. 共通応答のテストと、方式固有の認証・通信・異常終了のテストを追加する。MCP / HTTP入口への方式別分岐追加は不要。

## 確認方法

```powershell
backend_tools/.venv/Scripts/python.exe -m unittest discover -s backend_server/tests -p test_decisions.py -v
backend_tools/.venv/Scripts/python.exe -m unittest discover -s backend_tools/tests -p test_decisions_check.py -v
backend_tools/.venv/Scripts/python.exe -m unittest discover -s backend_tools/tests -p test_platform_registration.py -v
```

実接続では同一入力と3種の質問を両方式に送り、名前・型・候補が一致することを確認する。数値の完全一致は要件にしない。APIキー・OAuthトークンを出力に残さず、認証エラーと入力不正を区別して確認する。

参考: [Decisions API](https://developers.openai.com/api/docs/guides/decisions)、[Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs)。
