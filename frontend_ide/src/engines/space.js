// -*- coding: utf-8 -*-

// -------------------------------------------------------------------------
// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
// -------------------------------------------------------------------------

// AiDiy IDE 星図ビューア。いつも1階層だけを宇宙として描く。
//  - 直下のフォルダ → 銀河（星の数 = 配下の全ファイル数）
//  - 直下のファイル → 名前で決まる位置の自由惑星
// 銀河をダブルクリックすると、そのフォルダを新しい宇宙として突入する。
// 依存なしの Canvas 2D。名前のハッシュから3D座標を作り、透視投影して描く。

import { spacePosition, WORLD_RADIUS, HOME_VIEW, orbitView, panOffset, warpMotion } from '../../viewer/web/layout.js';
import { createAutoOrbit } from './auto-orbit.js';

export function createSpace(canvas, elements, { change = () => {}, layout = () => ({}), toggleExplorer = () => {} } = {}) {
let disposed = false, frameId = 0, loadGeneration = 0;
const listeners = new AbortController();
const listen = (target, name, callback, options = {}) => target.addEventListener(name, callback, { ...options, signal: listeners.signal });
const requestAnimationFrame = callback => disposed ? 0 : (frameId = window.requestAnimationFrame(callback));
const $ = id => elements[id];
const ctx = canvas.getContext('2d');
let W = 0, H = 0, DPR = 1, F = 800;
let CX = 0, CY = 0;          // 宇宙の画面中心。縦表示は上側の領域へ寄せる。

// ---------------------------------------------------------------- 種類と色
const KINDS = [
  { label: 'Python', color: '#ffd36b', ext: ['py', 'pyi', 'ipynb'] },
  { label: 'TS / JS', color: '#6fb8ff', ext: ['ts', 'tsx', 'js', 'mjs', 'cjs', 'jsx'] },
  { label: 'Vue', color: '#5cf2a6', ext: ['vue', 'svelte'] },
  { label: '文書', color: '#eef1ff', ext: ['md', 'txt', 'rst', 'pptx', 'pptm', 'docx', 'dotx', 'pdf', 'xlsx', 'xls', 'xlsm', 'ods'] },
  { label: '設定・データ', color: '#ffa25c', ext: ['json', 'yaml', 'yml', 'toml', 'ini', 'env', 'csv', 'sql', 'db', 'sqlite', 'lock'] },
  { label: 'HTML / CSS', color: '#ff7ac8', ext: ['html', 'htm', 'css', 'scss', 'less'] },
  { label: '画像', color: '#b98cff', ext: ['png', 'jpg', 'jpeg', 'gif', 'svg', 'ico', 'webp', 'bmp'] },
  { label: '音声・動画・3D', color: '#ff5c6a', ext: ['mp3', 'wav', 'ogg', 'mp4', 'webm', 'vrm', 'vrma', 'glb', 'fbx'] },
  { label: 'スクリプト', color: '#8ff7ea', ext: ['bat', 'cmd', 'sh', 'ps1'] },
  { label: 'その他', color: '#aab0c0', ext: [] },
];
const OTHER = KINDS.length - 1;
const KIND_BY_EXT = new Map();
KINDS.forEach((kind, index) => kind.ext.forEach(ext => KIND_BY_EXT.set(ext, index)));
function kindOf(name) {
  const lower = name.toLowerCase();
  if (lower === 'dockerfile') return 8;
  const dot = lower.lastIndexOf('.');
  return dot > 0 ? KIND_BY_EXT.get(lower.slice(dot + 1)) ?? OTHER : OTHER;
}
const rgb = hex => [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16));
const rgba = (hex, a) => `rgba(${rgb(hex).join(',')},${a})`;
const mix = (hex, to, t) => { const a = rgb(hex), b = rgb(to); return `rgb(${a.map((v, i) => Math.round(v + (b[i] - v) * t)).join(',')})`; };

// 大量に描く光の粒・銀河の光・惑星は事前に下絵を作る。
function sprite(size, draw) {
  const c = document.createElement('canvas');
  c.width = c.height = size;
  draw(c.getContext('2d'), size);
  return c;
}
function radial(stops) {
  return sprite(128, (g, size) => {
    const grad = g.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
    for (const [at, color] of stops) grad.addColorStop(at, color);
    g.fillStyle = grad;
    g.fillRect(0, 0, size, size);
  });
}
const STAR = KINDS.map(k => radial([[0, '#fff'], [0.1, rgba(k.color, 1)], [0.28, rgba(k.color, 0.35)], [0.6, rgba(k.color, 0.06)], [1, rgba(k.color, 0)]]));
const DISK = KINDS.map(k => radial([[0, rgba(k.color, 0.5)], [0.3, rgba(k.color, 0.2)], [0.7, rgba(k.color, 0.05)], [1, rgba(k.color, 0)]]));
const CORE = radial([[0, 'rgba(255,250,235,1)'], [0.12, 'rgba(255,236,200,.75)'], [0.4, 'rgba(255,210,160,.18)'], [1, 'rgba(255,200,150,0)']]);
const FLARE = radial([[0, 'rgba(255,255,255,1)'], [0.15, 'rgba(255,250,220,.6)'], [1, 'rgba(255,240,200,0)']]);
const PLANET = KINDS.map(k => sprite(128, (g, size) => {
  const c = size / 2, r = size * 0.3;
  // 大気の光
  const halo = g.createRadialGradient(c, c, r * 0.9, c, c, r * 1.6);
  halo.addColorStop(0, rgba(k.color, 0.45)); halo.addColorStop(1, rgba(k.color, 0));
  g.fillStyle = halo; g.fillRect(0, 0, size, size);
  // 左上から光が当たる球
  const body = g.createRadialGradient(c - r * 0.45, c - r * 0.45, r * 0.05, c, c, r);
  body.addColorStop(0, mix(k.color, '#ffffff', 0.7)); body.addColorStop(0.45, k.color); body.addColorStop(1, mix(k.color, '#000010', 0.85));
  g.fillStyle = body;
  g.beginPath(); g.arc(c, c, r, 0, Math.PI * 2); g.fill();
  // 縞模様
  g.save(); g.beginPath(); g.arc(c, c, r, 0, Math.PI * 2); g.clip();
  g.globalAlpha = 0.12; g.fillStyle = '#000';
  for (let i = -3; i <= 3; i++) g.fillRect(c - r, c + i * r * 0.28 - r * 0.05, r * 2, r * 0.08);
  g.restore();
}));

