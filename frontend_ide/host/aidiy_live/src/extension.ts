/*!
 * -*- coding: utf-8 -*-
 *
 * -------------------------------------------------------------------------
 * COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
 * Licensed under "AiDiy 公開利用ライセンス v1.1".
 * Commercial use requires prior written consent from all copyright holders.
 * See LICENSE for full terms. Thank you for keeping the rules.
 * https://github.com/monjyu1101/AiDiy2026
 * -------------------------------------------------------------------------
 */

import * as vscode from 'vscode';
import { developmentHtml } from '../../../vscode-html';
import { randomBytes } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { LiveHost, microphonePython } from './host';
import { ローカル接続先 } from '../local-backend.cjs';
import { ライブモデル読込, ライブモデル保存 } from '../../src/model-preferences';

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
    const backend = ローカル接続先(this.context.extensionPath, this.folder()?.パス);
    view.webview.options = { enableScripts: true, localResourceRoots: [vscode.Uri.joinPath(this.context.extensionUri, 'media'), vscode.Uri.joinPath(this.context.extensionUri, 'dist')] };
    const resource = (path: string) => view.webview.asWebviewUri(vscode.Uri.joinPath(this.context.extensionUri, path)).toString();
    const nonce = randomBytes(24).toString('hex');
    view.webview.html = developmentHtml(resource, view.webview.cspSource, nonce, { kind: 'live', live: { host: true, backend, captureUrl: resource('media/capture.js'), 作業フォルダ: this.folder(), 保存モデル設定: ライブモデル読込() } });
    const pending: { message: unknown; size: number }[] = [];
    let pendingSize = 0;
    const host = this.host = new LiveHost(backend, message => {
      if (this.view !== view) return;
      if (view.visible) { void view.webview.postMessage(message); return; }
      const packet = message as { type?: string; data?: string };
      // 非表示中の音声を復帰時にまとめて再生しない。会話と接続通知は保持する。
      if (packet.type === 'socket-data' && packet.data) {
        try { if (JSON.parse(packet.data).メッセージ識別 === 'output_audio') return; } catch { return; }
      }
      const size = JSON.stringify(message).length;
      pending.push({ message, size }); pendingSize += size;
      while (pending.length > 200 || pendingSize > 2_000_000) pendingSize -= pending.shift()!.size;
    }, () => microphonePython(
      vscode.workspace.getConfiguration('aidiyLive').get<string>('pythonPath', ''),
      (vscode.workspace.workspaceFolders || []).filter(folder => folder.uri.scheme === 'file').map(folder => folder.uri.fsPath)
    ), join(this.context.extensionPath, 'dist/microphone.py'));
    const resources = [
      view.webview.onDidReceiveMessage(message => {
        if (!vscode.workspace.isTrusted) { host.stop(); return; }
        if (message?.type === 'ui-ready') this.ready = true;
        else if (message?.type === 'save-model' && Number.isSafeInteger(message.id) && message.id > 0) {
          try {
            ライブモデル保存(message.settings);
            void view.webview.postMessage({ type: 'reply', id: message.id, value: { ok: true } });
          } catch (error) {
            void view.webview.postMessage({ type: 'reply', id: message.id, error: error instanceof Error ? error.message : String(error) });
          }
        }
        else void host.receive(message).catch(error => { void vscode.window.showErrorMessage(String(error)); });
      }),
      view.onDidChangeVisibility(() => {
        host.visibility(view.visible);
        if (view.visible) {
          for (const item of pending.splice(0)) void view.webview.postMessage(item.message);
          pendingSize = 0; this.folderChanged();
        }
      }),
    ];
    view.onDidDispose(() => { host.dispose(); resources.forEach(resource => resource.dispose()); if (this.view === view) { this.view = undefined; this.host = undefined; } });
  }
  stop() { this.host?.stop(); }
  async standalone() {
    if (!vscode.workspace.isTrusted) throw new Error('ライブ会話は信頼済みのワークスペースで開いてください。');
    this.stop();
    const generation = ++this.generation;
    await this.browser?.close(); this.browser = undefined;
    const backend = ローカル接続先(this.context.extensionPath, this.folder()?.パス);
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
    vscode.window.registerWebviewViewProvider('aidiyLive.chat', live, { webviewOptions: { retainContextWhenHidden: true } }),
    vscode.commands.registerCommand('aidiyLive.open', () => vscode.commands.executeCommand('aidiyLive.chat.focus')),
    vscode.commands.registerCommand('aidiyLive.stop', () => live.stop()),
    vscode.commands.registerCommand('aidiyLive.standalone', () => live.standalone()),
    vscode.commands.registerCommand('aidiyLive.settings', () => vscode.commands.executeCommand('workbench.action.openSettings', '@ext:aidiy.aidiy-live')),
    vscode.workspace.onDidChangeWorkspaceFolders(() => live.folderChanged()),
    vscode.window.onDidChangeActiveTextEditor(() => live.folderChanged())
  );
  return { stop: () => live.stop(), getState: () => ({ ready: live.ready }) };
}
