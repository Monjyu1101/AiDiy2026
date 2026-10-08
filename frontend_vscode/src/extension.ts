import * as vscode from 'vscode';
import { randomBytes, randomUUID } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { コードモデル読込, コードモデル保存, モデル保存先 } from './model-preferences';
import { Hermes既定モデル, オフラインモデル候補, オフラインモデル保存先, オフライン実行 } from '../aidiy_code/src/offline';
import { 起動解決 } from './runner';
import { CodeConnection, コード選択 } from './code-connection';
import { ローカル接続先 } from '../aidiy_live/local-backend.cjs';
import type { Packet } from '../aidiy_live/src/protocol';
import { streamControlOf, visibleStreamContent, type コードパケット } from './protocol';

interface メッセージ { 種別: 'user' | 'assistant' | 'error'; 本文: string }
interface 会話 { メッセージ: メッセージ[]; 作業URI: string; コアセッションID?: string; HermesセッションID?: string; provider: string; model: string; モデル選択済み?: boolean }
interface 保存会話 extends 会話 { id: string; 更新日時: number; 初回依頼?: string }
interface 会話履歴 { 現在ID: string; 一覧: 保存会話[] }
interface 添付 { 名前: string; 本文: string }

class Hermesチャット implements vscode.WebviewViewProvider, vscode.Disposable {
  private view?: vscode.WebviewView;
  private 会話: 会話;
  private 添付?: 添付;
  private 実行中 = false;
  private 進捗: string[] = [];
  private 保存待ち: PromiseLike<void> = Promise.resolve();
  private 破棄済み = false;
  private 会話ID: string = randomUUID();
  private 履歴: 保存会話[] = [];
  private 最終モデル: { provider: string; model: string };
  private オフラインモデル: { provider: string; model: string };
  private readonly オフライン保存先 = オフラインモデル保存先(モデル保存先('code'));
  private readonly オフライン候補: { id: string; label: string }[];
  private オフラインジョブ?: ReturnType<typeof オフライン実行>;
  private 最終作業URI?: vscode.Uri;
  private connection?: CodeConnection;
  private 接続フォルダ = '';
  private readonly ログ = vscode.window.createOutputChannel('AiDiy (Code)');

  constructor(private readonly context: vscode.ExtensionContext) {
    const config = vscode.workspace.getConfiguration('aidiyHermes');
    this.オフライン候補 = オフラインモデル候補(context.extensionPath);
    const defaultModel = Hermes既定モデル(context.extensionPath, this.選択フォルダ()?.uri.fsPath ?? context.extensionPath);
    const offlineSaved = コードモデル読込(this.オフライン保存先);
    const offlineModel = offlineSaved?.provider === 'aidiy_hermes' && this.オフライン候補.some(item => item.id === offlineSaved.model)
      ? offlineSaved.model : this.オフライン候補.some(item => item.id === defaultModel) ? defaultModel : 'auto';
    this.オフラインモデル = { provider: 'aidiy_hermes', model: offlineModel };
    const old = context.workspaceState.get<会話>('会話');
    const saved = context.workspaceState.get<会話履歴>('会話履歴');
    this.履歴 = Array.isArray(saved?.一覧) ? saved.一覧.filter(item => typeof item?.id === 'string' && Array.isArray(item.メッセージ) && typeof item.作業URI === 'string') : [];
    const selected = this.履歴.find(item => item.id === saved?.現在ID);
    this.最終モデル = コードモデル読込() ?? context.globalState.get<{ provider: string; model: string }>('最終モデル')
      ?? (selected?.モデル選択済み ? { provider: selected.provider, model: selected.model }
      : old?.モデル選択済み ? { provider: old.provider, model: old.model }
        : { provider: config.get('provider', ''), model: config.get('model', '') });
    if (selected) {
      this.会話ID = selected.id;
      this.会話 = { ...selected, メッセージ: [...selected.メッセージ] };
    } else if (!saved && old && (old.メッセージ.length || old.コアセッションID)) {
      this.会話 = old;
      this.保存();
    } else {
      this.会話 = { メッセージ: [], 作業URI: '', ...this.最終モデル, モデル選択済み: true };
    }
    this.最終モデル = コード選択(this.最終モデル);
    Object.assign(this.会話, コード選択(this.会話));
    const 作業更新 = (editor: vscode.TextEditor | undefined) => {
      if (editor && vscode.workspace.getWorkspaceFolder(editor.document.uri)) this.最終作業URI = editor.document.uri;
      this.通知();
    };
    作業更新(vscode.window.activeTextEditor);
    context.subscriptions.push(
      vscode.window.onDidChangeActiveTextEditor(作業更新),
      vscode.workspace.onDidChangeWorkspaceFolders(() => { this.接続更新(); this.通知(); })
    );
  }

