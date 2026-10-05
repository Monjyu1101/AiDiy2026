const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { join } = require('node:path');
const { runInNewContext } = require('node:vm');
const protocol = require('../../out/aidiy_live/protocol.cjs');
const backendRoutes = readFileSync(join(__dirname, '../../../backend_server/core_router/AIコア.py'), 'utf8');

function screen(host, rejectProject = false) {
  const elements = new Map(), sockets = [], calls = [], events = new Map();
  let folder = { 名前: '別プロジェクト', パス: 'C:\\work\\別プロジェクト' }, folderListener;
  let prepareResolve;
  const prepare = new Promise(resolve => { prepareResolve = resolve; });
  function element(id = '') {
    if (elements.has(id)) return elements.get(id);
    const values = new Set();
    const node = {
      id, value: '', textContent: '', children: [], hidden: false, strong: { textContent: '' },
      classList: { add: value => values.add(value), contains: value => values.has(value), toggle: (value, enabled) => enabled ? values.add(value) : values.delete(value) },
      setAttribute() {}, addEventListener() {}, remove() {}, focus() {},
      querySelector() { return this.strong; }, close() {}, showModal() {},
      replaceChildren(...children) { this.children = children; }, append(child) { this.children.push(child); },
      add(option) { if (!this.value) this.value = option.value; },
      cloneNode() { const copy = element(); copy.id = this.id; copy.textContent = this.textContent; return copy; },
    };
    if (id) elements.set(id, node);
    return node;
  }
  class Socket {
    readyState = 1; bufferedAmount = 0;
    constructor() { sockets.push(this); queueMicrotask(() => this.onopen?.()); }
    send(raw) {
      const packet = JSON.parse(raw); calls.push({ kind: 'socket', packet });
      if (packet.type === 'connect') {
        this.channel = packet.ソケット番号;
        queueMicrotask(() => this.emit({ メッセージ識別: 'init', セッションID: 'session' }));
      }
    }
    emit(packet) { this.onmessage?.({ data: JSON.stringify({ チャンネル: this.channel, ...packet }) }); }
    close() { this.readyState = 3; queueMicrotask(() => this.onclose?.()); }
  }
  const environment = {
    host, socketUrl: '', captureUrl: '', socket: () => new Socket(),
    onStop() {}, onMicrophoneStop() {}, onFolder(callback) { folderListener = callback; },
    async context() { return { backend: 'http://localhost:8091', 作業フォルダ: folder }; },
    async api(path, body) {
      calls.push({ kind: 'api', path, body });
      if (path === 'core/AIコア/モデル情報/設定') {
        if (rejectProject) return { status: 'NG', message: 'プロジェクト設定失敗' };
        if (body.モデル設定.CODE_BASE_PATH) await prepare;
        return { status: 'OK', data: {} };
      }
      assert.equal(path, 'core/AIコア/モデル情報/取得');
      return { status: 'OK', data: {
        モデル設定: { LIVE_AI_NAME: 'gemini_live', LIVE_GEMINI_MODEL: 'live-model', LIVE_GEMINI_VOICE: 'Kore' },
        available_models: { live_models: { gemini_live: { 'live-model': 'live-model' } }, live_voices: { gemini_live: { Kore: 'Kore' } } },
      } };
    }, ready() {}, dispose() {},
  };
  const window = { setTimeout: () => 0, addEventListener: (name, handler) => events.set(name, handler) };
  runInNewContext(readFileSync(join(__dirname, '../../out/aidiy_live/view.cjs'), 'utf8'), {
    require(name) {
      if (name === './protocol') return protocol;
      if (name === './bridge') return { LiveEnvironment: function () { return environment; } };
      if (name === './audio') return { LiveAudio: class {
        speaker = true;
        async unlock() {} async start() { return true; } close() {} stop() {} cancel() {} play() {}
        mute(enabled) { this.speaker = enabled; }
      } };
      if (name === './visualizer') return { AudioCloud: class { dispose() {} } };
      if (name === './microphone-error') return { microphoneError: String };
      throw new Error(name);
    },
    window, document: { body: element('body'), documentElement: element('html'),
      getElementById: element, createElement: () => element(), querySelectorAll: () => [] },
    Option: function (text, value) { this.text = text; this.value = value; },
    clearTimeout() {}, requestAnimationFrame: callback => callback(), setInterval: () => 1, clearInterval() {},
  });
  return {
    element, sockets, calls, allowProject: prepareResolve,
    async ready() { await new Promise(resolve => setImmediate(resolve)); },
    changeFolder(value) { folder = value; folderListener(value); },
    close() { events.get('pagehide')(); },
  };
}

