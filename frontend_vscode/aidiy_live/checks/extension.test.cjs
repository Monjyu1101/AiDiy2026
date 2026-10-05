const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { join } = require('node:path');
const { runInNewContext } = require('node:vm');

test('Live のタブ切り替え: 同じ接続を保持し、会話と切断通知を復帰時に届ける', () => {
  const extensionPath = join(__dirname, '..');
  const packets = [], sockets = [], timers = new Map();
  let provider, options, receive, visibility, dispose, timerId = 0;
  const resource = fsPath => ({ fsPath, scheme: 'file', toString: () => `https://webview.test/${fsPath}` });
  const disposable = () => ({ dispose() {} });
  const vscode = {
    Uri: { joinPath: (uri, ...parts) => resource(join(uri.fsPath, ...parts)) },
    workspace: {
      isTrusted: true, workspaceFolders: [],
      getConfiguration: () => ({ get: (_key, fallback) => fallback }),
      onDidChangeWorkspaceFolders: disposable, onDidChangeConfiguration: disposable,
    },
    window: {
      registerWebviewViewProvider: (_id, value, config) => { provider = value; options = config; return disposable(); },
      onDidChangeActiveTextEditor: disposable, showErrorMessage: error => assert.fail(error),
    },
    commands: { registerCommand: disposable },
  };
  class Socket {
    readyState = 1; bufferedAmount = 0; sent = [];
    constructor() { sockets.push(this); }
    send(data) { this.sent.push(JSON.parse(data)); }
    close() { this.closed = true; this.readyState = 3; this.onclose?.(); }
  }
  const module = { exports: {} };
  runInNewContext(readFileSync(join(extensionPath, 'dist/extension.js'), 'utf8'), {
    module, exports: module.exports, require: name => name === 'vscode' ? vscode : require(name),
    WebSocket: Socket, process, Buffer, URL, AbortController, console,
    setTimeout, clearTimeout,
    setInterval: callback => { timers.set(++timerId, callback); return timerId; },
    clearInterval: id => timers.delete(id),
  });
  const context = { extensionPath, extensionUri: resource(extensionPath), subscriptions: [] };
  module.exports.activate(context);
  assert.equal(options.webviewOptions.retainContextWhenHidden, true);
  const view = {
    visible: true,
    webview: {
      cspSource: 'https://webview.test', asWebviewUri: uri => uri,
      postMessage: message => { packets.push(message); return Promise.resolve(true); },
      onDidReceiveMessage: callback => { receive = callback; return disposable(); },
    },
    onDidChangeVisibility: callback => { visibility = callback; return disposable(); },
    onDidDispose: callback => { dispose = callback; return disposable(); },
  };
  provider.resolveWebviewView(view);
  try {
    for (const [index, channel] of ['input', '0', 'audio'].entries()) {
      const id = index + 1;
      receive({ type: 'socket-open', id }); sockets[index].onopen();
      receive({ type: 'socket-send', id, data: JSON.stringify({ type: 'connect', ソケット番号: channel }) });
      sockets[index].onmessage({ data: JSON.stringify({ メッセージ識別: 'init', セッションID: 'same-session' }) });
    }
    receive({ type: 'socket-send', id: 1, data: JSON.stringify({ メッセージ識別: 'operations', メッセージ内容: { ボタン: { マイク: true, スピーカー: false } } }) });
    view.visible = false; visibility();
    assert.ok(sockets.every(socket => !socket.closed));
    assert.equal(sockets[0].sent.at(-1).メッセージ内容.ボタン.マイク, false);
    assert.equal(sockets[0].sent.at(-1).メッセージ内容.ボタン.スピーカー, false);
    for (const tick of timers.values()) tick();
    assert.equal(sockets[0].sent.at(-1).type, 'ping');
    assert.equal(sockets[0].sent.at(-1).セッションID, 'same-session');
    const count = packets.length;
    sockets[1].onmessage({ data: JSON.stringify({ メッセージ識別: 'output_text', メッセージ内容: '非表示中の回答' }) });
    sockets[2].onmessage({ data: JSON.stringify({ メッセージ識別: 'output_audio', ファイル名: 'pcm' }) });
    assert.equal(packets.length, count);
    view.visible = true; visibility();
    assert.ok(sockets.every(socket => !socket.closed));
    assert.ok(packets.some(packet => packet.type === 'mic-paused'));
    assert.ok(packets.some(packet => packet.data?.includes('非表示中の回答')));
    assert.ok(!packets.some(packet => packet.data?.includes('output_audio')));
    receive({ type: 'socket-send', id: 1, data: JSON.stringify({ セッションID: 'same-session', メッセージ識別: 'input_text', メッセージ内容: '続き' }) });
    assert.equal(sockets.length, 3);
    assert.equal(sockets[0].sent.at(-1).セッションID, 'same-session');
    view.visible = false; visibility(); sockets[0].close();
    assert.equal(timers.size, 0);
    view.visible = true; visibility();
    assert.ok(packets.some(packet => packet.type === 'socket-closed' && packet.id === 1));
  } finally { dispose(); context.subscriptions[0].dispose(); }
  assert.ok(sockets.every(socket => socket.closed));
  assert.equal(timers.size, 0);
});
