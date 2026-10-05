const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { join } = require('node:path');
const { runInNewContext } = require('node:vm');
const protocol = require('../../out/aidiy_live/protocol.cjs');

function screen(host, rejectProject = false, holdInput = false) {
  const elements = new Map(), sockets = [], calls = [], events = new Map(), intervals = new Set();
  let folder = { 名前: '別プロジェクト', パス: 'C:\\work\\別プロジェクト' }, folderListener, sessionNumber = 0, intervalNumber = 0;
  const defaults = { LIVE_AI_NAME: 'gemini_live', LIVE_GEMINI_MODEL: 'live-model', LIVE_GEMINI_VOICE: 'Kore',
    LIVE_FREEAI_MODEL: 'free-model', LIVE_FREEAI_VOICE: 'Zephyr' };
  let liveSettings = { ...defaults }, releaseInput;
  const inputReady = new Promise(resolve => { releaseInput = resolve; });
  function element(id = '') {
    if (elements.has(id)) return elements.get(id);
    const values = new Set();
    const node = {
      id, value: '', textContent: '', children: [], hidden: false, strong: { textContent: '' },
      classList: { add: value => values.add(value), contains: value => values.has(value), toggle: (value, enabled) => enabled ? values.add(value) : values.delete(value) },
      setAttribute() {}, addEventListener() {}, remove() {}, focus() {},
      querySelector() { return this.strong; }, close() { this.open = false; }, showModal() { this.open = true; },
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
        this.session = packet.セッションID || `session-${++sessionNumber}`;
        if (!packet.セッションID) liveSettings = { ...defaults, ...packet.モデル設定 };
        if (rejectProject) {
          queueMicrotask(() => { this.emit({ メッセージ識別: 'error', メッセージ内容: 'プロジェクト設定失敗' }); this.close(); });
          return;
        }
        const init = () => this.emit({ メッセージ識別: 'init', セッションID: this.session });
        if (holdInput && this.channel === 'input') void inputReady.then(init);
        else queueMicrotask(init);
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
      assert.equal(path, 'core/AIコア/モデル情報/取得'); // 設定APIで起動後に差し替えない。
      return { status: 'OK', data: {
        モデル設定: body.セッションID ? liveSettings : defaults,
        available_models: { live_models: { gemini_live: { 'live-model': 'live-model', 'live-model-2': 'live-model-2' },
          freeai_live: { 'free-model': 'free-model' } }, live_voices: { gemini_live: { Kore: 'Kore' }, freeai_live: { Zephyr: 'Zephyr' } } },
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
    clearTimeout() {}, requestAnimationFrame: callback => callback(),
    setInterval() { const id = ++intervalNumber; intervals.add(id); return id; }, clearInterval: id => intervals.delete(id),
  });
  return { element, sockets, calls, intervals, releaseInput,
    async ready() { await new Promise(resolve => setImmediate(resolve)); },
    changeFolder(value) { folder = value; folderListener(value); }, close() { events.get('pagehide')(); },
  };
}

for (const host of [true, false]) {
  test(`Live ${host ? 'VS Code' : '単独画面'}: 既定接続・モデル再接続・切断表示・回答とエラー`, async t => {
    const ui = screen(host); t.after(() => ui.close()); await ui.ready();
    assert.equal(ui.element('connect').textContent, '接続');
    assert.equal(ui.element('connect').classList.contains('awaiting'), true);
    await ui.element('connect').onclick();
    assert.equal(ui.element('connect').textContent, '切断');
    assert.equal(ui.element('connect').classList.contains('awaiting'), false);
    assert.deepEqual(ui.sockets.map(socket => socket.channel), ['input', '0', 'audio']);
    for (const call of ui.calls.filter(call => call.kind === 'socket' && call.packet.type === 'connect')) {
      assert.equal(call.packet.CODE_BASE_PATH, 'C:\\work\\別プロジェクト');
      assert.equal('モデル設定' in call.packet, false); // 指定なしはバックエンドの既定値。
    }
    assert.equal(ui.element('mic').strong.textContent, 'OFF');
    const request = 'このプロジェクトの内容を説明してほしい。\nコードエージェントに確認してもらってもよい。';
    ui.element('text').value = request; ui.element('text-form').onsubmit({ preventDefault() {} });
    assert.equal(ui.calls.at(-1).packet.メッセージ内容, request);
    assert.equal(ui.calls.at(-1).packet.送信モード, 'Live');
    ui.sockets[1].emit({ メッセージ識別: 'output_text', メッセージ内容: 'プロジェクトの説明です。' });
    ui.sockets[1].emit({ メッセージ識別: 'output_request', メッセージ内容: 'コードエージェントが確認した結果です。' });
    assert.deepEqual(ui.element('transcript').children.map(row => row.textContent), ['プロジェクトの説明です。', 'コードエージェントが確認した結果です。']);
    ui.sockets[1].emit({ メッセージ識別: 'output_text', メッセージ内容: '!' });
    assert.match(ui.element('error').textContent, /LiveAI に送信できません/);
    ui.sockets[1].emit({ メッセージ識別: 'error', メッセージ内容: 'APIキーを確認してください。' });
    assert.equal(ui.element('error').textContent, 'APIキーを確認してください。');
    await ui.element('choose-model').onclick();
    assert.equal(ui.element('apply').disabled, true);
    ui.element('model').value = 'live-model-2'; ui.element('model').onchange();
    assert.equal(ui.element('apply').disabled, false);
    ui.element('cancel-model').onclick();
    await ui.element('choose-model').onclick();
    assert.equal(ui.element('model').value, 'live-model');
    assert.equal(ui.element('apply').disabled, true);
    ui.element('model').value = 'live-model-2'; ui.element('model').onchange();
    await ui.element('mic').onclick();
    ui.element('text').value = '下書き';
    await ui.element('apply').onclick();
    assert.equal(ui.element('mic').strong.textContent, 'OFF');
    assert.equal(ui.sockets.length, 6);
    assert.ok(ui.sockets.slice(0, 3).every(socket => socket.readyState === 3));
    assert.ok(ui.sockets.slice(3).every(socket => socket.readyState === 1));
    assert.notEqual(ui.sockets[0].session, ui.sockets[3].session);
    assert.equal(ui.element('transcript').children[0].textContent, 'プロジェクトの説明です。');
    assert.equal(ui.element('text').value, '下書き');
    for (const call of ui.calls.filter(call => call.packet?.モデル設定)) {
      assert.equal(call.packet.モデル設定.LIVE_GEMINI_MODEL, 'live-model-2');
    }
    assert.equal(ui.element('apply').disabled, true);
    assert.match(ui.element('model-label').textContent, /live-model-2/);
    assert.equal(ui.intervals.size, host ? 0 : 1);
    ui.sockets[3].bufferedAmount = 200000;
    ui.element('text').value = '再送'; ui.element('text-form').onsubmit({ preventDefault() {} });
    assert.equal(ui.element('text').value, '再送'); assert.match(ui.element('error').textContent, /送信できません/);
    await ui.element('mic').onclick(); await ui.element('speaker').onclick();
    await ui.element('connect').onclick();
    assert.ok(ui.sockets.every(socket => socket.readyState === 3));
    assert.equal(ui.intervals.size, 0);
    assert.equal(ui.element('connect').textContent, '接続');
    assert.equal(ui.element('status').textContent, '未接続');
    assert.equal(ui.element('text').value, '');
    assert.equal(ui.element('error').hidden, true);
    assert.equal(ui.element('model-label').textContent, 'AiDiy のライブ会話');
    assert.equal(ui.element('transcript').children[0].id, 'empty');
    assert.equal(ui.element('mic').strong.textContent, 'OFF');
    assert.equal(ui.element('speaker').strong.textContent, 'OFF');
    await ui.element('connect').onclick();
    assert.equal(ui.element('speaker').strong.textContent, 'ON');
    ui.changeFolder({ 名前: '次のプロジェクト', パス: 'C:\\next' });
    assert.equal(ui.element('transcript').children[0].id, 'empty');
    assert.match(ui.element('error').textContent, /プロジェクトフォルダが変わりました/);
    await ui.element('connect').onclick();
    assert.equal(ui.calls.filter(call => call.packet?.type === 'connect').at(-1).packet.CODE_BASE_PATH, 'C:\\next');
    ui.sockets.at(-1).close(); await ui.ready();
    assert.equal(ui.element('connect').textContent, '接続');
    assert.equal(ui.element('transcript').children[0].id, 'empty');
    assert.match(ui.element('error').textContent, /接続が切れました/);
  });

  test(`Live ${host ? 'VS Code' : '単独画面'}: 接続前に選択し、モデルとフォルダを初回から同時に渡す`, async t => {
    const ui = screen(host); t.after(() => ui.close()); await ui.ready();
    await ui.element('choose-model').onclick();
    assert.equal(ui.calls[0].body.セッションID, '');
    assert.equal(ui.element('apply').textContent, '選択する');
    ui.element('provider').value = 'freeai_live'; ui.element('provider').onchange();
    await ui.element('apply').onclick();
    assert.equal(ui.sockets.length, 0);
    assert.equal(ui.element('status').textContent, '未接続');
    assert.match(ui.element('model-label').textContent, /freeai_live/);
    await ui.element('connect').onclick();
    for (const call of ui.calls.filter(call => call.packet?.type === 'connect')) {
      assert.equal(call.packet.CODE_BASE_PATH, 'C:\\work\\別プロジェクト');
      assert.deepEqual(call.packet.モデル設定, { LIVE_AI_NAME: 'freeai_live', LIVE_FREEAI_MODEL: 'free-model', LIVE_FREEAI_VOICE: 'Zephyr' });
    }
    assert.equal(ui.element('mic').strong.textContent, 'OFF');
    assert.match(ui.element('model-label').textContent, /freeai_live/);
  });
}

test('Live: フォルダを拒否されたら音声接続せず、理由を表示する', async t => {
  const ui = screen(true, true); t.after(() => ui.close()); await ui.ready();
  await ui.element('connect').onclick();
  assert.equal(ui.sockets.length, 1); assert.equal(ui.sockets[0].readyState, 3);
  assert.equal(ui.element('send').disabled, true);
  assert.match(ui.element('error').textContent, /プロジェクト設定失敗/);
});

test('Live: input 初期化待ちにフォルダが変わっても接続を再開しない', async t => {
  const ui = screen(true, false, true); t.after(() => ui.close()); await ui.ready();
  const connecting = ui.element('connect').onclick(); await ui.ready();
  ui.changeFolder({ 名前: '次', パス: 'C:\\next' }); ui.releaseInput(); await connecting;
  assert.equal(ui.sockets.length, 1); assert.equal(ui.sockets[0].readyState, 3);
  assert.equal(ui.element('send').disabled, true);
});
