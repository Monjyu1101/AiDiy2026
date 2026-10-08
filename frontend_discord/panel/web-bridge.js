'use strict';
// ブラウザ版パネル用。Electron 版の preload.cjs と同じ window.discordPanel を WebSocket で提供する。
// view.js / visualizer.js は Electron 版と共通で、変更しない。
(() => {
  document.documentElement.classList.add('browser-mode');
  const listeners = { state: [], activity: [], meter: [], audio: [] };
  const pending = new Map();
  let sequence = 0, socket, opened;
  const fail = message => {
    for (const job of pending.values()) job.reject(new Error(message));
    pending.clear();
    for (const callback of listeners.state) callback({ phase: 'error', message, fatal: true });
  };
  function connect() {
    const url = new URL('ws', location.href); url.protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    socket = new WebSocket(url);
    opened = new Promise((resolve, reject) => { socket.onopen = resolve; socket.onerror = reject; });
    socket.onmessage = event => {
      let data;
      try { data = JSON.parse(event.data); } catch { return; }
      if (typeof data.id === 'number') {
        const job = pending.get(data.id); if (!job) return;
        pending.delete(data.id);
        if (data.error) job.reject(new Error(data.error)); else job.resolve(data.result);
        return;
      }
      for (const callback of listeners[data.type] || []) callback(data[data.type]);
    };
    socket.onclose = () => fail('パネルのサーバーとの接続が切れました。aidiy_discord を起動し直してください。');
  }
  connect();
  const request = async (action, value) => {
    await opened;
    return new Promise((resolve, reject) => {
      const id = ++sequence;
      pending.set(id, { resolve, reject });
      socket.send(JSON.stringify({ id, action, value }));
    });
  };
  const on = type => callback => { listeners[type].push(callback); };
  window.discordPanel = {
    initial: () => request('initial'),
    select: value => request('select', value),
    selectFeatures: value => request('select-features', value),
    selectCode: value => request('select-code', value),
    catalogCode: provider => request('catalog-code', provider),
    start: () => request('start'),
    stop: () => request('stop'),
    monitor: on => request('monitor', on),
    // ブラウザではタブ・ウィンドウの操作をブラウザに任せる（ボタンは CSS で隠す）。
    window: async () => {},
    onState: on('state'), onActivity: on('activity'), onMeter: on('meter'), onAudio: on('audio'),
  };
})();
