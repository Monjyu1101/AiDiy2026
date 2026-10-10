// -*- coding: utf-8 -*-

// -------------------------------------------------------------------------
// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
// -------------------------------------------------------------------------

// 文書ごとの iframe 内で描画する。Monaco の AMD ローダーや星図のキー操作と分離する。
// 表示ライブラリは frontend_ide/viewer 自身の node_modules から遅延ロードする。
const $ = id => document.getElementById(id);
const content = $('content');
const params = new URLSearchParams(location.search);
const path = params.get('path');
const format = params.get('format');
const labels = { word: 'Word', excel: 'Excel', powerpoint: 'PowerPoint', pdf: 'PDF' };
let page = 0, pageCount = 1, renderPage = null, busy = false, pending = false;
let resizeTimer;

function notice(text = '', error = false) {
  $('notice').hidden = !text;
  $('notice').textContent = text;
  $('notice').classList.toggle('error', error);
}
function loadScript(src) {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = src;
    script.onload = resolve;
    script.onerror = () => reject(new Error('表示ライブラリを読み込めません。frontend_ide/viewer のセットアップを実行してください。'));
    document.head.append(script);
  });
}
function controls() {
  $('previous').disabled = busy || page <= 0;
  $('next').disabled = busy || page >= pageCount - 1;
}
function navigation(count) {
  pageCount = count;
  $('previous').hidden = count <= 1;
  $('next').hidden = count <= 1;
  controls();
}
// サイズ変更とページ操作を直列化し、同じ canvas への並行描画を避ける。
async function refresh() {
  if (!renderPage) return;
  pending = true;
  if (busy) return;
  busy = true;
  controls();
  try {
    while (pending) {
      pending = false;
      await renderPage();
    }
  } catch (error) {
    notice(`表示できませんでした: ${error.message || error}`, true);
  } finally {
    busy = false;
    controls();
  }
}
function move(delta) {
  if (busy) return;
  page = Math.max(0, Math.min(pageCount - 1, page + delta));
  content.scrollTo(0, 0);
  refresh();
}
$('previous').onclick = () => move(-1);
$('next').onclick = () => move(1);
$('zoom').onchange = () => refresh();
addEventListener('keydown', event => {
  const toggleExplorer = (event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'b';
  if (toggleExplorer || event.key === 'Escape') {
    event.preventDefault();
    parent.postMessage({ type: 'aidiy-ide-document-key', key: toggleExplorer ? 'explorer' : 'close' }, location.origin);
    return;
  }
  if (event.target instanceof HTMLSelectElement || event.target instanceof HTMLInputElement) return;
  if (pageCount <= 1) return;
  if (event.key === 'ArrowLeft' || event.key === 'PageUp') { event.preventDefault(); move(-1); }
  if (event.key === 'ArrowRight' || event.key === 'PageDown') { event.preventDefault(); move(1); }
});
new ResizeObserver(() => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => refresh(), 120);
}).observe(content);
content.addEventListener('click', event => {
  const link = event.target.closest?.('a');
  if (link && !link.getAttribute('href')?.startsWith('#')) event.preventDefault();
});
function displayWidth(naturalWidth) {
  return $('zoom').value === 'fit'
    ? Math.max(100, content.clientWidth - 26)
    : naturalWidth * Number($('zoom').value);
}
function makeCanvas() {
  content.className = 'canvas-view';
  const canvas = document.createElement('canvas');
  canvas.setAttribute('role', 'img');
  content.replaceChildren(canvas);
  $('zoom-label').hidden = false;
  return canvas;
}

async function word(data) {
  await loadScript('/office-vendor/jszip.js');
  await loadScript('/office-vendor/docx.js');
  content.className = 'word-view';
  const pages = document.createElement('div');
  pages.className = 'word-pages';
  content.replaceChildren(pages);
  await window.docx.renderAsync(data, pages, pages, {
    inWrapper: true, breakPages: true, ignoreLastRenderedPageBreak: false,
    renderHeaders: true, renderFooters: true, renderFootnotes: true,
    renderEndnotes: true, renderAltChunks: false, useBase64URL: true,
  });
  const sections = [...pages.querySelectorAll('section.docx')];
  if (!sections.length) throw new Error('文書のページが見つかりません。');
  const width = Math.max(...sections.map(section => section.offsetWidth)) + 24;
  pages.style.width = `${width}px`;
  $('zoom-label').hidden = false;
  $('page-status').textContent = `${sections.length} ページ`;
  renderPage = async () => { pages.style.zoom = $('zoom').value === 'fit' ? Math.min(1, (content.clientWidth - 2) / width) : Number($('zoom').value); };
}

