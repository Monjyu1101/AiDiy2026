/* COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
 * Licensed under "AiDiy 公開利用ライセンス v1.1". See LICENSE. */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { Window } from 'happy-dom';

const palette = readFileSync(new URL('../panel/titlebar.css', import.meta.url), 'utf8');
const shared = readFileSync(new URL('../../frontend_ide/src/共通表示/タイトルバー配色.css', import.meta.url), 'utf8');
const css = readFileSync(new URL('../panel/style.css', import.meta.url), 'utf8');

test('Discord のタイトル配色は共通原本のコピーだけを読み、Web と Electron で同じ色にする', async () => {
  assert.equal(palette, shared);
  assert.match(css, /@import "\.\/titlebar\.css"/);
  const window = new Window({ settings: { disableCSSFileLoading: true } });
  try {
    // OS描画ではなく、配布CSSの変数・継承・状態別の適用範囲を確認する。
    const style = window.document.createElement('style');
    // 外部読込を使わず、先頭の import を同じ配布CSSで解決する。
    style.textContent = css.replace('@import "./titlebar.css";', palette);
    window.document.head.append(style);
    window.document.body.innerHTML = '<header><div id="status">未接続</div><div class="brand"><strong>AiDiy Discord</strong></div><div class="window-actions"><button id="minimize">－</button><button class="window-pin"><span>📌</span></button><button class="window-pin pinned"><span>📌</span></button></div></header><div id="activity-bar"></div><div class="conversation-toolbar">プロジェクト</div><main>本文<input id="settings-input"></main>';
    const computed = (selector: string) => window.getComputedStyle(window.document.querySelector(selector)!);
    for (const browser of [false, true]) for (const live of [false, true]) {
      window.document.documentElement.classList.toggle('browser-mode', browser);
      window.document.body.classList.toggle('live-view', live);
      assert.equal(computed('header').backgroundColor, '#30343a');
      assert.equal(computed('html').backgroundColor, '#000');
      assert.equal(computed('body').backgroundColor, '#000');
      assert.notEqual(computed('main').backgroundColor, '#30343a', '本文へタイトル背景を転用しない');
      assert.equal(computed('#settings-input').backgroundColor, '#1b202c', '入力の階層色は維持する');
      assert.equal(computed('.brand strong').color, '#f3f5f7');
      assert.equal(computed('#status').color, '#e1e6ed');
      assert.equal(computed('#minimize').color, '#e1e6ed');
      assert.equal(computed('.window-pin').color, '#778394');
      assert.equal(computed('.window-pin.pinned').color, '#c3f7ff');
      assert.equal(computed('#activity-bar').backgroundColor, '#000');
      assert.equal(computed('.conversation-toolbar').backgroundColor, '#000');
      assert.equal(computed('.conversation-toolbar').color, '#9aa7b8');
      assert.equal(computed('header').minHeight, '31px');
      assert.equal(computed('#minimize').width, '28px');
    }
    window.document.body.classList.add('connected');
    assert.equal(computed('#activity-bar').backgroundColor, '#00ffff');
  } finally { await window.happyDOM.close(); }
});
