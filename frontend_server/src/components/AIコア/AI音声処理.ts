// -*- coding: utf-8 -*-

// ------------------------------------------------
// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
// This software is licensed under the MIT License.
// https://github.com/monjyu1101
// Thank you for keeping the rules.
// ------------------------------------------------

/**
 * AIコア 音声ストリーム処理モジュール
 * 音声入力（マイク）と音声出力（スピーカー）の処理を管理
 */

import type { Ref } from 'vue';
import type { IWebSocketClient } from '@/api/websocket';

// 音声入力状態
interface InputAudioState {
  mediaRecorder: MediaRecorder | null;
  audioContext: AudioContext | null;
  audioProcessor: ScriptProcessorNode | null;
  isRecording: boolean;
  audioAnalyser: AnalyserNode | null;
  audioDataArray: Uint8Array | null;
  stream: MediaStream | null;
}

// 音声出力状態
interface OutputAudioState {
  currentAudioSource: { source: AudioBufferSourceNode; id: number } | null;
  audioSourceCounter: number;
  audioQueue: Array<{ base64Audio: string; mimeType: string }>;
  isPlaying: boolean;
  audioContext: AudioContext | null;
  audioAnalyser: AnalyserNode | null;
  audioDataArray: Uint8Array | null;
  // ビジュアライザー専用キュー
  visualizerQueue: Array<{ base64Audio: string; mimeType: string }>;
  isVisualizerProcessing: boolean;
  // ビジュアライザー専用analyser（destinationに接続しない）
  visualizerAnalyser: AnalyserNode | null;
  visualizerDataArray: Uint8Array | null;
}

export class AudioStreamProcessor {
  // 音声入力状態
  private inputAudioState: InputAudioState = {
    mediaRecorder: null,
    audioContext: null,
    audioProcessor: null,
    isRecording: false,
    audioAnalyser: null,
    audioDataArray: null,
    stream: null
  };

  // 音声出力状態
  private outputAudioState: OutputAudioState = {
    currentAudioSource: null,
    audioSourceCounter: 0,
    audioQueue: [],
    isPlaying: false,
    audioContext: null,
    audioAnalyser: null,
    audioDataArray: null,
    visualizerQueue: [],
    isVisualizerProcessing: false,
    visualizerAnalyser: null,
    visualizerDataArray: null
  };

  // サンプリングレート
  private inputSampleRate = 16000; // Gemini default
  private outputSampleRate = 24000;

  // 音声入力開始フラグ
  private audioInputStarted = false;

  // ビジュアライザー要素
  private inputVisualizerBars: HTMLElement[] = [];
  private outputVisualizerBars: HTMLElement[] = [];

  // WebSocketクライアント
  private wsClient: Ref<IWebSocketClient | null>;

  // セッションID
  private セッションID: Ref<string>;

  // スピーカー状態
  private isSpeakerOn: Ref<boolean>;

  // ビジュアライザーコンテナ要素
  private audioVisualizerOverlay: HTMLElement | null = null;
  private isVisualizerVisible = false;
  private isVisualizerLoopStarted = false;

  constructor(wsClient: Ref<IWebSocketClient | null>, セッションID: Ref<string>, isSpeakerOn: Ref<boolean>) {
    this.wsClient = wsClient;
    this.セッションID = セッションID;
    this.isSpeakerOn = isSpeakerOn;
  }

  /**
   * サンプリングレート設定（LiveAIプロバイダーに応じて切り替え）
   */
  setSampleRate(liveAIProvider: string) {
    if (liveAIProvider && liveAIProvider.toLowerCase() === 'openai') {
      this.inputSampleRate = 24000;
      this.outputSampleRate = 24000;
    } else {
      this.inputSampleRate = 16000;
      this.outputSampleRate = 24000;
    }

    // AudioContextを再作成
    if (this.outputAudioState.audioContext) {
      this.outputAudioState.audioContext.close();
    }
    this.setupOutputAudio();
  }