for (const host of [true, false]) {
  test(`Live ${host ? 'VS Code' : '単独画面'}: プロジェクト設定後に音声接続し、文字・コード結果・失敗を表示する`, async t => {
    const ui = screen(host); t.after(() => ui.close()); await ui.ready();
    assert.equal(ui.element('connect').textContent, '接続');
    assert.equal(ui.element('connect').classList.contains('awaiting'), true);
    const connecting = ui.element('connect').onclick(); await ui.ready();
    assert.equal(ui.sockets.length, 1); // 設定が完了するまでaudioを開かない。
    const setting = ui.calls.find(call => call.kind === 'api');
    assert.equal(setting.path, 'core/AIコア/モデル情報/設定');
    assert.ok(backendRoutes.includes(`@router.post("/${setting.path}")`));
    assert.equal(setting.body.セッションID, 'session');
    assert.equal(setting.body.モデル設定.CODE_BASE_PATH, 'C:\\work\\別プロジェクト');
    assert.equal(setting.body.save, false);
    ui.allowProject(); await connecting;
    assert.equal(ui.element('connect').textContent, '切断');
    assert.equal(ui.element('body').classList.contains('connected'), true);
    assert.equal(ui.element('connect').classList.contains('awaiting'), false);
    assert.deepEqual(ui.sockets.map(socket => socket.channel), ['input', '0', 'audio']);
    for (const call of ui.calls.filter(call => call.kind === 'socket' && call.packet.type === 'connect')) {
      assert.equal(call.packet.CODE_BASE_PATH, 'C:\\work\\別プロジェクト');
    }
    assert.equal(ui.element('mic').querySelector('strong').textContent, 'OFF');
    const request = 'このプロジェクトの内容を説明してほしい。\nコードエージェントに確認してもらってもよい。';
    ui.element('text').value = request;
    ui.element('text-form').onsubmit({ preventDefault() {} });
    const packet = ui.calls.at(-1).packet;
    assert.equal(packet.メッセージ内容, request);
    assert.equal(packet.送信モード, 'Live');
    assert.equal(packet.セッションID, 'session');
    assert.equal(ui.element('text').value, '');
    ui.sockets[1].emit({ メッセージ識別: 'output_text', メッセージ内容: 'プロジェクトの説明です。' });
    ui.sockets[1].emit({ メッセージ識別: 'output_request', メッセージ内容: 'コードエージェントが確認した結果です。' });
    assert.deepEqual(ui.element('transcript').children.map(row => row.textContent), [
      'プロジェクトの説明です。', 'コードエージェントが確認した結果です。',
    ]);
    ui.sockets[1].emit({ メッセージ識別: 'output_text', メッセージ内容: '!' });
    assert.match(ui.element('error').textContent, /LiveAI に送信できません/);
    ui.sockets[1].emit({ メッセージ識別: 'error', メッセージ内容: 'APIキーを確認してください。' });
    assert.equal(ui.element('error').textContent, 'APIキーを確認してください。');
    await ui.element('apply').onclick();
    const change = ui.calls.filter(call => call.kind === 'api' && call.body.モデル設定?.LIVE_AI_NAME).at(-1);
    assert.equal(change.path, 'core/AIコア/モデル情報/設定');
    assert.equal(change.body.save, false);
    ui.sockets[0].bufferedAmount = 200000;
    ui.element('text').value = '再送'; ui.element('text-form').onsubmit({ preventDefault() {} });
    assert.equal(ui.element('text').value, '再送'); assert.match(ui.element('error').textContent, /送信できません/);
    await ui.element('mic').onclick();
    await ui.element('speaker').onclick(); // OFF を次の会話へ持ち越さない。
    ui.element('choose-model').onclick();
    await ui.element('connect').onclick();
    assert.ok(ui.sockets.every(socket => socket.readyState === 3));
    assert.equal(ui.element('connect').textContent, '接続');
    assert.equal(ui.element('connect').classList.contains('awaiting'), true);
    assert.equal(ui.element('body').classList.contains('connected'), false);
    assert.equal(ui.element('status').textContent, '未接続');
    assert.equal(ui.element('text').value, '');
    assert.equal(ui.element('error').hidden, true);
    assert.equal(ui.element('model-label').textContent, 'AiDiy のライブ会話');
    assert.equal(ui.element('model').value, '');
    assert.equal(ui.element('transcript').children.length, 1);
    assert.equal(ui.element('transcript').children[0].id, 'empty');
    assert.equal(ui.element('mic').querySelector('strong').textContent, 'OFF');
    assert.equal(ui.element('speaker').querySelector('strong').textContent, 'OFF');
    await ui.element('connect').onclick();
    assert.equal(ui.element('speaker').querySelector('strong').textContent, 'ON');
    ui.changeFolder({ 名前: '次のプロジェクト', パス: 'C:\\next' });
    assert.ok(ui.sockets.every(socket => socket.readyState === 3));
    assert.equal(ui.element('transcript').children[0].id, 'empty');
    assert.match(ui.element('error').textContent, /プロジェクトフォルダが変わりました/);
    await ui.element('connect').onclick();
    const next = ui.calls.filter(call => call.kind === 'api' && call.body.モデル設定?.CODE_BASE_PATH).at(-1);
    assert.equal(next.body.モデル設定.CODE_BASE_PATH, 'C:\\next');
    ui.sockets.at(-1).close(); await ui.ready();
    assert.equal(ui.element('connect').textContent, '接続');
    assert.equal(ui.element('transcript').children[0].id, 'empty');
    assert.match(ui.element('error').textContent, /接続が切れました/);
  });
}

test('Live: プロジェクト設定失敗では接続を閉じて、AiDiy既定フォルダのまま送信しない', async t => {
  const ui = screen(true, true); t.after(() => ui.close()); await ui.ready();
  await ui.element('connect').onclick();
  assert.equal(ui.sockets.length, 1); assert.equal(ui.sockets[0].readyState, 3);
  assert.equal(ui.element('send').disabled, true);
  assert.equal(ui.element('error').textContent, 'プロジェクト設定失敗');
});

test('Live: プロジェクト設定待ちにフォルダが変わっても接続を再開しない', async t => {
  const ui = screen(true); t.after(() => ui.close()); await ui.ready();
  const connecting = ui.element('connect').onclick(); await ui.ready();
  ui.changeFolder({ 名前: '次', パス: 'C:\\next' }); ui.allowProject(); await connecting;
  assert.equal(ui.sockets.length, 1); assert.equal(ui.sockets[0].readyState, 3);
  assert.equal(ui.element('send').disabled, true);
});
