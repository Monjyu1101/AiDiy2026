// -*- coding: utf-8 -*-

// -------------------------------------------------------------------------
// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101
// -------------------------------------------------------------------------

import { AI_WS_ENDPOINT } from '@/api/config'

export type WebSocketMessage = {
  type?: string
  セッションID?: string
  ソケット番号?: string
  チャンネル?: string | null
  出力先チャンネル?: string
  メッセージ識別?: string
  メッセージ内容?: unknown
  ファイル名?: string | null
  サムネイル画像?: string | null
  error?: string
  [key: string]: unknown
}

export type MessageHandler = (message: WebSocketMessage) => void
export type StateHandler = (connected: boolean) => void

export interface IWebSocketClient {
  connect(): Promise<string>
  send(message: WebSocketMessage): void
  on(messageType: string, handler: MessageHandler): void
  off(messageType: string, handler?: MessageHandler): void
  disconnect(): void
  セッションID取得(): string | null
  isConnected(): boolean
  sendPing(): void
  updateState(ボタン: unknown): void
  sendChatMessage(message: string): void
  sendInputText(text: string, 出力先チャンネル?: string): void
  requestStream(data: unknown): void
  onStateChange(handler: StateHandler): () => void
}

export class AIWebSocket implements IWebSocketClient {
  private socket: WebSocket | null = null
  private sessionId: string | null = null
  private readonly handlers = new Map<string, Set<MessageHandler>>()
  private readonly stateHandlers = new Set<StateHandler>()
  private reconnectAttempts = 0
  private readonly maxReconnectAttempts = 5
  private reconnectTimer: number | null = null
  private intentionallyClosed = false

  constructor(
    private readonly url: string,
    private requestedSessionId = '',
    private requestedSocketNumber = '',
  ) {}

  async connect(): Promise<string> {
    this.clearReconnectTimer()
    this.intentionallyClosed = false

    return new Promise<string>((resolve, reject) => {
      const socket = new WebSocket(this.url)
      let settled = false

      const fail = (error: Error) => {
        if (settled) return
        settled = true
        reject(error)
      }

      const timeoutId = window.setTimeout(() => {
        fail(new Error('WebSocket initialization timeout'))
      }, 30000)

      socket.onopen = () => {
        this.socket = socket
        this.reconnectAttempts = 0
        this.emitState(true)
        socket.send(JSON.stringify({
          type: 'connect',
          セッションID: this.requestedSessionId || null,
          ソケット番号: this.requestedSocketNumber || null,
        }))
      }

      socket.onmessage = (event) => {
        let message: WebSocketMessage
        try {
          message = JSON.parse(String(event.data)) as WebSocketMessage
        } catch {
          return
        }

        const messageType = String(message.メッセージ識別 || message.type || '')
        if (messageType === 'init' && typeof message.セッションID === 'string' && message.セッションID) {
          this.sessionId = message.セッションID
          this.requestedSessionId = message.セッションID
          if (typeof message.ソケット番号 === 'string' && message.ソケット番号) {
            this.requestedSocketNumber = message.ソケット番号
          }
          if (!settled) {
            settled = true
            window.clearTimeout(timeoutId)
            resolve(this.sessionId)
          }
        }

        this.dispatchMessage(messageType, message)
      }

      socket.onerror = () => {
        if (!settled) {
          window.clearTimeout(timeoutId)
          fail(new Error('WebSocket connection error'))
        }
      }

      socket.onclose = (event) => {
        this.emitState(false)
        this.socket = null
        this.sessionId = null
        window.clearTimeout(timeoutId)

        if (!settled) {
          fail(new Error(`WebSocket connection closed: ${event.code} ${event.reason}`.trim()))
          return
        }

        if (!this.intentionallyClosed && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts += 1
          this.reconnectTimer = window.setTimeout(() => {
            void this.connect().catch(() => undefined)
          }, 3000)
        }
      }
    })
  }

  send(message: WebSocketMessage): void {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      return
    }

    const payload: WebSocketMessage = {
      ...message,
      セッションID: message.セッションID ?? this.sessionId ?? this.requestedSessionId,
    }
    this.socket.send(JSON.stringify(payload))
  }

  on(messageType: string, handler: MessageHandler): void {
    const handlers = this.handlers.get(messageType) ?? new Set<MessageHandler>()
    handlers.add(handler)
    this.handlers.set(messageType, handlers)
  }

  off(messageType: string, handler?: MessageHandler): void {
    if (!handler) {
      this.handlers.delete(messageType)
      return
    }

    const handlers = this.handlers.get(messageType)
    if (!handlers) return
    handlers.delete(handler)
    if (handlers.size === 0) {
      this.handlers.delete(messageType)
    }
  }

  セッションID取得(): string | null {
    return this.sessionId
  }

  isConnected(): boolean {
    return this.socket?.readyState === WebSocket.OPEN
  }

  sendPing(): void {
    this.send({ type: 'ping', timestamp: Date.now() })
  }

  updateState(ボタン: unknown): void {
    this.send({
      チャンネル: null,
      メッセージ識別: 'operations',
      メッセージ内容: { ボタン },
    })
  }

  sendChatMessage(message: string): void {
    this.sendInputText(message, '0')
  }

  sendInputText(text: string, 出力先チャンネル = '0'): void {
    this.send({
      チャンネル: 'input',
      メッセージ識別: 'input_text',
      メッセージ内容: text,
      出力先チャンネル,
      ファイル名: null,
      サムネイル画像: null,
    })
  }

  requestStream(_data: unknown): void {
    console.warn('[AIWebSocket] requestStream は未使用です')
  }

  onStateChange(handler: StateHandler): () => void {
    this.stateHandlers.add(handler)
    handler(this.isConnected())
    return () => {
      this.stateHandlers.delete(handler)
    }
  }

  disconnect(): void {
    this.intentionallyClosed = true
    this.clearReconnectTimer()
    if (this.socket) {
      this.socket.close()
      this.socket = null
    }
    this.sessionId = null
    this.emitState(false)
  }

  private dispatchMessage(messageType: string, message: WebSocketMessage): void {
    if (!messageType) return

    const channel = typeof message.チャンネル === 'string' ? message.チャンネル : null
    if (channel) {
      this.handlers.get(`${messageType}_${channel}`)?.forEach((handler) => handler(message))
    }
    this.handlers.get(messageType)?.forEach((handler) => handler(message))
    this.handlers.get('*')?.forEach((handler) => handler(message))
  }

  private emitState(connected: boolean): void {
    this.stateHandlers.forEach((handler) => handler(connected))
  }

  private clearReconnectTimer(): void {
    if (this.reconnectTimer !== null) {
      window.clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
  }
}

export { AIWebSocket as AIコアWebSocket }

export function createWebSocketUrl(path: string): string {
  if (path === '/core/ws/AIコア') {
    return AI_WS_ENDPOINT
  }

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.hostname
  const port = window.location.port
  return `${protocol}//${host}:${port}${path}`
}
