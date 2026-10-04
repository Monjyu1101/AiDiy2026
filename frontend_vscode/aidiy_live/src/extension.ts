import * as vscode from 'vscode';
import { randomBytes } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { LiveHost, microphonePython, backendUrl } from './host';

class LiveView implements vscode.WebviewViewProvider, vscode.Disposable {
  private host?: LiveHost;
  private view?: vscode.WebviewView;
  private browser?: Awaited<ReturnType<typeof import('./server').ライブ起動>>;
  private generation = 0;
  ready = false;
  constructor(private context: vscode.ExtensionContext) {}
  private folder() {
    const uri = vscode.window.activeTextEditor?.document.uri;
    const folder = (uri ? vscode.workspace.getWorkspaceFolder(uri) : undefined)
      || vscode.workspace.workspaceFolders?.find(folder => folder.uri.scheme === 'file');
    return folder?.uri.scheme === 'file' ? { 名前: folder.name, パス: folder.uri.fsPath } : null;
  }
  folderChanged() { void this.view?.webview.postMessage({ type: 'folder', 作業フォルダ: this.folder() }); }
  resolveWebviewView(view: vscode.WebviewView) {
    this.host?.dispose(); this.view = view; this.ready = false;
    const config = vscode.workspace.getConfiguration('aidiyLive');
    const backend = backendUrl(config.get<string>('backendUrl', 'http://127.0.0.1:8091')).origin;
    view.webview.options = { enableScripts: true, localResourceRoots: [vscode.Uri.joinPath(this.context.extensionUri, 'media'), vscode.Uri.joinPath(this.context.extensionUri, 'dist')] };
    const resource = (path: string) => view.webview.asWebviewUri(vscode.Uri.joinPath(this.context.extensionUri, path)).toString();
    const nonce = randomBytes(24).toString('hex');
    const csp = `default-src 'none'; style-src ${view.webview.cspSource}; script-src 'nonce-${nonce}' ${view.webview.cspSource}; img-src ${view.webview.cspSource}; connect-src ${view.webview.cspSource}; worker-src ${view.webview.cspSource} blob:; base-uri 'none';`;
    const boot = JSON.stringify({ host: true, backend, captureUrl: resource('media/capture.js'), 作業フォルダ: this.folder() }).replaceAll('<', '\\u003c');
    view.webview.html = readFileSync(join(this.context.extensionPath, 'media/index.html'), 'utf8')
      .replace('<head>', `<head><meta http-equiv="Content-Security-Policy" content="${csp}">`)
      .replace('href="style.css"', `href="${resource('media/style.css')}"`)
      .replace('<script src="view.js" defer>', `<script nonce="${nonce}" src="${resource('dist/view.js')}" defer>`)
      .replace('src="sending.png"', `src="${resource('dist/sending.png')}"`)
      .replace('src="AiDiy.png"', `src="${resource('dist/AiDiy.png')}"`)
      .replace('href="AiDiy.png"', `href="${resource('dist/AiDiy.png')}"`)
      .replace('</head>', `<script id="live-config" nonce="${nonce}" type="application/json">${boot}</script></head>`);
    const host = this.host = new LiveHost(backend, message => { if (this.view === view) void view.webview.postMessage(message); }, () => microphonePython(
      vscode.workspace.getConfiguration('aidiyLive').get<string>('pythonPath', ''),
      (vscode.workspace.workspaceFolders || []).filter(folder => folder.uri.scheme === 'file').map(folder => folder.uri.fsPath)
    ), join(this.context.extensionPath, 'dist/microphone.py'));
    const resources = [
      view.webview.onDidReceiveMessage(message => {
        if (!vscode.workspace.isTrusted) { host.stop(); return; }
        if (message?.type === 'ui-ready') this.ready = true;
        else if (message?.type === 'standalone') void this.standalone().catch(error => { void vscode.window.showErrorMessage(String(error)); });
        else void host.receive(message).catch(error => { void vscode.window.showErrorMessage(String(error)); });
      }),
      view.onDidChangeVisibility(() => { if (!view.visible) host.stop(); }),
    ];
    view.onDidDispose(() => { host.dispose(); resources.forEach(resource => resource.dispose()); if (this.view === view) { this.view = undefined; this.host = undefined; } });
  }
  stop() { this.host?.stop(); }
  backendChanged() { this.host?.backend(vscode.workspace.getConfiguration('aidiyLive').get<string>('backendUrl', 'http://127.0.0.1:8091')); }
  async standalone() {
    if (!vscode.workspace.isTrusted) throw new Error('ライブ会話は信頼済みのワークスペースで開いてください。');
    this.stop();
    const generation = ++this.generation;
    await this.browser?.close(); this.browser = undefined;
    const backend = backendUrl(vscode.workspace.getConfiguration('aidiyLive').get<string>('backendUrl', 'http://127.0.0.1:8091')).origin;
    // 配布済み Live 拡張だけで使えるブラウザ版。Code / 開発フォルダに依存しない。
    const { ライブ起動 } = await import('./server');
    const server = await ライブ起動(this.context.extensionPath, backend, true, this.folder()?.パス || null);
    if (generation !== this.generation) { await server.close(); return; }
    this.browser = server;
    await vscode.env.openExternal(vscode.Uri.parse(server.url));
  }
  dispose() { ++this.generation; this.host?.dispose(); this.host = undefined; this.view = undefined; void this.browser?.close(); this.browser = undefined; }
}

export function activate(context: vscode.ExtensionContext) {
  const live = new LiveView(context);
  context.subscriptions.push(live,
    vscode.window.registerWebviewViewProvider('aidiyLive.chat', live),
    vscode.commands.registerCommand('aidiyLive.open', () => vscode.commands.executeCommand('aidiyLive.chat.focus')),
    vscode.commands.registerCommand('aidiyLive.stop', () => live.stop()),
    vscode.commands.registerCommand('aidiyLive.standalone', () => live.standalone()),
    vscode.commands.registerCommand('aidiyLive.settings', () => vscode.commands.executeCommand('workbench.action.openSettings', '@ext:aidiy.aidiy-live')),
    vscode.workspace.onDidChangeWorkspaceFolders(() => live.folderChanged()),
    vscode.window.onDidChangeActiveTextEditor(() => live.folderChanged()),
    vscode.workspace.onDidChangeConfiguration(event => {
      if (event.affectsConfiguration('aidiyLive.backendUrl')) {
        try { live.backendChanged(); } catch (error) { void vscode.window.showErrorMessage(String(error)); }
      }
    })
  );
  return { stop: () => live.stop(), getState: () => ({ ready: live.ready }) };
}