  /**
   * ビジュアライザーセットアップ
   */
  setupAudioVisualizer(audioBarsElement: HTMLElement | null, overlayElement: HTMLElement | null) {
    console.log('[AudioStreamProcessor] ビジュアライザーセットアップ開始', { audioBarsElement, overlayElement });

    if (!audioBarsElement) {
      console.warn('[AudioStreamProcessor] audioBarsElement が見つかりません');
      return;
    }

    this.audioVisualizerOverlay = overlayElement;
    audioBarsElement.innerHTML = '';
    this.inputVisualizerBars = [];
    this.outputVisualizerBars = [];

    const barCount = 64;

    for (let i = 0; i < barCount; i++) {
      const container = document.createElement('div');
      container.className = 'audio-bar-container';
      container.style.cssText = 'flex: 1; display: flex; flex-direction: column; align-items: stretch; justify-content: flex-end; height: 100%; gap: 0px; min-width: 1px;';

      const outputBar = document.createElement('div');
      outputBar.className = 'audio-bar output-audio';
      outputBar.style.cssText = 'width: 100%; min-height: 2px; height: 10%; background: #44ff44; order: 1;';

      const inputBar = document.createElement('div');
      inputBar.className = 'audio-bar input-audio';
      inputBar.style.cssText = 'width: 100%; min-height: 2px; height: 10%; background: #ff4444; order: 2;';

      container.appendChild(outputBar);
      container.appendChild(inputBar);
      audioBarsElement.appendChild(container);

      this.inputVisualizerBars.push(inputBar);
      this.outputVisualizerBars.push(outputBar);
    }

    console.log('[AudioStreamProcessor] ビジュアライザーセットアップ完了', {
      barCount: this.inputVisualizerBars.length,
      overlayElement: this.audioVisualizerOverlay,
      firstInputBar: this.inputVisualizerBars[0],
      firstOutputBar: this.outputVisualizerBars[0]
    });
  }

  /**
   * 音声ビジュアライザー更新ループ
   */
  startAudioVisualization() {
    if (this.isVisualizerLoopStarted) return;
    this.isVisualizerLoopStarted = true;
    const visualize = () => {
      if (!this.inputAudioState.isRecording && !this.outputAudioState.isPlaying && !this.outputAudioState.isVisualizerProcessing) {
        requestAnimationFrame(visualize);
        return;
      }

      // 入力音声のビジュアライザー更新
      if (this.inputAudioState.isRecording && this.inputAudioState.audioAnalyser) {
        this.inputAudioState.audioAnalyser.getByteFrequencyData(this.inputAudioState.audioDataArray! as any);
        this.updateVisualizerBars(this.inputVisualizerBars, this.inputAudioState.audioDataArray!);
      }

      // 出力音声のビジュアライザー更新
      if (this.outputAudioState.isPlaying && this.outputAudioState.audioAnalyser) {
        // スピーカー再生中は通常のanalyserを使用
        this.outputAudioState.audioAnalyser.getByteFrequencyData(this.outputAudioState.audioDataArray! as any);
        this.updateVisualizerBars(this.outputVisualizerBars, this.outputAudioState.audioDataArray!);
      } else if (this.outputAudioState.isVisualizerProcessing && this.outputAudioState.visualizerAnalyser) {
        // ビジュアライザー専用処理中はビジュアライザー専用analyserを使用
        this.outputAudioState.visualizerAnalyser.getByteFrequencyData(this.outputAudioState.visualizerDataArray! as any);
        this.updateVisualizerBars(this.outputVisualizerBars, this.outputAudioState.visualizerDataArray!);
      }

      requestAnimationFrame(visualize);
    };

    visualize();
  }

  /**
   * ビジュアライザーバー更新
   */
  private updateVisualizerBars(bars: HTMLElement[], dataArray: Uint8Array) {
    for (let i = 0; i < bars.length; i++) {
      const value = dataArray[i] || 0;
      const height = Math.max(10, (value / 255) * 100);
      bars[i].style.height = `${height}%`;
    }
  }

  /**
   * ビジュアライザーをゼロ表示にリセット
   */
  private resetVisualizerBars() {
    const reset = (bars: HTMLElement[]) => {
      for (let i = 0; i < bars.length; i++) {
        bars[i].style.height = '2px';
      }
    };
    reset(this.inputVisualizerBars);
    reset(this.outputVisualizerBars);
  }

