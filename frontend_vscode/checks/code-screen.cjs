const { readFileSync } = require('node:fs');
const { join } = require('node:path');
const { runInNewContext } = require('node:vm');
const { transformSync } = require('esbuild');
const { scrollRuntime } = require('./scroll-screen.cjs');

function screen(postMessage = () => {}) {
  const runtime = scrollRuntime(), nodes = new Map(), events = new Map(), posts = [];
  function element(id = '') {
    if (nodes.has(id)) return nodes.get(id);
    const classes = new Set();
    const node = {
      value: '', textContent: '', hidden: false, children: [], listeners: new Map(),
      scrollHeight: 1000, clientHeight: 300, scrollTop: 0,
      classList: { add: name => classes.add(name), remove: name => classes.delete(name),
        contains: name => classes.has(name),
        toggle: (name, enabled) => enabled ? classes.add(name) : classes.delete(name) },
      addEventListener(name, callback) { this.listeners.set(name, callback); },
      querySelector() { return element('activity-dot'); },
      setAttribute() {}, focus() {}, setSelectionRange() {},
      append(...children) { this.children.push(...children); },
      add(child) { this.children.push(child); },
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
    acquireVsCodeApi: () => ({ getState() {}, setState() {}, postMessage(message) { posts.push(message); postMessage(message); } }),
    document: { getElementById: element, createElement: () => element(), body: element('body'), addEventListener() {} },
    window: { addEventListener: (name, callback) => events.set(name, callback), setTimeout() {},
      matchMedia: () => ({ matches: true }) },
    requestAnimationFrame: runtime.requestAnimationFrame, clearTimeout() {},
    Option: function (label, value) { this.textContent = label; this.value = value; },
  });
  let state = { type: 'state', 会話ID: 'conversation-1', メッセージ: [], 進捗: [], 履歴: [],
    信頼済み: true, 接続済み: true, 作業フォルダ: { 名前: 'project' }, 実行中: false };
  return { ...runtime, element, posts,
    notify(data) { events.get('message')({ data }); },
    state(data) { state = { ...state, ...data }; events.get('message')({ data: state }); },
    input(text) { element('prompt').value = text; element('prompt').listeners.get('input')(); },
  };
}

module.exports = { screen };
