# frontend_avatar 変更チェック

> 文書: `frontend_avatar,変更チェック.md` | 実装: `frontend_avatar/src/AiDiy.vue`, `frontend_avatar/src/components/AIコア.vue`, `frontend_avatar/electron/main.ts`

## このメモを使う場面

- `frontend_avatar` の Electron / Web 両対応を崩さず修正する。
- WindowRole、PanelKey、IPC、WebSocket、VRM、音声、モデル設定を変更する。
- Electron だけ、または Web だけで発生する不具合を切り分ける。

## 関連ファイル

- `frontend_avatar/electron/main.ts`
- `frontend_avatar/electron/preload.ts`
- `frontend_avatar/src/AiDiy.vue`
- `frontend_avatar/src/env.d.ts`
- `frontend_avatar/src/api/config.ts`
- `frontend_avatar/src/api/client.ts`
- `frontend_avatar/src/api/websocket.ts`
- `frontend_avatar/src/components/AiDiy/`
- `frontend_avatar/src/dialog/AI設定再起動.vue`

## Electron / Web の前提

| 項目 | Electron | Web |
|------|----------|-----|
| 判定 | `!!window.desktopApi` | `!window.desktopApi` |
| 認証 storage | `localStorage` | `sessionStorage` |
| パネル | BrowserWindow + IPC | 右ペインのタブ |
| 状態同期 | BroadcastChannel + IPC | BroadcastChannel / 単一タブ内 state |
| API | Vite proxy または config | Vite proxy / 動的 URL |

修正後は Electron と Web の両方を確認する。

## WindowRole / PanelKey を増やす場合

連動修正:

- `electron/main.ts` の `WindowRole` / `PanelKey`
- `electron/preload.ts` の公開 API 型
- `src/env.d.ts`
- `src/AiDiy.vue` の `PanelKey`、タイトル、表示制御、`PANEL_KEYS`
- `AIコア.vue` のボタンやタブ表示
- snapshot の `buildSnapshot()` と受信側反映

## パネル表示を変える場合

確認箇所:

- `electron/main.ts` の `panelStates`
- `setPanelVisibility()`
- `createPanelWindow()`
- `closePanelWindow()`
- `panel:toggle`
- `panel:apply-states`
- `src/AiDiy.vue` の `アクティブタブ`
- BroadcastChannel `avatar-desktop-sync`

Web では IPC がないため、必ず `isElectron` 分岐と fallback を確認する。

## IPC を追加する場合

最小セット:

1. `electron/main.ts` に `ipcMain.handle(...)` を追加する。
2. `electron/preload.ts` の `desktopApi` に公開する。
3. `src/env.d.ts` に型を追加する。
4. renderer 側では `window.desktopApi?.xxx` の optional chaining で呼ぶ。
5. Web モードで `desktopApi` 不在でも落ちないことを確認する。

詳細は `ElectronIPC追加手順.md` を使う。

## 接続まわりを変える場合

確認箇所:

- `src/api/config.ts`
- `src/api/client.ts`
- `src/api/websocket.ts`
- backend の `/core/AIコア/ws/*`
- Vite proxy。

WebSocket packet は `AIコアWebSocket仕様.md` を確認する。

## モデル設定を変える場合

- `CHAT_AI_NAME` は `_chat` 末尾。
- `LIVE_AI_NAME` は `_live` 末尾。
- `CODE_AI*_NAME` は原則 `_sdk` または `_cli`、例外として `aidiy_hermes` を許容する。
- 比較は完全一致を使い、`startswith` に寄せない。
- backend の `_config/AiDiy_key.json`、`conf_model.py`、`AIセッション管理.py` と整合させる。

詳細は `AIモデル設定変更手順.md` と `AIコードパネル拡張手順.md` を使う。

## アバター演出を変える場合

確認箇所:

- `AIコア_アバター.vue`
- `AIコア_自立身体制御.ts`
- `AIコア_自動カメラワーク.ts`
- `WindowShell.vue`
- `style.css`

透明ウィンドウでは Electron の `transparent`、renderer 背景、補助 UI、字幕、発光要素が重なるため、1箇所だけの修正で完結しない。

詳細は `アバター表示とVRMA.md` と `VRM_VRMA追加手順.md` を使う。

## 音声を変える場合

確認箇所:

- `AIコア_音声処理.ts`
- `AudioController`
- `input_audio`
- `output_audio`
- `cancel_audio`
- AudioContext resume。

詳細は [`backend_server,frontend_avatar,AI音声処理.md`](./backend_server,frontend_avatar,AI音声処理.md) を使う。

## よくある問題

| 症状 | 確認先 |
|------|--------|
| 401 | token storage、`認証延長ルール.md` |
| 音声が出ない | speaker 有効、AudioContext、audio WebSocket |
| マイクが使えない | Electron 権限、audio socket |
| 補助パネルが同期しない | BroadcastChannel snapshot |
| 透明ウィンドウが不自然 | `WindowShell.vue`、`AIコア_アバター.vue`、CSS |
| デスクトップキャプチャできない | `desktop:set-source`、source 選択 |
| Web モードでセッションが消える | `sessionStorage` の仕様 |
| Web モードでパネルが開かない | IPC ではなく `アクティブタブ` 分岐 |
| WebSocket が繋がらない | Vite proxy と WebSocket URL 解決 |

## Electron 設定ウィンドウのサイズ調整

設定ウィンドウ (`AI設定再起動.vue` / settings role) は Electron では独立 BrowserWindow で表示される。

| 調整箇所 | 説明 |
|----------|------|
| `electron/main.ts` の `SETTINGS_BOUNDS` | 初期サイズ (`width`, `height`) と最小サイズ (`minWidth`, `minHeight`) |
| `src/dialog/AI設定再起動.vue` の `.config-panel` | `max-width: 720px` で幅を制限 (AiDiy.vue の `settings-window-root :deep` で上書き) |
| `src/dialog/AI設定再起動.vue` の `@media` | avatar 版では `max-width: 500px` に変更 (元 1000px だと常時1カラムになるため) |
| `src/dialog/AI設定再起動.vue` の `.config-panel-field` | `grid-template-columns: 25% 1fr` でラベル幅を比率指定 (固定pxだと狭い時に2段になる) |

`SETTINGS_BOUNDS.width` は `.config-panel` の `max-width` と揃えること。不整合があるとウィンドウ枠が余る。

## 最小確認

- Electron で login / core / chat / file / image / code1〜code6 / settings を開ける。
- Web で `http://localhost:8092` を開ける。
- Electron と Web で storage の使い分けが崩れていない。
- WebSocket 接続、チャット送信、コード送信が通る。
- DevTools Console に `desktopApi` 未定義エラーがない。
- `npm run type-check` が通る。