  private resetBars(bars: HTMLElement[]) {
    for (let i = 0; i < bars.length; i++) {
      bars[i].style.height = '2px';
    }
  }

  /**
   * マイク開始
   */
  async startMicrophone(): Promise<{ success: boolean; error?: string }> {
    // WebSocket接続チェック
    if (!this.wsClient.value || !this.wsClient.value.isConnected()) {
      return { success: false, error: 'サーバーに接続されていません。\n接続が完了してからマイクをオンにしてください。' };
    }

    try {
      await this.startAudioCapture();

      // ビジュアライザー表示
      console.log('[AudioStreamProcessor] ビジュアライザー表示', this.audioVisualizerOverlay);
      if (this.audioVisualizerOverlay) {
        this.audioVisualizerOverlay.style.display = 'flex';
        console.log('[AudioStreamProcessor] ビジュアライザー表示設定完了');
      } else {
        console.warn('[AudioStreamProcessor] audioVisualizerOverlay が null です');
      }

      this.startAudioVisualization();

      // 音声録音開始時に再生中の音声をキャンセル
      this.cancelAudioOutput();

      return { success: true };
    } catch (error) {
      console.error('マイク開始エラー:', error);
      this.inputAudioState.isRecording = false;
      this.audioInputStarted = false;
      if (this.audioVisualizerOverlay) {
        this.audioVisualizerOverlay.style.display = 'none';
      }
      return { success: false, error: 'マイクアクセスに失敗しました。' };
    }
  }

  /**
   * マイク停止
   */
  stopMicrophone() {
    this.inputAudioState.isRecording = false;
    this.audioInputStarted = false;

    // audioProcessorを停止・切断
    if (this.inputAudioState.audioProcessor) {
      this.inputAudioState.audioProcessor.disconnect();
      this.inputAudioState.audioProcessor = null;
    }

    if (this.inputAudioState.stream) {
      this.inputAudioState.stream.getTracks().forEach(track => track.stop());
      this.inputAudioState.stream = null;
    }

    if (this.inputAudioState.audioContext) {
      this.inputAudioState.audioContext.close();
      this.inputAudioState.audioContext = null;
    }

    // ビジュアライザー表示は updateVisualizerVisibility に委譲
  }