  resolveWebviewView(view: vscode.WebviewView): void {
    this.view = view;
    view.webview.options = { enableScripts: true, localResourceRoots: [vscode.Uri.joinPath(this.context.extensionUri, 'dist'), vscode.Uri.joinPath(this.context.extensionUri, 'media')] };
    const nonce = randomBytes(24).toString('hex');
    const resource = (path: string) => view.webview.asWebviewUri(vscode.Uri.joinPath(this.context.extensionUri, path)).toString();
    view.webview.html = readFileSync(join(this.context.extensionPath, 'media', 'chat.html'), 'utf8')
      .replace('<body>', '<body class="vscode-host">')
      .replaceAll('{{CSP}}', view.webview.cspSource).replaceAll('{{NONCE}}', nonce)
      .replaceAll('{{STYLE}}', resource('media/chat.css')).replaceAll('{{SCRIPT}}', resource('dist/webview.js'))
      .replaceAll('{{SEND_ICON}}', resource('media/sending.png'))
      .replaceAll('{{APP_ICON}}', resource('media/AiDiy.png'))
      .replaceAll('{{STOP_ICON}}', resource('media/abort.png'));
    view.webview.onDidReceiveMessage(message => {
      void this.受信(message).catch(error => this.エラー(error));
    }, undefined, this.context.subscriptions);
    view.onDidDispose(() => { if (this.view === view) { this.view = undefined; this.オフラインジョブ?.停止(); this.connection?.disconnect(); this.接続フォルダ = ''; } }, undefined, this.context.subscriptions);
    view.onDidChangeVisibility(() => this.通知(), undefined, this.context.subscriptions);
  }