// ---------------------------------------------------------------- 乱数（パスから決まる）
function hash(text) {
  let h = 2166136261;
  for (let i = 0; i < text.length; i++) { h ^= text.charCodeAt(i); h = Math.imul(h, 16777619); }
  return h >>> 0;
}
function rngFor(text) {
  let a = hash(text) || 1;
  return () => {
    a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// ---------------------------------------------------------------- 宇宙（1階層）の組み立て
let scan = null;            // サーバーの走査結果
let trail = [];             // ルートから今の宇宙までのフォルダ名
let world = null;           // { galaxies, stars, planets, radius }
let knownPaths = null;      // 前回観測した全パス（新しく生まれた星の判定用）

const galaxyRadius = 160;

// 起点日時以降に更新したファイル（AI が触ったファイルを見つける目印）
let markMode = 'since', grepMatches = new Set(), grepController, grepRevision = 0;
const isFresh = file => markMode === 'grep' ? grepMatches.has(file.path) : since !== null && file.mtime >= since;
const fastBlink = t => 0.5 + 0.5 * Math.sin(t * 1.8);          // ファイル: 約3.5秒周期で穏やかに明滅
const slowBlink = t => 0.5 + 0.5 * Math.sin(t * 1.4 - 1.2);    // フォルダ: 約4.5秒周期
function recountFresh() {
  if (!world) return;
  for (const g of world.galaxies) g.fresh = g.stars.reduce((n, s) => n + (isFresh(s) ? 1 : 0), 0);
}

function collectFiles(node, prefix, out = []) {
  for (const [name, size, mtime] of node.f) out.push({ name, path: prefix ? `${prefix}/${name}` : name, size, mtime });
  for (const child of node.d) collectFiles(child, prefix ? `${prefix}/${child.n}` : child.n, out);
  return out;
}
function nodeAt(names) {
  let node = scan.tree;
  for (const name of names) {
    node = node.d.find(d => d.n === name);
    if (!node) return null;
  }
  return node;
}
const basePath = () => trail.join('/');

function buildWorld() {
  const node = nodeAt(trail);
  const prefix = basePath();
  const now = Date.now();
  const fileInfo = (file, rng) => {
    const ageDays = Math.max(0, (now - file.mtime) / 86400000);
    return {
      ...file, kind: kindOf(file.name), ageDays,
      mag: 1 + Math.log10(file.size + 1) * 0.55,
      glow: 0.5 + 0.5 * Math.exp(-ageDays / 90),
      phase: rng() * Math.PI * 2, speed: 0.6 + rng() * 1.8,
      born: knownPaths && !knownPaths.has(file.path) ? now : 0,
      x: 0, y: 0, z: 0,
    };
  };

  // 名前のハッシュを、件数に左右されない球内の3D座標へ対応させる。
  const galaxies = node.d.map(child => ({
    name: child.n, path: prefix ? `${prefix}/${child.n}` : child.n,
    files: collectFiles(child, prefix ? `${prefix}/${child.n}` : child.n),
    sub: child.d.length, R: galaxyRadius, ...spacePosition(child.n),
  }));

  // 銀河の星（名前で決まる球内の固定3D位置）
  const stars = [];
  for (const g of galaxies) {
    const rng = rngFor(`shape:${g.path}`);
    g.arms = 1;
    g.tilt = (rng() - 0.5) * 1.6;
    g.turn = rng() * Math.PI * 2;
    g.ct = Math.cos(g.tilt); g.st = Math.sin(g.tilt); g.cs = Math.cos(g.turn); g.ss = Math.sin(g.turn);
    g.kinds = new Array(KINDS.length).fill(0);
    g.stars = [];
    g.fresh = 0;
    for (const file of g.files) {
      const s = rngFor(file.path);
      const star = fileInfo(file, s);
      star.galaxy = g;
      // 別の下位フォルダにある同名ファイルは相対パスで区別する。
      const local = spacePosition(file.name, {
        scale: g.R, identity: file.path.slice(g.path.length + 1),
      });
      star.lr = Math.hypot(local.x, local.y, local.z);
      const [wx, wy, wz] = rotateLocal(g, local.x, local.y, local.z);
      star.x = g.x + wx; star.y = g.y + wy; star.z = g.z + wz;
      g.kinds[star.kind]++;
      if (isFresh(star)) g.fresh++;
      g.stars.push(star);
      stars.push(star);
    }
    g.kind = g.kinds.indexOf(Math.max(...g.kinds));
    // 円盤の法線（見かけの楕円を描くため）
    g.normal = rotateLocal(g, 0, 1, 0);
  }

  // 直下のファイルも同じ球状空間に固定する。
  const radius = WORLD_RADIUS;
  const planets = node.f.map(([name, size, mtime]) => {
    const path = prefix ? `${prefix}/${name}` : name;
    const planet = fileInfo({ name, path, size, mtime }, rngFor(`planet:${path}`));
    Object.assign(planet, spacePosition(name));
    planet.R = 9 + Math.log10(size + 1) * 3;
    planet.isPlanet = true;
    return planet;
  });

  const byPath = new Map();
  for (const s of stars) byPath.set(s.path, s);
  for (const p of planets) byPath.set(p.path, p);
  // 現在フォルダの目印は常に中心。ルートでも渦を表示する。
  const gate = {
    x: 0, y: 0, z: 0, R: 60,
    name: node.n,
  };
  return { galaxies, stars, planets, radius, byPath, gate };
}

function rotateLocal(g, x, y, z) {
  const y1 = y * g.ct - z * g.st, z1 = y * g.st + z * g.ct;
  return [x * g.cs - z1 * g.ss, y1, x * g.ss + z1 * g.cs];
}

// ---------------------------------------------------------------- 遠景の星（天の川）。色ごとにまとめて描く。
const FAR_GROUPS = [];
{
  const r = rngFor('far-sky');
  const colors = ['225,232,255', '255,214,170', '170,200,255'];
  for (let c = 0; c < 3; c++) for (let p = 0; p < 2; p++) FAR_GROUPS.push({ color: colors[c], phase: p * Math.PI, base: c === 0 ? 0.55 : 0.45, pts: [] });
  for (let i = 0; i < 2600; i++) {
    const band = i < 1500;
    const theta = r() * Math.PI * 2;
    const u = band ? (r() + r() + r() - 1.5) * 0.22 : r() * 2 - 1;
    const side = Math.sqrt(1 - u * u);
    const x = side * Math.cos(theta), y0 = u, z0 = side * Math.sin(theta);
    const tilt = 0.5, y = y0 * Math.cos(tilt) - z0 * Math.sin(tilt), z = y0 * Math.sin(tilt) + z0 * Math.cos(tilt);
    const tint = r(), group = (tint < 0.15 ? 1 : tint > 0.85 ? 2 : 0) * 2 + (r() < 0.5 ? 0 : 1);
    FAR_GROUPS[group].pts.push(x, y, z, r() < 0.03 ? 1.8 : band ? 0.5 + r() * 0.5 : 0.6 + r() * 0.8);
  }
}

// ---------------------------------------------------------------- カメラ
const cam = { tx: 0, ty: 0, tz: 0, ...HOME_VIEW, dist: 30000 };
const goal = { ...cam };
let autoSpin = true;
const autoOrbit = createAutoOrbit();
let cy = 1, sy = 0, cp = 1, sp = 0;
const P = { x: 0, y: 0, k: 0, z: 0 };

function project(x, y, z) {
  x -= cam.tx; y -= cam.ty; z -= cam.tz;
  const x1 = x * cy - z * sy, z1 = x * sy + z * cy;
  const y2 = y * cp - z1 * sp, z2 = y * sp + z1 * cp;
  const depth = z2 + cam.dist;
  if (depth < 4) return false;
  P.k = F / depth; P.z = depth;
  P.x = CX + x1 * P.k; P.y = CY - y2 * P.k;
  return true;
}
// 描画寸法はワールド寸法×透視倍率。画面上の最小/最大サイズで遠近差を潰さない。
const depthLight = depth => 0.3 + 0.7 / (1 + (depth / 2400) ** 2);
const nearFade = depth => Math.min(1, Math.max(0, (depth - 4) / 40));
/** 向きだけをカメラ座標へ回す（平行移動なし）。 */
function turn(x, y, z) {
  const x1 = x * cy - z * sy, z1 = x * sy + z * cy;
  return [x1, y * cp - z1 * sp, y * sp + z1 * cp];
}
// 画面の短辺に合わせて全景を広く使う。件数によらず同じ倍率で初期表示・全体表示する。
const overviewDistance = () => (world ? world.radius * 2.25 : 4000) * (F / Math.min(W, H));

// ---------------------------------------------------------------- 状態
let focus = null;            // 注目中の銀河
let selected = null;         // 選択中の星・惑星
let selectionOrigin = null;  // ファイルを選ぶ前の階層・視点（選び替えても保持）
let hovered = null;          // マウス下の星・惑星
let hoveredGalaxy = null;    // マウス下の銀河
let labelBoxes = [];
let galaxyHits = [];         // 画面上の銀河の当たり判定 [銀河, x, y, 半径]
let introAt = performance.now();
let bodies = [];             // 当たり判定する星・惑星
let projected = new Float32Array(0);
let diving = false;
let tracking = null;         // 追尾中の星・惑星
let hoveredGate = false;
let gateHit = null;          // 帰還ゲートの画面上の [x, y, 半径]
let since = null;            // 起点日時（ms）。これ以降に更新したファイルを明滅させる。null なら明滅なし
let voyages = {};            // 階層ごとの航路 { 階層パス: ['g:フォルダ' | 'f:ファイル', ...] }
let journal = [];            // 航海日誌（新しい順） [{ type, path, at }]

// ---------------------------------------------------------------- 描画
function resize() {
  DPR = Math.min(window.devicePixelRatio || 1, 2);
  W = innerWidth; H = innerHeight;
  canvas.width = Math.round(W * DPR); canvas.height = Math.round(H * DPR);
  F = Math.min(W, H) * 1.05;
}
listen(window, 'resize', resize);
resize();

/** 横表示は左右のパネル間。縦表示はプレビュー表示時だけ中心を上から25%へ寄せる。 */
let coverShown = '';
function measureCover() {
  const { left = 0, right = W, preview = false, centerY = H / 2 } = layout();
  return { x: preview ? (left + right) / 2 : W / 2, y: centerY };
}

let last = performance.now(), prevDist = cam.dist;
function frame(now) {
  if (disposed) { last = now; requestAnimationFrame(frame); return; }
  const dt = Math.min(0.25, (now - last) / 1000);
  last = now;
  const t = now / 1000;

  const flight = autoOrbit.step(now,dt,goal,overviewDistance(),!autoSpin || !world || !!selected || diving || dragging || document.hidden);
  if (flight) { Object.assign(goal,flight); tracking = null; }
  if (tracking) { goal.tx = tracking.x; goal.ty = tracking.y; goal.tz = tracking.z; }
  const ease = 1 - Math.exp(-dt * 4);
  for (const key of ['tx', 'ty', 'tz', 'yaw', 'pitch']) cam[key] += (goal[key] - cam[key]) * ease;
  cam.dist *= Math.exp((Math.log(goal.dist) - Math.log(cam.dist)) * ease);
  // パネル配置と縦横の切替に合わせ、投影中心を滑らかに移動する。
  const center = measureCover();
  CX = CX ? CX + (center.x - CX) * ease : center.x;
  CY = CY ? CY + (center.y - CY) * ease : center.y;
  cy = Math.cos(cam.yaw); sy = Math.sin(cam.yaw); cp = Math.cos(cam.pitch); sp = Math.sin(cam.pitch);
  const warp = Math.min(1.5, Math.abs(Math.log(cam.dist / prevDist)) / Math.max(dt, 1e-3) * 0.08);
  prevDist = cam.dist;

  ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
  ctx.globalCompositeOperation = 'source-over';
  ctx.globalAlpha = 1;
  ctx.fillStyle = '#000';
  ctx.fillRect(0, 0, W, H);

  ctx.globalCompositeOperation = 'lighter';
  drawFarSky(t, warp);
  if (world) drawFolderLinks(now);
  if (world) drawGalaxies(t, now);
  gateHit = null;
  if (world?.gate) drawGate(t);
  ctx.globalCompositeOperation = 'source-over';
  if (world) { drawPlanets(t, now); drawVoyage(t); drawLabels(t); }
  requestAnimationFrame(frame);
}

/** 現在フォルダの3D原点から、直下の銀河・ファイルへ静かな直線を引く。 */
function drawFolderLinks(now) {
  if (!project(0, 0, 0)) return;
  const x = P.x, y = P.y;
  const appear = Math.min(1, Math.max(0, (now - introAt) / 1000 - 0.8));
  if (!appear) return;
  ctx.save();
  ctx.globalCompositeOperation = 'source-over';
  ctx.strokeStyle = '#7897bf';
  ctx.lineWidth = 0.7;
  // 配下の全ファイルには引かず、現在見ている1階層の関係だけを表示する。
  for (const item of [...world.galaxies, ...world.planets]) {
    if (!project(item.x, item.y, item.z)) continue;
    // 背後だけでなく、画面外の天体へ伸びる線も表示しない。
    if (P.x < 0 || P.x > W || P.y < 0 || P.y > H) continue;
    ctx.globalAlpha = 0.2 * appear * depthLight(P.z) * nearFade(P.z);
    if (!ctx.globalAlpha) continue;
    ctx.beginPath();
    ctx.moveTo(x, y); ctx.lineTo(P.x, P.y);
    ctx.stroke();
  }
  ctx.restore();
}

function drawFarSky(t, warp) {
  for (const group of FAR_GROUPS) {
    const pts = group.pts;
    ctx.globalAlpha = group.base * (0.8 + 0.2 * Math.sin(t * 0.9 + group.phase));
    ctx.beginPath();
    for (let i = 0; i < pts.length; i += 4) {
      const [x1, y2, z2] = turn(pts[i], pts[i + 1], pts[i + 2]);
      if (z2 < 0.05) continue;
      const px = CX + x1 / z2 * F, py = CY - y2 / z2 * F, s = pts[i + 3];
      if (px < -50 || px > W + 50 || py < -50 || py > H + 50) continue;
      if (warp > 0.04) {
        // ワープ中は中心から放射状の光の筋にする
        ctx.moveTo(px, py); ctx.lineTo(px - (px - CX) * warp * 0.25, py - (py - CY) * warp * 0.25);
      } else ctx.rect(px - s / 2, py - s / 2, s, s);
    }
    if (warp > 0.04) { ctx.strokeStyle = `rgb(${group.color})`; ctx.lineWidth = 1; ctx.stroke(); }
    else { ctx.fillStyle = `rgb(${group.color})`; ctx.fill(); }
  }
  ctx.globalAlpha = 1;
}

const dimmed = g => focus && g !== focus;

function drawGalaxies(t, now) {
  const { galaxies } = world;
  const intro = (now - introAt) / 1000;
  bodies = [];
  galaxyHits = [];
  let p = 0;
  if (projected.length < (world.stars.length + world.planets.length) * 4) projected = new Float32Array((world.stars.length + world.planets.length) * 4);

  for (const g of galaxies) {
    const centerVisible = project(g.x, g.y, g.z);
    const gx = P.x, gy = P.y, gk = P.k, depth = P.z;
    const fade = Math.min(1, Math.max(0, (intro - 0.1 - Math.hypot(g.x, g.z) / world.radius * 0.8) / 1.0));
    const dim = dimmed(g) ? 0.3 : 1;
    if (centerVisible) {
      const light = depthLight(depth) * nearFade(depth);
      galaxyHits.push([g, gx, gy, g.R * gk]);

      // 円盤の光（見かけの傾きに合わせて楕円にする）。起点以降に更新したファイルを含む銀河はゆっくり明滅する。
      const [nx, ny, nz] = turn(...g.normal);
      const size = g.R * 2.6 * gk;
      const pulse = g.fresh ? slowBlink(t) : 0;
      if (size > 2) {
        ctx.save();
        ctx.translate(gx, gy);
        ctx.rotate(Math.atan2(-ny, nx));
        ctx.scale(Math.max(0.12, Math.abs(nz)), 1);
        ctx.globalAlpha = (0.28 + 0.4 * pulse) * fade * dim * light;
        ctx.drawImage(DISK[g.kind], -size / 2, -size / 2, size, size);
        ctx.restore();
        const core = g.R * (g.arms ? 0.7 : 1.0) * gk * (1 + 0.35 * pulse);
        ctx.globalAlpha = Math.min(1, (g.arms ? 0.55 : 0.4) + 0.4 * pulse) * fade * dim * light;
        ctx.drawImage(CORE, gx - core / 2, gy - core / 2, core, core);
      }
      if (g.fresh) {
        // 遠くからでも見つけられるよう、銀河を包む光の輪も明滅させる
        const halo = g.R * 3.2 * gk;
        ctx.globalAlpha = 0.22 * pulse * fade * light;
        ctx.drawImage(FLARE, gx - halo / 2, gy - halo / 2, halo, halo);
      }
    }

    // 銀河の中心が背後でも、手前にある個々の星は描く。
    for (const s of g.stars) {
      if (!project(s.x, s.y, s.z)) continue;
      const appear = Math.min(1, Math.max(0, fade * 1.6 - s.lr / g.R * 0.6));
      if (appear <= 0) continue;
      let alpha = s.glow * (0.78 + 0.22 * Math.sin(t * s.speed + s.phase)) * appear * dim;
      let size = s.mag * P.k * 4;
      const bornAge = s.born ? (now - s.born) / 1000 : 99;
      if (bornAge < 6) { alpha = 1; size *= 1 + 3 * (1 - bornAge / 6); }
      // 更新・検索対象は穏やかに明滅。選択中は白飛びを抑える。
      const fresh = isFresh(s);
      const blink = fresh ? fastBlink(t) : 0;
      if (fresh) { alpha = Math.min(s === selected ? 0.65 : 0.8, Math.max(alpha, (0.35 + 0.25 * blink) * appear)); size *= 1 + 0.08 * blink; }
      if (P.x < -size || P.x > W + size || P.y < -size || P.y > H + size) continue;
      alpha *= depthLight(P.z) * nearFade(P.z);
      ctx.globalAlpha = alpha;
      ctx.drawImage(STAR[s.kind], P.x - size / 2, P.y - size / 2, size, size);
      if (s !== selected && ((fresh && blink > 0.45) || bornAge < 6) && appear >= 1) drawNova(P.x, P.y, size, alpha, t, s.phase);
      bodies.push(s);
      projected[p++] = P.x; projected[p++] = P.y; projected[p++] = size; projected[p++] = 0;
    }
  }
  ctx.globalAlpha = 1;
}

function drawNova(x, y, size, alpha, t, phase) {
  const flare = size * (1.3 + 0.15 * Math.sin(t * 1.8 + phase));
  ctx.globalAlpha = alpha * 0.18;
  ctx.drawImage(FLARE, x - flare / 2, y - flare / 2, flare, flare);
  ctx.strokeStyle = 'rgba(255,248,220,.22)'; ctx.lineWidth = 0.8;
  ctx.beginPath();
  ctx.moveTo(x - flare, y); ctx.lineTo(x + flare, y);
  ctx.moveTo(x, y - flare * 0.7); ctx.lineTo(x, y + flare * 0.7);
  ctx.stroke();
}

function drawPlanets(t, now) {
  const intro = (now - introAt) / 1000;
  let p = bodies.length * 4;
  // 奥から順に描く
  const list = world.planets.map(planet => {
    return project(planet.x, planet.y, planet.z) ? { planet, x: P.x, y: P.y, k: P.k, z: P.z } : null;
  }).filter(Boolean).sort((a, b) => b.z - a.z);
  for (const { planet, x, y, k, z } of list) {
    const appear = Math.min(1, Math.max(0, intro - 1.2));
    let size = planet.R * k * 3.2;
    let alpha = appear * (focus ? 0.35 : 1);
    if (alpha <= 0) continue;
    const fresh = isFresh(planet);
    const blink = fresh ? fastBlink(t) : 0;
    if (fresh) { alpha = Math.max(alpha, appear * 0.6); size *= 1 + 0.025 * blink; }
    if (x < -size || x > W + size || y < -size || y > H + size) continue;
    alpha *= depthLight(z) * nearFade(z);
    ctx.globalAlpha = alpha;
    ctx.drawImage(PLANET[planet.kind], x - size / 2, y - size / 2, size, size);
    if (fresh) {
      ctx.globalCompositeOperation = 'lighter';
      ctx.globalAlpha = alpha * blink * (planet === selected ? 0.08 : 0.22);
      ctx.drawImage(FLARE, x - size * 0.55, y - size * 0.55, size * 1.1, size * 1.1);
      if (planet !== selected && blink > 0.45) drawNova(x, y, size * 0.45, alpha * blink, t, planet.phase);
      ctx.globalCompositeOperation = 'source-over';
    }
    bodies.push(planet);
    projected[p++] = x; projected[p++] = y; projected[p++] = size * 0.6; projected[p++] = 1;
  }
  ctx.globalAlpha = 1;
}

/** 帰還ゲート（親フォルダへ戻るワームホール）。 */
function drawGate(t) {
  const gate = world.gate;
  if (!project(gate.x, gate.y, gate.z)) return;
  const r = Math.max(16, gate.R * P.k);
  const alpha = Math.min(1, Math.max(0, (performance.now() - introAt) / 1000 - 1.2)) * (hoveredGate ? 1 : 0.8);
  gateHit = [P.x, P.y, r];
  ctx.globalAlpha = alpha * 0.8;
  ctx.drawImage(DISK[1], P.x - r * 2.4, P.y - r * 2.4, r * 4.8, r * 4.8);
  ctx.lineWidth = Math.max(1.2, r * 0.07);
  for (let i = 0; i < 4; i++) {
    const rr = r * (1 - i * 0.2), spin = t * (0.8 + i * 0.5) * (i % 2 ? -1 : 1);
    ctx.globalAlpha = alpha * (0.9 - i * 0.15);
    ctx.strokeStyle = i % 2 ? '#9fd8ff' : '#c8b6ff';
    ctx.beginPath(); ctx.arc(P.x, P.y, rr, spin, spin + Math.PI * 1.2); ctx.stroke();
  }
  ctx.globalAlpha = alpha;
  ctx.drawImage(FLARE, P.x - r * 0.7, P.y - r * 0.7, r * 1.4, r * 1.4);
  ctx.globalAlpha = 1;
}

/** 航路: この宇宙で訪れた銀河・星を訪れた順に結ぶ。古い区間ほど薄い。 */
function voyageTargets() {
  return (voyages[basePath()] || [])
    .map(key => key[0] === 'g' ? world.galaxies.find(g => g.path === key.slice(2)) : world.byPath.get(key.slice(2)))
    .filter(Boolean);
}
function drawVoyage(t) {
  const points = voyageTargets().map(p => (project(p.x, p.y, p.z) ? [P.x, P.y] : null));
  if (!points.length) return;
  const n = points.length;
  ctx.lineWidth = 1.4;
  ctx.strokeStyle = '#ffd98c';
  ctx.setLineDash([5, 7]);
  ctx.lineDashOffset = -t * 18;
  for (let i = 1; i < n; i++) {
    const a = points[i - 1], b = points[i];
    if (!a || !b) continue;
    ctx.globalAlpha = 0.15 + 0.65 * (i / (n - 1));
    ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke();
  }
  ctx.setLineDash([]);
  ctx.fillStyle = '#ffe2a0';
  points.forEach((s, i) => {
    if (!s) return;
    const latest = i === n - 1;
    const r = latest ? 5 + Math.sin(t * 3) * 1.2 : 3;
    ctx.globalAlpha = latest ? 0.95 : 0.25 + 0.5 * (i / n);
    ctx.beginPath();
    ctx.moveTo(s[0], s[1] - r); ctx.lineTo(s[0] + r, s[1]); ctx.lineTo(s[0], s[1] + r); ctx.lineTo(s[0] - r, s[1]);
    ctx.closePath(); ctx.fill();
  });
  ctx.globalAlpha = 1;
}

function drawLabels(t) {
  const font = '"Segoe UI","Yu Gothic UI",sans-serif';
  const intro = (performance.now() - introAt) / 1000;
  labelBoxes = [];
  ctx.textBaseline = 'middle';
  ctx.textAlign = 'center';
  const placed = box => {
    if (labelBoxes.some(b => box.x < b.x + b.w && box.x + box.w > b.x && box.y < b.y + b.h && box.y + box.h > b.y)) return false;
    labelBoxes.push(box);
    return true;
  };
  // 銀河の名前。更新のある銀河を優先して置き、残りは大きい順。
  // 重なる時は 下 → 上 → 右 → 左 の順に空いている位置を探す。
  for (const [g, gx, gy, r] of [...galaxyHits].sort((a, b) => (b[0].fresh ? 1 : 0) - (a[0].fresh ? 1 : 0) || b[3] - a[3])) {
    const hover = g === hoveredGalaxy;
    let alpha = Math.min(1, Math.max(0, intro - 1.0)) * (dimmed(g) ? 0.45 : 1);
    if (alpha <= 0.02) continue;
    // 「名前 (ファイル数)」の1行だけ。起点以降の更新があるフォルダは金色でゆっくり明滅させる。
    const name = `${g.name} (${g.files.length.toLocaleString()})`;
    ctx.font = `600 13px ${font}`;
    const w = ctx.measureText(name).width + 12;
    const below = Math.min(Math.max(r * 0.45, 18), 160), side = Math.min(Math.max(r * 0.5, 14), 160);
    const spot = [[gx, gy + below], [gx, gy - below - 14], [gx + side + w / 2 + 6, gy], [gx - side - w / 2 - 6, gy]]
      .find(([cx, cy]) => placed({ x: cx - w / 2, y: cy - 10, w, h: 20, g }));
    if (!spot) continue;
    const [x, ly] = spot;
    ctx.globalAlpha = hover ? 1 : alpha * (g.fresh ? 0.6 + 0.4 * slowBlink(t) : 0.95);
    ctx.shadowColor = g.fresh ? '#ffd36b' : KINDS[g.kind].color; ctx.shadowBlur = hover ? 16 : 8;
    ctx.fillStyle = hover ? '#fff' : g.fresh ? '#ffe9a8' : 'rgba(235,242,255,.95)';
    ctx.fillText(name, x, ly);
    ctx.shadowBlur = 0;
  }
  // 中央のワームホールには現在フォルダ名を表示する。
  if (gateHit) {
    const [x, y, r] = gateHit;
    const text = world.gate.name;
    ctx.font = `600 12px ${font}`;
    const w = ctx.measureText(text).width + 10;
    if (placed({ x: x - w / 2, y: y + r + 6, w, h: 20, gate: true })) {
      ctx.globalAlpha = hoveredGate ? 1 : 0.85;
      ctx.fillStyle = hoveredGate ? '#fff' : '#bfe3ff';
      ctx.shadowColor = '#7fc8ff'; ctx.shadowBlur = 10;
      ctx.fillText(text, x, y + r + 16);
      ctx.shadowBlur = 0;
    }
  }
  // 自由惑星の名前
  ctx.font = `11.5px ${font}`;
  ctx.textAlign = 'left';
  for (let i = 0; i < bodies.length; i++) {
    const b = bodies[i];
    const o = i * 4;
    const near = !b.isPlanet && projected[o + 2] >= 22 && (!focus || b.galaxy === focus);
    if (!b.isPlanet && !near) continue;
    const x = projected[o] + projected[o + 2] * (b.isPlanet ? 0.55 : 0.22) + 4, y = projected[o + 1];
    const w = ctx.measureText(b.name).width + 6;
    if (!placed({ x, y: y - 8, w, h: 16 })) continue;
    ctx.globalAlpha = b.isPlanet ? Math.min(0.9, Math.max(0, intro - 1.4)) * (focus ? 0.4 : 1) : Math.min(0.85, (projected[o + 2] - 22) / 20);
    ctx.fillStyle = b.isPlanet ? 'rgba(215,225,250,1)' : 'rgba(200,212,240,1)';
    ctx.fillText(b.name, x, y);
  }
  // 選択中・マウス下の照準
  for (const target of [selected, hovered]) {
    if (!target) continue;
    const i = bodies.indexOf(target);
    if (i < 0) continue;
    const x = projected[i * 4], y = projected[i * 4 + 1];
    const r = Math.max(9, Math.min(60, projected[i * 4 + 2] * (target.isPlanet ? 0.6 : 0.35)));
    ctx.globalAlpha = target === selected ? 0.95 : 0.6;
    ctx.strokeStyle = KINDS[target.kind].color;
    ctx.lineWidth = 1.2;
    const spin = t / 1.4;
    for (let q = 0; q < 4; q++) {
      ctx.beginPath();
      ctx.arc(x, y, r, spin + q * Math.PI / 2, spin + q * Math.PI / 2 + Math.PI / 4);
      ctx.stroke();
    }
  }
  ctx.globalAlpha = 1;
}

// ---------------------------------------------------------------- 操作
let dragging = false, dragMoved = 0, dragButton = 0, lastX = 0, lastY = 0;
const touch = new Map();
const touchIdle = () => { autoOrbit.interact(performance.now()); };

function setAutoSpin(value) {
  autoSpin = !!value;
  if (autoSpin) autoOrbit.resume();
  else {
    autoOrbit.reset();
    if (!selected && !focus && !diving) Object.assign(goal, cam);
  }
  notify();
}

listen(canvas, 'contextmenu', e => e.preventDefault());
listen(canvas, 'pointerdown', e => {
  if (diving) return;
  canvas.setPointerCapture(e.pointerId);
  touch.set(e.pointerId, [e.clientX, e.clientY]);
  dragging = true; dragMoved = 0; dragButton = e.button === 2 || e.shiftKey ? 2 : 0;
  lastX = e.clientX; lastY = e.clientY;
  canvas.classList.add('dragging');
  autoOrbit.reset();
});
listen(canvas, 'pointermove', e => {
  if (diving) return;
  if (touch.has(e.pointerId) && touch.size === 2) {
    // 2本指: ピンチでズーム
    const [a, b] = [...touch.values()];
    const before = Math.hypot(a[0] - b[0], a[1] - b[1]);
    touch.set(e.pointerId, [e.clientX, e.clientY]);
    const [c, d] = [...touch.values()];
    const after = Math.hypot(c[0] - d[0], c[1] - d[1]);
    if (before > 0 && after > 0) goal.dist = clampDist(goal.dist * before / after);
    dragMoved += 10;
    touchIdle();
    return;
  }
  if (dragging) {
    const dx = e.clientX - lastX, dy = e.clientY - lastY;
    lastX = e.clientX; lastY = e.clientY;
    dragMoved += Math.abs(dx) + Math.abs(dy);
    if (dragButton === 2) pan(dx, dy);
    else {
      orbitView(goal, dx, dy);
    }
    touchIdle();
    return;
  }
  updateHover(e.clientX, e.clientY);
});
const endDrag = e => {
  touch.delete(e.pointerId);
  if (!dragging) return;
  dragging = touch.size > 0;
  if (dragMoved >= 5) touchIdle();
  canvas.classList.remove('dragging');
  if (dragMoved < 5 && e.type === 'pointerup') handleClick(e.clientX, e.clientY);
};
listen(canvas, 'pointerup', endDrag);
listen(canvas, 'pointercancel', endDrag);
listen(canvas, 'pointerleave', () => { hovered = null; hoveredGalaxy = null; $('tooltip').hidden = true; });
listen(canvas, 'wheel', e => {
  if (!e.ctrlKey) return;
  // 宇宙上の Ctrl＋ホイールは、ブラウザ倍率ではなく視点の距離を変える。
  e.preventDefault();
  if (diving) return;
  goal.dist = clampDist(goal.dist * Math.exp(e.deltaY * 0.0012));
  touchIdle();
}, { passive: false });
listen(canvas, 'dblclick', e => {
  if (diving) return;
  handleDoubleClick(e.clientX, e.clientY);
});


const clampDist = d => Math.max(20, Math.min(overviewDistance() * 4, d));

function pan(dx, dy) {
  tracking = null;
  const delta = panOffset(cam.yaw, cam.pitch, dx, dy, cam.dist / F);
  goal.tx += delta.x; goal.ty += delta.y; goal.tz += delta.z;
}

function updateHover(mx, my) {
  if (!world) return;
  hovered = null;
  const inBox = b => mx >= b.x && mx <= b.x + b.w && my >= b.y && my <= b.y + b.h;
  hoveredGate = !!gateHit && (Math.hypot(mx - gateHit[0], my - gateHit[1]) < gateHit[2] * 1.2 || labelBoxes.some(b => b.gate && inBox(b)));
  hoveredGalaxy = hoveredGate ? null : labelBoxes.find(b => b.g && inBox(b))?.g ?? null;
  if (!hoveredGalaxy && !hoveredGate) {
    // 遠くの銀河は丸ごと1つの的にする。近づいた銀河と惑星は1つずつ選べる。
    let best = 196;
    for (let i = 0; i < bodies.length; i++) {
      const b = bodies[i], o = i * 4;
      if (!b.isPlanet) {
        const hit = galaxyHits.find(h => h[0] === b.galaxy);
        if (hit && hit[3] < 150) continue;
      }
      const d = (projected[o] - mx) ** 2 + (projected[o + 1] - my) ** 2;
      const reach = Math.max(144, (projected[o + 2] * 0.5) ** 2);
      if (d < best && d < reach) { best = d; hovered = b; }
    }
    if (!hovered) {
      let bestG = Infinity;
      for (const [g, x, y, r] of galaxyHits) {
        const d = Math.hypot(x - mx, y - my);
        if (d < Math.max(24, r * 0.75) && d < bestG) { bestG = d; hoveredGalaxy = g; }
      }
    }
  }
  canvas.classList.toggle('pointing', !!(hovered || hoveredGalaxy || hoveredGate));
  const tip = $('tooltip');
  const show = (title, sub) => {
    tip.innerHTML = '<div class="t-name"></div><div class="t-sub"></div>';
    tip.querySelector('.t-name').textContent = title;
    tip.querySelector('.t-sub').textContent = sub;
    tip.style.left = `${mx}px`; tip.style.top = `${my}px`;
    tip.hidden = false;
  };
  if (hoveredGate) show(world.gate.name, trail.length ? '現在のフォルダ ・ ダブルクリックで1つ上のフォルダへ' : '現在のフォルダ ・ ルート');
  else if (hovered) show(hovered.name, `${hovered.path} ・ ${formatSize(hovered.size)} ・ ${formatAge(hovered.mtime)} ・ クリックでズームとプレビュー`);
  else if (hoveredGalaxy) show(hoveredGalaxy.path, `ファイル ${hoveredGalaxy.files.length} ・ サブフォルダ ${hoveredGalaxy.sub} ・ ダブルクリックで開く`);
  else tip.hidden = true;
}

function handleClick(mx, my) {
  if (diving) return;
  updateHover(mx, my);
  if (hoveredGate) return;  // ダブルクリックが成立するまで階層を変えない。
  if (hovered) selectBody(hovered);
  else if (hoveredGalaxy) {
    // 初回クリックでカメラを動かさず、2回目も同じフォルダを押せるようにする。
    selected = null; selectionOrigin = null; focus = hoveredGalaxy; tracking = null;
    updateSide();
  } else selectBody(null);
}

function handleDoubleClick(mx, my) {
  if (diving) return;
  updateHover(mx, my);
  if (hoveredGate) { if (trail.length) ascend(trail.length - 1); return; }
  if (hoveredGalaxy) return dive(hoveredGalaxy);
  if (hovered) return approach(hovered);
  flyHome();
}

function flyTo(g) {
  selected = null; selectionOrigin = null;
  focus = g;
  tracking = null;
  goal.tx = g.x; goal.ty = g.y; goal.tz = g.z;
  goal.dist = Math.max(120, g.R * 2.8) * (F / Math.min(W, H));
  touchIdle();
  remember('dir', g.path);
  updateSide();
}
function flyHome() {
  selected = null; selectionOrigin = null;
  focus = null;
  tracking = null;
  goal.tx = goal.ty = goal.tz = 0;
  goal.dist = overviewDistance();
  Object.assign(goal, HOME_VIEW);
  autoOrbit.reset();
  touchIdle();
  updateSide();
}
/** 星・惑星の選択を共通化する（一覧・検索・フォーカス操作も同じ）。 */
function approach(body) {
  return selectBody(body);
}

// ---------------------------------------------------------------- フォルダ移動のワープ
let warpSequence = 0;
let sceneAnimation = null;
function setWarpBusy(value) {
  diving = value;
  canvas.classList.toggle('warping', value);
  canvas.setAttribute('aria-busy', String(value));
}

/** 古い移動はキャンセルし、最後に選ばれた階層だけへ切り替える。 */
async function travelTo(next, { direction = 'in', target = null, history = true, after = null, preserveSelection = false } = {}) {
  if (!nodeAt(next)) return;
  if (!preserveSelection) selectionOrigin = null;
  const sequence = ++warpSequence;
  sceneAnimation?.cancel();
  setWarpBusy(true);
  autoOrbit.reset();
  tracking = null;
  dragging = false; touch.clear(); canvas.classList.remove('dragging');
  $('tooltip').hidden = true;
  Object.assign(goal, cam);  // カメラは止め、画面全体の拡縮とフェードを滑らかに重ねる。
  let originX = CX, originY = CY;
  if (target && project(target.x, target.y, target.z)) {
    originX = Math.max(0, Math.min(W, P.x)); originY = Math.max(0, Math.min(H, P.y));
  }
  canvas.style.transformOrigin = `${originX}px ${originY}px`;
  const motion = warpMotion(direction);
  const play = async stage => {
    sceneAnimation = canvas.animate(stage.frames, {
      duration: stage.duration, easing: 'cubic-bezier(.4,0,.2,1)', fill: 'forwards',
    });
    try { await sceneAnimation.finished; } catch { return false; }
    return sequence === warpSequence;
  };
  try {
    if (!await play(motion.exit)) return;
    trail = [...next];
    enterWorld({ history, immediate: true });
    after?.();
    // 次の全景を初めから表示し、従来の出現待ち・急なズームを重ねない。
    canvas.style.transformOrigin = `${CX}px ${CY}px`;
    sceneAnimation.cancel();
    if (!await play(motion.entry)) return;
  } finally {
    if (sequence === warpSequence) {
      sceneAnimation?.cancel(); sceneAnimation = null;
      canvas.style.removeProperty('transform-origin');
      setWarpBusy(false);
    }
  }
}

/** 入る時は拡大しながら消え、次の階層がぼんやり現れる。 */
function dive(g) {
  if (diving) return;
  remember('dir', g.path);
  return travelTo(g.path.split('/'), { direction: 'in', target: g });
}
/** 戻る時は今の宇宙が遠ざかりながら消える。 */
function ascend(count) {
  if (count >= trail.length || count < 0) return;
  return travelTo(trail.slice(0, count), { direction: 'out' });
}

// URL の #/フォルダ/… に今の階層を反映する。ブラウザの戻る・進むで階層を行き来できる。
const trailHash = () => `#/${trail.map(encodeURIComponent).join('/')}`;
function trailFromHash() {
  const parts = location.hash.replace(/^#\/?/, '').split('/').filter(Boolean);
  try { return parts.map(decodeURIComponent); } catch { return []; }
}
listen(window, 'popstate', () => {
  if (!scan) return;
  const next = trailFromHash();
  if ((!diving && next.join('/') === basePath()) || !nodeAt(next)) return;
  travelTo(next, { direction: next.length < trail.length ? 'out' : 'in', history: false });
});

function enterWorld({ from, leaving, history = true, immediate = false } = {}) {
  if (history && location.hash !== trailHash()) {
    if (location.hash || trail.length) window.history.pushState(null, '', trailHash());
  }
  world = buildWorld();
  focus = null; selected = null; hovered = null; hoveredGalaxy = null; hoveredGate = false; tracking = null;
  introAt = performance.now();
  const home = overviewDistance();
  goal.tx = goal.ty = goal.tz = 0; goal.dist = home;
  Object.assign(goal, HOME_VIEW);
  autoOrbit.reset();
  if (immediate) {
    Object.assign(cam, goal);
    prevDist = cam.dist;
    introAt = performance.now() - 5000;
  } else if (from === 'outside' || from === 'warp') {
    // 外から突入・ワープ: 遠くから光の筋をくぐって全景へ
    cam.tx = cam.ty = cam.tz = 0;
    cam.dist = home * 8;
    introAt = performance.now() - (from === 'warp' ? 1500 : 300);
  } else if (from === 'inside') {
    // 内から脱出: 出てきた銀河の中心から引いていく
    const g = world.galaxies.find(x => x.path === leaving);
    if (g) { cam.tx = g.x; cam.ty = g.y; cam.tz = g.z; cam.dist = Math.max(20, g.R * 0.2); }
    introAt = performance.now() - 5000;
  }
  renderAll();
  updateSide();
}

/** 全体検索・航海日誌から、そのファイル（自由惑星として）やフォルダ（銀河として）がある宇宙へワープする。 */
function goTo(entry) {
  const parts = entry.path.split('/');
  if (entry.type === 'dir') {
    if (!nodeAt(parts)) return;
    if (!diving && entry.path === basePath()) { revealCurrent(); return; }
    const target = world.galaxies.find(g => g.path === entry.path) ?? null;
    const upward = parts.length < trail.length && parts.every((name, i) => name === trail[i]);
    remember('dir', entry.path);
    return travelTo(parts, { direction: upward ? 'out' : 'in', target });
  }
  const level = parts.slice(0, -1);
  const node = nodeAt(level);
  if (!node || !node.f.some(file => file[0] === parts.at(-1))) return;
  rememberSelectionView();
  const select = () => {
    const body = world.byPath.get(entry.path);
    if (body) selectBody(body);
  };
  if (diving || level.join('/') !== basePath()) {
    return travelTo(level, {
      direction: level.length < trail.length ? 'out' : 'in',
      after: select, preserveSelection: true,
    });
  }
  select();
}

// ---------------------------------------------------------------- 航路と航海日誌（ブラウザに保存）
const storeKey = () => `aidiy_ide:${scan.root}`;
function saveVoyage() {
  try { localStorage.setItem(storeKey(), JSON.stringify({ voyages, journal })); } catch { /* 保存できない環境 */ }
}
function loadVoyage() {
  try {
    const saved = JSON.parse(localStorage.getItem(storeKey()) || '{}');
    voyages = saved.voyages && typeof saved.voyages === 'object' ? saved.voyages : {};
    journal = Array.isArray(saved.journal) ? saved.journal : [];
  } catch { voyages = {}; journal = []; }
}
function remember(type, path) {
  const route = voyages[basePath()] ??= [];
  const key = `${type === 'dir' ? 'g' : 'f'}:${path}`;
  if (route.at(-1) !== key) route.push(key);
  if (route.length > 40) route.splice(0, route.length - 40);
  journal = [{ type, path, at: Date.now() }, ...journal.filter(j => !(j.type === type && j.path === path))].slice(0, 80);
  saveVoyage();
}
function clearVoyage() {
  delete voyages[basePath()];
  saveVoyage();
}

const tail = (text, max = 44) => (text.length > max ? `…${text.slice(-(max - 1))}` : text);
const parentOf = path => path.split('/').slice(0, -1).join('/');

function rememberSelectionView() {
  if (selectionOrigin) return;
  selectionOrigin = {
    trail: [...trail], camera: { ...goal }, focusPath: focus?.path ?? null,
  };
}

function selectBody(body, { record = true, zoom = true } = {}) {
  if (!body) {
    const origin = selectionOrigin;
    selectionOrigin = null; selected = null; tracking = null;
    updateSide();
    if (!origin) return;
    const restore = () => {
      focus = world.galaxies.find(g => g.path === origin.focusPath) ?? null;
      Object.assign(goal, origin.camera);
      updateSide();
    };
    if (diving || origin.trail.join('/') !== basePath()) {
      if (nodeAt(origin.trail)) return travelTo(origin.trail, {
        direction: origin.trail.length < trail.length ? 'out' : 'in', after: restore,
      });
      flyHome(); // 再読み込みで元の階層が消えた場合は、現在の全景へ戻る。
    } else restore();
    return;
  }
  if (zoom) rememberSelectionView();
  const sameFile = selected?.path === body.path;
  const followed = tracking?.path === body.path;
  selected = body;
  if (zoom) {
    focus = body.galaxy ?? null;
    tracking = body;
    goal.tx = body.x; goal.ty = body.y; goal.tz = body.z;
    goal.dist = (body.isPlanet ? Math.max(180, body.R * 22) : 170) * (F / Math.min(W, H));
    autoOrbit.reset();
  } else if (followed) tracking = body; // 再走査後も新しいオブジェクトを追う。
  if (record && !sameFile) remember('file', body.path);
  updateSide();
}

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
}
function formatAge(ms) {
  const sec = (Date.now() - ms) / 1000;
  if (sec < 60) return 'たった今';
  if (sec < 3600) return `${Math.floor(sec / 60)}分前`;
  if (sec < 86400) return `${Math.floor(sec / 3600)}時間前`;
  if (sec < 86400 * 60) return `${Math.floor(sec / 86400)}日前`;
  return new Date(ms).toLocaleDateString('ja-JP');
}


function notify() {
  if (disposed) return;
  change({ scan, trail: [...trail], selected, focus, autoSpin, loading: !scan });
}
function updateSide() { notify(); }
function renderAll() { notify(); }
function revealCurrent() {}
async function refresh(startedAt) {
  const run = ++loadGeneration;
  if (Number.isFinite(startedAt)) since = startedAt;
  try {
    const response = await fetch('/api/galaxy', { cache: 'no-store', signal: listeners.signal });
    if (!response.ok) throw Error(await response.text());
    const data = await response.json();
    if (disposed || run !== loadGeneration) return;
    const first = !scan; scan = data;
    while (trail.length && !nodeAt(trail)) trail.pop();
    if (first) {
      loadVoyage(); const start = trailFromHash(); if (nodeAt(start)) trail = start;
      enterWorld({ from: 'outside', history: false }); cam.dist = overviewDistance() * 10;
    } else {
      const path = selected?.path; world = buildWorld();
      selectBody([...world.stars, ...world.planets].find(item => item.path === path) || null, { record: false, zoom: false });
    }
    knownPaths = new Set(collectFiles(scan.tree, '').map(file => file.path)); notify();
  } catch (error) { if (!disposed) change({ error: error.message, loading: false }); }
}
listen(window, 'keydown', event => {
  if (disposed || diving) return;
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'b') { event.preventDefault(); toggleExplorer(); return; }
  if (event.target instanceof Element && event.target.closest('input, textarea, select, button, [contenteditable="true"], .ai-component')) return;
  if (event.key === 'Escape') { if (selected) selectBody(null); else if (focus) flyHome(); else if (trail.length) ascend(trail.length - 1); }
  else if (event.key === 'Backspace' && trail.length) ascend(trail.length - 1);
  else if (event.key === ' ') { event.preventDefault(); setAutoSpin(!autoSpin); }
  else if (event.key.toLowerCase() === 'r') void refresh();
  else if (event.key.toLowerCase() === 'c') clearVoyage();
});
requestAnimationFrame(frame);
return {
  refresh, goTo, ascend, flyHome, dive, approach, setAutoSpin, clear: () => selectBody(null),
  get world() { return world; }, get trail() { return trail; }, get labels() { return labelBoxes; }, cam, goal,
  color: name => KINDS[kindOf(name)].color,
  marks(value) { markMode = value.mode; since = value.since; grepMatches = new Set(value.paths || []); recountFresh(); },
  dispose() { disposed = true; ++loadGeneration; ++warpSequence; listeners.abort(); window.cancelAnimationFrame(frameId); sceneAnimation?.cancel(); },
};
}
