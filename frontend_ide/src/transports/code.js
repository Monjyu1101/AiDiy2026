// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
export function codeTransport({ host = false, base = '', api } = {}, receive) {
  let events, disposed = false, draft = '';
  const vscode = host ? api || window.acquireVsCodeApi() : null;
  const listener = event => { if (event.data && !disposed) receive(event.data); };
  async function request(route, data) {
    const response = await fetch(new URL(route, new URL(base, location.href)), data === undefined ? {} : {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || '接続できません。');
    return result;
  }
  return {
    draft: () => vscode?.getState()?.下書き || draft,
    saveDraft(text) { draft = text; vscode?.setState({ 下書き: text }); },
    async start() {
      if (host) { window.addEventListener('message', listener); vscode.postMessage({ type: 'ready' }); }
      else {
        events = new EventSource(new URL('events', new URL(base, location.href)));
        events.onmessage = event => { if (!disposed) receive(JSON.parse(event.data)); };
        events.onerror = () => receive({ type: 'transportError', message: '画面との接続が切れました。再接続しています…' });
      }
    },
    async send(message) {
      if (disposed) return;
      if (host) { vscode.postMessage(message); return; }
      if (message.type === 'chooseModel') {
        const result = await request(`catalog?provider=${encodeURIComponent(message.provider || '')}`);
        receive({ type: 'modelCatalog', provider: message.provider || '', items: message.provider ? result.models : result.providers });
      } else {
        await request('message', message.type === 'setModel' ? { ...message, type: 'model' } : message);
      }
    },
    link(url) { if (!/^https?:\/\//i.test(url)) return; if (host) vscode.postMessage({ type: 'link', url }); else window.open(url, '_blank', 'noopener,noreferrer'); },
    dispose() { disposed = true; events?.close(); window.removeEventListener('message', listener); },
  };
}
