(() => {
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
        events = new EventSource('events');
        events.onmessage = event => {
          const data = JSON.parse(event.data);
          if (data.type === 'state') { state = data; document.getElementById('standalone-new').disabled = data.実行中; }
          emit(data);
        };
        events.onerror = () => {
          if (state) emit({...state, 作業フォルダ:null});
          error('接続が切れました。再接続しています…');
        };
      } else if (message.type === 'chooseModel') {
        const provider = typeof message.provider === 'string' ? message.provider : '';
        void request(`catalog?provider=${encodeURIComponent(provider)}`).then(result => {
          emit({type:'modelCatalog', provider, items:provider ? result.models : result.providers});
        }).catch(value => emit({type:'modelCatalogError', provider, message:String(value.message || value)}));
      }
      else if (message.type === 'setModel') void send({type:'model',provider:message.provider,model:message.model}).catch(error);
      else if (message.type === 'deleteHistory') {
        if (window.confirm('この会話を削除しますか？')) void send(message).catch(error);
      }
      else if (message.type === 'copy') void navigator.clipboard.writeText(message.text).catch(error);
      else if (message.type === 'link' && /^https?:\/\//i.test(message.url)) window.open(message.url,'_blank','noopener,noreferrer');
      else void send(message).catch(error);
    }
  });
  document.getElementById('standalone-new').onclick = () => { void send({type:'new'}).catch(error); };
})();
