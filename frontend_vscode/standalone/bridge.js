(() => {
  let state, draft = '', events, picker;
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
  async function chooseModel() {
    if (picker || state?.実行中) return;
    picker = document.createElement('dialog');
    const dialog = picker;
    // 名前やモデル ID は textContent/value で設定する。
    dialog.innerHTML = '<form method="dialog"><h2>プロバイダ / モデル</h2><label>プロバイダ<select id="provider-select"></select></label><label>モデル<select id="model-select"></select></label><label id="custom-label" hidden>モデル ID<input id="custom-model" maxlength="300"></label><p class="picker-error" role="status"></p><div class="picker-actions"><button value="cancel">キャンセル</button><button id="apply-model" type="button" class="primary">選択</button></div></form>';
    document.body.append(dialog);
    dialog.addEventListener('close', () => { dialog.remove(); picker = undefined; });
    dialog.showModal();
    const providers = dialog.querySelector('#provider-select');
    const models = dialog.querySelector('#model-select');
    const apply = dialog.querySelector('#apply-model');
    const status = dialog.querySelector('.picker-error');
    const custom = dialog.querySelector('#custom-model');
    let revision = 0;
    const customVisibility = () => { dialog.querySelector('#custom-label').hidden = models.value !== '__manual__'; };
    models.onchange = customVisibility;
    const loadModels = async () => {
      const current = ++revision;
      apply.disabled = true; models.disabled = true; status.textContent = '取得中…';
      try {
        const slug = providers.value;
        const rows = slug ? (await request(`catalog?provider=${encodeURIComponent(slug)}`)).models : [];
        if (current !== revision || !dialog.isConnected) return;
        models.replaceChildren(new Option(slug ? '既定モデル' : 'CLI の設定', ''), ...rows.map(row => new Option(row.label,row.id)));
        if (slug && slug === state.provider && state.model && !rows.some(row => row.id === state.model)) models.add(new Option(state.model,state.model));
        if (slug) models.add(new Option('モデル ID を入力…','__manual__'));
        models.value = slug === state.provider ? state.model : '';
        if (models.selectedIndex < 0) models.selectedIndex = 0;
        models.disabled = !slug; apply.disabled = false; status.textContent = ''; customVisibility();
      } catch (e) { if (current === revision) status.textContent = e.message; }
    };
    apply.onclick = async () => {
      const model = models.value === '__manual__' ? custom.value.trim() : models.value;
      if (models.value === '__manual__' && !model) { custom.focus(); return; }
      apply.disabled = true;
      try { await send({type:'model', provider:providers.value, model}); dialog.close(); }
      catch (e) { status.textContent = e.message; apply.disabled = false; }
    };
    providers.onchange = loadModels;
    apply.disabled = true;
    try {
      const result = await request('catalog');
      if (!dialog.isConnected) return;
      providers.replaceChildren(new Option('自動',''), ...result.providers.map(row => new Option(row.label,row.id)));
      providers.value = state.provider;
      await loadModels();
    } catch (e) { status.textContent = e.message; }
  }
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
      } else if (message.type === 'chooseModel') void chooseModel().catch(error);
      else if (message.type === 'copy') void navigator.clipboard.writeText(message.text).catch(error);
      else if (message.type === 'link' && /^https?:\/\//i.test(message.url)) window.open(message.url,'_blank','noopener,noreferrer');
      else void send(message).catch(error);
    }
  });
  document.getElementById('standalone-new').onclick = () => { void send({type:'new'}).catch(error); };
})();
