import { backendUrl } from '../aidiy_live/src/host';
import { 接続エラー詳細 } from '../aidiy_live/src/connection-error';
import type { LiveSocket, Packet } from '../aidiy_live/src/protocol';
import type { CodeModel } from './model-preferences';

const MODEL_KEYS: Record<string, string> = {
  claude_sdk: 'CODE_CLAUDE_SDK_MODEL', claude_cli: 'CODE_CLAUDE_CLI_MODEL',
  copilot_cli: 'CODE_COPILOT_CLI_MODEL', codex_cli: 'CODE_CODEX_CLI_MODEL',
  antigravity_cli: 'CODE_ANTIGRAVITY_CLI_MODEL', grok_cli: 'CODE_GROK_CLI_MODEL',
  opencode_cli: 'CODE_OPENCODE_CLI_MODEL', aidiy_hermes: 'CODE_AIDIY_HERMES_MODEL',
  claude_ollama: 'CODE_CLAUDE_OLLAMA_MODEL', codex_ollama: 'CODE_CODEX_OLLAMA_MODEL',
};
// 旧ランチャー・保存値を AIコアの Code AI 名へ移行する。
export function コード選択(value: CodeModel): CodeModel {
  const aliases: Record<string, string> = {
    'copilot-cli': 'copilot_cli', 'codex-cli': 'codex_cli', 'claude-code': 'claude_cli',
    'antigravity-cli': 'antigravity_cli', 'grok-cli': 'grok_cli', 'opencode-cli': 'opencode_cli', hermes_cli: 'aidiy_hermes',
  };
  const provider = value.provider.trim();
  const model = value.model.trim();
  const hermesProvider = provider && !aliases[provider] && !MODEL_KEYS[provider] && !provider.endsWith('_cli');
  return { provider: aliases[provider] || (hermesProvider ? 'aidiy_hermes' : provider),
    model: hermesProvider && model && model !== 'auto' ? `${provider}/${model}` : model };
}
type Info = { available_models: { code_models: Record<string, Record<string, string>> }; モデル設定: Record<string, string> };

