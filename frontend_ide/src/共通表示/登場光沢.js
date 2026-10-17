// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026

const active = new WeakMap();
export function stopOpeningShine(element) { active.get(element)?.(); }

// サイズを変更せず、表示が完了した面だけに一度光を走らせる。
export function openingShine(element) {
  stopOpeningShine(element);
  const doc = element?.ownerDocument, win = doc?.defaultView;
  if (!win || !element.isConnected || !element.animate) return () => {};
  const media = win.matchMedia('(prefers-reduced-motion: reduce)');
  if (media.matches) return () => {};
  const rect = element.getBoundingClientRect();
  if (rect.width <= 0 || rect.height <= 0) return () => {};
  const overlay = doc.createElement('div'), band = doc.createElement('div');
  overlay.className = 'opening-shine'; band.className = 'opening-shine-band';
  overlay.setAttribute('aria-hidden', 'true');
  Object.assign(overlay.style, { left: rect.left + 'px', top: rect.top + 'px', width: rect.width + 'px', height: rect.height + 'px', borderRadius: win.getComputedStyle(element).borderRadius });
  overlay.append(band); doc.body.append(overlay);
  const animation = band.animate([
    { transform: 'translateX(-100%)', opacity: 0 },
    { opacity: 1, offset: .18 },
    { opacity: 1, offset: .72 },
    { transform: 'translateX(100%)', opacity: 0 },
  ], { duration: 680, easing: 'cubic-bezier(.22,.61,.36,1)' });
  const clear = () => {
    win.clearTimeout(timeout); animation.cancel(); overlay.remove();
    win.removeEventListener('pagehide', clear); win.removeEventListener('resize', clear);
    media.removeEventListener('change', clear);
    if (active.get(element) === clear) active.delete(element);
  };
  const timeout = win.setTimeout(clear, 1000);
  active.set(element, clear);
  win.addEventListener('pagehide', clear); win.addEventListener('resize', clear);
  media.addEventListener('change', clear);
  animation.finished.then(clear, clear);
  return clear;
}

export function installOpeningShine(win = window) {
  let clear = () => {}, revision = 0;
  const shown = async () => {
    const own = ++revision, element = win.document.querySelector('.development-app');
    clear();
    // ネイティブのズーム後に始まる本文のフェードも完了してから光らせる。
    const animations = element?.getAnimations({ subtree: true }).filter(animation => ['startup-fade-in', 'standalone-reveal'].includes(animation.animationName)) || [];
    await Promise.allSettled(animations.map(animation => animation.finished));
    if (own === revision) clear = openingShine(element);
  };
  const faded = event => {
    if (event.animationName === 'panel-fade-in' && event.target.matches('.viewer-popup,.panel-opening')) openingShine(event.target);
  };
  win.addEventListener('aidiy-window-shown', shown);
  win.document.addEventListener('animationend', faded);
  return () => { revision++; clear(); win.removeEventListener('aidiy-window-shown', shown); win.document.removeEventListener('animationend', faded); };
}
