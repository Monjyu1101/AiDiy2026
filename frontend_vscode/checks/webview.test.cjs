const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { join } = require('node:path');
const { runInNewContext } = require('node:vm');
const { transformSync } = require('esbuild');
const { scrollRuntime } = require('./scroll-screen.cjs');

function screen() {
  const runtime = scrollRuntime(), nodes = new Map(), events = new Map(), posts = [];
  function element(id = '') {
    if (nodes.has(id)) return nodes.get(id);
    const classes = new Set();
    const node = {
      value: '', textContent: '', hidden: false, children: [], listeners: new Map(),
      scrollHeight: 1000, clientHeight: 300, scrollTop: 0,
      classList: { add: name => classes.add(name), remove: name => classes.delete(name),
        toggle: (name, enabled) => enabled ? classes.add(name) : classes.delete(name) },
      addEventListener(name, callback) { this.listeners.set(name, callback); },
      querySelector() { return element('activity-dot'); },
      setAttribute() {}, focus() {}, setSelectionRange() {},
      append(...children) { this.children.push(...children); },
      replaceChildren(...children) { this.children = children; },
      replaceWith() {}, cloneNode() { return element(); },
      close() { this.open = false; }, showModal() { this.open = true; },
    };
    if (id) nodes.set(id, node);
    return node;
  }
  runInNewContext(transformSync(readFileSync(join(__dirname, '../src/webview.ts'), 'utf8'), {
    loader: 'ts', format: 'cjs',
  }).code, {
    require(name) {
      if (name === './scroll-follow') return { 最下部追従: runtime.follow };
      if (name === './stream-control') return {
        streamControlOf: text => ({ '\x02': 'start', '\x03': 'end', '\x18': 'cancel' })[text],
        visibleStreamContent: text => text,
      };
      return require(name);
    },
    acquireVsCodeApi: () => ({ getState() {}, setState() {}, postMessage(message) { posts.push(message); } }),
    document: { getElementById: element, createElement: () => element(), body: element('body'), addEventListener() {} },
    window: { addEventListener: (name, callback) => events.set(name, callback), setTimeout() {},
      matchMedia: () => ({ matches: true }) },
    requestAnimationFrame: runtime.requestAnimationFrame, clearTimeout() {},
  });
  let state = { type: 'state', 会話ID: 'conversation-1', メッセージ: [], 進捗: [], 履歴: [],
    信頼済み: true, 接続済み: true, 作業フォルダ: { 名前: 'project' }, 実行中: false };
  return { ...runtime, element, posts,
    notify(data) { events.get('message')({ data }); },
    state(data) { state = { ...state, ...data }; events.get('message')({ data: state }); },
    input(text) { element('prompt').value = text; element('prompt').listeners.get('input')(); },
  };
}

test('Code: 履歴を上へスクロール中でも、入力メッセージ追加と送信受理後は末尾へ移動する', () => {
  const ui = screen(), history = ui.element('conversation');
  ui.state({ メッセージ: [{ 種別: 'user', 本文: '以前の入力' }] }); ui.render();
  history.scrollTop = 0;
  ui.state({ メッセージ: [{ 種別: 'user', 本文: '以前の入力' }, { 種別: 'user', 本文: '今回の入力' }] });
  assert.equal(history.scrollTop, history.scrollHeight);
  ui.input('複数行\nの入力'); history.scrollTop = 0;
  ui.notify({ type: 'accepted' });
  assert.equal(ui.element('prompt').value, '');
  history.scrollHeight = 1200; ui.render();
  assert.equal(history.scrollTop, 1200);
});

test('Code: ストリーム枠の開閉・更新・伸縮で、進捗と履歴の両方が末尾へ追従する', () => {
  const ui = screen(), history = ui.element('conversation'), progress = ui.element('progress');
  ui.state({ メッセージ: [{ 種別: 'user', 本文: '入力' }] }); ui.render();
  for (const content of ['\x02', '実行中の進捗', '\x03', '\x18']) {
    history.scrollTop = progress.scrollTop = 0;
    ui.notify({ メッセージ識別: 'output_stream', メッセージ内容: content });
    history.scrollHeight += 100; progress.scrollHeight += 100; ui.render();
    assert.equal(history.scrollTop, history.scrollHeight);
    assert.equal(progress.scrollTop, progress.scrollHeight);
  }
  history.scrollTop = 0;
  ui.element('progress-details').listeners.get('toggle')(); ui.render();
  assert.equal(history.scrollTop, history.scrollHeight);
  history.scrollTop = progress.scrollTop = 0;
  ui.resize(history); ui.render();
  assert.equal(history.scrollTop, history.scrollHeight);
  assert.equal(progress.scrollTop, progress.scrollHeight);
});

test('Code: 入力欄の伸縮と一覧からの復帰後も、描画後の履歴末尾へ揃える', () => {
  const ui = screen(), history = ui.element('conversation');
  ui.input('長い\n入力'); history.scrollHeight = 1400; ui.render();
  assert.equal(history.scrollTop, 1400);
  ui.element('history-toggle').listeners.get('click')();
  history.scrollTop = 0; ui.resize(history); ui.render();
  assert.equal(history.scrollTop, 0); // 非表示中の会話欄は動かさない。
  ui.notify({ type: 'showConversation' }); ui.render();
  assert.equal(history.scrollTop, 1400);
});

test('Code: タイトルバーに接続状態を表示し、切断中は送信を無効化する', () => {
  const ui = screen(); ui.state({}); ui.input('依頼');
  assert.equal(ui.element('activity-label').textContent, '接続中');
  assert.equal(ui.element('activity-dot').textContent, '●');
  assert.equal(ui.element('send').disabled, false);
  ui.state({接続済み:false});
  assert.equal(ui.element('activity-label').textContent, '未接続');
  assert.equal(ui.element('activity-dot').textContent, '〇');
  assert.equal(ui.element('send').disabled, true);
  const count = ui.posts.length;
  ui.element('composer').listeners.get('submit')({preventDefault(){}});
  assert.equal(ui.posts.length,count);
  ui.state({接続済み:true});
  assert.equal(ui.element('send').disabled,false);
  const html = readFileSync(join(__dirname,'../media/chat.html'),'utf8');
  assert.ok(html.indexOf('id="activity"') < html.indexOf('id="conversation-toolbar"'));
  assert.ok(!html.slice(html.indexOf('<footer')).includes('id="activity"'));
});
