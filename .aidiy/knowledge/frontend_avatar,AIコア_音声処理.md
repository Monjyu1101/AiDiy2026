# AudioController 音声処理

> 文書: `frontend_avatar,AIコア_音声処理.md` | 実装: `frontend_avatar/src/components/AIコア_音声処理.ts`, `frontend_avatar/src/components/AIコア.vue`

## このメモを使う場面

- 音声入力（マイク）の開始・停止・品質を変更するとき
- 音声出力（AI音声再生）のキュー管理や再生ロジックを変更するとき
- エコー抑制パラメータを調整するとき
- ビジュアライザーのレベル取得方法を変更するとき

## AudioController 概要

`AudioController` class は AI コアの音声入出力を一元管理します。WebSocket 経由で音声ストリームを送受信します。

```
マイク → getUserMedia → ScriptProcessor → PCM16 → WebSocket → AIサーバー
AIサーバー → WebSocket → base64デコード → AudioBuffer → スケジュール再生 → スピーカー
```

## 入力パイプライン（startMicrophone）

```typescript
// 音声入力設定
navigator.mediaDevices.getUserMedia({
    audio: {
        sampleRate: this.inputSampleRate,  // 16000 or 24000 (ベンダー依存)
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
    },
})
```

| 項目 | 値 |
|------|-----|
| サンプルレート | 16000 Hz（OpenAI 系は 24000 Hz） |
| チャンネル | 1（モノラル） |
| エコーキャンセル | ON |
| ノイズ抑制 | ON |
| オートゲイン | ON |

### 入力処理フロー

1. `getUserMedia` でマイクストリーム取得
2. `AudioContext` 作成（`inputSampleRate`）
3. `ScriptProcessorNode` (1024, 1, 1) で PCM データ取得
4. **エコー抑制** 適用（スピーカー出力レベルに応じて減衰）
5. Float32 → PCM16 変換
6. `input_audio` メッセージとして WebSocket 送信

```typescript
// WebSocket 送信パケット
{
    セッションID: this.sessionId,
    チャンネル: 'audio',
    メッセージ識別: 'input_audio',
    メッセージ内容: 'audio/pcm',
    ファイル名: this.arrayBufferToBase64(pcmBuffer),  // PCM16データ
    サムネイル画像: null,
}
```

## 出力パイプライン（handleAudioMessage → processOutputQueue）

### 受信から再生まで

1. `output_audio` メッセージを WebSocket で受信
2. Base64 → AudioBuffer デコード（PCM は自力デコード、それ以外は `decodeAudioData`）
3. 出力キューに追加
4. `processOutputQueue()` で逐次再生スケジュール

### 再生スケジュール

```typescript
const leadTime = 0.03  // 30ms 先行スケジュール
```

- `AudioBufferSourceNode` を生成し、`GainNode` に接続
- `nextPlaybackTime` で連続再生のタイミングを管理
- スピーカー状態を `currentSpeakerLevel` で追跡（エコー抑制に利用）
- ビジュアライザー用の AnalyserNode も同時接続

### キャンセル出力（cancelOutput）

AI音声再生を中断するときに呼ばれます。

```typescript
cancelOutput({ resetLevel, notifyServer })
```

- 0.1秒の **フェードアウト** で音声を滑らかに停止（人間の割り込みを最優先）
- フェード中も `currentSpeakerLevel` は維持（エコー抑制継続）
- フェード完了後にレベルリセット
- `notifyServer = true` でサーバーに `cancel_audio` 通知

## エコー抑制

スピーカー出力がマイクに回り込むのを抑制します。

```typescript
private static readonly FADE_OUT_DURATION = 0.1           // キャンセル時フェードアウト秒数
private static readonly ECHO_SUPPRESSION_GAIN = 1.5       // 抑制係数（大きいほど強く抑制）
private static readonly ECHO_SUPPRESSION_THRESHOLD = 0.01 // この値未満はスキップ
```

`applyEchoSuppression(inputData: Float32Array): Float32Array`:
- 現在の `currentSpeakerLevel` が閾値を超えている場合のみ適用
- 入力信号からスピーカー信号の推定値を減算（抑制係数で強度調整）

## サンプルレートのベンダー依存

```typescript
setLiveModelName(modelName: string): void {
    const normalized = modelName.toLowerCase()
    this.inputSampleRate = normalized.includes('openai') ? 24000 : 16000
}
```

| AI ベンダー | 入力サンプルレート | 出力サンプルレート |
|------------|-------------------|-------------------|
| OpenAI 系 | 24000 Hz | 24000 Hz |
| それ以外 | 16000 Hz | 24000 Hz |

## ビジュアライザー

| 項目 | バー数 | 取得方法 |
|------|--------|----------|
| 入力レベル | 32 | `inputAnalyser.getByteFrequencyData()` |
| 出力レベル | 32 | `visualizerAnalyser.getByteFrequencyData()` |

`onInputLevel`, `onInputSpectrum`, `onOutputLevel`, `onOutputSpectrum` コールバックで UI にレベルを通知します。

## 使用箇所

`AIコア.vue` 内で生成され、`AIコア_アバター.vue` へミュート/アンミュート制御やレベル表示を連携します。

```typescript
// AIコア.vue
const audioController = new AudioController({
    getSocket: () => inputSocket.value,
    getSessionId: () => props.sessionId,
    onInputLevel: (level) => { 入力レベル.value = level },
    onOutputLevel: (level) => { 出力レベル.value = level },
    onInputSpectrum: (values) => { 入力スペクトル.value = values },
    onOutputSpectrum: (values) => { 出力スペクトル.value = values },
})
```

## 注意点

- **AudioContext 再開**: `unlockAudio()` で `context.resume()` を呼ぶ。ユーザー操作後に実行しないとブラウザがブロックする
- **キュー世代管理**: `outputQueueGeneration` でキャンセル後の古いキューを破棄。キャンセル中に届いた古いパケットを再生しない
- **エコー抑制の限界**: ソフトウェア処理のため、完全な除去はできない。ハードウェアのエコーキャンセルと併用
- **フェードアウト競合**: `fadeOutTimer` で連続キャンセル時のタイマー競合を防止
