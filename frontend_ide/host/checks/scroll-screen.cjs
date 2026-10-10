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
const { runInNewContext } = require('node:vm');
const { transformSync } = require('esbuild');

// 描画の前後と表示領域の伸縮を分けて再現し、古い高さへのスクロールを検出する。
function scrollRuntime() {
  const frames = [], observers = [];
  const requestAnimationFrame = callback => { frames.push(callback); return frames.length; };
  class ResizeObserver {
    constructor(callback) { this.callback = callback; this.targets = []; observers.push(this); }
    observe(target) { this.targets.push(target); }
  }
  const module = { exports: {} };
  const source = readFileSync(join(__dirname, '../src/scroll-follow.ts'), 'utf8');
  runInNewContext(transformSync(source, { loader: 'ts', format: 'cjs' }).code, {
    exports: module.exports, module, requestAnimationFrame, ResizeObserver,
  });
  return {
    requestAnimationFrame, ResizeObserver, follow: module.exports.最下部追従,
    render() { const pending = frames.splice(0); for (const frame of pending) frame(); },
    resize(target) { for (const observer of observers) if (observer.targets.includes(target)) observer.callback(); },
  };
}
module.exports = { scrollRuntime };
