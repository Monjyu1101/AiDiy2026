export type Packet = {
  メッセージ識別?: string; セッションID?: string; チャンネル?: string;
  メッセージ内容?: unknown; ファイル名?: string; [key: string]: unknown;
};
export interface LiveSocket {
  readyState: number; bufferedAmount: number;
  onopen: ((event: Event) => void) | null; onmessage: ((event: MessageEvent) => void) | null;
  onerror: ((event: Event) => void) | null; onclose: ((event: CloseEvent) => void) | null;
  send(data: string): void; close(): void;
}

export function 入力レート(provider: string): number { return provider.includes('openai') ? 24000 : 16000; }
export function 音声入力(base64: string): Packet {
  return { チャンネル: 'audio', メッセージ識別: 'input_audio', メッセージ内容: 'audio/pcm', ファイル名: base64, サムネイル画像: null };
}
export function 音声操作(mic: boolean, speaker: boolean): Packet {
  return { チャンネル: 'input', メッセージ識別: 'operations', メッセージ内容: { ボタン: { マイク: mic, スピーカー: speaker } } };
}

// init 到着で確定する。途中の失敗では3ソケット全部を閉じる。
export class LiveConnection {
  private sockets = new Map<string, LiveSocket>();
  private generation = 0;
  session = '';
  constructor(private url: string, private onPacket: (packet: Packet) => void, private onLost: () => void,
    private createSocket: (url: string) => LiveSocket = url => new WebSocket(url)) {}

  async connect(prepare?: (session: string) => Promise<void>, codeBasePath = '') {
    this.disconnect();
    const generation = this.generation;
    try {
      const session = await this.open('input', '', generation, codeBasePath);
      if (generation !== this.generation) throw new Error('接続を中断しました。');
      this.session = session;
      // LiveAIを起動するaudioソケットより先に、セッションのプロジェクトを設定する。
      await prepare?.(this.session);
      if (generation !== this.generation) throw new Error('接続を中断しました。');
      await this.open('0', this.session, generation, codeBasePath);
      if (generation !== this.generation) throw new Error('接続を中断しました。');
      await this.open('audio', this.session, generation, codeBasePath);
    } catch (error) { if (generation === this.generation) this.disconnect(); throw error; }
  }
  private open(channel: string, session: string, generation: number, codeBasePath: string): Promise<string> {
    return new Promise((resolve, reject) => {
      const socket = this.createSocket(this.url);
      this.sockets.set(channel, socket);
      let ready = false;
      const timer = setTimeout(() => { reject(new Error('接続がタイムアウトしました。')); socket.close(); }, 30000);
      socket.onopen = () => socket.send(JSON.stringify({ type: 'connect', セッションID: session || null, ソケット番号: channel,
        ...(codeBasePath ? { CODE_BASE_PATH: codeBasePath } : {}) }));
      socket.onmessage = event => {
        if (generation !== this.generation) return;
        let packet: Packet;
        try { packet = JSON.parse(String(event.data)); } catch { return; }
        if (!ready && packet.メッセージ識別 === 'error') {
          clearTimeout(timer); reject(new Error(String(packet.メッセージ内容 || '接続に失敗しました。')));
        }
        if (packet.メッセージ識別 === 'init' && packet.セッションID) {
          if (session && packet.セッションID !== session) { reject(new Error('セッションが一致しません。')); socket.close(); return; }
          ready = true; clearTimeout(timer); resolve(packet.セッションID);
        }
        this.onPacket(packet);
      };
      socket.onerror = () => { clearTimeout(timer); if (!ready) reject(new Error('バックエンドに接続できません。')); };
      socket.onclose = () => {
        clearTimeout(timer);
        if (!ready) reject(new Error('接続が閉じられました。'));
        if (generation === this.generation) { this.disconnect(); this.onLost(); }
      };
    });
  }
  send(channel: string, packet: Packet): boolean {
    const socket = this.sockets.get(channel);
    if (!socket || socket.readyState !== 1 || socket.bufferedAmount > 128000) return false;
    socket.send(JSON.stringify({ ...packet, セッションID: this.session })); return true;
  }
  disconnect() {
    ++this.generation;
    for (const socket of this.sockets.values()) socket.close();
    this.sockets.clear(); this.session = '';
  }
}