async function excel(data) {
  await loadScript('/office-vendor/xlsx.js');
  const XLSX = window.XLSX;
  let input = data;
  const isDelimited = /\.(csv|tsv)$/i.test(path);
  if (isDelimited) {
    try { input = new TextDecoder('utf-8', { fatal: true }).decode(data); }
    catch { input = new TextDecoder('shift_jis').decode(data); }
  }
  const book = XLSX.read(input, { type: isDelimited ? 'string' : 'array', cellStyles: true, sheetRows: 100000 });
  if (!book.SheetNames.length) throw new Error('シートが見つかりません。');
  let sheetName = book.SheetNames[0];
  const ROWS = 200, COLS = 100;
  content.className = 'sheet-view';
  $('sheets').hidden = false;
  $('sheets').setAttribute('role', 'tablist');
  for (const name of book.SheetNames) {
    const button = document.createElement('button');
    button.type = 'button'; button.textContent = name;
    button.setAttribute('role', 'tab');
    button.onclick = () => { sheetName = name; page = 0; content.scrollTo(0, 0); refresh(); };
    $('sheets').append(button);
  }
  renderPage = async () => {
    const sheet = book.Sheets[sheetName];
    for (const button of $('sheets').children) button.setAttribute('aria-selected', String(button.textContent === sheetName));
    if (!sheet['!ref']) {
      navigation(1); $('page-status').textContent = '空のシート'; content.replaceChildren(); notice(); return;
    }
    const range = XLSX.utils.decode_range(sheet['!ref']);
    // 値のない結合先は !ref の外になることがあるため、結合範囲まで含める。
    for (const merge of sheet['!merges'] || []) {
      range.e.r = Math.max(range.e.r, Math.min(99999, merge.e.r));
      range.e.c = Math.max(range.e.c, merge.e.c);
    }
    navigation(Math.ceil((range.e.r - range.s.r + 1) / ROWS));
    const first = range.s.r + page * ROWS, last = Math.min(range.e.r, first + ROWS - 1);
    const lastCol = Math.min(range.e.c, range.s.c + COLS - 1);
    $('page-status').textContent = `${first + 1}–${last + 1} / ${range.e.r + 1} 行`;
    notice(lastCol < range.e.c || sheet['!fullref'] ? '大きいシートのため先頭100列・最大100,000行まで表示します。' : '');
    const table = document.createElement('table'); table.className = 'sheet-table';
    table.setAttribute('aria-label', sheetName);
    const head = table.createTHead().insertRow(); head.append(document.createElement('th'));
    for (let c = range.s.c; c <= lastCol; c++) {
      const cell = document.createElement('th'); cell.textContent = XLSX.utils.encode_col(c); cell.scope = 'col';
      const column = sheet['!cols']?.[c];
      const width = Math.min(360, Math.max(80, column?.wpx || (column?.wch || 12) * 7));
      cell.style.width = `${width}px`; cell.style.minWidth = `${width}px`; head.append(cell);
    }
    const merges = (sheet['!merges'] || []).filter(m => m.e.r >= first && m.s.r <= last && m.e.c >= range.s.c && m.s.c <= lastCol);
    const covered = new Set(), starts = new Map();
    for (const m of merges) {
      const r0 = Math.max(m.s.r, first), c0 = Math.max(m.s.c, range.s.c);
      const r1 = Math.min(m.e.r, last), c1 = Math.min(m.e.c, lastCol);
      starts.set(`${r0}:${c0}`, { rowSpan: r1 - r0 + 1, colSpan: c1 - c0 + 1, source: m.s });
      for (let r = r0; r <= r1; r++) for (let c = c0; c <= c1; c++) if (r !== r0 || c !== c0) covered.add(`${r}:${c}`);
    }
    const tbody = table.createTBody();
    for (let r = first; r <= last; r++) {
      const row = tbody.insertRow();
      const number = document.createElement('th'); number.textContent = String(r + 1); number.scope = 'row'; row.append(number);
      for (let c = range.s.c; c <= lastCol; c++) {
        if (covered.has(`${r}:${c}`)) continue;
        const cell = row.insertCell();
        const merge = starts.get(`${r}:${c}`);
        if (merge) { cell.rowSpan = merge.rowSpan; cell.colSpan = merge.colSpan; }
        const value = sheet[XLSX.utils.encode_cell(merge?.source || { r, c })];
        // 文書の値を HTML として解釈しない。数式は保存済みの計算結果を表示する。
        cell.textContent = value ? XLSX.utils.format_cell(value) : '';
        if (value?.f) cell.title = `数式: =${value.f}`;
        if (value?.t === 'n') cell.className = 'numeric';
        const fill = value?.s?.fgColor?.rgb;
        if (/^[0-9a-f]{6}$/i.test(fill || '')) cell.style.backgroundColor = `#${fill}`;
      }
    }
    content.replaceChildren(table);
  };
}

