import type { AIWebSocket, WebSocketMessage } from '@/_share/websocket'

type AudioControllerOptions = {
  onInputLevel?: (value: number) => void
  onOutputLevel?: (value: number) => void
  getSocket: () => AIWebSocket | null
  getSessionId: () => string
}

type StartResult = { success: boolean; error?: string }

export class AudioController {
  private inputAudioContext: AudioContext | null = null
  private outputAudioContext: AudioContext | null = null
  private inputAnalyser: AnalyserNode | null = null
  private outputAnalyser: AnalyserNode | null = null
  private inputProcessor: ScriptProcessorNode | null = null
  private inputStream: MediaStream | null = null
  private audioSocket: AIWebSocket | null = null
  private sessionId = ''
  private speakerEnabled = true
  private inputLevelFrame = 0
  private outputLevelFrame = 0
  private outputSources = new Set<AudioBufferSourceNode>()
  private inputSampleRate = 16000
  private outputSampleRate = 24000

  constructor(private readonly options: AudioControllerOptions) {}

  setAudioSocket(socket: AIWebSocket | null): void {
    this.audioSocket = socket
  }

  setSessionId(sessionId: string): void {
    this.sessionId = sessionId
  }

  setLiveModelName(modelName: string): void {
    const normalized = modelName.toLowerCase()
    this.inputSampleRate = normalized.includes('openai') ? 24000 : 16000
    this.outputSampleRate = 24000
  }

  setSpeakerEnabled(enabled: boolean): void {
    this.speakerEnabled = enabled
    if (!enabled) {
      this.cancelOutput(false)
    }
  }

  async unlockAudio(): Promise<void> {
    const context = this.ensureOutputContext()
    if (context.state === 'suspended') {
      await context.resume()
    }
  }

  async startMicrophone(): Promise<StartResult> {
    const socket = this.options.getSocket()
    if (!socket?.isConnected()) {
      return { success: false, error: 'サーバーに接続されていません。' }
    }

    try {
      await this.unlockAudio()
      await this.stopMicrophoneInternal()

      this.inputStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: this.inputSampleRate,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      })

      this.inputAudioContext = new AudioContext({ sampleRate: this.inputSampleRate })
      const source = this.inputAudioContext.createMediaStreamSource(this.inputStream)
      this.inputAnalyser = this.inputAudioContext.createAnalyser()
      this.inputAnalyser.fftSize = 256
      source.connect(this.inputAnalyser)

      this.inputProcessor = this.inputAudioContext.createScriptProcessor(2048, 1, 1)
      source.connect(this.inputProcessor)
      this.inputProcessor.connect(this.inputAudioContext.destination)
      this.inputProcessor.onaudioprocess = (event) => {
        const activeSocket = this.options.getSocket()
        if (!activeSocket?.isConnected()) return

        const pcm = this.floatTo16BitPCM(event.inputBuffer.getChannelData(0))
        const pcmBuffer = pcm.buffer.slice(pcm.byteOffset, pcm.byteOffset + pcm.byteLength) as ArrayBuffer
        activeSocket.send({
          セッションID: this.sessionId || this.options.getSessionId(),
          チャンネル: 'audio',
          メッセージ識別: 'input_audio',
          メッセージ内容: 'audio/pcm',
          ファイル名: this.arrayBufferToBase64(pcmBuffer),
          サムネイル画像: null,
        })
      }

