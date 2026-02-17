// -*- coding: utf-8 -*-

// -------------------------------------------------------------------------
// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101
// -------------------------------------------------------------------------

/**
 * WebSocketクライアント
 * AIコアのWebSocket接続を管理
 */

export interface WebSocketMessage {
  type?: string;
  セッションID?: string;
  [key: string]: any;
}

export type MessageHandler = (message: WebSocketMessage) => void;

// WebSocketクライアントの公開インターフェース
export interface IWebSocketClient {
  connect(): Promise<string>;
  send(message: WebSocketMessage): void;
  on(messageType: string, handler: MessageHandler): void;
  off(messageType: string, handler?: MessageHandler): void;
  disconnect(): void;
  セッションID取得(): string | null;
  isConnected(): boolean;
  sendPing(): void;
  updateState(ボタン: any): void;
  sendChatMessage(message: string): void;
  sendInputText(text: string, チャンネル?: string): void;
  requestStream(data: any): void;
}

export class AIコアWebSocket implements IWebSocketClient {
  private ws: WebSocket | null = null;
  private セッションID: string | null = null;
  private messageHandlers: Map<string, MessageHandler[]> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 3000; // 3秒
  private isIntentionallyClosed = false;
  private isInitialConnection = true; // 初回接続フラグ
  private 要求セッションID: string | null = null; // 要求されたセッションID
  private 要求ソケット番号: string | null = null; // 要求されたソケット番号

  constructor(private url: string, セッションID?: string, ソケット番号?: string) {
    this.要求セッションID = セッションID || null;
    this.要求ソケット番号 = typeof ソケット番号 === 'string' ? ソケット番号 : null;
  }