  private フォルダ一覧() { return (vscode.workspace.workspaceFolders ?? []).filter(item => item.uri.scheme === 'file'); }
  private 選択フォルダ(): vscode.WorkspaceFolder | undefined {
    const folders = this.フォルダ一覧();
    const active = this.最終作業URI && vscode.workspace.getWorkspaceFolder(this.最終作業URI);
    return folders.find(item => item.uri.toString() === active?.uri.toString()) ?? folders[0];
  }
  private 現在フォルダ(): vscode.WorkspaceFolder | undefined {
    const folders = this.フォルダ一覧();
    // 再開する会話は開始時のフォルダを維持し、別プロジェクトへ履歴を渡さない。
    if (this.会話.作業URI) return folders.find(item => item.uri.toString() === this.会話.作業URI);
    return this.選択フォルダ();
  }
  private オフライン使用(): boolean { return !this.connection?.connected || Boolean(this.オフラインジョブ); }
  private 通知(): void {
    if (this.破棄済み) return;
    const folder = this.現在フォルダ();
    void this.view?.webview.postMessage({
      type: 'state', ...this.会話, 会話ID: this.会話ID, 添付: this.添付?.名前, 実行中: this.実行中, 進捗: this.進捗,
      ...(this.オフライン使用() ? this.オフラインモデル : {}),
      オフライン対応: true, 実行モード: this.オフライン使用() ? 'offline' : 'online',
      履歴: this.履歴.filter(item => item.作業URI === folder?.uri.toString())
        .sort((a, b) => b.更新日時 - a.更新日時)
        .map(item => ({ id: item.id, 題名: this.題名(item), 更新日時: item.更新日時 })),
      作業フォルダ: folder ? { 名前: folder.name, パス: folder.uri.fsPath } : null,
      新規可能: Boolean(this.選択フォルダ()), 信頼済み: vscode.workspace.isTrusted,
      モデル変更中: this.connection?.modelChanging === true, 接続済み: this.connection?.connected === true, 接続中: this.connection?.接続中 === true, 接続エラー: this.connection?.error || ''
    });
  }
  private 題名(item: 会話): string {
    return ('初回依頼' in item && typeof item.初回依頼 === 'string' ? item.初回依頼 : item.メッセージ.find(message => message.種別 === 'user')?.本文)?.replace(/\s+/g, ' ').slice(0, 160) || '新しい会話';
  }
  private 保存(更新日時を変更 = true): void {
    // 大量の会話による workspaceState 肥大化を防ぐ。AIコアの履歴はコアセッションIDで継続する。
    let サイズ = 0;
    const messages = this.会話.メッセージ.slice(-60).reverse().filter(item => (サイズ += item.本文.length) <= 2_000_000).reverse();
    if (this.会話.作業URI && (messages.length || this.会話.コアセッションID)) {
      const previous = this.履歴.find(item => item.id === this.会話ID);
      const snapshot = JSON.parse(JSON.stringify({ ...this.会話, メッセージ: messages, id: this.会話ID,
        初回依頼: previous?.初回依頼 ?? this.会話.メッセージ.find(item => item.種別 === 'user')?.本文.replace(/\s+/g, ' ').slice(0, 160),
        更新日時: 更新日時を変更 ? Date.now() : previous?.更新日時 ?? Date.now() })) as 保存会話;
      this.履歴 = [snapshot, ...this.履歴.filter(item => item.id !== this.会話ID)];
    }
    const snapshot: 会話履歴 = { 現在ID: this.会話ID, 一覧: this.履歴 };
    this.保存待ち = this.保存待ち.then(() => this.context.workspaceState.update('会話履歴', snapshot)).then(undefined, error => {
      this.ログ.appendLine(`会話を保存できません: ${String(error)}`);
    });
  }
  private エラー(error: unknown): void {
    const text = error instanceof Error ? error.message : String(error);
    this.会話.メッセージ.push({ 種別: 'error', 本文: text });
    this.保存(); this.通知();
  }
  private 信頼確認(): void {
    if (!vscode.workspace.isTrusted) throw new Error('ワークスペースを信頼してから実行してください。');
  }
  private 作業フォルダ(): vscode.WorkspaceFolder {
    const folder = this.現在フォルダ();
    if (!folder) throw new Error('作業フォルダを VS Code で開いてください。以前のフォルダを閉じた場合は、新しい会話を開始してください。');
    return folder;
  }
  private 起動設定(folder: vscode.WorkspaceFolder) {
    const config = vscode.workspace.getConfiguration('aidiyHermes', folder.uri);
    return 起動解決(config.get('cliPath', 'aidiy_hermes'), config.get('pythonPath', ''), folder.uri.fsPath);
  }

