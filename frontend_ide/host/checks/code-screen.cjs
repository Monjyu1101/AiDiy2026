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

const { readFileSync } = require('node:fs');
const { join } = require('node:path');
const { runInNewContext, runInContext } = require('node:vm');
const { transformSync } = require('esbuild');
const { scrollRuntime } = require('./scroll-screen.cjs');

/** TypeScript のモジュールを、画面と同じ vm 文脈（document / window）で評価して exports を返す。 */
function moduleInContext(sandbox, file) {
  const code = transformSync(readFileSync(file, 'utf8'), { loader: 'ts', format: 'cjs' }).code;
  const module = { exports: {} };
  runInContext(`(function (module, exports, require) {\n${code}\n})`, sandbox)(module, module.exports, sandbox.require);
  return module.exports;
}

function screen(postMessage = () => {}) {
  const runtime = scrollRuntime(), nodes = new Map(), events = new Map(), posts = [];
  function element(id = '') {
    if (nodes.has(id)) return nodes.get(id);
    const classes = new Set(), attributes = new Map();
    const node = {
      value: '', textContent: '', hidden: false, children: [], listeners: new Map(), style: {},
      scrollHeight: 1000, clientHeight: 300, scrollTop: 0,
      classList: { add: name => classes.add(name), remove: name => classes.delete(name),
        contains: name => classes.has(name),
        toggle: (name, enabled) => enabled ? classes.add(name) : classes.delete(name) },
      addEventListener(name, callback) { this.listeners.set(name, callback); },
      querySelector() { return element('activity-dot'); },
      setAttribute(name, value) { attributes.set(name, value); }, getAttribute(name) { return attributes.get(name); }, focus() {}, setSelectionRange() {},
      getBoundingClientRect() { return { left: 0, top: 0, width: 0, height: 0 }; }, remove() {},
      append(...children) { this.children.push(...children); },
      add(child) { this.children.push(child); },
      replaceChildren(...children) { this.children = children; },
      replaceWith() {}, cloneNode() { return element(); },
      close() { this.open = false; }, showModal() { this.open = true; },
    };
    if (id) nodes.set(id, node);
    return node;
  }
  const sandbox = {
    require(name) {
      // 共通の登場演出は、画面と同じ document / window で動くよう同じ文脈で読み込む。
      if (name === './arrival-effect') return moduleInContext(sandbox, join(__dirname, '../src/arrival-effect.ts'));
      if (name === './scroll-follow') return { 最下部追従: runtime.follow };
      if (name === './stream-control') return {
        streamControlOf: text => ({ '\x02': 'start', '\x03': 'end', '\x18': 'cancel' })[text],
        visibleStreamContent: text => text,
      };
      return require(name);
    },
    acquireVsCodeApi: () => ({ getState() {}, setState() {}, postMessage(message) { posts.push(message); postMessage(message); } }),
    document: { getElementById: element, createElement: () => element(), body: element('body'), addEventListener() {} },
    window: { addEventListener: (name, callback) => events.set(name, callback), setTimeout() {}, setInterval() {}, clearInterval() {},
      matchMedia: () => ({ matches: true }) },
    requestAnimationFrame: runtime.requestAnimationFrame, clearTimeout() {},
    Option: function (label, value) { this.textContent = label; this.value = value; },
  };
  runInNewContext(transformSync(readFileSync(join(__dirname, '../src/webview.ts'), 'utf8'), {
    loader: 'ts', format: 'cjs',
  }).code, sandbox);
  let state = { type: 'state', 会話ID: 'conversation-1', メッセージ: [], 進捗: [], 履歴: [],
    信頼済み: true, 接続済み: true, 作業フォルダ: { 名前: 'project' }, 実行中: false };
  return { ...runtime, element, posts,
    notify(data) { events.get('message')({ data }); },
    state(data) { state = { ...state, ...data }; events.get('message')({ data: state }); },
    input(text) { element('prompt').value = text; element('prompt').listeners.get('input')(); },
  };
}

module.exports = { screen, moduleInContext };