async function powerpoint(data) {
  await loadScript('/office-vendor/jszip.js');
  await loadScript('/office-vendor/chart.js');
  await loadScript('/office-vendor/pptx.js');
  const canvas = makeCanvas();
  const viewer = new window.PptxViewJS.PPTXViewer({ canvas, autoChartRerenderDelayMs: 0 });
  await viewer.loadFile(data);
  if (!viewer.getSlideCount()) throw new Error('スライドが見つかりません。');
  navigation(viewer.getSlideCount());
  // ライブラリは canvas の CSS サイズを描画サイズとして扱う。
  const size = viewer.processor.getSlideDimensions();
  const ratio = size.cx / size.cy;
  renderPage = async () => {
    const width = displayWidth(960);
    canvas.style.width = `${width}px`; canvas.style.height = `${width / ratio}px`;
    await viewer.render(canvas, { slideIndex: page });
    canvas.setAttribute('aria-label', `スライド ${page + 1}`);
    $('page-status').textContent = `${page + 1} / ${pageCount}`;
  };
  addEventListener('pagehide', () => viewer.destroy(), { once: true });
}

async function pdf(data) {
  const pdfjs = await import('/office-vendor/pdf.mjs');
  pdfjs.GlobalWorkerOptions.workerSrc = '/office-vendor/pdf.worker.mjs';
  const task = pdfjs.getDocument({
    data, cMapUrl: '/office-vendor/cmaps/', cMapPacked: true,
    standardFontDataUrl: '/office-vendor/standard_fonts/', wasmUrl: '/office-vendor/wasm/',
    isEvalSupported: false,
  });
  task.onPassword = () => { notice('パスワード付きPDFは表示できません。', true); task.destroy(); };
  const doc = await task.promise;
  navigation(doc.numPages);
  const canvas = makeCanvas();
  renderPage = async () => {
    const pdfPage = await doc.getPage(page + 1);
    const natural = pdfPage.getViewport({ scale: 1 });
    const width = displayWidth(natural.width);
    const viewport = pdfPage.getViewport({ scale: width / natural.width });
    const dpr = Math.min(devicePixelRatio || 1, 2);
    canvas.width = Math.ceil(viewport.width * dpr); canvas.height = Math.ceil(viewport.height * dpr);
    canvas.style.width = `${viewport.width}px`; canvas.style.height = `${viewport.height}px`;
    await pdfPage.render({ canvasContext: canvas.getContext('2d'), viewport, transform: [dpr, 0, 0, dpr, 0, 0] }).promise;
    canvas.setAttribute('aria-label', `PDF ${page + 1} ページ`);
    $('page-status').textContent = `${page + 1} / ${pageCount}`;
  };
  addEventListener('pagehide', () => { task.destroy(); }, { once: true });
}

async function main() {
  if (!path || !labels[format]) throw new Error('文書の指定が正しくありません。');
  $('format-name').textContent = labels[format];
  document.title = `${path.split('/').at(-1)} - ${labels[format]}`;
  const response = await fetch(`/api/document?path=${encodeURIComponent(path)}`, { cache: 'no-store' });
  if (!response.ok) throw new Error(response.status === 404 ? 'ファイルが見つかりません。' : await response.text());
  const data = await response.arrayBuffer();
  await ({ word, excel, powerpoint, pdf })[format](data);
  notice();
  await refresh();
}
main().catch(error => notice(`表示できませんでした: ${error.message || error}`, true));
