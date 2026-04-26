# AI音声処理（AudioController）

## このメモを使う場面
- マイク入力・スピーカー出力の動作を変更したい
- 音声処理の実装箇所を把握したい
- 音声が出ない / マイクが使えない問題を調査したい

## 関連ファイル
- `frontend_avatar/src/components/AIコア_音声処理.ts` — `AudioController` クラス
- `frontend_avatar/src/AiDiy.vue` — `AudioController` の生成と `audioSocket` の渡し方
- `frontend_avatar/src/components/AIコア.vue` — マイク ON/OFF、スピーカー ON/OFF の UI

## AudioController の主な仕様

| 項目 | 値 |
|------|-----|
| 入力サンプルレート | 16kHz（`inputSampleRate = 16000`） |
| 出力サンプルレート | 24kHz（`outputSampleRate = 24000`） |
| ビジュアライザーバンド数 | 32（`VISUALIZER_BAR_COUNT = 32`） |
| 音声送信チャンネル | `input_audio`（`audioSocket` 経由） |

## 接続と責務分担

- `AIコア.vue` が `AIWebSocket(AI_WS_ENDPOINT, sessionId, 'audio')` を生成する
- `output_audio` は `AudioController.handleAudioMessage()` へ渡す
- `cancel_audio` は `AudioController.cancelOutput({ resetLevel: false })` へ渡す
- `AudioController` は PCM 変換、再生キュー、レベル計測に集中し、接続状態そのものは `AIコア.vue` が管理する
- マイク ON/OFF やスピーカー ON/OFF の UI 状態は `AIコア.vue` から `AudioController` へ反映する

音声チャンネルは入力ソケットと分ける。`input_audio` を通常の入力ソケットへ混ぜると、高頻度送信でテキスト入力や状態制御の遅延を招きやすい。

## 入出力データの扱い

### マイク入力

- `getUserMedia({ audio: { echoCancellation, noiseSuppression, autoGainControl } })` を使う
- `AudioContext({ sampleRate: 16000 })` と `ScriptProcessorNode(1024, 1, 1)` で入力を受ける
- Float32 を 16bit PCM に変換し、Base64 化して `ファイル名` に載せる
- `メッセージ内容` は `audio/pcm`、`チャンネル` は `audio`

### AI 音声出力

- `output_audio` の Base64 音声をキューに積む
- PCM の場合は `createPcmAudioBuffer()`、それ以外は `decodeAudioData()` を試す
- `nextPlaybackTime` によりチャンクを連続再生し、チャンク間の途切れを抑える
- スピーカー OFF の場合でもビジュアライザー用の再生系は残るため、口パクや出力スペクトラム表示の挙動を確認する

### キャンセル

`cancelOutput()` はキューを破棄し、再生中ソースを 0.1 秒フェードアウトして止める。短時間に連続キャンセルしてもゲイン復元が競合しないようタイマーを管理しているため、停止処理を追加するときは `fadeOutTimer` と `speakerSources` / `visualizerSources` の両方を見る。

## よくある問題と対処

| 現象 | 原因 | 対処 |
|------|------|------|
| 音声が出ない | speaker 無効 | AIコア.vue のスピーカートグルを確認 |
| 音声が出ない | AudioContext 未 resume | ブラウザのユーザーインタラクション後に `audioContext.resume()` |
| 音声が出ない | audio ソケット未接続 | `audioSocket` の接続状態を確認 |
| マイクが使えない | Electron 権限 | `main.ts` の `session.setPermissionRequestHandler` を確認 |
| マイクが使えない | audio ソケット未接続 | `audioSocket` の接続状態を確認 |
| AI 音声が二重に聞こえる | 古い audioSocket / AudioController が残っている | `音声接続世代` と `cleanup()` / `disconnect()` の呼び出しを確認 |
| 口パクだけ動いて音が出ない | スピーカー OFF だが visualizer は動いている | `speakerEnabled` と `visualizerSources` の設計どおりか確認 |
| マイクが AI 音声を拾う | エコー抑制レベルが早く 0 に戻っている | `currentSpeakerLevel` とフェードアウト処理を確認 |

## 実装の結論

- マイク入力は `getUserMedia` で取得し、`ScriptProcessorNode` で PCM 化して `input_audio` として送信する
- AI から返る音声 PCM はキューに積み、順番に再生して発話途切れを抑える
- `cancelOutput()` は再生中キューを破棄するため、AI の発話を即時停止したい操作で使う
- 入力/出力レベルと 32 バンドのビジュアライザー値は、UI 表示とアバターの口パク演出へ連動する
- 音声は高頻度送信のため、通常のテキスト入力と違って送信ごとのトークン延長対象から外す
- 音声モデル変更時は frontend の同期経路だけでなく、backend の Live AI 初期化タイミングも確認する

## 変更時の確認観点

1. マイク ON で入力レベルと入力スペクトラムが動く
2. AI 発話で出力レベルと出力スペクトラムが動く
3. スピーカー OFF で実音は止まり、必要な視覚演出だけ残る
4. `cancel_audio` 受信時に即時停止し、キューが再開しない
5. Electron と Web の両方で、初回クリック後に AudioContext が resume する

## 確認方法

ブラウザ DevTools の Console で `AudioController` のログを確認。  
ビジュアライザーのバーが動いていれば入力/出力が機能している。
