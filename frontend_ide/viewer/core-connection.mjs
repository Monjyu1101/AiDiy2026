// -*- coding: utf-8 -*-
// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026

import { existsSync, readFileSync } from 'node:fs';
import { basename, dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

// Live と同じ規則: AiDiy 配置先を優先し、共通設定から PORT_CORE だけを使う。
export function coreTarget(...folders) {
  const visited = new Set();
  for (const folder of folders) {
    let current = resolve(folder);
    while (!visited.has(current)) {
      visited.add(current);
      const path = join(current, '_config', 'AiDiy_key.json');
      if (existsSync(path)) {
        let settings;
        try { settings = JSON.parse(readFileSync(path, 'utf8').replace(/^\uFEFF/, '')); }
        catch { throw new Error('共通設定 AiDiy_key.json を読み込めません。'); }
        const port = Number(settings.PORT_CORE ?? 8091);
        if (!Number.isInteger(port) || port < 1 || port > 65535) throw new Error('共通設定 PORT_CORE は1〜65535の整数で指定してください。');
        return `http://127.0.0.1:${port}`;
      }
      const parent = dirname(current);
      if (parent === current) break;
      current = parent;
    }
  }
  return 'http://127.0.0.1:8091';
}

export function createCoreConnection(project, { target, fetcher = fetch, interval = 5000, timeout = 4000 } = {}) {
  let backend, configError;
  try { backend = target || coreTarget(fileURLToPath(new URL('.', import.meta.url)), project); }
  catch (error) { configError = error.message; }
  let startedAt = null;
  let mode = 'initial', connected = false, wanted = false, message = configError || '', pending, controller, timer, generation = 0, disposed = false;
  const state = () => ({ mode, startedAt, active: startedAt !== null, connected, connecting: !!pending, wanted, message, backend: backend || '',
    project: { name: basename(project), path: project } });
  async function check() {
    if (!wanted || disposed) return state();
    if (pending) return pending;
    const run = generation;
    controller = new AbortController();
    pending = (async () => {
      try {
        if (configError) throw new Error(configError);
        // Live と同じ読み取り API で AiDiy コアの応答を確認する。AI会話や音声は開始しない。
        const response = await fetcher(new URL('/core/AIコア/モデル情報/取得', backend), {
          method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ セッションID: '' }),
          signal: AbortSignal.any([controller.signal, AbortSignal.timeout(timeout)]),
        });
        if (!response.ok) throw new Error(`AiDiy コアが応答エラーを返しました（HTTP ${response.status}）。`);
        const result = await response.json();
        if (result.status !== 'OK' || !result.data?.available_models || !result.data?.モデル設定) {
          throw new Error('AiDiy コアの接続確認に失敗しました。');
        }
        if (run === generation && wanted) { if (startedAt === null) startedAt = Date.now(); connected = true; message = ''; }
      } catch (error) {
        if (run === generation && wanted) {
          connected = false;
          // 利用開始後のコア停止は接続状態だけを変える。作業・Code子窓の寿命とは分ける。
          if (startedAt === null) {
            mode = 'initial'; wanted = false;
            clearInterval(timer); timer = undefined;
          }
          message = configError || (error.name === 'TimeoutError' ? 'AiDiy コアの応答がタイムアウトしました。' : 'AiDiy コアに接続できません。AiDiy を起動してください。');
        }
      }
      return state();
    })();
    const task = pending;
    try { await task; } finally { if (run === generation) pending = undefined; }
    return state();
  }
  function disconnect() {
    ++generation; mode = 'initial'; startedAt = null; wanted = false; connected = false; message = configError || '';
    controller?.abort(); pending = undefined;
    clearInterval(timer); timer = undefined;
    return state();
  }
  return {
    state, check,
    async connect() {
      if (disposed) return state();
      if (mode !== 'online') disconnect();
      mode = 'online'; wanted = true;
      if (!timer) { timer = setInterval(() => void check(), interval); timer.unref?.(); }
      return check();
    },
    disconnect,
    offline() {
      if (disposed) return state();
      disconnect(); mode = 'offline'; startedAt = Date.now(); message = '';
      return state();
    },
    close() { disposed = true; disconnect(); },
  };
}
