# AI音声処理（AudioController）

> 文書: `backend_server,frontend_avatar,AI音声処理.md` | 実装: `frontend_avatar/src/components/AIコア_音声処理.ts`, `frontend_avatar/src/AiDiy.vue`

## このメモを使う場面
- マイク入力、スピーカー出力、ビジュアライザー、口パク連動を変更する
- 音声が出ない / マイクが使えない / AI 音声が二重に聞こえる問題を調査する
- 音声用 WebSocket と `AudioController` の責務分担を確認する

## 関連ファイル
- `frontend_avatar/src/components/AIコア_音声処理.ts` — `AudioController`
- `frontend_avatar/src/AiDiy.vue` — `AudioController` の生成と lifecycle
- `frontend_avatar/src/components/AIコア.vue` — マイク / スピーカー UI、audio socket 接続
- `backend_server` 側の AIコア WebSocket 実装 — `input_audio` / `output_audio` / `cancel_audio`

## 主な仕様

| 項目 | 値 |
|------|-----|
| 入力サンプルレート | 16kHz（`inputSampleRate = 16000`） |
| 出力サンプルレート | 24kHz（`outputSampleRate = 24000`） |
| ビジュアライザーバンド数 | 32（`VISUALIZER_BAR_COUNT = 32`） |
| 音声送信チャンネル | `input_audio`（`audioSocket` 経由） |

## 責務分担
- `AIコア.vue` が `AIWebSocket(AI_WS_ENDPOINT, sessionId, 'audio')` を生成する。
- `output_audio` は `AudioController.handleAudioMessage()` へ渡す。
- `cancel_audio` は `AudioController.cancelOutput({ resetLevel: false })` へ渡す。
- `AudioController` は PCM 変換、再生キュー、レベル計測、ビジュアライザーに集中する。
- 接続状態、マイク ON/OFF、スピーカー ON/OFF の UI 状態は `AIコア.vue` が管理し、`AudioController` へ反映する。

音声は高頻度送信なので、通常のテキスト入力ソケットと分ける。`input_audio` を通常入力へ混ぜると、テキスト入力や状態制御が遅延しやすい。

## マイク入力
- `getUserMedia({ audio: { echoCancellation, noiseSuppression, autoGainControl } })` を使う。
- `AudioContext({ sampleRate: 16000 })` と `ScriptProcessorNode(1024, 1, 1)` で入力を受ける。
- Float32 を 16bit PCM に変換し、Base64 化して送信する。
- 送信 payload は `メッセージ内容: 'audio/pcm'`, `チャンネル: 'audio'`, `ファイル名: <base64>` の形式に合わせる。

## AI 音声出力
- `output_audio` の Base64 音声をキューに積む。
- PCM の場合は `createPcmAudioBuffer()`、それ以外は `decodeAudioData()` を試す。
- `nextPlaybackTime` でチャンクを連続再生し、チャンク間の途切れを抑える。
- スピーカー OFF でもビジュアライザー用の再生系を残す設計があるため、実音と視覚演出を分けて確認する。

## キャンセル処理

`cancelOutput()` はキューを破棄し、再生中ソースを短くフェードアウトして停止する。

- 連続キャンセルでゲイン復元が競合しないよう `fadeOutTimer` を見る。
- 停止対象は `speakerSources` と `visualizerSources` の両方を確認する。
- `cancel_audio` 受信後に古いキューが再開しないことを確認する。

## よくある問題と対処

| 現象 | 主な原因 | 確認箇所 |
|------|----------|----------|
| 音声が出ない | スピーカー OFF | `AIコア.vue` のスピーカートグル |
| 音声が出ない | `AudioContext` 未 resume | 初回ユーザー操作後の `audioContext.resume()` |
| 音声が出ない | audio socket 未接続 | `audioSocket` の接続状態 |
| マイクが使えない | Electron 権限 | `main.ts` の `session.setPermissionRequestHandler` |
| マイクが使えない | audio socket 未接続 | `audioSocket` の接続状態 |
| AI 音声が二重に聞こえる | 古い socket / controller が残っている | `音声接続世代`, `cleanup()`, `disconnect()` |
| 口パクだけ動いて音が出ない | スピーカー OFF だが visualizer は動いている | `speakerEnabled`, `visualizerSources` |
| マイクが AI 音声を拾う | エコー抑制や出力レベル処理の戻りが早い | `currentSpeakerLevel`, fade out 処理 |

## 変更時の注意点
- `AudioContext` はブラウザの自動再生制限を受ける。初回クリック後に resume する経路を維持する。
- 音声送信はトークン延長対象から外す。高頻度送信で認証延長 API を叩かない。
- 音声モデル変更時は frontend の同期だけでなく、backend の Live AI 初期化タイミングも確認する。
- `ScriptProcessorNode` を変更する場合は、入力サンプルレート、PCM 変換、Base64 payload の互換性を見る。
- 再生キューの停止処理を追加するときは、実音、ビジュアライザー、口パクのどれを止めるかを分けて考える。

## 確認方法
1. マイク ON で入力レベルと入力スペクトラムが動く。
2. AI 発話で出力レベルと出力スペクトラムが動く。
3. スピーカー OFF で実音は止まり、必要な視覚演出だけ残る。
4. `cancel_audio` 受信時に即時停止し、キューが再開しない。
5. Electron と Web の両方で、初回クリック後に `AudioContext` が resume する。
6. DevTools Console で AudioController 関連のエラーがないことを確認する。
