// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
import { createApp, h, reactive } from 'vue';
import StatusBar from '../共通表示/状態バー.vue';
import WindowActions from '../共通表示/窓操作.vue';
import { createPanelWindowApi } from '../共通表示/窓操作.js';

// 既存Viewerと同じ状態バーを使用。窓操作は所有元IDE経由で対象の別窓だけへ送る。
export function mountPanelTitle(host, child, owner, title, kind) {
  const container = child.document.createElement('div');
  container.className = kind === 'panel-routes' ? 'route-window-actions' : 'panel-window-title';
  host.prepend(container);
  const state = reactive({ connected: false, mode: '', hideClose: false });
  const preserveDuringVR = kind === 'explorer' || kind === 'panel-routes';
  const ide = owner.document.querySelector('.development-app.ide');
  const source = owner.document.querySelector('.development-app.ide .ide-heading > .connection-bar');
  const sync = () => {
    state.connected = !!source?.classList.contains('online');
    state.mode = source?.classList.contains('offline') ? 'offline' : 'online';
    state.hideClose = preserveDuringVR && !!ide?.classList.contains('all-displays');
  };
  sync();
  const observer = new owner.MutationObserver(sync);
  if (source) observer.observe(source, { attributes: true, attributeFilter: ['class'] });
  if (preserveDuringVR && ide) observer.observe(ide, { attributes: true, attributeFilter: ['class'] });
  const windowApi = createPanelWindowApi(owner.aidiyWindow, child.name);
  const app = createApp({ render: () => kind === 'panel-routes'
    ? h(WindowActions, { windowApi, windowContext: child, hideClose: state.hideClose, maximizeDisabled: true, maximizeTitle: '軌跡バーは最大化できません' })
    : h(StatusBar, { title, status: '別ウィンドウ', ...state, desktop: true, windowApi, windowContext: child }) });
  app.mount(container);
  return () => { observer.disconnect(); app.unmount(); container.remove(); };
}
