(() => {
  if (window.aidiyWindow) {
    document.documentElement.classList.add('desktop-window', 'desktop-opening');
    document.getElementById('desktop-controls').hidden = false;
    document.getElementById('window-minimize').addEventListener('click', () => window.aidiyWindow.minimize());
    document.getElementById('window-maximize').addEventListener('click', () => window.aidiyWindow.maximize());
    document.getElementById('window-close').addEventListener('click', () => window.aidiyWindow.close());
    window.aidiyWindow.onState(({ maximized, opening }) => {
      document.documentElement.classList.toggle('window-maximized', maximized);
      document.documentElement.classList.toggle('desktop-opening', opening);
      const button = document.getElementById('window-maximize');
      button.title = maximized ? '元のサイズに戻す' : '最大化';
      button.setAttribute('aria-label', button.title);
    });
  }
  let state, draft = '', events;
  const emit = data => window.dispatchEvent(new MessageEvent('message', {data}));
  const error = value => {
    const status = document.getElementById('status');
    status.textContent = String(value.message || value); status.hidden = false;
  };
  const request = async (route, data) => {
    const response = await fetch(route, data === undefined ? {} : {
      method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || '接続できません。');
    return result;
  };
  const send = async data => {
    try { await request('message',data); }
    catch (e) { if (state) emit(state); throw e; }
  };
  window.acquireVsCodeApi = () => ({
    getState: () => ({下書き:draft}), setState: value => { draft = value.下書き; },
    postMessage: message => {
      if (message.type === 'ready') {
        if (events) return;
        events = new EventSource('events');
        events.onmessage = event => {
          const data = JSON.parse(event.data);
          if (data.type === 'state') state = data;
          emit(data);
        };
        events.onerror = () => {
          if (state) emit({...state, 画面接続済み:false, 接続エラー:'画面との接続が切れました。再接続しています…'});
          else error('接続が切れました。再接続しています…');
        };
      } else if (message.type === 'chooseModel') {
        const provider = typeof message.provider === 'string' ? message.provider : '';
        void request(`catalog?provider=${encodeURIComponent(provider)}`).then(result => {
          emit({type:'modelCatalog', provider, items:provider ? result.models : result.providers});
        }).catch(value => emit({type:'modelCatalogError', provider, message:String(value.message || value)}));
      }
      else if (message.type === 'setModel') void send({type:'model',provider:message.provider,model:message.model}).catch(error);
      else if (message.type === 'copy') void navigator.clipboard.writeText(message.text).catch(error);
      else if (message.type === 'link' && /^https?:\/\//i.test(message.url)) window.open(message.url,'_blank','noopener,noreferrer');
      else void send(message).catch(error);
    }
  });
})();
