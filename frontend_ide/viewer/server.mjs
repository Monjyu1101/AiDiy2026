// -*- coding: utf-8 -*-

// -------------------------------------------------------------------------
// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
// -------------------------------------------------------------------------

// AiDiy IDE の単独サーバー。作業フォルダを走査して星図用のツリーを返し、ファイルの中身と web/ の画面を配信する。
// 依存パッケージなし（Node 標準のみ）。待受は 127.0.0.1 だけ。
import { createServer } from 'node:http';
import { open, readFile, readdir, realpath, stat } from 'node:fs/promises';
import { basename, extname, isAbsolute, join, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { forwardedOrigin } from './launch-options.mjs';
import { createCoreConnection } from './core-connection.mjs';
import { createPanels } from './panels.mjs';

const webRoot = fileURLToPath(new URL('./web/', import.meta.url));
// ファイルビューア用の Monaco Editor（`python frontend_ide/viewer/_setup.py` で導入。無ければ画面側が簡易表示にする）
const monacoRoot = fileURLToPath(new URL('./node_modules/monaco-editor/min/', import.meta.url));
const modulesRoot = fileURLToPath(new URL('./node_modules/', import.meta.url));
const ASSET_TYPES = {
  '.js': 'text/javascript; charset=utf-8', '.mjs': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.ttf': 'font/ttf',
  '.json': 'application/json; charset=utf-8', '.svg': 'image/svg+xml',
  '.bcmap': 'application/octet-stream', '.pfb': 'application/octet-stream', '.wasm': 'application/wasm',
};
// Office Viewer と同系統の表示ライブラリを、自前の依存から配信する。
// node_modules 全体は公開せず、表示に必要な資産だけを許可する。
const OFFICE_ASSETS = {
  '/office-vendor/jszip.js': 'jszip/dist/jszip.min.js',
  '/office-vendor/docx.js': 'docx-preview/dist/docx-preview.min.js',
  '/office-vendor/xlsx.js': 'xlsx/dist/xlsx.full.min.js',
  '/office-vendor/chart.js': 'chart.js/dist/chart.umd.js',
  '/office-vendor/pptx.js': 'pptxviewjs/dist/PptxViewJS.min.js',
  '/office-vendor/pdf.mjs': 'pdfjs-dist/build/pdf.mjs',
  '/office-vendor/pdf.worker.mjs': 'pdfjs-dist/build/pdf.worker.mjs',
};
const OFFICE_CSP = "default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data: blob:; connect-src 'self' blob:; worker-src 'self' blob:; base-uri 'none'; form-action 'none'; frame-ancestors 'self'";

// 星にしないフォルダ（依存物・生成物・キャッシュ）。
const IGNORED = new Set([
  'node_modules', '.git', 'dist', 'out', 'build', '__pycache__', '.venv', 'venv',
  '_cache', '.pytest_cache', '.mypy_cache', '.ruff_cache', '.next', '.turbo', '.cache',
]);
const MAX_FILES = 30000;
const MAX_TEXT = 1024 * 1024;          // ビューアに送るテキストの上限（先頭のみ）
const MAX_IMAGE = 20 * 1024 * 1024;    // ビューアに送る画像の上限
const MAX_DOCUMENT = 50 * 1024 * 1024; // Office / PDF の表示上限
const DOCUMENTS = {
  '.docx': 'word', '.dotx': 'word',
  '.xlsx': 'excel', '.xls': 'excel', '.xlsm': 'excel', '.ods': 'excel', '.csv': 'excel', '.tsv': 'excel',
  '.pptx': 'powerpoint', '.pptm': 'powerpoint', '.pdf': 'pdf',
};

const STATIC = {
  '/': ['index.html', 'text/html; charset=utf-8'],
  '/app.js': ['app.js', 'text/javascript; charset=utf-8'],
  '/desktop.js': ['desktop.js', 'text/javascript; charset=utf-8'],
  '/connection.js': ['connection.js', 'text/javascript; charset=utf-8'],
  '/connection.css': ['connection.css', 'text/css; charset=utf-8'],
  '/panels.js': ['panels.js', 'text/javascript; charset=utf-8'],
  '/panels.css': ['panels.css', 'text/css; charset=utf-8'],
  '/AiDiy.png': ['AiDiy.png', 'image/png'],
  '/layout.js': ['layout.js', 'text/javascript; charset=utf-8'],
  '/style.css': ['style.css', 'text/css; charset=utf-8'],
  '/office.html': ['office.html', 'text/html; charset=utf-8'],
  '/office.js': ['office.js', 'text/javascript; charset=utf-8'],
  '/office.css': ['office.css', 'text/css; charset=utf-8'],
  '/licenses.html': ['licenses.html', 'text/html; charset=utf-8'],
  '/licenses.css': ['licenses.css', 'text/css; charset=utf-8'],
  '/LICENSE.txt': ['LICENSE.txt', 'text/plain; charset=utf-8'],
  '/THIRD_PARTY_NOTICES.txt': ['THIRD_PARTY_NOTICES.txt', 'text/plain; charset=utf-8'],
};
const IMAGES = {
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.gif': 'image/gif',
  '.webp': 'image/webp', '.bmp': 'image/bmp', '.ico': 'image/x-icon', '.svg': 'image/svg+xml',
};

/** フォルダを再帰的に走査する。フォルダは {n, d:[子フォルダ], f:[[名前, サイズ, 更新ms]]}。 */
export async function scanTree(root) {
  let count = 0, truncated = false;
  async function walk(dir, name) {
    const node = { n: name, d: [], f: [] };
    let entries;
    try { entries = await readdir(dir, { withFileTypes: true }); } catch { return node; }
    entries.sort((a, b) => a.name.localeCompare(b.name));
    for (const entry of entries) {
      if (count >= MAX_FILES) { truncated = true; break; }
      const full = join(dir, entry.name);
      if (entry.isDirectory()) {
        if (IGNORED.has(entry.name)) continue;
        node.d.push(await walk(full, entry.name));
      } else if (entry.isFile()) {
        try {
          const info = await stat(full);
          node.f.push([entry.name, info.size, Math.round(info.mtimeMs)]);
          count++;
        } catch { /* 走査中に消えたファイル */ }
      }
    }
    return node;
  }
  const tree = await walk(root, basename(root) || root);
  return { root, scannedAt: Date.now(), files: count, truncated, tree };
}

/** 作業フォルダからの相対パス（/ 区切り）を実ファイルへ解決する。作業フォルダの外（.. やリンク先）は null。 */
async function insideRoot(root, rel) {
  if (!rel || rel.includes('\0')) return null;
  const realRoot = await realpath(root);
  let full;
  try { full = await realpath(resolve(realRoot, ...rel.split('/'))); } catch { return null; }
  const back = relative(realRoot, full);
  // 空（ルート自身）、親への脱出、別ドライブ（絶対パスが返る）を拒否する
  if (!back || back === '..' || back.startsWith(`..${sep}`) || isAbsolute(back)) return null;
  return full;
}

/** 先頭 max バイトを読む。 */
async function readHead(full, max) {
  const handle = await open(full, 'r');
  try {
    const buffer = Buffer.alloc(max);
    const { bytesRead } = await handle.read(buffer, 0, max, 0);
    return buffer.subarray(0, bytesRead);
  } finally { await handle.close(); }
}

/** UTF-8 として読めなければ Shift_JIS（Windows の .bat など）で読む。 */
function decodeText(bytes) {
  try { return { text: new TextDecoder('utf-8', { fatal: true }).decode(bytes), encoding: 'UTF-8' }; } catch { /* 次へ */ }
  try { return { text: new TextDecoder('shift_jis', { fatal: true }).decode(bytes), encoding: 'Shift_JIS' }; } catch { /* 次へ */ }
  return { text: new TextDecoder('utf-8').decode(bytes), encoding: 'UTF-8（一部読めない文字あり）' };
}

/** ビューア用: テキストは中身、画像は種類、それ以外はバイナリとして返す。 */
async function describeFile(root, rel) {
  const full = await insideRoot(root, rel);
  if (!full) return null;
  const info = await stat(full);
  if (!info.isFile()) return null;
  const image = IMAGES[extname(full).toLowerCase()];
  if (image) return { kind: 'image', size: info.size, tooLarge: info.size > MAX_IMAGE };
  const format = DOCUMENTS[extname(full).toLowerCase()];
  if (format) return { kind: 'office', format, size: info.size, tooLarge: info.size > MAX_DOCUMENT };
  const head = await readHead(full, Math.min(info.size, MAX_TEXT));
  // 先頭 8KB に NUL があればバイナリとみなす（UTF-16 のテキストもここではバイナリ扱い）
  if (head.subarray(0, 8192).includes(0)) return { kind: 'binary', size: info.size };
  // 上限で切った場合、末尾の文字が途中で切れていることがあるので最後の改行までにそろえる
  let bytes = head;
  const truncated = info.size > head.length;
  if (truncated) { const lastNewline = bytes.lastIndexOf(0x0a); if (lastNewline > 0) bytes = bytes.subarray(0, lastNewline + 1); }
  return { kind: 'text', size: info.size, truncated, ...decodeText(bytes) };
}

/** テキスト内容の部分一致検索。外部コマンドや正規表現は実行しない。 */
export async function grepFiles(root, query, { caseSensitive = false, signal } = {}) {
  const needle = caseSensitive ? query : query.toLocaleLowerCase();
  if (!needle || query.length > 256) throw new Error('検索語は1〜256文字で指定してください。');
  const paths = [], files = [];
  let checked = 0, skipped = 0, bytes = 0, truncated = false, cursor = 0;
  const deadline = Date.now() + 30000;
  async function walk(dir, prefix = '') {
    const entries = await readdir(dir, { withFileTypes: true }).catch(() => []);
    entries.sort((a, b) => a.name.localeCompare(b.name));
    for (const entry of entries) {
      if (signal?.aborted) return;
      if (files.length >= MAX_FILES || Date.now() > deadline) { truncated = true; return; }
      const path = prefix ? `${prefix}/${entry.name}` : entry.name;
      if (entry.isDirectory()) {
        if (!IGNORED.has(entry.name) && entry.name !== 'backup') await walk(join(dir, entry.name), path);
      } else if (entry.isFile()) files.push(path);
      if (truncated) return;
    }
  }
  await walk(root);
  // 読み取りは8件に制限する。大きなプロジェクトでも同時オープン数を増やさない。
  async function worker() {
    while (cursor < files.length && !signal?.aborted) {
      if (bytes >= 256 * MAX_TEXT || Date.now() > deadline) { truncated = true; return; }
      const path = files[cursor++];
      try {
        const full = await insideRoot(root, path);
        if (!full) { skipped++; continue; }
        const info = await stat(full);
        const ext = extname(full).toLowerCase();
        if (!info.isFile() || info.size > MAX_TEXT || IMAGES[ext] || (DOCUMENTS[ext] && !['.csv', '.tsv'].includes(ext))) { skipped++; continue; }
        if (bytes + info.size > 256 * MAX_TEXT) { truncated = true; continue; }
        bytes += info.size;
        const head = await readHead(full, Math.min(info.size, MAX_TEXT));
        if (head.includes(0)) { skipped++; continue; }
        const { text, encoding } = decodeText(head);
        if (encoding.includes('一部')) { skipped++; continue; }
        checked++;
        if ((caseSensitive ? text : text.toLocaleLowerCase()).includes(needle)) paths.push(path);
      } catch { skipped++; }
    }
  }
  await Promise.all(Array.from({ length: 8 }, worker));
  paths.sort();
  return { paths, checked, skipped, truncated };
}

/** 既定は OS による空きポート割り当て。明示ポートが使用中なら再割り当て（strict なら失敗）。 */
export async function startServer(root, port = 0, { strict = false, env = process.env, connection = createCoreConnection(root), requestHandler, panelsFactory = createPanels } = {}) {
  let allowedHosts = new Set();
  let allowedOrigins = new Set();
  const panels = panelsFactory(root, connection.state);
  const server = createServer(async (req, res) => {
    const url = new URL(req.url, 'http://127.0.0.1');
    const fail = (status, message) => { res.writeHead(status, { 'content-type': 'text/plain; charset=utf-8' }); res.end(message); };
    // DNS リバインディング対策: 127.0.0.1 / localhost 以外の Host 名で来た要求は受けない
    if (!allowedHosts.has(req.headers.host)) return fail(403, 'forbidden host');
    if (req.headers.origin && !allowedOrigins.has(req.headers.origin)) return fail(403, 'forbidden origin');
    if (req.headers['sec-fetch-site'] === 'cross-site') return fail(403, 'cross-site request');
    try {
      if (requestHandler && await requestHandler(req, res, url)) return;
      const json = value => {
        res.writeHead(200, { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' });
        res.end(JSON.stringify(value));
      };
      if (url.pathname === '/api/connection' && req.method === 'GET') return json(connection.state());
      if (['/api/connection/connect', '/api/connection/disconnect', '/api/connection/offline'].includes(url.pathname)) {
        if (req.method !== 'POST') return fail(405, 'POST required');
        req.resume();
        return json(url.pathname.endsWith('/disconnect') ? connection.disconnect() : url.pathname.endsWith('/offline') ? connection.offline() : await connection.connect());
      }
      // 画面を隠すだけでなく、未接続時はファイル取得も停止する。
      if (url.pathname.startsWith('/api/') && !connection.state().active) return fail(503, 'AiDiy接続利用またはオフライン利用を選択してください。');
      if (url.pathname === '/api/panels/code' || url.pathname === '/api/panels/live') {
        if (req.method !== 'POST') return fail(405, 'POST required');
        if (url.pathname.endsWith('/live') && connection.state().mode !== 'online') return fail(403, 'オフラインではCodeだけを利用できます。');
        req.resume();
        return json({ url: await panels.open(url.pathname.split('/').at(-1)) });
      }
      if (url.pathname.startsWith('/panels/')) return await panels.http(req, res);
      const desktopLegal = {
        '/electron-license.txt': ['electron/LICENSE', 'text/plain; charset=utf-8'],
        '/chromium-licenses.html': ['electron/dist/LICENSES.chromium.html', 'text/html; charset=utf-8'],
      }[url.pathname];
      if (desktopLegal) {
        const body = await readFile(join(modulesRoot, desktopLegal[0])).catch(() => null);
        if (!body) return fail(404, 'Electron 版のセットアップ後に参照できます。');
        res.writeHead(200, { 'content-type': desktopLegal[1], 'content-security-policy': "default-src 'none'; style-src 'unsafe-inline'; sandbox", 'x-content-type-options': 'nosniff' });
        res.end(body); return;
      }
      if (url.pathname === '/api/grep') {
        if (req.method !== 'GET') return fail(405, 'GET required');
        const query = url.searchParams.get('q') || '';
        if (!query || query.length > 256) return fail(400, '検索語は1〜256文字で指定してください。');
        const controller = new AbortController();
        res.once('close', () => controller.abort());
        const result = await grepFiles(root, query, { caseSensitive: url.searchParams.get('case') === '1', signal: controller.signal });
        if (controller.signal.aborted) return;
        if (!connection.state().active) return fail(503, '利用が終了しました。');
        return json(result);
      }
      if (url.pathname === '/api/galaxy') {
        const body = JSON.stringify(await scanTree(root));
        res.writeHead(200, { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' });
        res.end(body);
        return;
      }
      if (url.pathname === '/api/file') {
        const result = await describeFile(root, url.searchParams.get('path'));
        if (!result) return fail(404, 'not found');
        res.writeHead(200, { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' });
        res.end(JSON.stringify(result));
        return;
      }
      if (url.pathname === '/api/raw') {
        // 画像だけを生で返す（SVG はスクリプトを動かさないよう CSP を付ける）
        const full = await insideRoot(root, url.searchParams.get('path'));
        const type = full && IMAGES[extname(full).toLowerCase()];
        if (!type) return fail(404, 'not found');
        const info = await stat(full);
        if (!info.isFile() || info.size > MAX_IMAGE) return fail(413, 'too large');
        res.writeHead(200, {
          'content-type': type, 'cache-control': 'no-store', 'x-content-type-options': 'nosniff',
          'content-security-policy': "default-src 'none'; style-src 'unsafe-inline'; sandbox",
        });
        res.end(await readFile(full));
        return;
      }
      if (url.pathname === '/api/document') {
        const full = await insideRoot(root, url.searchParams.get('path'));
        if (!full || !DOCUMENTS[extname(full).toLowerCase()]) return fail(404, 'not found');
        const info = await stat(full);
        if (!info.isFile()) return fail(404, 'not found');
        if (info.size > MAX_DOCUMENT) return fail(413, '文書が大きすぎます（上限 50MB）。');
        res.writeHead(200, {
          'content-type': 'application/octet-stream', 'cache-control': 'no-store',
          'x-content-type-options': 'nosniff', 'content-disposition': 'attachment',
        });
        res.end(await readFile(full));
        return;
      }
      if (url.pathname.startsWith('/office-vendor/')) {
        let asset = OFFICE_ASSETS[url.pathname];
        // PDF の日本語 CMap・標準フォント・画像デコーダー。
        const pdfAsset = /^\/office-vendor\/(cmaps|standard_fonts|wasm)\/([a-zA-Z0-9_.-]+)$/.exec(url.pathname);
        if (pdfAsset && !pdfAsset[2].startsWith('.')) asset = `pdfjs-dist/${pdfAsset[1]}/${pdfAsset[2]}`;
        if (!asset) return fail(404, 'not found');
        let body;
        try { body = await readFile(join(modulesRoot, asset)); } catch { return fail(404, '表示ライブラリがありません。frontend_ide/viewer のセットアップを実行してください。'); }
        res.writeHead(200, { 'content-type': ASSET_TYPES[extname(asset)] || 'application/octet-stream', 'cache-control': 'no-cache', 'x-content-type-options': 'nosniff' });
        res.end(body);
        return;
      }
      if (url.pathname.startsWith('/monaco/')) {
        const full = resolve(monacoRoot, ...decodeURIComponent(url.pathname.slice('/monaco/'.length)).split('/'));
        const back = relative(monacoRoot, full);
        const type = ASSET_TYPES[extname(full).toLowerCase()];
        if (!type || !back || back.startsWith('..') || isAbsolute(back)) return fail(404, 'not found');
        let body;
        try { body = await readFile(full); } catch { return fail(404, 'not found'); }
        res.writeHead(200, { 'content-type': type, 'cache-control': 'max-age=86400' });
        res.end(body);
        return;
      }
      const file = STATIC[url.pathname];
      if (!file) return fail(404, 'not found');
      res.writeHead(200, {
        'content-type': file[1], 'cache-control': 'no-store',
        ...(url.pathname === '/office.html' ? { 'content-security-policy': OFFICE_CSP } : {}),
      });
      res.end(await readFile(join(webRoot, file[0])));
    } catch (error) {
      fail(500, String(error?.message || error));
    }
  });
  server.on('upgrade', (req, socket, head) => {
    if (!allowedHosts.has(req.headers.host) || !allowedOrigins.has(req.headers.origin)
        || req.headers['sec-fetch-site'] === 'cross-site') { socket.destroy(); return; }
    void panels.upgrade(req, socket, head).catch(() => socket.destroy());
  });
  server.once('close', () => { connection.close(); void panels.close(); });
  const listen = p => new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(p, '127.0.0.1', () => { server.off('error', reject); resolve(); });
  });
  try { await listen(port); } catch (error) {
    if (error.code !== 'EADDRINUSE' || strict) { await panels.close(); connection.close(); throw error; }
    await listen(0);
  }
  const actual = server.address().port;
  allowedHosts = new Set([`127.0.0.1:${actual}`, `localhost:${actual}`]);
  const forwarded = forwardedOrigin(actual, env);
  if (forwarded) allowedHosts.add(new URL(forwarded).host);
  allowedOrigins = new Set([`http://127.0.0.1:${actual}`, `http://localhost:${actual}`, ...(forwarded ? [forwarded] : [])]);
  async function close() {
    connection.close();
    // upgrade済みの音声ソケットはcloseAllConnectionsでは閉じないため先に破棄する。
    await panels.close();
    server.closeAllConnections();
    await new Promise(done => server.close(done));
  }
  return { server, close, url: `http://127.0.0.1:${actual}/`, publicUrl: `${forwarded || `http://127.0.0.1:${actual}`}/` };
}