  /**
   * 音声キャプチャ開始
   */
  private async startAudioCapture() {
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        sampleRate: this.inputSampleRate,
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true
      }
    });
    this.inputAudioState.stream = stream;

    // AudioContextセットアップ
    this.inputAudioState.audioContext = new AudioContext({ sampleRate: this.inputSampleRate });
    const source = this.inputAudioState.audioContext.createMediaStreamSource(stream);

    // 音声分析用
    this.inputAudioState.audioAnalyser = this.inputAudioState.audioContext.createAnalyser();
    this.inputAudioState.audioAnalyser.fftSize = 128;
    source.connect(this.inputAudioState.audioAnalyser);
    this.inputAudioState.audioDataArray = new Uint8Array(this.inputAudioState.audioAnalyser.frequencyBinCount);

    // ScriptProcessorNodeを使用
    const bufferSize = 1024;
    const processor = this.inputAudioState.audioContext.createScriptProcessor(bufferSize, 1, 1);

    processor.onaudioprocess = (event) => {
      if (this.wsClient.value && this.wsClient.value.isConnected()) {
        const inputBuffer = event.inputBuffer.getChannelData(0);

        // Float32ArrayをInt16Arrayに変換（16-bit PCM）
        const pcmData = new Int16Array(inputBuffer.length);
        for (let i = 0; i < inputBuffer.length; i++) {
          pcmData[i] = Math.max(-32768, Math.min(32767, inputBuffer[i] * 32767));
        }

        // ArrayBufferをBase64エンコード
        const base64Audio = this.arrayBufferToBase64(pcmData.buffer);

        // 音声データ送信前にキャンセル通知（初回のみ）
        if (!this.audioInputStarted) {
          this.audioInputStarted = true;
          this.cancelAudioOutput();
        }

        // リアルタイムストリーミング送信
        this.wsClient.value.send({
          セッションID: this.wsClient.value.セッションID取得?.() ?? '',
          チャンネル: -1,
          メッセージ識別: 'input_audio',
          メッセージ内容: 'audio/pcm',
          ファイル名: base64Audio,
          サムネイル画像: null
        });
      }
    };

    // 音声処理チェーンを接続
    source.connect(processor);
    processor.connect(this.inputAudioState.audioContext.destination);

    this.inputAudioState.audioProcessor = processor;
    this.inputAudioState.isRecording = true;
  }

  /**
   * ArrayBufferをBase64エンコード
   */
  private arrayBufferToBase64(buffer: ArrayBuffer): string {
    let binary = '';
    const bytes = new Uint8Array(buffer);
    const len = bytes.byteLength;
    for (let i = 0; i < len; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return window.btoa(binary);
  }

  /**
   * 音声出力AudioContextセットアップ
   */
  setupOutputAudio() {
    this.outputAudioState.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)({
      sampleRate: this.outputSampleRate
    });
    
    // スピーカー出力用analyser（destinationに接続）
    this.outputAudioState.audioAnalyser = this.outputAudioState.audioContext.createAnalyser();
    this.outputAudioState.audioAnalyser.fftSize = 256;
    this.outputAudioState.audioAnalyser.connect(this.outputAudioState.audioContext.destination);
    this.outputAudioState.audioDataArray = new Uint8Array(this.outputAudioState.audioAnalyser.frequencyBinCount);
    
    // ビジュアライザー専用analyser（destinationに接続しない）
    this.outputAudioState.visualizerAnalyser = this.outputAudioState.audioContext.createAnalyser();
    this.outputAudioState.visualizerAnalyser.fftSize = 256;
    this.outputAudioState.visualizerDataArray = new Uint8Array(this.outputAudioState.visualizerAnalyser.frequencyBinCount);
    
    console.log('[AudioStreamProcessor] 出力AudioContextセットアップ完了（analyser × 2）');
  }

  /**
   * 音声メッセージ処理
   */
  handleAudioMessage(data: any) {
    const messageType = data?.メッセージ識別 || data?.type;
    if (messageType === 'output_audio') {
      const base64Audio = data?.ファイル名 || data?.base64_data || data?.audio || data?.data;
      const mimeType = data?.メッセージ内容 || data?.mime_type || 'audio/pcm';
      if (base64Audio) {
        // ビジュアライザーキューには常に追加
        this.queueVisualizerAudio({ base64Audio, mimeType });
        
        // 音声再生キューにはスピーカーオンの時だけ追加
        if (this.isSpeakerOn.value) {
          this.queueAudio({ base64Audio, mimeType });
        }
      }
    }
  }

  /**
   * ビジュアライザー用音声をキューに追加
   */
  private queueVisualizerAudio(audioData: { base64Audio: string; mimeType: string }) {
    this.outputAudioState.visualizerQueue.push(audioData);
    console.log('[AudioStreamProcessor] ビジュアライザーキュー追加:', this.outputAudioState.visualizerQueue.length);

    if (!this.outputAudioState.isVisualizerProcessing) {
      this.processVisualizerQueue();
    }
  }

  /**
   * ビジュアライザーキュー処理
   */
  private async processVisualizerQueue() {
    if (this.outputAudioState.visualizerQueue.length === 0) {
      this.outputAudioState.isVisualizerProcessing = false;
      console.log('[AudioStreamProcessor] ビジュアライザーキュー処理完了');
      return;
    }

    this.outputAudioState.isVisualizerProcessing = true;
    console.log('[AudioStreamProcessor] ビジュアライザーキュー処理開始:', this.outputAudioState.visualizerQueue.length);

    const { base64Audio, mimeType } = this.outputAudioState.visualizerQueue.shift()!;
    await this.playAudioForVisualizer(base64Audio, mimeType);

    this.processVisualizerQueue();
  }

  /**
   * ビジュアライザー専用音声再生（音は出さない、analyserにだけデータを流す）
   */
  private async playAudioForVisualizer(base64Audio: string, mimeType: string = 'audio/pcm') {
    console.log('[AudioStreamProcessor] ビジュアライザー専用再生開始');
    const binaryString = window.atob(base64Audio);
    const len = binaryString.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }

    if (!this.outputAudioState.audioContext) {
      this.setupOutputAudio();
    }

    if (this.outputAudioState.audioContext!.state === 'suspended') {
      try {
        await this.outputAudioState.audioContext!.resume();
      } catch (e) {
        console.warn('audioContext resume失敗:', e);
      }
    }

    let audioBuffer: AudioBuffer;

    // audio/pcmは手動でFloat32に変換
    if (mimeType && mimeType.toLowerCase().includes('pcm')) {
      const pcmData = new Int16Array(bytes.buffer);
      const float32Data = new Float32Array(pcmData.length);
      for (let i = 0; i < pcmData.length; i++) {
        float32Data[i] = pcmData[i] / 32768;
      }
      audioBuffer = this.outputAudioState.audioContext!.createBuffer(1, float32Data.length, this.outputSampleRate);
      audioBuffer.copyToChannel(float32Data, 0);
    } else {
      try {
        audioBuffer = await this.outputAudioState.audioContext!.decodeAudioData(bytes.buffer);
      } catch (e) {
        const pcmData = new Int16Array(bytes.buffer);
        const float32Data = new Float32Array(pcmData.length);
        for (let i = 0; i < pcmData.length; i++) {
          float32Data[i] = pcmData[i] / 32768;
        }
        audioBuffer = this.outputAudioState.audioContext!.createBuffer(1, float32Data.length, this.outputSampleRate);
        audioBuffer.copyToChannel(float32Data, 0);
      }
    }

    const source = this.outputAudioState.audioContext!.createBufferSource();
    source.buffer = audioBuffer;
    // ビジュアライザー専用analyserに接続（destinationには接続しないので音は出ない）
    source.connect(this.outputAudioState.visualizerAnalyser!);

    console.log('[AudioStreamProcessor] ビジュアライザー専用再生: visualizerAnalyserに接続完了（音は出ない）');

    return new Promise<void>((resolve) => {
      source.onended = () => {
        console.log('[AudioStreamProcessor] ビジュアライザー専用再生終了');
        resolve();
      };
      source.start(0);
    });
  }

  /**
   * 音声をキューに追加（スピーカー再生用）
   */
  private queueAudio(audioData: { base64Audio: string; mimeType: string }) {
    this.outputAudioState.audioQueue.push(audioData);

    if (!this.outputAudioState.isPlaying) {
      this.processAudioQueue();
    }
  }

  /**
   * 音声キュー処理
   */
  private async processAudioQueue() {
    if (this.outputAudioState.audioQueue.length === 0) {
      this.outputAudioState.isPlaying = false;
      return;
    }

    this.outputAudioState.isPlaying = true;

    const { base64Audio, mimeType } = this.outputAudioState.audioQueue.shift()!;
    await this.playAudioFromBuffer(base64Audio, mimeType);

    this.processAudioQueue();
  }

  /**
   * AudioBufferから音声再生
   */
  private async playAudioFromBuffer(base64Audio: string, mimeType: string = 'audio/pcm') {
    const binaryString = window.atob(base64Audio);
    const len = binaryString.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }

    if (!this.outputAudioState.audioContext) {
      this.setupOutputAudio();
    }

    if (this.outputAudioState.audioContext!.state === 'suspended') {
      try {
        await this.outputAudioState.audioContext!.resume();
      } catch (e) {
        console.warn('audioContext resume失敗:', e);
      }
    }

    let audioBuffer: AudioBuffer;

    // audio/pcmは手動でFloat32に変換
    if (mimeType && mimeType.toLowerCase().includes('pcm')) {
      const pcmData = new Int16Array(bytes.buffer);
      const float32Data = new Float32Array(pcmData.length);
      for (let i = 0; i < pcmData.length; i++) {
        float32Data[i] = pcmData[i] / 32768;
      }
      audioBuffer = this.outputAudioState.audioContext!.createBuffer(1, float32Data.length, this.outputSampleRate);
      audioBuffer.copyToChannel(float32Data, 0);
    } else {
      try {
        audioBuffer = await this.outputAudioState.audioContext!.decodeAudioData(bytes.buffer);
      } catch (e) {
        const pcmData = new Int16Array(bytes.buffer);
        const float32Data = new Float32Array(pcmData.length);
        for (let i = 0; i < pcmData.length; i++) {
          float32Data[i] = pcmData[i] / 32768;
        }
        audioBuffer = this.outputAudioState.audioContext!.createBuffer(1, float32Data.length, this.outputSampleRate);
        audioBuffer.copyToChannel(float32Data, 0);
      }
    }

    const source = this.outputAudioState.audioContext!.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(this.outputAudioState.audioAnalyser!);

    this.outputAudioState.audioSourceCounter++;
    const currentSourceId = this.outputAudioState.audioSourceCounter;
    this.outputAudioState.currentAudioSource = { source, id: currentSourceId };

    return new Promise<void>((resolve) => {
      source.onended = () => {
        if (this.outputAudioState.currentAudioSource?.id === currentSourceId) {
          this.outputAudioState.currentAudioSource = null;
        }
        resolve();
      };
      source.start(0);
    });
  }

  /**
   * 音声出力キャンセル
   */
  cancelAudioOutput() {
    // 再生中の音声を停止
    if (this.outputAudioState.currentAudioSource) {
      try {
        this.outputAudioState.currentAudioSource.source.stop();
      } catch (e) {
        // Already stopped
      }
      this.outputAudioState.currentAudioSource = null;
    }

    // キューをクリア
    this.outputAudioState.audioQueue = [];
    this.outputAudioState.isPlaying = false;

    // サーバーにキャンセル通知（統一フォーマット）
    if (this.wsClient.value && this.wsClient.value.isConnected()) {
      this.wsClient.value.send({
        セッションID: this.セッションID.value,
        チャンネル: -1,
        メッセージ識別: 'cancel_audio',
        メッセージ内容: null,
        ファイル名: null,
        サムネイル画像: null
      });
    }
  }

  /**
   * スピーカーOFF時のクリーンアップ
   */
  clearAudioPlayback() {
    if (this.outputAudioState.currentAudioSource) {
      try {
        this.outputAudioState.currentAudioSource.source.stop();
      } catch (e) {
        // Already stopped
      }
      this.outputAudioState.currentAudioSource = null;
    }
    this.outputAudioState.audioQueue = [];
    this.outputAudioState.isPlaying = false;
  }

  /**
   * クリーンアップ
   */
  cleanup() {
    if (this.inputAudioState.isRecording) {
      this.stopMicrophone();
    }

    if (this.outputAudioState.currentAudioSource) {
      try {
        this.outputAudioState.currentAudioSource.source.stop();
      } catch (e) {
        // Already stopped
      }
    }

    if (this.inputAudioState.audioContext) {
      this.inputAudioState.audioContext.close();
    }
    if (this.outputAudioState.audioContext) {
      this.outputAudioState.audioContext.close();
    }
  }

  /**
   * マイク録音中かどうか
   */
  isRecording(): boolean {
    return this.inputAudioState.isRecording;
  }

  /**
   * 音声再生中かどうか
   */
  isPlaying(): boolean {
    return this.outputAudioState.isPlaying;
  }

  /**
   * ビジュアライザー表示/非表示を更新
   */
  updateVisualizerVisibility(microphoneEnabled: boolean, speakerEnabled: boolean) {
    if (!this.audioVisualizerOverlay) return;

    const shouldShow = microphoneEnabled || speakerEnabled;

    if (shouldShow) {
      this.audioVisualizerOverlay.style.display = 'flex';
      if (!this.isVisualizerVisible) {
        this.resetVisualizerBars();
      }
      if (!microphoneEnabled) {
        this.resetBars(this.inputVisualizerBars);
      }
      if (!speakerEnabled) {
        this.resetBars(this.outputVisualizerBars);
      }
      this.startAudioVisualization();
      this.isVisualizerVisible = true;
      console.log('[AudioStreamProcessor] ビジュアライザー表示 (マイク:', microphoneEnabled, 'スピーカー:', speakerEnabled, ')');
    } else {
      this.resetVisualizerBars();
      this.audioVisualizerOverlay.style.display = 'none';
      this.isVisualizerVisible = false;
      console.log('[AudioStreamProcessor] ビジュアライザー非表示');
    }
  }
}


