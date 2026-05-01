# AIコードパネル拡張手順（パネル数変更）

## 目的

コードAIパネルの数を増減させる（既定 4→6 への拡張実績あり）。

## 修正が必要な全レイヤー

### 1. 設定ファイル（backend_server）

| ファイル | 変更内容 |
|---------|---------|
| `_config/AiDiy_key.json` | `CODE_AI<N>_NAME` / `CODE_AI<N>_MODEL` を追加 |
| `conf/conf_json.py` DEFAULT_CONFIG | 同キーを追加 |
| `conf/conf_json.py` `_apply_code_ai_auto()` | ループ範囲を `range(2, N+1)` に変更 |

### 2. バックエンドセッション管理（backend_server/AIコア/）

| ファイル | 変更内容 |
|---------|---------|
| `AIセッション管理.py` `初期モデル設定生成()` | CODE_AI<N>_NAME/MODEL を追加 |
| `AIセッション管理.py` `モデル設定正規化()` | ループ範囲を `range(1, N+1)` に変更 |

### 3. バックエンドルーター（backend_server/core_router/）

| ファイル | 変更内容 |
|---------|---------|
| `AIコア.py` の `コードチャンネル一覧` | `"<N>"` を追加 |
| `AIコア.py` の `数値チャンネル一覧` | `"<N>"` を追加 |
| `AIコア.py` の `許可キー` set | `CODE_AI<N>_NAME` / `CODE_AI<N>_MODEL` を追加 |
| `AIコア.py` の `range(1, N)` ループ（2箇所） | N+1 に変更 |
| `AIコア.py` の `code_agent_processors` 長さチェック | `!= N` に変更 |

### 4. バックエンド AI 処理（backend_server/AIコア/）

| ファイル | 変更内容 |
|---------|---------|
| `AIストリーミング処理.py` の `range(1, N)` | N+1 に変更 |
| `AI内部ツール.py` のチャンネルバリデーション | `[1, ..., N]` に変更、エラーメッセージの範囲も更新 |

### 5. フロントエンド Web（frontend_web）

| ファイル | 変更内容 |
|---------|---------|
| `AiDiy.vue` PanelKey 型 | `'code<N>'` を追加 |
| `AiDiy.vue` チャットモード型 | `'code<N>'` を追加 |
| `AiDiy.vue` PANEL_KEYS | `'code<N>'` を追加 |
| `AiDiy.vue` パネル状態生成/モデル設定/ボタン状態 | code<N> を追加 |
| `AiDiy.vue` テンプレート | code<N> の Transition + AIコアコード ブロックを追加 |
| `dialog/AI設定再起動.vue` selections | codeAi<N>/codeModel<N> を追加 |
| `dialog/AI設定再起動.vue` computed options | codeModelOptions<N> を追加 |
| `dialog/AI設定再起動.vue` loadConfig/buildNextSettings | code<N> の読み書きを追加 |
| `dialog/AI設定再起動.vue` テンプレートUI | CODE_AI<N>_NAME / CODE_MODEL<N> の select 行を追加 |
| `compornents/AIコア.vue` PanelKey 型 | `'code<N>'` を追加 |
| `compornents/AIコア.vue` テンプレートボタン | コード<N> ボタンを追加 |
| `compornents/AIチャット.vue` 型/選択モード/emit | `'code<N>'` を追加 |
| `compornents/AIチャット.vue` テンプレートラジオ | Code<N> ラジオを追加 |

### 6. フロントエンド Avatar（frontend_avatar）

| ファイル | 変更内容 |
|---------|---------|
| `types.ts` ModelSettings | CODE_AI<N>_NAME を追加 |
| `api/config.ts` defaultModelSettings() | CODE_AI<N>_NAME を追加 |
| `AiDiy.vue` PanelKey/WindowRole/チャットモード型 | `'code<N>'` を追加 |
| `AiDiy.vue` PANEL_KEYS | 追加 |
| `AiDiy.vue` コードAI名/コードチャンネル/コードモデル | case追加 |
| `AiDiy.vue` ソケット状態/モデル設定初期化 | 追加 |
| `dialog/AI設定再起動.vue` | Web版と同様の selections/options/loadConfig/buildNextSettings/テンプレート追加 |
| `components/AIコア.vue` PanelKey 型 + テンプレートボタン | 追加 |
| `components/AIチャット.vue` チャットモード型 + ラジオ | 追加 |
| `electron/main.ts` PanelKey/PANEL_BOUNDS/panelStates/orderMap | 追加 |
| `electron/preload.ts` PanelKey | 追加 |

## 関連: フロント設定UIの構成変更

`AI設定再起動.vue` のレイアウトを変更する場合のパターン:

- **4カテゴリ構成**: Chat AI Model / Live AI Model / Code AI Setting / Code AI Model
- **Code AI Model は左右2列**: `.config-panel-code-grid` で `grid-template-columns: 1fr 1fr`、左列に1/2/3、右列に4/5/6
- **AI1変更時はAI2-6にコピー**: watch 内のコピー対象を全て更新する（6を忘れやすい）
- **コードラジオボタンは2列4行グリッド**: `.mode-grid` で `grid-template-columns: 1fr 1fr`、順序は Chat/Code3, Live/Code4, Code1/Code5, Code2/Code6

## 注意点

- `backend_server/conf/conf_json.py` の `_apply_code_ai_auto()` は「NAMEが`auto`の場合に CODE_AI1_NAME の値をコピー」する。範囲が狭いと新規パネルが auto のままで埋まらないため、ループ範囲の更新を忘れない。
- `frontend_web` のグリッドレイアウトCSSは既に `layout-multi`（5-6枚以上）に対応済み。新しいパネル数に対応するCSSクラスが必要なら追加する。
- `frontend_avatar` の Electron モードでは `electron/main.ts` の `PANEL_CREATION_ORDER`（無ければ `Object.keys(panelStates)` を forEach）で全パネルが列挙されていることを確認する。
- `frontend_avatar` Web モードのタブ一覧は `AiDiy.vue` 内の `webTabs` 配列で定義されている（該当箇所を確認して追加）。
- バックエンドの `AiDiy_key.json` にキーを追加した後、サーバー再起動（または reboot ファイル作成）が必要。
- フロントエンドの変更後は型チェック（`npm run type-check`）を必ず実行する。特に `AIチャット.vue` の defineProps/defineEmits の union 型はコンパイルエラーになりやすい。
