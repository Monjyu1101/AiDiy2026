# AIモデル設定変更手順

## このメモを使う場面
- 使用する AI モデル（Claude / Gemini / OpenAI など）を変更したい
- `AiDiy_key.json` に新しい API キーを設定したい
- 設定 UI から AI モデルを切り替えたい

## 関連ファイル
- `backend_server/_config/AiDiy_key.json` — API キーと現在の AI モデル設定（**正マスタ**）
- `backend_server/conf/conf_json.py` — JSON 読み書き、不足キーの自動補完
- `frontend_avatar/src/api/config.ts` — `defaultModelSettings()`（backend 取得前のフォールバック）
- `frontend_avatar/src/dialog/AI設定再起動.vue` — 設定変更 UI（モデル選択 + 再起動トリガー）
- `backend_server/core_router/AIコア/AIセッション管理.py` — モデル設定の初期化

## AI モデル命名規則（必須）

| キー | 末尾ルール | 正しい例 | 誤りの例 |
|------|-----------|---------|---------|
| `CHAT_AI_NAME` | `_chat` | `gemini_chat`, `openrt_chat`, `freeai_chat` | `gemini`, `claude_chat_v2` |
| `LIVE_AI_NAME` | `_live` | `gemini_live`, `openai_live` | `gemini` |
| `CODE_AI1_NAME`〜`CODE_AI4_NAME` | `_sdk` または `_cli` | `claude_sdk`, `copilot_cli`, `codex_cli` | `claude`, `claude_code` |

**比較は完全一致のみ**（`startswith` 等の前方一致は使用禁止）。

## 設定変更の手順

### AiDiy_key.json を直接編集する場合

```json
{
  "CLAUDE_KEY": "sk-ant-...",
  "GEMINI_KEY": "AIza...",
  "OPENAI_KEY": "sk-...",
  "CHAT_AI_NAME": "gemini_chat",
  "LIVE_AI_NAME": "gemini_live",
  "CODE_AI1_NAME": "claude_sdk",
  "CODE_AI2_NAME": "copilot_cli",
  "CODE_AI3_NAME": "codex_cli",
  "CODE_AI4_NAME": "gemini_cli"
}
```

変更後はバックエンドを再起動する（`echo. > backend_server/temp/reboot_core.txt`）。

### 設定 UI から変更する場合

`frontend_avatar` の設定ダイアログ（`AI設定再起動.vue`）から変更すると、  
`POST /core/AIコア/モデル設定/更新` API 経由で `AiDiy_key.json` が書き換えられ自動再起動される。

### 設定ダイアログの呼び出し経路

- Electron: core ウィンドウから `window.desktopApi.openSettingsWindow(sessionId)` を呼び、`settings:open` IPC で専用 `settings` ウィンドウを開く
- Web: `AiDiy.vue` 内で `AI設定再起動.vue` をモーダル表示する
- settings ウィンドウは `onSettingsPrepare()` で sessionId を受け取るため、sessionId が空の状態で開かないようにする

Electron 専用ウィンドウとして設定画面を直す場合でも、Web モードのモーダル表示が同じコンポーネントを使う。`window.desktopApi` 前提の処理を `AI設定再起動.vue` に直接入れない。

## デフォルト設定との整合

`config.ts` の `defaultModelSettings()` は backend から設定を取得する前のフォールバック値。  
ここの `CODE_AI*_NAME` の値が `_sdk`/`_cli` サフィックスになっていないとバックエンド側ハンドラと不一致になる。  
→ `conf_json.py` のデフォルト値と完全一致させること。

## available_models の取得フロー

1. frontend が `/core/AIコア/モデル情報/取得` を呼び出す
2. backend が現在設定と利用可能モデル一覧を返す
3. `AI設定再起動.vue` が `availableModels` を更新し、チャット・ライブ・コード用の選択肢を生成する
4. 保存時に `/core/AIコア/モデル設定/更新` へ送信し、`AiDiy_key.json` を更新する
5. 更新後は Reboot 機構で core server を再起動し、次回接続から新設定を使う

### 選択肢の生成ルール

- チャット AI 選択肢: `available_models.chat_models` のキー
- ライブ AI 選択肢: `available_models.live_models` のキー
- ライブ voice 選択肢: `available_models.live_voices[選択中LIVE_AI_NAME]`
- コード AI 選択肢: `available_models.code_models` のキー
- 各モデル選択肢: 選択中 AI 名に対応するモデル辞書

frontend の `CHAT_MODEL_KEYS` / `LIVE_MODEL_KEYS` / `LIVE_VOICE_KEYS` / `CODE_MODEL_KEYS` は、選択中 AI 名から保存キーへ変換する辞書。新しい AI 名を追加するときは、backend が返す `available_models` のキー名と、この辞書のキー名を完全一致させる。

`CODE_AI1_MODEL`〜`CODE_AI4_MODEL` は選択スロットごとの現在モデルとして保存される。一方で `CODE_CODEX_CLI_MODEL` のような CLI 種別別モデルキーもあるため、追加時は「スロット設定」と「CLI 種別別デフォルト」を混同しない。

## 実装の結論

- `AiDiy_key.json` を正マスタとし、frontend の `defaultModelSettings()` は取得前フォールバックとして扱う
- AI 種別名は完全一致で判定するため、`_chat` / `_live` / `_sdk` / `_cli` のサフィックスを崩さない
- Code CLI を増やした場合は、backend のモデル定義、設定 JSON、frontend の `CODE_MODEL_KEYS` を合わせて更新する
- 設定変更後は既存 WebSocket セッションに即時完全反映される前提にしない。Reboot 後の再接続で新設定を確認する

## 確認方法

`GET http://localhost:8091/core/AIコア/モデル情報/取得`（要認証）で現在の設定と利用可能モデル一覧を確認する。