  private async 受信(message: unknown): Promise<void> {
    if (!message || typeof message !== 'object') return;
    const data = message as Record<string, unknown>;
    switch (data.メッセージ識別 ?? data.type) {
      case 'ready': this.接続更新(); this.通知(); break;
      case 'connect': this.信頼確認(); this.接続更新(true); break;
      case 'disconnect': this.connection?.disconnect(); break;
      case 'input_text':
      case 'input_request':
        if (typeof data.メッセージ内容 === 'string') {
          await this.送信(data.メッセージ内容, data.self_check_loop);
        }
        break;
      case 'cancel_run':
        if (this.オフラインジョブ) this.オフラインジョブ.停止();
        else this.connection?.send({ メッセージ識別: 'cancel_run', メッセージ内容: '強制停止！' });
        break;
      case 'new': this.新規(); break;
      case 'selectHistory': if (typeof data.id === 'string') this.履歴選択(data.id); break;
      case 'deleteHistory': if (typeof data.id === 'string') this.履歴削除(data.id); break;
      case 'attach': await this.選択添付(); break;
      case 'removeAttachment': if (!this.実行中) { this.添付 = undefined; this.通知(); } break;
      case 'settings': await vscode.commands.executeCommand('aidiyHermes.settings'); break;
      case 'chooseModel': await this.モデル候補通知(data.provider); break;
      case 'setModel': await this.モデル反映(data.provider, data.model); break;
      case 'terminal': await this.ターミナル(); break;
      case 'logs': this.ログ.show(true); break;
      case 'link':
        if (typeof data.url === 'string' && /^https?:\/\//i.test(data.url)) await vscode.env.openExternal(vscode.Uri.parse(data.url));
        break;
      case 'copy': if (typeof data.text === 'string') await vscode.env.clipboard.writeText(data.text); break;
    }
  }

  private 接続更新(force = false): void {
    const folder = this.現在フォルダ();
    if (!vscode.workspace.isTrusted || !folder || this.破棄済み) { this.connection?.disconnect(); return; }
    if (!this.connection) this.connection = new CodeConnection(
      ローカル接続先(this.context.extensionPath, folder.uri.fsPath), packet => {
        if (!this.オフラインジョブ) this.パケット受信(packet);
      }, () => {
        if (this.connection?.connected) {
          this.会話.コアセッションID = this.connection.session;
          this.会話.provider = this.connection.model.provider; this.会話.model = this.connection.model.model;
          this.保存(false);
        } else if (!this.オフラインジョブ) this.実行中 = false;
        this.通知();
      });
    if (!force && this.接続フォルダ === folder.uri.fsPath) return;
    if (!this.会話.作業URI) this.会話.作業URI = folder.uri.toString();
    this.接続フォルダ = folder.uri.fsPath;
    this.connection.start(folder.uri.fsPath, this.会話, this.会話.コアセッションID, this.会話.メッセージ);
  }
  private パケット受信(packet: Packet | コードパケット): void {
    if (this.破棄済み) return;
    void this.view?.webview.postMessage(packet);
    const text = typeof packet.メッセージ内容 === 'string' ? packet.メッセージ内容 : '';
    if (packet.メッセージ識別 === 'output_stream') {
      const control = streamControlOf(text);
      if (control === 'start') this.実行中 = true;
      else if (control === 'cancel' && !this.オフラインジョブ) this.実行中 = false;
      else if (!control && text) {
        const line = visibleStreamContent(text);
        this.ログ.appendLine(line); this.進捗 = [...this.進捗, line.slice(0, 4000)].slice(-100);
      }
    } else if (packet.メッセージ識別 === 'output_text' || packet.メッセージ識別 === 'output') {
      if (text) this.会話.メッセージ.push({ 種別: 'assistant', 本文: text });
      if (!this.オフラインジョブ) this.実行中 = false;
    } else if (['error', 'cancel_run', 'output_end'].includes(packet.メッセージ識別 || '')) {
      if (text) this.会話.メッセージ.push({ 種別: 'error', 本文: text });
      if (!this.オフラインジョブ) this.実行中 = false;
    } else return;
    this.保存(); this.通知();
  }
  private async 候補取得(provider = ''): Promise<{ id: string; label: string }[]> {
    this.信頼確認(); this.接続更新();
    if (this.オフライン使用()) {
      return provider === 'aidiy_hermes' ? this.オフライン候補 : provider ? [] : [{ id: 'aidiy_hermes', label: 'aidiy_hermes' }];
    }
    if (!this.connection) throw new Error('作業フォルダを開いてください。');
    return this.connection.catalog(provider);
  }

  private async モデル候補通知(value: unknown): Promise<void> {
    if (this.実行中 || typeof value !== 'string' || value.length > 200) return;
    try {
      const items = await this.候補取得(value);
      if (!this.破棄済み) await this.view?.webview.postMessage({ type: 'modelCatalog', provider: value, items });
    } catch (error) {
      if (!this.破棄済み) await this.view?.webview.postMessage({ type: 'modelCatalogError', provider: value, message: error instanceof Error ? error.message : String(error) });
    }
  }

  private async モデル反映(providerValue: unknown, modelValue: unknown): Promise<void> {
    if (this.実行中 || typeof providerValue !== 'string' || typeof modelValue !== 'string'
      || providerValue.length > 200 || modelValue.length > 300 || modelValue === '__manual__') return;
    const selectedProvider = providerValue.trim();
    const selectedModel = modelValue.trim();
    this.信頼確認();
    if (this.オフライン使用()) {
      if (selectedProvider !== 'aidiy_hermes' || !this.オフライン候補.some(item => item.id === selectedModel))
        throw new Error('オフライン用のHermesモデルを選択してください。');
      this.オフラインモデル = コードモデル保存({ provider: selectedProvider, model: selectedModel }, this.オフライン保存先);
      this.通知(); return;
    }
    this.作業フォルダ();
    if (selectedProvider) {
      const providers = await this.候補取得();
      if (!providers.some(item => item.id === selectedProvider)) throw new Error('選択したプロバイダを確認できません。');
    }
    if (!this.connection) throw new Error('作業フォルダを開いてください。');
    const selected = コード選択({ provider: selectedProvider, model: selectedModel });
    await this.connection.setModel(selected);
    const persisted = コードモデル保存(selected);
    this.会話.provider = persisted.provider; this.会話.model = persisted.model;
    this.会話.モデル選択済み = true;
    this.最終モデル = { provider: this.会話.provider, model: this.会話.model };
    void this.context.globalState.update('最終モデル', this.最終モデル).then(undefined, error => this.ログ.appendLine(`モデルを保存できません: ${String(error)}`));
    this.保存(false); this.通知();
  }

  private async 送信(本文: string, 検証ループ回数: unknown = 1): Promise<void> {
    if (this.実行中 || !本文.trim()) return;
    if (this.connection?.modelChanging) throw new Error('モデルを変更しています。');
    this.信頼確認();
    const { provider, model } = this.会話;
    if (本文.length > 200_000 || provider.length > 200 || model.length > 300) throw new Error('入力が長すぎます。文章を分けて送信してください。');
    const folder = this.作業フォルダ();
    const fullPrompt = this.添付 ? `${本文}\n\n--- 選択コード: ${this.添付.名前} ---\n${this.添付.本文}\n--- 選択コードここまで ---` : 本文;
    const self_check_loop = typeof 検証ループ回数 === 'number' && Number.isInteger(検証ループ回数) ? Math.max(0, Math.min(3, 検証ループ回数)) : 1;
    const offline = this.オフライン使用();
    const launch = offline ? this.起動設定(folder) : undefined;
    if (!offline && !this.connection?.send({ メッセージ識別: 'input_text', メッセージ内容: fullPrompt, self_check_loop }))
      throw new Error('AIコアが未接続のため送信できません。');
    this.会話.作業URI = folder.uri.toString();
    this.会話.メッセージ.push({ 種別: 'user', 本文: fullPrompt });
    this.添付 = undefined; this.実行中 = true; this.進捗 = [];
    this.ログ.clear(); this.保存(); this.通知();
    void this.view?.webview.postMessage({ type: 'accepted' });
    if (offline) {
      try {
        const job = オフライン実行(this.context.extensionPath, folder.uri.fsPath, this.オフラインモデル.model,
          fullPrompt, this.会話.HermesセッションID, packet => this.パケット受信(packet), launch);
        this.オフラインジョブ = job;
        void job.完了.then(result => {
          if (this.破棄済み) return;
          if (result.セッションID || result.セッション復旧) this.会話.HermesセッションID = result.セッションID;
          if (result.停止理由) this.エラー(result.停止理由);
          else if (result.終了コード !== 0) this.エラー(`Hermesが終了コード ${result.終了コード} で終了しました。`);
        }).catch(error => { if (!this.破棄済み) this.エラー(error); }).finally(() => {
          if (this.オフラインジョブ !== job) return;
          this.オフラインジョブ = undefined; this.実行中 = false;
          if (!this.破棄済み) { this.保存(); this.通知(); }
        });
      } catch (error) {
        this.実行中 = false; this.通知(); throw error;
      }
    }
  }

  新規(): void {
    if (this.実行中) return;
    this.会話 = { メッセージ: [], 作業URI: this.選択フォルダ()?.uri.toString() ?? '', ...this.最終モデル, モデル選択済み: true };
    this.会話ID = randomUUID();
    this.添付 = undefined; this.進捗 = []; this.保存(); this.接続更新(true); this.通知();
    void this.view?.webview.postMessage({ type: 'showConversation' });
  }
  private 履歴選択(id: string): void {
    if (this.実行中) return;
    const entry = this.履歴.find(item => item.id === id && item.作業URI === this.現在フォルダ()?.uri.toString());
    if (!entry) return;
    this.会話ID = entry.id;
    this.会話 = { ...entry, メッセージ: [...entry.メッセージ] };
    this.添付 = undefined; this.進捗 = [];
    this.保存(false); this.接続更新(true); this.通知();
  }
  private 履歴削除(id: string): void {
    if (this.実行中) return;
    const entry = this.履歴.find(item => item.id === id && item.作業URI === this.現在フォルダ()?.uri.toString());
    if (!entry) return;
    this.履歴 = this.履歴.filter(item => item.id !== id);
    if (this.会話ID === id) {
      this.会話 = { メッセージ: [], 作業URI: entry.作業URI, ...this.最終モデル, モデル選択済み: true };
      this.会話ID = randomUUID(); this.添付 = undefined; this.進捗 = []; this.接続更新(true);
    }
    this.保存(); this.通知();
  }
  async 選択添付(): Promise<void> {
    this.信頼確認();
    if (this.実行中) return;
    const editor = vscode.window.activeTextEditor;
    if (!editor || editor.selection.isEmpty) { void vscode.window.showInformationMessage('エディターでコードを選択してから添付してください。'); return; }
    const text = editor.document.getText(editor.selection);
    if (text.length > 80_000) throw new Error('選択コードが長すぎます。80,000 文字以内で選択してください。');
    this.添付 = { 名前: `${vscode.workspace.asRelativePath(editor.document.uri)}:${editor.selection.start.line + 1}–${editor.selection.end.line + 1}`, 本文: text };
    await vscode.commands.executeCommand('aidiyHermes.chat.focus'); this.通知();
  }
  async ターミナル(): Promise<void> {
    this.信頼確認();
    const folder = this.作業フォルダ();
    const 起動 = this.起動設定(folder);
    vscode.window.createTerminal({ name: 'AiDiy (Code)', shellPath: 起動.実行ファイル, shellArgs: 起動.引数, cwd: folder.uri.fsPath, env: { PYTHONIOENCODING: 'utf-8', PYTHONUTF8: '1', TERMINAL_CWD: folder.uri.fsPath } }).show();
  }
  ログ表示(): void { this.ログ.show(true); }
  dispose(): void {
    this.破棄済み = true;
    if (this.オフラインジョブ) this.オフラインジョブ.停止();
    else if (this.実行中) this.connection?.send({ メッセージ識別: 'cancel_run' });
    this.connection?.dispose(); this.ログ.dispose();
  }
}

export function activate(context: vscode.ExtensionContext): void {
  const chat = new Hermesチャット(context);
  const command = (name: string, action: () => unknown) => vscode.commands.registerCommand(name, async () => {
    try { await action(); } catch (error) { void vscode.window.showErrorMessage(error instanceof Error ? error.message : String(error)); }
  });
  context.subscriptions.push(chat,
    vscode.window.registerWebviewViewProvider('aidiyHermes.chat', chat, { webviewOptions: { retainContextWhenHidden: true } }),
    command('aidiyHermes.open', () => vscode.commands.executeCommand('aidiyHermes.chat.focus')),
    command('aidiyHermes.newChat', () => chat.新規()),
    command('aidiyHermes.attachSelection', () => chat.選択添付()),
    command('aidiyHermes.settings', () => vscode.commands.executeCommand('workbench.action.openSettings', '@ext:aidiy.aidiy-code')),
    command('aidiyHermes.terminal', () => chat.ターミナル()),
    command('aidiyHermes.logs', () => chat.ログ表示())
  );
}