  /**
   * WebSocket接続を確立
   */
  async connect(): Promise<string> {
    return new Promise((resolve, reject) => {
      try {
        console.log('[WebSocket] 接続開始:', this.url);
        this.ws = new WebSocket(this.url);
        this.isIntentionallyClosed = false;

        this.ws.onopen = () => {
          console.log('[WebSocket] 接続確立');
          this.reconnectAttempts = 0;
          this.isInitialConnection = false; // 初回接続完了

          // セッションIDを送信
          if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            const initMessage = {
              type: 'connect',
              セッションID: this.要求セッションID,
              ソケット番号: this.要求ソケット番号
            };
            console.log('[WebSocket] セッションID送信:', this.要求セッションID, 'ソケット番号:', this.要求ソケット番号);
            this.ws.send(JSON.stringify(initMessage));
          }
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);

            // デバッグ: 受信メッセージの詳細をログ出力
            const messageType = message.type || message.メッセージ識別 || 'unknown';
            const channel = message.チャンネル ?? 'null';
            console.log(`[WebSocket] 受信: type="${messageType}", チャンネル=${channel}`, message);

            // 初期化メッセージの場合、セッションIDを保存
            const initType = message.type || message.メッセージ識別;
            if (initType === 'init' && message.セッションID) {
              this.セッションID = message.セッションID;
              this.要求セッションID = message.セッションID; // 以降の再接続で使用
              if (message.ソケット番号 !== undefined && message.ソケット番号 !== null) {
                this.要求ソケット番号 = String(message.ソケット番号);
              }
              console.log('[WebSocket] セッションID確定:', this.セッションID);
              resolve(this.セッションID);
            }

            // 登録されたハンドラを実行
            this.handleMessage(message);
          } catch (error) {
            console.error('[WebSocket] メッセージ解析エラー:', error);
          }
        };

        this.ws.onerror = (error) => {
          console.error('[WebSocket] エラー:', error);
          console.error('[WebSocket] URL:', this.url);
          console.error('[WebSocket] ReadyState:', this.ws?.readyState);

          // 初回接続時のエラーはすぐにreject
          if (this.isInitialConnection) {
            console.log('[WebSocket] 初回接続エラー - フォールバックに切り替えます');
            reject(new Error('WebSocket connection error'));
          }
        };

        this.ws.onclose = (event) => {
          console.log('[WebSocket] 接続切断:', event.code, event.reason);
          this.セッションID = null;

          // 初回接続時のエラーはすぐにreject
          if (this.isInitialConnection) {
            console.log('[WebSocket] 初回接続失敗 - フォールバックに切り替えます');
            reject(new Error(`WebSocket connection closed: ${event.code} ${event.reason}`));
            return;
          }

          // 意図的な切断でない場合は再接続を試みる
          if (!this.isIntentionallyClosed && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`[WebSocket] 再接続試行 ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
            setTimeout(() => {
              this.connect().catch((err) => {
                console.error('[WebSocket] 再接続失敗:', err);
              });
            }, this.reconnectDelay);
          }
        };

        // 初期化タイムアウト（30秒）
        setTimeout(() => {
          if (!this.セッションID) {
            console.error('[WebSocket] 初期化タイムアウト (30秒)');
            reject(new Error('WebSocket initialization timeout'));
          }
        }, 30000);
      } catch (error) {
        console.error('[WebSocket] 接続エラー:', error);
        reject(error);
      }
    });
  }

  /**
   * メッセージを送信
   */
  send(message: WebSocketMessage): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
      console.log('[WebSocket] 送信:', message.type);
    } else {
      console.error('[WebSocket] 送信失敗: 接続されていません');
    }
  }

  /**
   * メッセージハンドラを登録
   */
  on(messageType: string, handler: MessageHandler): void {
    if (!this.messageHandlers.has(messageType)) {
      this.messageHandlers.set(messageType, []);
    }
    this.messageHandlers.get(messageType)!.push(handler);
  }

  /**
   * メッセージハンドラを削除
   */
  off(messageType: string, handler?: MessageHandler): void {
    if (!handler) {
      // ハンドラ指定なしの場合は全て削除
      this.messageHandlers.delete(messageType);
    } else {
      const handlers = this.messageHandlers.get(messageType);
      if (handlers) {
        const index = handlers.indexOf(handler);
        if (index !== -1) {
          handlers.splice(index, 1);
        }
      }
    }
  }

  /**
   * 受信メッセージを処理
   */
  private handleMessage(message: WebSocketMessage): void {
    // メッセージ識別をtypeに統一
    const messageType = message.メッセージ識別 || message.type || '';
    if (!message.type && message.メッセージ識別) {
      message.type = message.メッセージ識別;
    }
    const channel = message.チャンネル ?? null;

    // チャンネルが指定されている場合はチャンネル別イベントを配信
    if (channel !== null && channel !== undefined) {
      const channelSpecificType = `${messageType}_${channel}`;
      const channelHandlers = this.messageHandlers.get(channelSpecificType);
      if (channelHandlers) {
        channelHandlers.forEach((handler) => {
          try {
            handler(message);
          } catch (error) {
            console.error('[WebSocket] チャンネル別ハンドラエラー:', error);
          }
        });
      }
    }

    // チャンネル指定の有無に関わらず、共通イベントハンドラを実行
    const handlers = this.messageHandlers.get(messageType);
    if (handlers) {
      handlers.forEach((handler) => {
        try {
          handler(message);
        } catch (error) {
          console.error('[WebSocket] ハンドラエラー:', error);
        }
      });
    }

    // 全てのメッセージを受け取る汎用ハンドラ
    const allHandlers = this.messageHandlers.get('*');
    if (allHandlers) {
      allHandlers.forEach((handler) => {
        try {
          handler(message);
        } catch (error) {
          console.error('[WebSocket] 汎用ハンドラエラー:', error);
        }
      });
    }
  }

  /**
   * 接続を切断
   */
  disconnect(): void {
    if (this.ws) {
      this.isIntentionallyClosed = true;
      this.ws.close();
      this.ws = null;
      this.セッションID = null;
      console.log('[WebSocket] 切断完了');
    }
  }

  /**
   * セッションIDを取得
   */
  セッションID取得(): string | null {
    return this.セッションID;
  }

  /**
   * 接続状態を取得
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  /**
   * Pingを送信
   */
  sendPing(): void {
    this.send({
      type: 'ping',
      timestamp: Date.now()
    });
  }

  /**
   * ボタン状態を更新
   */
  updateState(ボタン: any): void {
    this.send({
      セッションID: this.セッションID,
      チャンネル: null,
      メッセージ識別: 'operations',
      メッセージ内容: { ボタン }
    });
  }

  /**
   * チャットメッセージを送信
   */
  sendChatMessage(message: string): void {
    console.warn('[WebSocket] sendChatMessage は廃止されました');
  }

  /**
   * テキスト入力を送信
   * 入力は常にチャンネルinputで送信、出力先チャンネルを別途指定
   */
  sendInputText(text: string, 出力先チャンネル: string): void {
    console.log(`[WebSocket] sendInputText: 入力チャンネル="input", 出力先チャンネル=${出力先チャンネル}, text="${text.substring(0, 50)}..."`);
    this.send({
      セッションID: this.セッションID,
      チャンネル: 'input',  // 入力は常にinput
      メッセージ識別: 'input_text',
      メッセージ内容: text,
      出力先チャンネル: 出力先チャンネル,  // バックエンドが参照して振り分け
      ファイル名: null,
      サムネイル画像: null
    });
  }

  /**
   * ストリーミングリクエストを送信
   */
  requestStream(data: any): void {
    console.warn('[WebSocket] requestStream は廃止されました');
  }
}

/**
 * WebSocket URLを生成
 */
export function createWebSocketUrl(path: string): string {
  // 現在のプロトコルとホストを使用（Vite proxyを経由）
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.hostname;
  const port = window.location.port;

  const url = `${protocol}//${host}:${port}${path}`;
  console.log('[WebSocket] URL生成:', url, '(DEV:', import.meta.env.DEV, ')');
  return url;
}