/** Live と同じ AIコアへ input → 設定 API → コード出力(1) の順に接続する。 */
export class CodeConnection {
  private target: URL;
  private sockets = new Map<string, LiveSocket>();
  private pending = new Set<() => void>();
  private requests = new Set<AbortController>();
  private generation = 0;
  private retry?: ReturnType<typeof setTimeout>;
  private heartbeat?: ReturnType<typeof setInterval>;
  private enabled = false;
  private connecting = false;
  private disposed = false;
  private outputHistory: string[] = [];
  private replay = new Map<string, number>();
  connected = false;
  modelChanging = false;
  session = '';
  model: CodeModel = { provider: '', model: '' };
  error = '';
  get 接続中() { return this.connecting; }
  constructor(backend: string, private onPacket: (packet: Packet) => void, private onState: () => void,
    private createSocket: (url: string) => LiveSocket = url => new WebSocket(url), private request: typeof fetch = fetch) {
    this.target = backendUrl(backend);
  }
  private project = '';
  start(project: string, model: CodeModel, session = '', messages: { 種別: string; 本文: string }[] = []) {
    this.disconnect();
    this.project = project; this.model = コード選択(model); this.session = session;
    this.outputHistory = messages.filter(item => item.種別 === 'assistant').map(item => item.本文).slice(-60);
    this.enabled = true; void this.connect();
  }
  private async api(path: '取得' | '設定', body: object): Promise<Info> {
    const controller = new AbortController(); this.requests.add(controller);
    const timer = setTimeout(() => controller.abort(), 30000);
    try {
      const response = await this.request(new URL(`/core/AIコア/モデル情報/${path}`, this.target), {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body), signal: controller.signal,
      });
      const value = await response.json() as { status: string; message?: string; data: Info };
      if (!response.ok || value.status !== 'OK') throw new Error(value.message || 'モデル情報を取得・設定できません。');
      return value.data;
    } catch (error) { throw new Error(接続エラー詳細(this.target, error)); }
    finally { clearTimeout(timer); this.requests.delete(controller); }
  }
  async catalog(provider = '') {
    const info = await this.api('取得', { セッションID: '' });
    const models = info.available_models.code_models;
    return provider ? Object.entries(models[provider] || {}).map(([id, label]) => ({ id, label }))
      : Object.keys(models).filter(id => MODEL_KEYS[id]).map(id => ({ id, label: id }));
  }
  async setModel(value: CodeModel) {
    if (this.modelChanging) throw new Error('モデルを変更しています。');
    this.modelChanging = true; this.onState();
    const generation = this.generation;
    try {
      let model = コード選択(value);
      if (model.provider && !MODEL_KEYS[model.provider]) throw new Error('コードAIを選び直してください。');
      const info = await this.api('取得', { セッションID: '' });
      if (generation !== this.generation || this.disposed) throw new Error('接続が変わりました。モデルを選び直してください。');
      if (model.provider && !Object.hasOwn(info.available_models.code_models, model.provider)) throw new Error('コードAIを選び直してください。');
      if (!model.provider) model = this.defaultModel(info);
      if (this.connected) {
        await this.configure(model);
        if (generation !== this.generation || !this.connected) throw new Error('接続が切れました。モデルを選び直してください。');
      } else if (this.connecting) {
        this.start(this.project, model, this.session, this.outputHistory.map(本文 => ({ 種別: 'assistant', 本文 }))); return;
      }
      this.model = model;
    } finally {
      this.modelChanging = false; this.onState();
    }
  }
  private defaultModel(info: Info): CodeModel {
    const settings = info.モデル設定, provider = settings.CODE_AI1_NAME;
    return { provider, model: settings.CODE_AI1_MODEL || settings[MODEL_KEYS[provider]] || '' };
  }
  private async configure(model: CodeModel) {
    if (!model.provider) return;
    await this.api('設定', { セッションID: this.session,
      モデル設定: { CODE_AI1_NAME: model.provider, CODE_AI1_MODEL: model.model }, save: false });
  }
  private async connect() {
    if (!this.enabled || this.disposed || this.connecting || this.connected) return;
    this.connecting = true;
    const generation = this.generation;
    this.onState();
    const current = () => generation === this.generation && this.enabled && !this.disposed;
    try {
      const session = await this.open('input', this.session, generation);
      if (!current()) return;
      this.session = session;
      const info = await this.api('取得', { セッションID: this.session });
      if (!current()) return;
      if (!this.model.provider) this.model = { ...this.defaultModel(info), ...(this.model.model ? { model: this.model.model } : {}) };
      if (this.model.provider !== info.モデル設定.CODE_AI1_NAME
          || (this.model.model !== info.モデル設定.CODE_AI1_MODEL && this.model.model !== this.defaultModel(info).model))
        await this.configure(this.model);
      if (!current()) return;
      this.replay.clear();
      for (const text of this.outputHistory) this.replay.set(text, (this.replay.get(text) || 0) + 1);
      await this.open('1', this.session, generation);
      if (!current()) return;
      this.connected = true; this.error = ''; this.connecting = false;
      this.heartbeat = setInterval(() => this.send({ type: 'ping' }), 20000);
      this.onState();
    } catch (error) {
      if (!current()) return;
      this.error = error instanceof Error ? error.message : String(error);
      this.lost();
    }
  }
  private open(channel: string, session: string, generation: number): Promise<string> {
    return new Promise((resolve, reject) => {
      const url = new URL('/core/ws/AIコア', this.target); url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
      const socket = this.createSocket(url.toString()); this.sockets.set(channel, socket);
      let ready = false;
      const cancel = () => { clearTimeout(timer); this.pending.delete(cancel); reject(new Error('接続を中断しました。')); };
      const timer = setTimeout(() => { cancel(); socket.close(); }, 30000);
      this.pending.add(cancel);
      socket.onopen = () => {
        if (generation !== this.generation) return;
        socket.send(JSON.stringify({ type: 'connect', セッションID: session || null, ソケット番号: channel, CODE_BASE_PATH: this.project }));
      };
      socket.onmessage = event => {
        if (generation !== this.generation) return;
        let packet: Packet;
        try { packet = JSON.parse(String(event.data)); } catch { return; }
        if (!ready && packet.メッセージ識別 === 'error') {
          clearTimeout(timer); this.pending.delete(cancel); reject(new Error(String(packet.メッセージ内容))); return;
        }
        if (!ready && packet.メッセージ識別 === 'init' && packet.セッションID) {
          if (session && session !== packet.セッションID) { cancel(); return; }
          ready = true; clearTimeout(timer); this.pending.delete(cancel); resolve(packet.セッションID);
        }
        // input は制御用。正式な出力とエコーはコード用ソケットで受ける。
        if (channel === 'input' && ready && packet.メッセージ識別 === 'error') this.onPacket(packet);
        if (channel === '1' && ready) {
          if ((packet.メッセージ識別 === 'output_text' || packet.メッセージ識別 === 'output') && typeof packet.メッセージ内容 === 'string') {
            const text = packet.メッセージ内容, count = this.replay.get(text) || 0;
            if (count) { this.replay.set(text, count - 1); return; }
            this.outputHistory = [...this.outputHistory, text].slice(-60);
          }
          if (packet.メッセージ識別 === 'output_stream' && packet.メッセージ内容 === '\x02') this.replay.clear();
          this.onPacket(packet);
        }
      };
      socket.onerror = () => { if (generation === this.generation) { this.error = 'AIコアに接続できません。'; this.lost(); } };
      socket.onclose = () => { if (generation === this.generation) this.lost(); };
    });
  }
  send(packet: Packet): boolean {
    const socket = this.sockets.get('input');
    if (!this.connected || this.modelChanging || socket?.readyState !== 1 || socket.bufferedAmount > 128000) return false;
    try {
      socket.send(JSON.stringify({ ...packet, セッションID: this.session, チャンネル: '1' }));
      if (packet.メッセージ識別 === 'input_text' || packet.メッセージ識別 === 'input_request') this.replay.clear();
      return true;
    }
    catch { this.lost(); return false; }
  }
  private clear() {
    ++this.generation;
    clearTimeout(this.retry); this.retry = undefined;
    clearInterval(this.heartbeat); this.heartbeat = undefined;
    for (const cancel of [...this.pending]) cancel();
    for (const controller of this.requests) controller.abort();
    for (const socket of this.sockets.values()) socket.close(); this.sockets.clear();
    this.connected = false; this.connecting = false;
  }
  private lost() {
    this.clear(); this.onState();
    if (this.enabled && !this.disposed) this.retry = setTimeout(() => { this.retry = undefined; void this.connect(); }, 5000);
  }
  disconnect() { this.enabled = false; this.clear(); this.onState(); }
  dispose() { this.disposed = true; this.disconnect(); }
}