      this.startInputLevelLoop()
      return { success: true }
    } catch (error) {
      await this.stopMicrophoneInternal()
      return {
        success: false,
        error: error instanceof Error ? error.message : 'マイクアクセスに失敗しました。',
      }
    }
  }

  stopMicrophone(): void {
    void this.stopMicrophoneInternal()
  }

  handleAudioMessage(message: WebSocketMessage): void {
    const base64Audio = this.extractBase64Audio(message)
    if (!base64Audio) return

    void this.playAudio(base64Audio, String(message.メッセージ内容 || 'audio/pcm'))
  }

  cancelOutput(resetLevel = true): void {
    this.outputSources.forEach((source) => {
      try {
        source.stop()
      } catch {
        return
      }
    })
    this.outputSources.clear()

    if (resetLevel) {
      this.options.onOutputLevel?.(0)
    }
  }

  cleanup(): void {
    this.cancelOutput()
    void this.stopMicrophoneInternal()
    if (this.outputLevelFrame) {
      window.cancelAnimationFrame(this.outputLevelFrame)
      this.outputLevelFrame = 0
    }
    if (this.outputAudioContext) {
      void this.outputAudioContext.close()
      this.outputAudioContext = null
      this.outputAnalyser = null
    }
  }

  private async playAudio(base64Audio: string, mimeType: string): Promise<void> {
    const context = this.ensureOutputContext()
    if (context.state === 'suspended') {
      await context.resume()
    }

    const audioBuffer = mimeType.includes('audio/pcm')
      ? this.createPcmAudioBuffer(context, base64Audio)
      : await context.decodeAudioData(this.base64ToArrayBuffer(base64Audio))

    const source = context.createBufferSource()
    source.buffer = audioBuffer
    source.connect(this.outputAnalyser ?? context.destination)
    if (!this.speakerEnabled) {
      source.connect(context.createGain())
    }
    source.onended = () => {
      this.outputSources.delete(source)
      if (this.outputSources.size === 0) {
        this.options.onOutputLevel?.(0)
      }
    }
    this.outputSources.add(source)
    source.start()
    this.startOutputLevelLoop()
  }

  private ensureOutputContext(): AudioContext {
    if (!this.outputAudioContext) {
      this.outputAudioContext = new AudioContext({ sampleRate: this.outputSampleRate })
      this.outputAnalyser = this.outputAudioContext.createAnalyser()
      this.outputAnalyser.fftSize = 256
      this.outputAnalyser.connect(this.outputAudioContext.destination)
    }
    return this.outputAudioContext
  }

  private startInputLevelLoop(): void {
    if (!this.inputAnalyser) return
    const data = new Uint8Array(this.inputAnalyser.frequencyBinCount)
    const tick = () => {
      if (!this.inputAnalyser) {
        this.options.onInputLevel?.(0)
        this.inputLevelFrame = 0
        return
      }
      this.inputAnalyser.getByteFrequencyData(data)
      this.options.onInputLevel?.(this.computeLevel(data))
      this.inputLevelFrame = window.requestAnimationFrame(tick)
    }
    if (!this.inputLevelFrame) {
      tick()
    }
  }

  private startOutputLevelLoop(): void {
    if (!this.outputAnalyser) return
    const data = new Uint8Array(this.outputAnalyser.frequencyBinCount)
    const tick = () => {
      if (!this.outputAnalyser) {
        this.options.onOutputLevel?.(0)
        this.outputLevelFrame = 0
        return
      }
      this.outputAnalyser.getByteFrequencyData(data)
      this.options.onOutputLevel?.(this.computeLevel(data))
      if (this.outputSources.size > 0) {
        this.outputLevelFrame = window.requestAnimationFrame(tick)
      } else {
        this.options.onOutputLevel?.(0)
        this.outputLevelFrame = 0
      }
    }
    if (!this.outputLevelFrame) {
      tick()
    }
  }

  private computeLevel(data: Uint8Array): number {
    if (data.length === 0) return 0
    const sum = data.reduce((acc, value) => acc + value, 0)
    return Math.min(1, sum / data.length / 128)
  }

  private floatTo16BitPCM(input: Float32Array): Int16Array {
    const output = new Int16Array(input.length)
    for (let index = 0; index < input.length; index += 1) {
      const sample = Math.max(-1, Math.min(1, input[index] ?? 0))
      output[index] = sample < 0 ? sample * 0x8000 : sample * 0x7fff
    }
    return output
  }

  private createPcmAudioBuffer(context: AudioContext, base64Audio: string): AudioBuffer {
    const pcmBytes = this.base64ToArrayBuffer(base64Audio)
    const int16 = new Int16Array(pcmBytes)
    const audioBuffer = context.createBuffer(1, int16.length, this.outputSampleRate)
    const channelData = audioBuffer.getChannelData(0)
    for (let index = 0; index < int16.length; index += 1) {
      channelData[index] = (int16[index] ?? 0) / 0x8000
    }
    return audioBuffer
  }

  private extractBase64Audio(message: WebSocketMessage): string {
    const raw = message.ファイル名 || message.base64_data || message.audio || message.data
    return typeof raw === 'string' ? raw : ''
  }

  private arrayBufferToBase64(buffer: ArrayBuffer): string {
    let binary = ''
    const bytes = new Uint8Array(buffer)
    for (let index = 0; index < bytes.byteLength; index += 1) {
      binary += String.fromCharCode(bytes[index] ?? 0)
    }
    return window.btoa(binary)
  }

  private base64ToArrayBuffer(base64: string): ArrayBuffer {
    const binary = window.atob(base64)
    const bytes = new Uint8Array(binary.length)
    for (let index = 0; index < binary.length; index += 1) {
      bytes[index] = binary.charCodeAt(index)
    }
    return bytes.buffer
  }

  private async stopMicrophoneInternal(): Promise<void> {
    if (this.inputLevelFrame) {
      window.cancelAnimationFrame(this.inputLevelFrame)
      this.inputLevelFrame = 0
    }
    this.options.onInputLevel?.(0)

    if (this.inputProcessor) {
      this.inputProcessor.disconnect()
      this.inputProcessor.onaudioprocess = null
      this.inputProcessor = null
    }

    this.inputStream?.getTracks().forEach((track) => track.stop())
    this.inputStream = null
    this.inputAnalyser = null

    if (this.inputAudioContext) {
      await this.inputAudioContext.close()
      this.inputAudioContext = null
    }
  }
}