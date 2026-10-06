// 接続時の状態ハンドラが送信しても、サーバーの初回受信は connect になる。
// node --test frontend_avatar/checks/websocket-handshake.test.cjs
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');
const ts = require('typescript');

const root = path.resolve(__dirname, '../..');

for (const project of ['frontend_avatar', 'frontend_web']) {
  test(`${project}: 状態同期より先に接続通知を送り、initでセッションを確定する`, async () => {
    const sockets = [];
    class Socket {
      static OPEN = 1;
      readyState = 0;
      sent = [];
      constructor() { sockets.push(this); }
      send(data) { this.sent.push(JSON.parse(data)); }
      close() { this.readyState = 3; }
      open() { this.readyState = Socket.OPEN; this.onopen(); }
      receive(data) { this.onmessage({ data: JSON.stringify(data) }); }
    }
    const source = fs.readFileSync(path.join(root, project, 'src/api/websocket.ts'), 'utf8');
    // Viteが注入する環境変数は、ブラウザを使わない検証用の値へ置き換える。
    const compiled = ts.transpileModule(source.replaceAll('import.meta.env', '({ DEV: true })'), {
      compilerOptions: { target: ts.ScriptTarget.ES2020, module: ts.ModuleKind.CommonJS },
    }).outputText;
    const exports = {};
    const timers = { setTimeout: () => 1, clearTimeout: () => {} };
    vm.runInNewContext(compiled, {
      exports, WebSocket: Socket, window: timers, ...timers,
      console: { log() {}, error() {} },
      require: (name) => {
        if (name === '@/api/config') return { AI_WS_ENDPOINT: 'ws://test' };
        if (name === '@/api/client') return { default: {} };
        if (name === '@/stores/auth') return { useAuthStore: () => ({}) };
        throw new Error(`Unexpected import: ${name}`);
      },
    });
    const client = new exports.AIWebSocket('ws://test', 'existing', 'input', '/project');
    client.onStateChange((connected) => {
      if (connected) client.updateState({ マイク: true });
    });
    // 初回接続と同じクライアントの再接続を検証する。
    for (let attempt = 0; attempt < 2; attempt++) {
      const connected = client.connect();
      const socket = sockets.at(-1);
      socket.open();
      assert.equal(socket.sent[0].type, 'connect', '接続通知が最初のパケットになる');
      assert.equal(socket.sent[0].ソケット番号, 'input');
      assert.equal(socket.sent[0].CODE_BASE_PATH, '/project');
      assert.equal(socket.sent[1].メッセージ識別, 'operations');
      socket.receive({ メッセージ識別: 'init', セッションID: 'existing', ソケット番号: 'input' });
      assert.equal(await connected, 'existing');
      client.disconnect();
    }
  });
}
