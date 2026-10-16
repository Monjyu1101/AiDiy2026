// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026

// ブラウザーのscreen座標はCSS px。devicePixelRatio（OS拡大率を含む）は重ねて掛けない。
// 外枠/表示領域の差からツールバーを見積もる。配置要求の最終判断はブラウザーが行う。
export function popupFeatures(rect, win = window) {
  const screen = win.screen, margin = 8;
  const left = Number.isFinite(screen.availLeft) ? screen.availLeft : win.screenX;
  const top = Number.isFinite(screen.availTop) ? screen.availTop : win.screenY;
  const width = Math.min(Math.max(300, Math.round(rect.width)), Math.max(100, screen.availWidth - margin * 2));
  const height = Math.min(Math.max(320, Math.round(rect.height)), Math.max(100, screen.availHeight - 80));
  const border = Math.max(0, (win.outerWidth - win.innerWidth) / 2);
  const chrome = Math.max(0, win.outerHeight - win.innerHeight - border);
  const x = Math.round(Math.max(left + margin, Math.min(win.screenX + border + rect.left, left + screen.availWidth - width - margin)));
  const y = Math.round(Math.max(top + margin, Math.min(win.screenY + chrome + rect.top, top + screen.availHeight - height - 60)));
  return `popup,left=${x},top=${y},width=${width},height=${height}`;
}

export const panelRect = element => {
  const rect = element?.getBoundingClientRect();
  return rect ? { left: rect.left, top: rect.top, width: rect.width, height: rect.height } : { left: 24, top: 78, width: 380, height: 680 };
};

// 内容の再描画では呼ばず、非表示から開いた時・別窓から戻した時だけ使う。
const fades = new WeakMap();
export function fadePanel(element) {
  if (!element?.animate) return;
  fades.get(element)?.cancel();
  if (element.ownerDocument?.defaultView?.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  fades.set(element, element.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 260, easing: 'ease-out' }));
}

// Vueのインスタンス・DOM・イベントをそのまま移動する。検索ジョブを再発行せず、
// AI入力、検索結果、展開、選択、スクロールも同じ実体を保持する。
export function createPanelWindow({ element, changed, report, win = window }) {
  let child, parent, anchor, timer, opening = false, disposed = false, detached = false, documentSeen;
  let cleanupDocument = () => {};
  const restoreScroll = () => {
    const positions = [element(), ...element().querySelectorAll('*')].map(node => [node, node.scrollTop, node.scrollLeft]);
    return () => positions.forEach(([node, top, left]) => { node.scrollTop = top; node.scrollLeft = left; });
  };
  function restore() {
    clearInterval(timer); timer = undefined; cleanupDocument(); documentSeen = undefined;
    const node = element();
    if (node && parent) {
      const scroll = restoreScroll(); parent.insertBefore(node, anchor?.parentNode === parent ? anchor : null); scroll();
    }
    anchor?.remove(); anchor = parent = undefined;
    const closing = child; child = undefined;
    if (closing && !closing.closed) closing.close();
    if (detached) { detached = false; changed(false); }
  }
  async function attach() {
    const target = child, doc = target.document;
    if (doc === documentSeen || opening) return;
    opening = true;
    try {
      cleanupDocument(); doc.title = 'AiDiy IDE / Explorer';
      const base = doc.createElement('base'); base.href = win.document.baseURI; doc.head.append(base);
      const loads = [...win.document.querySelectorAll('style, link[rel="stylesheet"]')].map(style => {
        const copy = style.cloneNode(true);
        const loaded = copy.tagName === 'LINK' ? new Promise((resolve, reject) => {
          copy.onload = resolve; copy.onerror = () => reject(Error('別窓の表示を準備できません。'));
        }) : Promise.resolve();
        doc.head.append(copy); return loaded;
      });
      let timeout;
      try { await Promise.race([Promise.all(loads), new Promise((_, reject) => { timeout = setTimeout(() => reject(Error('別窓の準備がタイムアウトしました。')), 8000); })]); }
      finally { clearTimeout(timeout); }
      if (disposed || child !== target || target.closed || target.document !== doc) return;
      const host = doc.createElement('main'); host.className = 'development-app explorer-window';
      doc.body.replaceChildren(host);
      // 元Documentのタイムラインを別窓へ持ち込まない（裏のIDEでは停止し得る）。
      fades.get(element())?.cancel(); fades.delete(element());
      const scroll = restoreScroll(); host.append(element()); scroll();
      documentSeen = doc;
      if (!detached) { detached = true; changed(true); }
      // リロードで旧Documentが消える前にDOMを親へ退避する。次のDocumentに同じ実体を戻す。
      const leaving = () => { const keepScroll = restoreScroll(); parent.insertBefore(element(), anchor); element().style.visibility = 'hidden'; keepScroll(); };
      target.addEventListener('beforeunload', leaving);
      cleanupDocument = () => { target.removeEventListener('beforeunload', leaving); if (element()) element().style.visibility = ''; };
      element().style.visibility = '';
      if (win.aidiyWindow?.showExplorer) {
        const result = await win.aidiyWindow.showExplorer(target.name, win.matchMedia('(prefers-reduced-motion: reduce)').matches);
        if (!result?.ok) throw Error(result?.error || '別窓を表示できません。');
      } else host.classList.add('panel-opening');
      target.focus();
    } finally { opening = false; }
  }
  async function pin() {
    if (disposed) return;
    if (child && !child.closed) { child.focus(); return; }
    if (opening) return;
    report(''); opening = true;
    try {
      const node = element(), rect = panelRect(node);
      let name = 'aidiy-explorer-' + win.crypto.randomUUID();
      if (win.aidiyWindow?.prepareExplorer) {
        const result = await win.aidiyWindow.prepareExplorer(rect);
        if (!result?.ok) throw Error(result?.error || '別窓を準備できません。');
        name = result.name;
      }
      if (disposed) return;
      child = win.open('about:blank', name, popupFeatures(rect, win));
      if (!child) throw Error('ポップアップがブロックされました。');
      parent = node.parentNode; anchor = win.document.createComment('Explorerを戻す位置'); parent.insertBefore(anchor, node);
      opening = false;
      await attach();
      if (!child || child.closed || disposed) { restore(); return; }
      timer = setInterval(() => {
        if (!child || child.closed) { restore(); return; }
        void attach().catch(error => { restore(); report(error.message); });
      }, 250);
    } catch (error) { restore(); report(error.message); }
    finally { opening = false; }
  }
  const end = () => { disposed = true; restore(); win.removeEventListener('pagehide', end); };
  win.addEventListener('pagehide', end);
  return { pin, restore, close: end, focus: () => { if (child && !child.closed) { child.focus(); return true; } return false; } };
}
