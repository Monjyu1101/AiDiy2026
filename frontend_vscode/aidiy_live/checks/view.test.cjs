const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { join } = require('node:path');
const { runInNewContext } = require('node:vm');
const protocol = require('../../out/aidiy_live/protocol.cjs');
const { scrollRuntime } = require('../../checks/scroll-screen.cjs');

function screen(host, rejectProject = false, holdInput = false, reducedMotion = true, initialModelSettings, blockAudioUnlock = false, backendOptions = {}) {
  const scrolling = scrollRuntime();
  const elements = new Map(), sockets = [], calls = [], events = new Map(), intervals = new Set(), timers = new Map();
  const audioCalls = [];
  let clock = 0, timerNumber = 0;
  let folder = { 名前: '別プロジェクト', パス: 'C:\\work\\別プロジェクト' }, folderListener, sessionNumber = 0, intervalNumber = 0;
  const defaults = { LIVE_AI_NAME: 'gemini_live', LIVE_GEMINI_MODEL: 'live-model', LIVE_GEMINI_VOICE: 'Kore',
    LIVE_FREEAI_MODEL: 'free-model', LIVE_FREEAI_VOICE: 'Zephyr', LIVE_OPENAI_MODEL: 'realtime-model', LIVE_OPENAI_VOICE: 'marin', ...backendOptions.settings };
  let liveSettings = { ...defaults }, releaseInput;
  const inputReady = new Promise(resolve => { releaseInput = resolve; });
  function element(id = '') {
    if (elements.has(id)) return elements.get(id);
    const values = new Set();
    const node = {
      id, value: '', _textContent: '', children: [], hidden: false, strong: { textContent: '' }, listeners: new Map(),
      scrollTop: 0, scrollHeight: 1000, clientHeight: 300,
      get textContent() { return this.children.length ? this.children.map(child => child.textContent).join('') : this._textContent; },
      set textContent(text) { this.children = []; this._textContent = text; },
      get firstElementChild() { return this.children[0]; },
      classList: { add: value => values.add(value), remove: value => values.delete(value), contains: value => values.has(value), toggle: (value, enabled) => enabled ? values.add(value) : values.delete(value) },
      setAttribute() {}, addEventListener(name, handler) { this.listeners.set(name, handler); },
      click() { this.listeners.get('click')?.(); },
      remove() { if (this.parent) this.parent.children = this.parent.children.filter(child => child !== this); },
      focus() { this.focused = true; }, setSelectionRange(start, end) { this.selectionStart = start; this.selectionEnd = end; },
      querySelector() { return this.strong; }, close() { this.open = false; }, showModal() { this.open = true; },
      replaceChildren(...children) { this.children = children; this._textContent = ''; if (['provider', 'model', 'voice'].includes(id)) this.value = ''; for (const child of children) child.parent = this; }, append(child) { child.parent = this; this.children.push(child); },
      add(option) { this.children.push(option); if (!this.value) this.value = option.value; },
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
    async context() { return { backend: 'http://localhost:8091', 作業フォルダ: folder, モデル設定: initialModelSettings, 保存モデル設定: backendOptions.saved }; },
    async saveModel(settings) {
      await backendOptions.saveModel?.();
      calls.push({ kind: 'save-model', settings: JSON.parse(JSON.stringify(settings)) });
    },
    async api(path, body) {
      calls.push({ kind: 'api', path, body });
      assert.equal(path, 'core/AIコア/モデル情報/取得'); // 設定APIで起動後に差し替えない。
      if (!body.セッションID) await backendOptions.loadDefaults?.();
      return { status: 'OK', data: {
        モデル設定: body.セッションID ? liveSettings : defaults,
        available_models: backendOptions.catalog || { live_models: { gemini_live: { 'live-model': 'live-model', 'live-model-2': 'live-model-2' },
          freeai_live: { 'free-model': 'free-model' }, openai_live: { 'realtime-model': 'realtime-model' } },
          live_voices: { gemini_live: { Kore: 'Kore' }, freeai_live: { Zephyr: 'Zephyr', Kore: 'Kore' }, openai_live: { marin: 'marin' } } },
      } };
    }, ready() {}, dispose() {},
  };
  const window = { setTimeout(callback, delay) { const id = ++timerNumber; timers.set(id, { callback, at: clock + delay }); return id; },
    matchMedia: () => ({ matches: reducedMotion }), addEventListener: (name, handler) => events.set(name, handler) };
  runInNewContext(readFileSync(join(__dirname, '../../out/aidiy_live/view.cjs'), 'utf8'), {
    require(name) {
      if (name === '../../src/scroll-follow') return { 最下部追従: scrolling.follow };
      if (name === './protocol') return protocol;
      if (name === './model-catalog') return require('../../out/aidiy_live/model-catalog.cjs');
      if (name === './bridge') return { LiveEnvironment: function () { return environment; } };
      if (name === './audio') return { LiveAudio: class {
        speaker = true;
        async unlock() { audioCalls.push('unlock'); if (blockAudioUnlock) await new Promise(() => {}); }
        async start() { audioCalls.push('start'); return true; } close() {} stop() {} cancel() {} play() {}
        mute(enabled) { this.speaker = enabled; }
      } };
      if (name === './visualizer') return { AudioCloud: class { dispose() {} } };
      if (name === './microphone-error') return { microphoneError: String };
      throw new Error(name);
    },
    window, document: { body: element('body'), documentElement: element('html'),
      getElementById: element, createElement: () => element(), querySelectorAll: () => [] },
    Option: function (text, value) { this.text = text; this.value = value; },
    clearTimeout: id => timers.delete(id), requestAnimationFrame: callback => callback(),
    setInterval() { const id = ++intervalNumber; intervals.add(id); return id; }, clearInterval: id => intervals.delete(id),
  });
  return { element, sockets, calls, intervals, timers, releaseInput, audioCalls, ...scrolling,
    rejectNextConnection() { rejectProject = true; },
    advance(milliseconds) {
      const target = clock + milliseconds;
      while (true) {
        const next = [...timers.entries()].filter(([, timer]) => timer.at <= target).sort((a, b) => a[1].at - b[1].at)[0];
        if (!next) break;
        clock = next[1].at; timers.delete(next[0]); next[1].callback();
      }
      clock = target;
    },
    async ready() { await new Promise(resolve => setImmediate(resolve)); },
    changeFolder(value) { folder = value; folderListener(value); }, close() { events.get('pagehide')(); },
  };
}

test('Live: 入力・送信直後と会話表示後、描画後の履歴末尾へ揃える', async t => {
  for (const host of [false, true]) {
    await t.test(host ? 'VS Code' : '単独画面', async t => {
      const ui = screen(host); t.after(() => ui.close()); await ui.ready();
      await ui.element('connect').onclick();
      const transcript = ui.element('transcript'), input = ui.element('text');
      input.value = '長い\n入力';
      transcript.scrollTop = 0;
      input.listeners.get('input')();
      transcript.scrollHeight = 1200; ui.render();
      assert.equal(transcript.scrollTop, 1200);
      transcript.scrollTop = 0;
      ui.element('text-form').onsubmit({ preventDefault() {} });
      assert.equal(input.value, '');
      transcript.scrollHeight = 1400; ui.render();
      assert.equal(transcript.scrollTop, 1400);
      for (const type of ['input_text', 'output_text', 'output_request', 'recognition_output']) {
        transcript.scrollTop = 0;
        ui.sockets[1].emit({ メッセージ識別: type, メッセージ内容: '表示する会話です。' });
        transcript.scrollHeight += 100; ui.render();
        assert.equal(transcript.scrollTop, transcript.scrollHeight);
      }
    });
  }
});

test('Live: 回答演出の完了と表示領域の伸縮後も履歴末尾へ追従する', async t => {
  for (const host of [false, true]) {
    await t.test(host ? 'VS Code' : '単独画面', async t => {
      const ui = screen(host, false, false, false); t.after(() => ui.close()); await ui.ready();
      await ui.element('connect').onclick();
      const transcript = ui.element('transcript');
      ui.sockets[1].emit({ メッセージ識別: 'output_text', メッセージ内容: '回答全文の表示です。' });
      ui.advance(1000);
      transcript.scrollHeight = 1600; ui.render();
      assert.equal(transcript.scrollTop, 1600);
      assert.equal(transcript.children.at(-1).textContent, '回答全文の表示です。');
      transcript.scrollTop = 0; transcript.clientHeight = 100;
      ui.resize(transcript); ui.render();
      assert.equal(transcript.scrollTop, 1600);
    });
  }
});

test('Live 単独画面: 起動時の3種のモデル指定で自動接続し、画面で変更できる', async t => {
  for (const [provider, key, model] of [
    ['freeai_live', 'LIVE_FREEAI_MODEL', 'free-model'],
    ['gemini_live', 'LIVE_GEMINI_MODEL', 'live-model-2'],
    ['openai_live', 'LIVE_OPENAI_MODEL', 'realtime-model'],
  ]) {
    await t.test(provider, async t => {
      const initial = { LIVE_AI_NAME: provider, [key]: model };
      const ui = screen(false, false, false, true, initial); t.after(() => ui.close());
      await ui.ready();
      assert.match(ui.element('model-label').textContent, new RegExp(model));
       assert.equal(ui.element('connect').textContent, '切断');
       assert.equal(ui.element('mic').strong.textContent, 'OFF');
      const connects = ui.calls.filter(call=>call.packet?.type==='connect');
      assert.equal(connects.length, 3);
       for (const call of connects) {
         assert.deepEqual(call.packet.モデル設定, initial);
         assert.equal(call.packet.CODE_BASE_PATH, 'C:\\work\\別プロジェクト');
       }
      await ui.element('connect').onclick();
      await ui.element('choose-model').onclick();
      ui.element('provider').value = 'gemini_live'; ui.element('provider').onchange();
      ui.element('model').value = 'live-model'; ui.element('model').onchange();
      ui.element('voice').value = 'Kore'; ui.element('voice').onchange();
      assert.equal(ui.element('apply').disabled, false);
      await ui.element('apply').onclick();
      await ui.element('connect').onclick();
      for (const call of ui.calls.filter(call=>call.packet?.type==='connect').slice(-3)) {
        assert.deepEqual(call.packet.モデル設定, { LIVE_AI_NAME: 'gemini_live', LIVE_GEMINI_MODEL: 'live-model', LIVE_GEMINI_VOICE: 'Kore' });
      }
    });
  }
});

test('Live 単独画面: 自動接続は音声再生の許可を待たず、マイクを開始しない', async t => {
  const initial = { LIVE_AI_NAME: 'gemini_live', LIVE_GEMINI_MODEL: 'live-model' };
  const ui = screen(false, false, false, true, initial, true); t.after(() => ui.close());
  await ui.ready();
  assert.equal(ui.element('connect').textContent, '切断');
  assert.equal(ui.sockets.length, 3);
  assert.deepEqual(ui.audioCalls, []);
  assert.equal(ui.element('mic').strong.textContent, 'OFF');
  await ui.element('connect').onclick(); await ui.ready();
  assert.equal(ui.element('connect').textContent, '接続');
  assert.equal(ui.sockets.length, 3); // 手動切断後は自動でつなぎ直さない。
});

test('Live: モデル未指定・Provider だけの指定・VS Code では自動接続しない', async t => {
  for (const [host, initial] of [[false, undefined], [false, { LIVE_AI_NAME: 'gemini_live' }],
    [true, { LIVE_AI_NAME: 'gemini_live', LIVE_GEMINI_MODEL: 'live-model' }]]) {
    const ui = screen(host, false, false, true, initial); t.after(() => ui.close());
    await ui.ready();
    assert.equal(ui.element('connect').textContent, '接続');
    assert.equal(ui.sockets.length, 0);
  }
});

test('Live 単独画面: 自動接続の失敗は画面に表示し、再試行を繰り返さない', async t => {
  const ui = screen(false, true, false, true, { LIVE_AI_NAME: 'gemini_live', LIVE_GEMINI_MODEL: 'live-model' });
  t.after(() => ui.close()); await ui.ready();
  assert.equal(ui.element('connect').textContent, '接続');
  assert.match(ui.element('error').textContent, /プロジェクト設定失敗/);
  assert.equal(ui.sockets.length, 1); assert.equal(ui.sockets[0].readyState, 3);
});

test('Live 単独画面: 初期設定の読み込み中に画面を閉じたら自動接続しない', async () => {
  const ui = screen(false, false, false, true, { LIVE_AI_NAME: 'gemini_live', LIVE_GEMINI_MODEL: 'live-model' });
  ui.close(); await ui.ready();
  assert.equal(ui.sockets.length, 0);
});

for (const host of [true, false]) {
  test(`Live ${host ? 'VS Code' : '単独画面'}: JSON外の保存モデル・声を候補へ追加せず、選び直すまで接続しない`, async t => {
    for (const field of ['LIVE_OPENAI_MODEL', 'LIVE_OPENAI_VOICE']) {
      const saved = { LIVE_AI_NAME: 'openai_live', LIVE_OPENAI_MODEL: 'realtime-model', LIVE_OPENAI_VOICE: 'marin', [field]: 'removed' };
      const ui = screen(host, false, false, true, undefined, false, { saved });
      t.after(() => ui.close()); await ui.ready();
      await ui.element('connect').onclick();
      assert.equal(ui.sockets.length, 0);
      assert.match(ui.element('error').textContent, /選び直してください/);
      await ui.element('choose-model').onclick();
      const picker = ui.element(field.endsWith('VOICE') ? 'voice' : 'model');
      assert.equal(picker.value, '');
      assert.ok(!picker.children.some(option => option.value === 'removed'));
      assert.equal(ui.element('apply').disabled, true);
      picker.value = field.endsWith('VOICE') ? 'marin' : 'realtime-model'; picker.onchange();
      await ui.element('apply').onclick();
      await ui.element('connect').onclick();
      assert.equal(ui.sockets.length, 3);
      const sent = ui.calls.find(call => call.packet?.type === 'connect').packet.モデル設定;
      assert.equal(sent.LIVE_OPENAI_MODEL, 'realtime-model'); assert.equal(sent.LIVE_OPENAI_VOICE, 'marin');
    }
  });

  test(`Live ${host ? 'VS Code' : '単独画面'}: JSONの声の表示名・順序を使い、声だけの変更でも保存して再接続する`, async t => {
    const catalog = { live_models: { gemini_live: { 'live-model': 'Model' } },
      live_voices: { gemini_live: { Zephyr: '先頭の声', Kore: '次の声' } } };
    const ui = screen(host, false, false, true, undefined, false, { catalog });
    t.after(() => ui.close()); await ui.ready(); await ui.element('connect').onclick();
    await ui.element('choose-model').onclick();
    assert.deepEqual(ui.element('voice').children.map(option => [option.value, option.text]), [['Zephyr', '先頭の声'], ['Kore', '次の声']]);
    ui.element('voice').value = 'Zephyr'; ui.element('voice').onchange();
    await ui.element('apply').onclick();
    assert.equal(ui.calls.find(call => call.kind === 'save-model').settings.LIVE_GEMINI_VOICE, 'Zephyr');
    assert.equal(ui.sockets.length, 6);
    assert.ok(ui.sockets.slice(0, 3).every(socket => socket.readyState === 3));
    assert.equal(ui.calls.filter(call => call.packet?.type === 'connect').at(-1).packet.モデル設定.LIVE_GEMINI_VOICE, 'Zephyr');
  });

  test(`Live ${host ? 'VS Code' : '単独画面'}: 保存した手動選択を接続前から復元し、変更の確定時だけ保存する`, async t => {
    const saved = { LIVE_AI_NAME: 'openai_live', LIVE_OPENAI_MODEL: 'realtime-model', LIVE_OPENAI_VOICE: 'marin' };
    const ui = screen(host, false, false, true, undefined, false, { saved });
    t.after(() => ui.close()); await ui.ready();
    assert.equal(ui.element('model-label').textContent, 'openai_live · realtime-model · marin');
    assert.equal(ui.sockets.length, 0);
    assert.ok(!ui.calls.some(call => call.kind === 'save-model'));
    await ui.element('choose-model').onclick();
    ui.element('provider').value = 'freeai_live'; ui.element('provider').onchange();
    ui.element('cancel-model').onclick();
    assert.ok(!ui.calls.some(call => call.kind === 'save-model'));
    await ui.element('choose-model').onclick();
    assert.equal(ui.element('provider').value, 'openai_live');
    ui.element('provider').value = 'freeai_live'; ui.element('provider').onchange();
    await ui.element('apply').onclick();
    assert.deepEqual(ui.calls.find(call => call.kind === 'save-model').settings,
      { LIVE_AI_NAME: 'freeai_live', LIVE_FREEAI_MODEL: 'free-model', LIVE_FREEAI_VOICE: 'Zephyr' });
    await ui.element('connect').onclick();
    assert.equal(ui.calls.filter(call => call.kind === 'save-model').length, 1);
  });

  test(`Live ${host ? 'VS Code' : '単独画面'}: 保存失敗時は選択と現在の接続を維持する`, async t => {
    const ui = screen(host, false, false, true, undefined, false, { saveModel() { throw new Error('書込失敗'); } });
    t.after(() => ui.close()); await ui.ready(); await ui.element('connect').onclick();
    await ui.element('choose-model').onclick();
    ui.element('provider').value = 'freeai_live'; ui.element('provider').onchange();
    await ui.element('apply').onclick();
    assert.match(ui.element('error').textContent, /モデルを保存できません.*書込失敗/);
    assert.equal(ui.element('model-label').textContent, 'gemini_live · live-model · Kore');
    assert.equal(ui.element('status').textContent, '接続済み');
    assert.equal(ui.sockets.length, 3);
    assert.ok(ui.sockets.every(socket => socket.readyState === 1));
  });

  test(`Live ${host ? 'VS Code' : '単独画面'}: Provider だけ指定した場合は同じ Provider の保存モデルだけを復元する`, async t => {
    const saved = { LIVE_AI_NAME: 'openai_live', LIVE_OPENAI_MODEL: 'realtime-model', LIVE_OPENAI_VOICE: 'marin' };
    for (const provider of ['openai_live', 'freeai_live']) {
      const ui = screen(host, false, false, true, { LIVE_AI_NAME: provider }, false, { saved });
      t.after(() => ui.close()); await ui.ready();
      assert.equal(ui.element('model-label').textContent, provider === 'openai_live'
        ? 'openai_live · realtime-model · marin' : 'freeai_live · free-model · Zephyr');
      assert.equal(ui.sockets.length, 0);
      await ui.element('connect').onclick();
      assert.deepEqual(ui.calls.find(call => call.packet?.type === 'connect').packet.モデル設定,
        provider === 'openai_live' ? saved : { LIVE_AI_NAME: provider });
    }
  });

  test(`Live ${host ? 'VS Code' : '単独画面'}: 保存待ちに画面を閉じたら再接続しない`, async () => {
    let release;
    const pending = new Promise(resolve => { release = resolve; });
    const ui = screen(host, false, false, true, undefined, false, { saveModel: () => pending });
    await ui.ready(); await ui.element('connect').onclick();
    await ui.element('choose-model').onclick();
    ui.element('provider').value = 'freeai_live'; ui.element('provider').onchange();
    const saving = ui.element('apply').onclick();
    assert.equal(ui.element('apply').disabled, true);
    assert.equal(ui.element('apply').textContent, '保存中…');
    ui.close(); release(); await saving;
    assert.equal(ui.sockets.length, 3);
    assert.ok(ui.sockets.every(socket => socket.readyState === 3));
  });

  test(`Live ${host ? 'VS Code' : '単独画面'}: 明示したモデルを保存済みモデルより優先し、保存は上書きしない`, async t => {
    const saved = { LIVE_AI_NAME: 'openai_live', LIVE_OPENAI_MODEL: 'realtime-model', LIVE_OPENAI_VOICE: 'marin' };
    const initial = { LIVE_AI_NAME: 'freeai_live', LIVE_FREEAI_MODEL: 'free-model' };
    const ui = screen(host, false, false, true, initial, false, { saved });
    t.after(() => ui.close()); await ui.ready();
    assert.equal(ui.element('model-label').textContent, 'freeai_live · free-model · Zephyr');
    assert.ok(!ui.calls.some(call => call.kind === 'save-model'));
    if (host) await ui.element('connect').onclick();
    for (const call of ui.calls.filter(call => call.packet?.type === 'connect')) assert.deepEqual(call.packet.モデル設定, initial);
  });

  test(`Live ${host ? 'VS Code' : '単独画面'}: 起動時に共通設定を表示し、接続前に3種のモデルと音声を変更できる`, async t => {
    const settings = {
      LIVE_AI_NAME: 'freeai_live',
      LIVE_GEMINI_MODEL: 'gemini-2.5-flash-native-audio-preview-12-2025', LIVE_GEMINI_VOICE: 'Zephyr',
      LIVE_FREEAI_MODEL: 'gemini-2.5-flash-native-audio-preview-09-2025', LIVE_FREEAI_VOICE: 'Zephyr',
      LIVE_OPENAI_MODEL: 'gpt-realtime-2.1-mini', LIVE_OPENAI_VOICE: 'marin',
    };
    const catalog = { live_models: {}, live_voices: {} };
    for (const vendor of ['GEMINI', 'FREEAI', 'OPENAI']) {
      const provider = `${vendor.toLowerCase()}_live`;
      catalog.live_models[provider] = { [settings[`LIVE_${vendor}_MODEL`]]: 'JSON model' };
      catalog.live_voices[provider] = vendor === 'OPENAI' ? { marin: 'Marin' } : { Zephyr: 'Zephyr', Kore: 'Kore' };
    }
    const ui = screen(host, false, false, true, undefined, false, { settings, catalog });
    t.after(() => ui.close()); await ui.ready();
    assert.equal(ui.sockets.length, 0);
    assert.deepEqual(ui.calls.map(call => call.body.セッションID), ['']);
    assert.equal(ui.element('model-label').textContent, `${settings.LIVE_AI_NAME} · ${settings.LIVE_FREEAI_MODEL} · Zephyr`);
    assert.equal(ui.element('status').textContent, '未接続');
    await ui.element('choose-model').onclick();
    assert.equal(ui.element('provider').value, 'freeai_live');
    assert.equal(ui.element('apply').disabled, true);
    for (const vendor of ['GEMINI', 'OPENAI', 'FREEAI']) {
      const name = `${vendor.toLowerCase()}_live`, model = settings[`LIVE_${vendor}_MODEL`], voice = settings[`LIVE_${vendor}_VOICE`];
      ui.element('provider').value = name; ui.element('provider').onchange();
      assert.equal(ui.element('model').value, model);
      assert.equal(ui.element('voice').value, voice);
      // 共通設定がJSON由来の候補内にある場合だけ復元する。
      assert.ok(ui.element('model').children.some(option => option.value === model));
      assert.ok(ui.element('voice').children.some(option => option.value === voice));
    }
    ui.element('voice').value = 'Kore'; ui.element('voice').onchange();
    assert.equal(ui.element('apply').disabled, false);
    ui.element('cancel-model').onclick();
    await ui.element('choose-model').onclick();
    assert.equal(ui.element('voice').value, 'Zephyr');
    assert.equal(ui.element('apply').disabled, true);
    ui.element('provider').value = 'openai_live'; ui.element('provider').onchange();
    await ui.element('apply').onclick();
    assert.equal(ui.sockets.length, 0);
    assert.equal(ui.element('model-label').textContent, 'openai_live · gpt-realtime-2.1-mini · marin');
    await ui.element('connect').onclick();
    for (const call of ui.calls.filter(call => call.packet?.type === 'connect')) {
      assert.deepEqual(call.packet.モデル設定, { LIVE_AI_NAME: 'openai_live', LIVE_OPENAI_MODEL: settings.LIVE_OPENAI_MODEL, LIVE_OPENAI_VOICE: 'marin' });
    }
    await ui.element('connect').onclick();
    assert.equal(ui.element('model-label').textContent, 'openai_live · gpt-realtime-2.1-mini · marin');
    await ui.element('choose-model').onclick();
    assert.equal(ui.element('provider').value, 'openai_live');
    assert.equal(ui.element('apply').disabled, true);
  });

  test(`Live ${host ? 'VS Code' : '単独画面'}: 起動時の設定取得失敗を表示し、モデル選択から再取得できる`, async t => {
    let failing = true;
    const ui = screen(host, false, false, true, undefined, false, {
      loadDefaults() { if (failing) throw new Error('設定取得に失敗しました。'); },
    });
    t.after(() => ui.close()); await ui.ready();
    assert.match(ui.element('error').textContent, /設定取得に失敗/);
    assert.equal(ui.element('choose-model').disabled, false);
    assert.equal(ui.sockets.length, 0);
    failing = false;
    await ui.element('choose-model').onclick();
    assert.equal(ui.element('error').hidden, true);
    assert.equal(ui.element('model-label').textContent, 'gemini_live · live-model · Kore');
  });

  test(`Live ${host ? 'VS Code' : '単独画面'}: 起動時の候補取得中は接続を待ち、選択を照合してから開始する`, async t => {
    let release;
    const pending = new Promise(resolve => { release = resolve; });
    const initial = { LIVE_AI_NAME: 'openai_live' }; // Provider のみなので自動接続しない。
    const ui = screen(host, false, false, true, initial, false, { loadDefaults: () => pending });
    t.after(() => ui.close()); await ui.ready();
    assert.equal(ui.sockets.length, 0);
    const connecting = ui.element('connect').onclick();
    await ui.ready();
    assert.equal(ui.sockets.length, 0);
    assert.equal(ui.element('model-label').textContent, 'openai_live');
    release(); await connecting; await ui.ready();
    assert.equal(ui.element('model-label').textContent, 'openai_live · realtime-model · marin');
    assert.equal(ui.element('status').textContent, '接続済み');
  });

  test(`Live ${host ? 'VS Code' : '単独画面'}: 接続中の新しい会話は設定を保って新規セッションへ接続する`, async t => {
    const ui = screen(host); t.after(() => ui.close()); await ui.ready();
    await ui.element('connect').onclick();
    const session = ui.sockets[0].session;
    ui.sockets[1].emit({ メッセージ識別: 'output_text', メッセージ内容: '前の会話です。' });
    ui.element('text').value = '前の下書き';
    await ui.element('mic').onclick(); await ui.element('speaker').onclick();
    await ui.element('new').onclick();
    assert.equal(ui.element('connect').textContent, '切断');
    assert.equal(ui.element('status').textContent, '会話中');
    assert.equal(ui.element('mic').strong.textContent, 'ON');
    assert.equal(ui.element('speaker').strong.textContent, 'OFF');
    assert.equal(ui.audioCalls.filter(call => call === 'start').length, 2);
    assert.deepEqual(ui.calls.filter(call => call.packet?.メッセージ識別 === 'operations').at(-1).packet.メッセージ内容,
      { ボタン: { マイク: true, スピーカー: false } });
    assert.equal(ui.element('text').value, '');
    assert.equal(ui.element('transcript').children.length, 1);
    assert.equal(ui.element('transcript').children[0].id, 'empty');
    assert.equal(ui.sockets.length, 6);
    assert.ok(ui.sockets.slice(0, 3).every(socket => socket.readyState === 3));
    assert.ok(ui.sockets.slice(3).every(socket => socket.readyState === 1));
    assert.deepEqual(ui.sockets.slice(3).map(socket => socket.channel), ['input', '0', 'audio']);
    assert.notEqual(ui.sockets[3].session, session);
    for (const call of ui.calls.filter(call => call.packet?.type === 'connect').slice(-3)) {
      assert.equal(call.packet.CODE_BASE_PATH, 'C:\\work\\別プロジェクト');
      assert.deepEqual(call.packet.モデル設定, {
        LIVE_AI_NAME: 'gemini_live', LIVE_GEMINI_MODEL: 'live-model', LIVE_GEMINI_VOICE: 'Kore',
      });
    }
    assert.equal(ui.intervals.size, host ? 0 : 1);
    await ui.element('connect').onclick();
    await ui.element('new').onclick();
    assert.equal(ui.element('connect').textContent, '接続');
    assert.equal(ui.sockets.length, 6); // 未接続の新しい会話では接続を開始しない。
  });

  test(`Live ${host ? 'VS Code' : '単独画面'}: 新しい会話でもマイク OFF とスピーカー ON を保持する`, async t => {
    const ui = screen(host); t.after(() => ui.close()); await ui.ready();
    await ui.element('connect').onclick();
    await ui.element('new').onclick();
    assert.equal(ui.element('status').textContent, '接続済み');
    assert.equal(ui.element('mic').strong.textContent, 'OFF');
    assert.equal(ui.element('speaker').strong.textContent, 'ON');
    assert.ok(!ui.audioCalls.includes('start'));
    assert.deepEqual(ui.calls.filter(call => call.packet?.メッセージ識別 === 'operations').at(-1).packet.メッセージ内容,
      { ボタン: { マイク: false, スピーカー: true } });
  });

  test(`Live ${host ? 'VS Code' : '単独画面'}: 新しい会話の再接続失敗を表示する`, async t => {
    const ui = screen(host); t.after(() => ui.close()); await ui.ready();
    await ui.element('connect').onclick(); ui.rejectNextConnection();
    await ui.element('new').onclick();
    assert.equal(ui.element('connect').textContent, '接続');
    assert.equal(ui.sockets.length, 4);
    assert.ok(ui.sockets.every(socket => socket.readyState === 3));
    assert.match(ui.element('error').textContent, /プロジェクト設定失敗/);
    assert.equal(ui.intervals.size, 0);
  });

  test(`Live ${host ? 'VS Code' : '単独画面'}: 新しい会話の初期化中に画面を閉じたら再接続しない`, async () => {
    const ui = screen(host); await ui.ready(); await ui.element('connect').onclick();
    const restarting = ui.element('new').onclick(); ui.close(); await restarting;
    assert.equal(ui.sockets.length, 3);
    assert.ok(ui.sockets.every(socket => socket.readyState === 3));
  });

  test(`Live ${host ? 'VS Code' : '単独画面'}: 手入力と音声認識をクリックして入力欄へコピーする`, async t => {
    const ui = screen(host, false, false, false); t.after(() => ui.close()); await ui.ready();
    await ui.element('connect').onclick();
    for (const type of ['input_text', 'recognition_input', 'recognition_output']) {
      const text = `日本語の入力です。\n${type} の続きです。`;
      ui.sockets[1].emit({ メッセージ識別: type, メッセージ内容: text });
      const row = ui.element('transcript').children.at(-1);
      assert.equal(row.classList.contains(type), true);
      assert.equal(row.classList.contains('recognition'), type !== 'input_text');
      assert.equal(row.title, 'クリックして入力欄へ戻す');
      if (type === 'recognition_output') assert.equal(row.textContent, ''); // 演出中でも全文をコピー。
      ui.element('text').value = '古い下書き';
      const sentCount = ui.calls.length;
      row.click();
      const input = ui.element('text');
      assert.equal(input.value, text);
      assert.equal(input.focused, true);
      assert.equal(input.selectionStart, text.length);
      assert.equal(input.selectionEnd, text.length);
      assert.equal(ui.element('send').disabled, false);
      assert.equal(ui.calls.length, sentCount); // コピーだけで送信しない。
      ui.advance(1000);
    }
    const longText = '長い入力'.repeat(6000);
    ui.sockets[1].emit({ メッセージ識別: 'recognition_input', メッセージ内容: longText });
    const truncated = ui.element('transcript').children.at(-1);
    assert.equal(truncated.textContent.length, 20000);
    truncated.click();
    assert.equal(ui.element('text').value, longText);
    ui.sockets[1].emit({ メッセージ識別: 'output_text', メッセージ内容: '通常のAI回答です。' });
    const answer = ui.element('transcript').children.at(-1);
    assert.equal(answer.classList.contains('recognition'), false);
    answer.click();
    assert.equal(ui.element('text').value, longText);
  });

  test(`Live ${host ? 'VS Code' : '単独画面'}: AI回答の文字送り・連続回答・新規会話での停止`, async t => {
    const ui = screen(host, false, false, false); t.after(() => ui.close()); await ui.ready();
    await ui.element('connect').onclick();
    ui.sockets[1].emit({ メッセージ識別: 'recognition_input', メッセージ内容: '音声の入力です。' });
    assert.equal(ui.element('transcript').children[0].textContent, '音声の入力です。');
    ui.sockets[1].emit({ メッセージ識別: 'welcome_text', メッセージ内容: '会話準備ができました。' });
    assert.equal(ui.element('transcript').children[1].textContent, '会話準備ができました。');
    const answer = '日本語の回答です。\n次の行です。';
    ui.sockets[1].emit({ メッセージ識別: 'output_text', メッセージ内容: answer });
    const row = ui.element('transcript').children.at(-1);
    assert.equal(row.classList.contains('output_text'), true);
    assert.equal(row.classList.contains('console-effect'), true);
    assert.equal(row.children[1].className, 'terminal-cursor');
    assert.equal(row.textContent, '');
    ui.advance(499); assert.equal(row.textContent, '');
    ui.advance(1); assert.equal(row.textContent, answer.slice(0, 1));
    ui.advance(10); assert.equal(row.textContent, answer.slice(0, 2));
    ui.advance(1000);
    assert.equal(row.textContent, answer);
    assert.equal(row.classList.contains('console-effect'), false);
    assert.equal(row.children.length, 0);
    ui.sockets[1].emit({ メッセージ識別: 'output_request', メッセージ内容: 'コードエージェントの回答です。' });
    const previous = ui.element('transcript').children.at(-1);
    assert.equal(previous.classList.contains('output_request'), true);
    ui.advance(500);
    ui.sockets[1].emit({ メッセージ識別: 'recognition_output', メッセージ内容: '音声回答の字幕です。' });
    assert.equal(previous.textContent, 'コードエージェントの回答です。');
    assert.equal(previous.classList.contains('console-effect'), false);
    const current = ui.element('transcript').children.at(-1);
    assert.equal(current.classList.contains('recognition_output'), true);
    assert.equal(current.classList.contains('console-effect'), true);
    assert.equal(ui.timers.size, 1);
    await ui.element('new').onclick();
    assert.equal(ui.timers.size, 0);
    assert.equal(current.classList.contains('console-effect'), false);
    ui.advance(2000);
    assert.equal(ui.element('transcript').children.length, 1);
    assert.equal(ui.element('transcript').children[0].id, 'empty');
  });

  test(`Live ${host ? 'VS Code' : '単独画面'}: 演出抑制時は全文表示し、画面終了ではタイマーを破棄する`, async t => {
    const ui = screen(host); t.after(() => ui.close()); await ui.ready();
    await ui.element('connect').onclick();
    ui.sockets[1].emit({ メッセージ識別: 'output', メッセージ内容: '回答の全文です。' });
    const row = ui.element('transcript').children[0];
    assert.equal(row.textContent, '回答の全文です。');
    assert.equal(row.classList.contains('console-effect'), false);
    assert.equal(ui.timers.size, 0);
    const animated = screen(host, false, false, false); await animated.ready();
    await animated.element('connect').onclick();
    animated.sockets[1].emit({ メッセージ識別: 'output', メッセージ内容: '表示途中の回答です。' });
    assert.equal(animated.timers.size, 1);
    animated.close();
    assert.equal(animated.timers.size, 0);
  });

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
    assert.match(ui.element('error').textContent, /接続状態/);
    assert.doesNotMatch(ui.element('error').textContent, /APIキー/);
    ui.sockets[1].emit({ メッセージ識別: 'error', メッセージ内容: 'APIキーを確認してください。' });
    assert.equal(ui.element('error').textContent, 'APIキーを確認してください。');
    const creditError = 'OpenAI API のクレジット残高がありません。Billing で残高を確認してください。 (credit_balance_exhausted)';
    ui.sockets[1].emit({ メッセージ識別: 'error', メッセージ内容: creditError, エラーコード: 'credit_balance_exhausted' });
    assert.equal(ui.element('error').textContent, creditError);
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
    assert.equal(ui.element('model-label').textContent, 'gemini_live · live-model-2 · Kore');
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
