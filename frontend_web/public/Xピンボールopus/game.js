/*
  COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
  Licensed under "AiDiy 公開利用ライセンス v1.1".
*/

/*
  Xピンボールopus — 3D 大渓谷ステージ層。

  盤の物理は 2D の盤座標 (W=720 / H=1080) で扱う方針なので、この層は
  「盤座標 → ワールド座標」の写像と three.js の描画だけを担当する。

    盤 x: 0(左の岩壁) → 720(右の岩壁)
    盤 y: 0(奥 = 遺跡の高台) → 1080(手前 = 谷底へ落ちる縁)

  奥へ向かって標高が上がり、手前は谷底へ急落する岩の斜面になっている。
  three.js はこの公開ディレクトリに固定版を同梱して module import する。
  CDN やネットワーク接続に依存せず、配布物だけで初期化できる。
*/

import * as THREE from './vendor/three.module.js';

/* ============================================================
   盤座標系とワールドへの写像
   ============================================================ */

const BOARD_W = 720;
const BOARD_H = 1080;
const SCALE = 0.052;   // 盤 1px あたりのワールド長
const RISE = 21.5;     // 奥の高台までの標高差
const FALL = 34;       // 手前の谷底への落差

// 斜面の基準標高。手前(y=1080)を 0 とし、奥ほど高く、縁を越えると急落する。
const slopeHeight = (by) => {
  const t = Math.max(0, 1 - by / BOARD_H);
  const rise = Math.pow(t, 1.22) * RISE;
  if (by <= 1040) return rise;
  return rise - Math.pow((by - 1040) / 140, 1.55) * FALL;
};

// 岩肌の起伏。乱数ではなく三角関数の重ね合わせにして、毎回同じ地形にする。
const ridge = (bx, by) => (
  Math.sin(bx * 0.0210 + by * 0.0130) * 1.00
  + Math.sin(bx * 0.0470 - by * 0.0310) * 0.52
  + Math.sin(bx * 0.0085 + by * 0.0550) * 0.74
  + Math.sin(bx * 0.0930 + by * 0.0710) * 0.22
);

// 盤の外へ出るほど岩を荒らす。盤内は球の転がりを邪魔しない程度に抑える。
const ridgeGain = (bx, by) => {
  const outX = Math.max(0, -20 - bx, bx - (BOARD_W + 20)) / 240;
  const outY = Math.max(0, -40 - by, by - (BOARD_H + 40)) / 300;
  return 0.34 + Math.min(1, outX + outY) * 0.62;
};

// 盤の外へ出た距離(盤座標)。左右どちらも 0 → WALL_RUN で壁の頂へ達する。
const WALL_MARGIN = 60;
const WALL_RUN = 380;
const wallOut = (bx) => Math.max(0, -WALL_MARGIN - bx, bx - (BOARD_W + WALL_MARGIN));

// 左右の谷壁。垂直に立てると俯瞰カメラからは薄板にしか見えないので、
// 急斜面としてせり上がらせ、面がカメラを向くようにする。
const canyonWall = (bx, by) => {
  const t = Math.min(1, wallOut(bx) / WALL_RUN);
  const s = t * t * (3 - 2 * t);   // smoothstep。盤際は水平のまま立ち上がらせる
  return s * (30 + Math.sin(by * 0.0037 + bx * 0.0021) * 6.5 + Math.sin(by * 0.0092) * 3.5);
};

// 盤の右側に張り出す岩球投入峰。地形そのものを盛り上げるため、見た目だけでなく
// 勾配物理にも効く。球は峰の左肩へ置き、盤を横切る左向きに解放する。
const launchMountain = (bx, by) => {
  const dx = (bx - 704) / 96;
  const dy = (by - 350) / 128;
  return Math.exp(-(dx * dx + dy * dy)) * 7.2;
};

const terrainHeight = (bx, by) => slopeHeight(by) + ridge(bx, by) * ridgeGain(bx, by)
  + canyonWall(bx, by) + launchMountain(bx, by);

// 盤座標をワールド座標へ写す。lift は地表からの浮かせ量。
const boardToWorld = (bx, by, lift = 0, target = new THREE.Vector3()) => target.set(
  (bx - BOARD_W / 2) * SCALE,
  terrainHeight(bx, by) + lift,
  (by - BOARD_H / 2) * SCALE,
);

/* ============================================================
   共通ユーティリティ
   ============================================================ */

const stage = document.getElementById('stage');
const canvas = document.getElementById('game');
const loadError = document.getElementById('load-error');

const disposables = [];   // BufferGeometry / Material
const textureBin = [];    // Texture

const keep = (item) => { disposables.push(item); return item; };
const keepTexture = (texture) => { textureBin.push(texture); return texture; };

// 見た目を毎回同じにするための決定的な擬似乱数。
let seed = 20260727;
const rand = () => {
  seed = (seed * 1664525 + 1013904223) >>> 0;
  return seed / 4294967296;
};
const range = (min, max) => min + (max - min) * rand();

const paint = (width, height, draw, repeatX = 1, repeatY = 1) => {
  const c = document.createElement('canvas');
  c.width = width;
  c.height = height;
  draw(c.getContext('2d'), width, height);
  const texture = new THREE.CanvasTexture(c);
  texture.colorSpace = THREE.SRGBColorSpace;
  if (repeatX !== 1 || repeatY !== 1) {
    texture.wrapS = THREE.RepeatWrapping;
    texture.wrapT = THREE.RepeatWrapping;
    texture.repeat.set(repeatX, repeatY);
  }
  texture.anisotropy = 4;
  return keepTexture(texture);
};

const reducedMotion = window.matchMedia
  ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
  : false;

/* ============================================================
   テクスチャ
   ============================================================ */

const createRockTexture = () => paint(512, 512, (ctx, w, h) => {
  ctx.fillStyle = '#c0ae90';
  ctx.fillRect(0, 0, w, h);
  // 砂粒
  for (let i = 0; i < 5200; i += 1) {
    const v = Math.floor(range(-34, 34));
    ctx.fillStyle = `rgba(${176 + v}, ${158 + v}, ${128 + v}, .5)`;
    ctx.fillRect(rand() * w, rand() * h, range(1, 3), range(1, 3));
  }
  // 水平の地層
  for (let i = 0; i < 15; i += 1) {
    const y = rand() * h;
    ctx.strokeStyle = `rgba(${Math.floor(range(96, 138))}, ${Math.floor(range(82, 118))}, ${Math.floor(range(60, 92))}, .2)`;
    ctx.lineWidth = range(1, 6);
    ctx.beginPath();
    ctx.moveTo(0, y);
    for (let x = 0; x <= w; x += 32) ctx.lineTo(x, y + Math.sin(x * 0.021 + i) * 5);
    ctx.stroke();
  }
  // ひび割れ
  for (let i = 0; i < 26; i += 1) {
    ctx.strokeStyle = 'rgba(78, 62, 42, .22)';
    ctx.lineWidth = range(0.6, 1.8);
    let x = rand() * w;
    let y = rand() * h;
    ctx.beginPath();
    ctx.moveTo(x, y);
    for (let s = 0; s < 7; s += 1) {
      x += range(-40, 40);
      y += range(-40, 40);
      ctx.lineTo(x, y);
    }
    ctx.stroke();
  }
}, 16, 22);

const createCliffTexture = () => paint(512, 512, (ctx, w, h) => {
  ctx.fillStyle = '#9b8567';
  ctx.fillRect(0, 0, w, h);
  // 地層は薄く敷く。濃くすると縞が目立ち、岩ではなく木目板に見える。
  for (let i = 0; i < 46; i += 1) {
    const y = (i / 46) * h + range(-5, 5);
    const shade = Math.floor(range(96, 176));
    ctx.fillStyle = `rgba(${shade + 32}, ${shade + 12}, ${Math.floor(shade * 0.78)}, .18)`;
    ctx.fillRect(0, y, w, range(4, 15));
  }
  for (let i = 0; i < 3800; i += 1) {
    const v = Math.floor(range(-30, 30));
    ctx.fillStyle = `rgba(${168 + v}, ${144 + v}, ${110 + v}, .42)`;
    ctx.fillRect(rand() * w, rand() * h, range(1, 4), range(1, 2));
  }
  for (let i = 0; i < 22; i += 1) {
    ctx.strokeStyle = 'rgba(58, 45, 30, .2)';
    ctx.lineWidth = range(1, 2.6);
    const x = rand() * w;
    ctx.beginPath();
    ctx.moveTo(x, 0);
    for (let y = 0; y <= h; y += 40) ctx.lineTo(x + Math.sin(y * 0.03 + i) * 13, y);
    ctx.stroke();
  }
// 壁は横に長いので、繰り返しを詰めないと地層が引き伸ばされて木目に見える。
}, 34, 5);

const createSkyTexture = () => paint(1024, 512, (ctx, w, h) => {
  const sky = ctx.createLinearGradient(0, 0, 0, h);
  sky.addColorStop(0.00, '#1b3357');   // 天頂
  sky.addColorStop(0.26, '#3f6a8c');
  sky.addColorStop(0.46, '#8fa9ab');
  sky.addColorStop(0.56, '#e0b57e');
  sky.addColorStop(0.62, '#c98f52');   // 地平の霞
  sky.addColorStop(0.78, '#5c4630');
  sky.addColorStop(1.00, '#221a11');
  ctx.fillStyle = sky;
  ctx.fillRect(0, 0, w, h);

  // 太陽側のハレーション
  const glow = ctx.createRadialGradient(w * 0.63, h * 0.50, 6, w * 0.63, h * 0.50, h * 0.52);
  glow.addColorStop(0, 'rgba(255, 244, 214, .95)');
  glow.addColorStop(0.22, 'rgba(255, 205, 132, .48)');
  glow.addColorStop(1, 'rgba(255, 180, 96, 0)');
  ctx.fillStyle = glow;
  ctx.fillRect(0, 0, w, h);

  // 薄雲
  for (let i = 0; i < 90; i += 1) {
    const cy = range(h * 0.10, h * 0.52);
    const cx = rand() * w;
    const rx = range(40, 190);
    const ry = range(4, 17);
    const cloud = ctx.createRadialGradient(cx, cy, 0, cx, cy, rx);
    const a = range(0.05, 0.22);
    cloud.addColorStop(0, `rgba(255, 238, 214, ${a})`);
    cloud.addColorStop(1, 'rgba(255, 238, 214, 0)');
    ctx.save();
    ctx.translate(cx, cy);
    ctx.scale(1, ry / rx);
    ctx.translate(-cx, -cy);
    ctx.fillStyle = cloud;
    ctx.beginPath();
    ctx.arc(cx, cy, rx, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }
});

const createSoftDotTexture = () => paint(64, 64, (ctx, w, h) => {
  const g = ctx.createRadialGradient(w / 2, h / 2, 0, w / 2, h / 2, w / 2);
  g.addColorStop(0, 'rgba(255, 255, 255, 1)');
  g.addColorStop(0.45, 'rgba(255, 255, 255, .38)');
  g.addColorStop(1, 'rgba(255, 255, 255, 0)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, w, h);
});

// 鉄砲水の水面。縦(v)方向へ送って流れを出すので、上下は必ずつながる模様にする。
const createTorrentTexture = () => paint(256, 512, (ctx, w, h) => {
  ctx.fillStyle = '#2f7f96';
  ctx.fillRect(0, 0, w, h);
  // 濁った土砂の縞。縦に長く伸ばして流れの向きを見せる。
  for (let i = 0; i < 120; i += 1) {
    const x = rand() * w;
    const y = rand() * h;
    const len = range(40, 210);
    ctx.strokeStyle = `rgba(${Math.floor(range(150, 226))}, ${Math.floor(range(198, 246))}, 255, ${range(0.06, 0.26).toFixed(3)})`;
    ctx.lineWidth = range(1, 7);
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineTo(x + range(-10, 10), y + len);
    ctx.stroke();
  }
  // 白波。上下端をまたぐぶんを写して継ぎ目を消す。
  for (let i = 0; i < 46; i += 1) {
    const cx = rand() * w;
    const cy = rand() * h;
    const rx = range(10, 42);
    const ry = range(3, 11);
    [0, -h, h].forEach((shift) => {
      ctx.fillStyle = `rgba(240, 252, 255, ${range(0.10, 0.30).toFixed(3)})`;
      ctx.beginPath();
      ctx.ellipse(cx, cy + shift, rx, ry, 0, 0, Math.PI * 2);
      ctx.fill();
    });
  }
}, 3, 5);

/* ============================================================
   シーン構築
   ============================================================ */

const FOG_COLOR = 0xbba07c;

let renderer = null;
let scene = null;
let camera = null;
let skyDome = null;
let sunSprite = null;
let mistPoints = null;
let idolStatue = null;      // 門の奥の黄金像。IDOL 完成で起立させる
let idolStatueBaseY = 0;    // 起立前の局所 y。演出はここからの相対で動かす
let idolStatueLight = null;
const boulderPool = [];   // 岩球メッシュ。マルチボールを見込んで 3 個まで持つ
let ready = false;

const buildRenderer = () => {
  renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    alpha: false,
    powerPreference: 'high-performance',
  });
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  // style.css の .vignette / .dust が上に重なるぶん、明るめに焼く。
  renderer.toneMappingExposure = 1.52;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.8));
};

const buildScene = () => {
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x9bb0b8);
  // 遠景の稜線だけが霞むよう、盤面には掛からない距離からフォグを効かせる。
  scene.fog = new THREE.Fog(FOG_COLOR, 78, 340);

  // アクション視点では岩球がレンズ直前まで来る。near を小さくし、巨大な球の
  // 手前側が通常のカメラより早く欠けてしまわないようにする。
  camera = new THREE.PerspectiveCamera(50, 1, 0.1, 1400);
};

const buildLights = () => {
  // 昼下がりの渓谷。空の青と岩の照り返しを環境光に、太陽を主光源にする。
  scene.add(new THREE.HemisphereLight(0xdcecf7, 0x8a6f46, 1.45));

  const focus = new THREE.Object3D();
  boardToWorld(BOARD_W / 2, BOARD_H / 2, 0, focus.position);
  scene.add(focus);

  const sun = new THREE.DirectionalLight(0xfff0cf, 3.15);
  sun.position.set(-42, 62, -34);
  sun.target = focus;
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  sun.shadow.camera.left = -34;
  sun.shadow.camera.right = 34;
  sun.shadow.camera.top = 40;
  sun.shadow.camera.bottom = -40;
  sun.shadow.camera.near = 12;
  sun.shadow.camera.far = 190;
  sun.shadow.normalBias = 0.035;
  scene.add(sun);

  // 谷底からの冷たい反射光。斜面の陰が潰れないようにする。
  const fill = new THREE.DirectionalLight(0xa8cee6, 0.95);
  fill.position.set(30, 12, 46);
  fill.target = focus;
  scene.add(fill);

  // 奥の高台を縁取る逆光。
  const rim = new THREE.DirectionalLight(0xffd9a0, 0.95);
  rim.position.set(16, 24, -58);
  rim.target = focus;
  scene.add(rim);

  return { sun, fill, rim };
};

const buildSky = () => {
  const geo = keep(new THREE.SphereGeometry(560, 40, 24));
  const mat = keep(new THREE.MeshBasicMaterial({
    map: createSkyTexture(),
    side: THREE.BackSide,
    fog: false,
    depthWrite: false,
  }));
  skyDome = new THREE.Mesh(geo, mat);
  skyDome.renderOrder = -10;
  scene.add(skyDome);

  const sunMat = keep(new THREE.SpriteMaterial({
    map: createSoftDotTexture(),
    color: 0xfff2cd,
    transparent: true,
    depthWrite: false,
    fog: false,
    blending: THREE.AdditiveBlending,
  }));
  sunSprite = new THREE.Sprite(sunMat);
  sunSprite.position.set(-42, 62, -34).normalize().multiplyScalar(420);
  sunSprite.scale.set(190, 190, 1);
  sunSprite.renderOrder = -9;
  scene.add(sunSprite);
};

// 遠景の山並み。低ポリの円錐を二列に並べ、フォグで奥ほど霞ませる。
const buildDistantRidges = () => {
  const mat = keep(new THREE.MeshStandardMaterial({
    color: 0x9a8f76,
    roughness: 1,
    metalness: 0,
    flatShading: true,
  }));
  const group = new THREE.Group();
  const rows = [
    { z: -118, count: 13, height: [30, 52], radius: [26, 46], spread: 230, base: 6 },
    { z: -186, count: 11, height: [46, 82], radius: [34, 62], spread: 300, base: -2 },
    { z: -268, count: 9, height: [64, 116], radius: [46, 84], spread: 380, base: -12 },
  ];
  rows.forEach((row) => {
    for (let i = 0; i < row.count; i += 1) {
      const geo = keep(new THREE.ConeGeometry(range(row.radius[0], row.radius[1]), range(row.height[0], row.height[1]), Math.round(range(5, 8)), 1, false));
      const cone = new THREE.Mesh(geo, mat);
      const x = (i / Math.max(1, row.count - 1) - 0.5) * row.spread + range(-16, 16);
      cone.position.set(x, row.base + range(-6, 8), row.z + range(-22, 22));
      cone.rotation.y = rand() * Math.PI;
      cone.scale.set(1, range(0.8, 1.25), range(0.85, 1.2));
      group.add(cone);
    }
  });
  scene.add(group);
  return group;
};

const COL_PLATEAU = new THREE.Color(0xd9b072);
const COL_SLOPE = new THREE.Color(0xb2915c);
const COL_MOSS = new THREE.Color(0x8a8657);   // 谷側の乾いた草地。彩度を上げると芝生に見える
const COL_ABYSS = new THREE.Color(0x3d3728);
const COL_WALL = new THREE.Color(0xa78d64);   // 谷壁の岩肌

const buildTerrain = () => {
  // 画角の外まで地面を広げ、どの縦横比でも地形の端が空に浮かないようにする。
  const COLS = 132;
  const ROWS = 136;
  const BX0 = -900;
  const BX1 = 1620;
  const BY0 = -560;
  const BY1 = 1320;

  const geo = keep(new THREE.PlaneGeometry(1, 1, COLS, ROWS));
  const pos = geo.attributes.position;
  const colors = new Float32Array(pos.count * 3);
  const v = new THREE.Vector3();
  const c = new THREE.Color();

  for (let i = 0; i < pos.count; i += 1) {
    const u = pos.getX(i) + 0.5;   // 0(左) → 1(右)
    const w = 0.5 - pos.getY(i);   // 0(奥) → 1(手前)
    const bx = BX0 + (BX1 - BX0) * u;
    const by = BY0 + (BY1 - BY0) * w;
    boardToWorld(bx, by, 0, v);
    pos.setXYZ(i, v.x, v.y, v.z);

    const t = by / BOARD_H;
    if (t < 0.45) c.copy(COL_PLATEAU).lerp(COL_SLOPE, THREE.MathUtils.clamp((t + 0.35) / 0.8, 0, 1));
    else if (t < 0.92) c.copy(COL_SLOPE).lerp(COL_MOSS, Math.pow((t - 0.45) / 0.47, 1.5));
    else c.copy(COL_MOSS).lerp(COL_ABYSS, THREE.MathUtils.clamp((t - 0.92) / 0.18, 0, 1));
    // 谷壁へ移るほど岩肌へ寄せる。斜面まで草地色だと盤の続きに見えてしまう。
    c.lerp(COL_WALL, Math.min(1, wallOut(bx) / WALL_RUN) * 0.88);
    const shade = 1 + Math.sin(bx * 0.017 + by * 0.023) * 0.07 + Math.sin(bx * 0.058) * 0.04;
    colors[i * 3] = c.r * shade;
    colors[i * 3 + 1] = c.g * shade;
    colors[i * 3 + 2] = c.b * shade;
  }
  pos.needsUpdate = true;
  geo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
  geo.computeVertexNormals();

  const mat = keep(new THREE.MeshStandardMaterial({
    map: createRockTexture(),
    vertexColors: true,
    roughness: 0.96,
    metalness: 0.02,
  }));
  const mesh = new THREE.Mesh(geo, mat);
  mesh.receiveShadow = true;
  scene.add(mesh);
  return mesh;
};

// 谷壁の頂に載せる岩の稜。斜面(canyonWall)の上端から一段だけ切り立たせ、
// 空との境界に岩のシルエットを作る。盤面には覆いかぶさらない位置に置く。
const buildCliff = (side) => {
  const COLS = 96;
  const ROWS = 14;
  const BY0 = -560;
  const BY1 = 1240;
  const edge = side < 0 ? -(WALL_MARGIN + WALL_RUN) : BOARD_W + WALL_MARGIN + WALL_RUN;

  const geo = keep(new THREE.PlaneGeometry(1, 1, COLS, ROWS));
  const pos = geo.attributes.position;
  const colors = new Float32Array(pos.count * 3);
  // 谷壁の地表と同系にする。明るくすると稜線の岩だけが浮いて見える。
  const base = new THREE.Color(0x74624a);
  const top = new THREE.Color(0xa38b68);
  const c = new THREE.Color();

  for (let i = 0; i < pos.count; i += 1) {
    const u = pos.getX(i) + 0.5;   // 0(奥) → 1(手前)
    const w = 0.5 - pos.getY(i);   // 0(頂) → 1(基部) なので反転して使う
    const h = 1 - w;               // 0(基部) → 1(頂)
    const by = BY0 + (BY1 - BY0) * u;

    // うねりは低周波だけで作る。高周波を混ぜると頂が細かく割れ、
    // 岩壁ではなく薄い羽根が並んだように見えてしまう。
    const jag = Math.sin(by * 0.0068 + side * 1.7) * 12
      + Math.sin(by * 0.0151 + side * 0.6) * 6.5
      + Math.sin(by * 0.0272 + side * 2.4) * 2.8;
    // 基部は斜面へ食い込ませ、上へ向かってだけ外へ張り出させる。
    const bx = edge + side * (h * h * 30 + jag * (0.42 + h * 0.72));
    // 高さを by 方向に強く変えて、一枚壁ではなく岩塔が連なる稜線に見せる。
    const tooth = 0.60 + Math.sin(by * 0.0125 + side * 1.3) * 0.26
      + Math.sin(by * 0.0310 + side * 2.6) * 0.17
      + Math.sin(by * 0.0064) * 0.11;
    const wallH = THREE.MathUtils.clamp(17 + (1 - by / BOARD_H) * 10, 12, 32) * Math.max(0.12, tooth);
    // 稜線だけを緩く欠けさせ、のっぺりした一枚板に見えないようにする。
    const crown = Math.pow(h, 3) * (Math.sin(by * 0.0198 + side * 2.1) * 3.4 + Math.sin(by * 0.0091) * 2.6);

    pos.setXYZ(
      i,
      (bx - BOARD_W / 2) * SCALE,
      terrainHeight(edge - side * 30, by) - 6 + h * wallH + crown + Math.sin(by * 0.0125 + h * 4.5) * 0.8,
      (by - BOARD_H / 2) * SCALE,
    );

    c.copy(base).lerp(top, h * h);
    const shade = 1 + Math.sin(by * 0.014 + h * 5.1) * 0.09;
    colors[i * 3] = c.r * shade;
    colors[i * 3 + 1] = c.g * shade;
    colors[i * 3 + 2] = c.b * shade;
  }
  pos.needsUpdate = true;
  geo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
  geo.computeVertexNormals();

  const mat = keep(new THREE.MeshStandardMaterial({
    map: createCliffTexture(),
    vertexColors: true,
    side: THREE.DoubleSide,
    roughness: 0.98,
    metalness: 0.02,
  }));
  const mesh = new THREE.Mesh(geo, mat);
  mesh.receiveShadow = true;
  mesh.castShadow = true;
  scene.add(mesh);
  return mesh;
};

// 足元の地表の最低点。基壇の下端をここより下げ、傾いた斜面から浮かないようにする。
const lowestGround = (bx, by, halfW, halfD) => {
  let low = Infinity;
  for (let i = -2; i <= 2; i += 1) {
    for (let j = -2; j <= 2; j += 1) {
      low = Math.min(low, terrainHeight(bx + (halfW * i) / 2, by + (halfD * j) / 2));
    }
  }
  return low;
};

const RUIN_BY = -215;   // 遺跡群の基準となる盤 y

// 奥の遺跡風の高台。石柱の門と段状の基壇だけを置く（ギミックは後続ステップ）。
// 斜面に建つので group をひとつの基準点へ据え、部材はすべて局所座標で組む。
// そうしないと部材ごとに違う地表高を拾い、門と基壇がずれる。
const buildRuins = () => {
  const group = new THREE.Group();
  boardToWorld(BOARD_W / 2, RUIN_BY, 0, group.position);
  const baseY = group.position.y;

  const stone = keep(new THREE.MeshStandardMaterial({ color: 0xa89272, roughness: 0.92, metalness: 0.04, flatShading: true }));
  const darkStone = keep(new THREE.MeshStandardMaterial({ color: 0x7d6a4e, roughness: 0.95, metalness: 0.04, flatShading: true }));
  const gold = keep(new THREE.MeshStandardMaterial({ color: 0xc79331, roughness: 0.34, metalness: 0.85, emissive: 0x3a2405, emissiveIntensity: 0.5 }));

  const put = (mesh, bx, by, y) => {
    mesh.position.set((bx - BOARD_W / 2) * SCALE, y, (by - RUIN_BY) * SCALE);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    group.add(mesh);
    return mesh;
  };

  // 段状の基壇。天面の高さだけ決め、厚みは足元の最低地表から逆算して潜らせる。
  // 天面を上げすぎると門が画角から外れるので、最上段は 4.2 に抑える。
  let deck = 0;
  [[600, 230, 2.0], [470, 175, 3.2], [350, 130, 4.2]].forEach(([w, d, top], i) => {
    const low = lowestGround(BOARD_W / 2, RUIN_BY, w / 2, d / 2) - baseY;
    const thick = top - low + 2.5;
    const geo = keep(new THREE.BoxGeometry(w * SCALE, thick, d * SCALE));
    put(new THREE.Mesh(geo, i % 2 ? darkStone : stone), BOARD_W / 2, RUIN_BY, top - thick / 2);
    deck = top;
  });

  // 門の石柱。最上段の天面から立ち上げる。
  const PILLAR_H = 14;
  const GATE_BY = RUIN_BY + 30;
  [232, 488].forEach((bx) => {
    const pillar = keep(new THREE.CylinderGeometry(1.9, 2.5, PILLAR_H, 9, 1));
    put(new THREE.Mesh(pillar, stone), bx, GATE_BY, deck + PILLAR_H / 2 - 0.4);
    const capital = keep(new THREE.BoxGeometry(6, 1.5, 6));
    put(new THREE.Mesh(capital, darkStone), bx, GATE_BY, deck + PILLAR_H + 0.35);
  });

  // まぐさ石
  const lintel = keep(new THREE.BoxGeometry((488 - 232) * SCALE + 8.4, 2.6, 5.4));
  put(new THREE.Mesh(lintel, darkStone), BOARD_W / 2, GATE_BY, deck + PILLAR_H + 2.4);

  // 門の奥に据えた黄金像。IDOL ターゲットが 4 基そろうと起立する（updateIdolVisuals）。
  const pedestal = keep(new THREE.CylinderGeometry(2.6, 3.2, 5, 8));
  put(new THREE.Mesh(pedestal, stone), BOARD_W / 2, RUIN_BY - 55, deck + 2.1);
  const idol = keep(new THREE.OctahedronGeometry(2.5, 0));
  idolStatueBaseY = deck + 7;
  idolStatue = put(new THREE.Mesh(idol, gold), BOARD_W / 2, RUIN_BY - 55, idolStatueBaseY);
  idolStatue.rotation.y = Math.PI * 0.25;

  // 起立に合わせて灯る像の光。影は落とさない（主光源の影で足りる）。
  idolStatueLight = new THREE.PointLight(0xffc86a, 0, 120, 1.6);
  idolStatueLight.position.set(0, idolStatueBaseY + 4, (RUIN_BY - 55 - RUIN_BY) * SCALE);
  group.add(idolStatueLight);

  scene.add(group);

  // 崩れた石塊。地表基準なので group には入れず、基壇の footprint も避ける。
  const rubble = new THREE.Group();
  const v = new THREE.Vector3();
  for (let i = 0; i < 16; i += 1) {
    // 谷壁の急斜面へ置くと石塊が浮くので、盤とその平坦な余白へ収める。
    const front = rand() < 0.55;
    const bx = front ? range(40, 680) : (rand() < 0.5 ? range(-40, 140) : range(580, 760));
    const by = front ? range(-100, -15) : range(-440, -60);
    const h = range(1.4, 3.4);
    const geo = keep(new THREE.BoxGeometry(range(2, 5), h, range(2, 5)));
    const block = new THREE.Mesh(geo, i % 2 ? stone : darkStone);
    boardToWorld(bx, by, h * 0.08, v);
    block.position.copy(v);
    block.rotation.set(range(-0.2, 0.2), rand() * Math.PI, range(-0.2, 0.2));
    block.castShadow = true;
    block.receiveShadow = true;
    rubble.add(block);
  }
  scene.add(rubble);

  return group;
};

// 盤の外側に散らす岩。発射レーンと盤面の経路は避ける。
const buildScatteredRocks = () => {
  const mat = keep(new THREE.MeshStandardMaterial({ color: 0x8a7550, roughness: 0.97, metalness: 0.02, flatShading: true }));
  const group = new THREE.Group();
  const v = new THREE.Vector3();
  for (let i = 0; i < 38; i += 1) {
    const outside = rand() < 0.5;
    const bx = outside ? range(-330, -40) : range(BOARD_W + 40, 1060);
    const by = range(-460, 1180);
    // 谷壁は急斜面なので、大きな岩を置くと下り側で浮いて見える。
    const r = range(0.6, 2.1);
    const geo = keep(new THREE.DodecahedronGeometry(r, 0));
    const rock = new THREE.Mesh(geo, mat);
    // 斜面では中心を地表より下げないと、下り側で浮いて見える。
    boardToWorld(bx, by, -r * 0.55, v);
    rock.position.copy(v);
    rock.rotation.set(rand() * Math.PI, rand() * Math.PI, rand() * Math.PI);
    rock.scale.set(1, range(0.55, 0.95), range(0.8, 1.25));
    rock.castShadow = true;
    rock.receiveShadow = true;
    group.add(rock);
  }
  scene.add(group);
  return group;
};

// 谷底。地形の落ち込みを暗い床で塞ぎ、立ちのぼる霧で底を見せない。
const buildAbyss = () => {
  const group = new THREE.Group();

  const floorGeo = keep(new THREE.PlaneGeometry(260, 150));
  const floorMat = keep(new THREE.MeshStandardMaterial({ color: 0x14100a, roughness: 1, metalness: 0 }));
  const floor = new THREE.Mesh(floorGeo, floorMat);
  floor.rotation.x = -Math.PI / 2;
  floor.position.set(0, -112, (1400 - BOARD_H / 2) * SCALE);
  group.add(floor);

  const COUNT = 260;
  const positions = new Float32Array(COUNT * 3);
  const speeds = new Float32Array(COUNT);
  for (let i = 0; i < COUNT; i += 1) {
    const bx = range(-260, 980);
    // 谷底の縁(by=1040)より手前だけに置く。斜面の上に載ると霧ではなく光の粒に見える。
    const by = range(1060, 1320);
    positions[i * 3] = (bx - BOARD_W / 2) * SCALE;
    positions[i * 3 + 1] = slopeHeight(by) + range(-14, 6);
    positions[i * 3 + 2] = (by - BOARD_H / 2) * SCALE;
    speeds[i] = range(0.35, 1.5);
  }
  const mistGeo = keep(new THREE.BufferGeometry());
  mistGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  const mistMat = keep(new THREE.PointsMaterial({
    map: createSoftDotTexture(),
    color: 0xd7e2e6,
    size: 5.5,
    sizeAttenuation: true,
    transparent: true,
    opacity: 0.13,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  }));
  mistPoints = new THREE.Points(mistGeo, mistMat);
  mistPoints.userData.speeds = speeds;
  group.add(mistPoints);

  scene.add(group);
  return group;
};

// 岩球。後続ステップの 2D 物理から setBall() で位置を受け取る。
const buildBoulder = () => {
  const geo = keep(new THREE.IcosahedronGeometry(1, 2));
  const pos = geo.attributes.position;
  const v = new THREE.Vector3();
  for (let i = 0; i < pos.count; i += 1) {
    v.fromBufferAttribute(pos, i);
    const bump = 1 + Math.sin(v.x * 5.1) * 0.07 + Math.sin(v.y * 6.3 + 1.1) * 0.06 + Math.sin(v.z * 4.7 + 2.2) * 0.07;
    pos.setXYZ(i, v.x * bump, v.y * bump, v.z * bump);
  }
  pos.needsUpdate = true;
  geo.computeVertexNormals();

  const mat = keep(new THREE.MeshStandardMaterial({
    color: 0x8f8368,
    roughness: 0.82,
    metalness: 0.12,
    flatShading: true,
  }));
  const mesh = new THREE.Mesh(geo, mat);
  mesh.scale.setScalar(BALL_WORLD_R);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  scene.add(mesh);
  return mesh;
};

/* ============================================================
   カメラ（投入時の全体俯瞰 → 盤面進入後の低い迫力視点）
   ============================================================ */

const OVERVIEW_PITCH = 0.45;
const OVERVIEW_FOV = 50;
const OVERVIEW_HEAD = 6.5;
const ACTION_PITCH = 0.001; // 盤面とほぼ完全に平行。岩肌をかすめる目線
const ACTION_FOV = 96;      // 超広角。長大な谷と、レンズ前の岩球を同時に成立させる
const ACTION_HEAD = -0.32;
const ACTION_DISTANCE = 7.5;
const ACTION_DANGER_DISTANCE = 2.9; // 排出口の外、岩球表面までわずかな距離
const camAxis = new THREE.Vector3();  // カメラ → 注視点
const camRight = new THREE.Vector3(1, 0, 0);
const camUp = new THREE.Vector3();
const camAnchor = new THREE.Vector3();
const overviewAnchor = new THREE.Vector3();
const actionAnchor = new THREE.Vector3();
const fitPoints = [];

const buildCameraRig = () => {
  boardToWorld(BOARD_W / 2, BOARD_H * 0.44, 4, overviewAnchor);
  // 低い視点では注視の中心も手前へ寄せる。手前の球が大きく迫り、
  // 盤面上部の遺跡は奥の地平近くへ退いて見える。
  boardToWorld(BOARD_W / 2, BOARD_H * 0.95, 0.45, actionAnchor);
  camAnchor.copy(overviewAnchor);
  fitPoints.length = 0;
  // 谷底(by>1040)は fit に入れない。落差が大きく、含めるとカメラが極端に引いて盤が小さくなる。
  [-40, BOARD_W / 2, BOARD_W + 40].forEach((bx) => {
    [-70, 0, BOARD_H * 0.5, BOARD_H * 0.85, BOARD_H].forEach((by) => {
      fitPoints.push(boardToWorld(bx, by, 2, new THREE.Vector3()));
    });
  });
};

// 盤面全体が画角に収まる距離を求める。縦横比が変わっても切れないようにする。
const fitDistance = (aspect, anchor, axis, up, fov, head) => {
  const tanV = Math.tan(THREE.MathUtils.degToRad(fov) / 2);
  const tanH = tanV * Math.max(aspect, 0.32);
  const v = new THREE.Vector3();
  let need = 34;
  for (let i = 0; i < fitPoints.length; i += 1) {
    v.copy(fitPoints[i]).sub(anchor);
    const depth = v.dot(axis);
    need = Math.max(need, (Math.abs(v.dot(up)) + head) / tanV - depth, Math.abs(v.dot(camRight)) / tanH - depth);
  }
  return need * 1.05;
};

const view = {
  distance: 96,
  overviewDistance: 96,
  actionDistance: ACTION_DISTANCE,
  cameraBlend: 0,
  dangerRush: 0,
  focusX: 0,      // 追従先（ワールド X）
  followX: 0,     // 追従の現在値
  shake: 0,
  shakeSeed: 0,
};

const lookTarget = new THREE.Vector3();

const updateCamera = (dt, elapsed) => {
  // 球の左右だけを緩く追う。狙いを付ける操作感を壊さないよう振り幅は抑える。
  view.followX += (view.focusX - view.followX) * Math.min(1, dt * 2.6);

  const followBlend = view.cameraBlend * view.cameraBlend * (3 - 2 * view.cameraBlend);
  const swayX = view.followX * THREE.MathUtils.lerp(0.22, 0.72, followBlend);
  const swayLook = view.followX * THREE.MathUtils.lerp(0.34, 0.78, followBlend);

  // 発射レーンを登り切るまでは全体を見せ、盤面進入後だけ低い視点へ移る。
  const activeBall = balls.find((ball) => ball.alive);
  const actionTarget = mode === 'play' && activeBall && activeBall.entered ? 1 : 0;
  view.cameraBlend += (actionTarget - view.cameraBlend) * Math.min(1, dt * (actionTarget ? 1.8 : 3.2));
  const blend = view.cameraBlend * view.cameraBlend * (3 - 2 * view.cameraBlend);
  // 球が手前へ落ちてくるほど、カメラもフリッパー間から球へ突進する。
  // 固定俯瞰にはない圧迫感を作り、落球直前には岩球が画面を占領する。
  const dangerTarget = activeBall && activeBall.entered
    ? clamp((activeBall.y - 650) / (DRAIN_Y - 650), 0, 1)
    : 0;
  // 落球は一瞬なので、接近側はほぼ即応させる。戻りだけを遅くして余韻を残す。
  view.dangerRush += (dangerTarget - view.dangerRush) * Math.min(1, dt * (dangerTarget > view.dangerRush ? 18 : 3));
  const danger = view.dangerRush;
  const pitch = THREE.MathUtils.lerp(OVERVIEW_PITCH, ACTION_PITCH, blend);
  const head = THREE.MathUtils.lerp(OVERVIEW_HEAD, ACTION_HEAD, blend);
  camera.fov = THREE.MathUtils.lerp(OVERVIEW_FOV, ACTION_FOV, blend);
  camera.updateProjectionMatrix();
  camAxis.set(0, -Math.sin(pitch), -Math.cos(pitch));
  camUp.set(0, Math.cos(pitch), -Math.sin(pitch));
  camAnchor.lerpVectors(overviewAnchor, actionAnchor, blend);
  const actionDistance = THREE.MathUtils.lerp(view.actionDistance, ACTION_DANGER_DISTANCE, danger);
  view.distance = THREE.MathUtils.lerp(view.overviewDistance, actionDistance, blend);

  // 視線ごと head だけ持ち上げる（回さず平行移動）。
  camera.position.set(
    camAnchor.x - camAxis.x * view.distance + swayX + camUp.x * head,
    camAnchor.y - camAxis.y * view.distance + camUp.y * head,
    camAnchor.z - camAxis.z * view.distance + camUp.z * head,
  );
  lookTarget.set(
    camAnchor.x + swayLook + camUp.x * head,
    camAnchor.y + camUp.y * head,
    camAnchor.z + camUp.z * head,
  );

  if (view.shake > 0.0005) {
    const amp = view.shake * (reducedMotion ? 0.35 : 1);
    const s = view.shakeSeed + elapsed * 47;
    camera.position.x += Math.sin(s * 1.7) * amp;
    camera.position.y += Math.sin(s * 2.3 + 1.9) * amp * 0.8;
    camera.position.z += Math.sin(s * 1.3 + 3.4) * amp * 0.5;
    view.shake = Math.max(0, view.shake - dt * (2.6 + view.shake * 2.4));
  }

  camera.lookAt(lookTarget);
};

const shakeView = (amount) => {
  view.shake = Math.min(2.6, view.shake + amount);
  view.shakeSeed = Math.random() * 100;
};

/* ============================================================
   盤面レイアウト（2D 盤座標）

   物理はすべて盤座標(720 x 1080)で解き、3D へは boardToWorld() で写す。
   平面で当たり判定を持たせておくと、地形の見た目を変えても球の挙動は壊れず、
   盤の座標だけを見て挙動を検証できる。
   ============================================================ */

const clamp = (value, min, max) => Math.max(min, Math.min(max, value));

const BALL_R = 20;                        // 岩球の半径（盤 px）
const BALL_WORLD_R = BALL_R * SCALE;      // 同じ半径のワールド長。浮かせ量と転がり量に使う

// 地形全体を盤として扱い、盤を囲う外周レールは置かない。
// 物理的な岩は排出口（ホッパー）両側だけ。外側を流れる球も拾える長い
// 漏斗形にして、左右2段の天然岩ガードからフリッパー中央へ導く。
const walls = [
  { a: [34, 590], b: [94, 782], bounce: 0.92 },
  { a: [94, 782], b: [190, 928], bounce: 0.98 },
  { a: [686, 590], b: [626, 782], bounce: 0.92 },
  { a: [626, 782], b: [530, 928], bounce: 0.98 },
];

const LANE_X = 676;     // 盤右側の投入峰。ここから左向きに岩球を解放する
const LANE_Y = 350;
const LAUNCH_ENTRY_X = 610; // 投入峰を抜けて盤面へ入ったとみなす x 座標
const LAUNCH_MIN_SPEED = 270;
const DRAIN_Y = 1058;   // 谷底へ落ちた判定。3D 地形が急落し始める by=1040 の少し先
const DRAIN_TERROR_SPAN = 0.32; // 失敗球がレンズ目前を覆う時間

// 手前の谷底の縁に張り出したフリッパー。角度は盤座標の +x から +y(谷側)へ測る。
//
// 軸の間隔と長さは、休止角のときに先端どうしが
//   485 - 235 - 2 * 96 * cos(0.32) ≒ 68px
// 離れるよう決めてある。当たり半径 FLIPPER_R を差し引いた実効の隙間は約 46px で、
// 直径 40px の岩球がぎりぎり通り抜けて谷底へ落ちる。ここを詰めると
// 球が左右のフリッパーに乗り上げたまま止まり、谷底へ落ちられなくなる。
const flippers = [
  { side: 'left', x: 235, y: 875, length: 96, angle: 0.32, rest: 0.32, active: -0.72, omega: 0, pivot: null },
  { side: 'right', x: 485, y: 875, length: 96, angle: Math.PI - 0.32, rest: Math.PI - 0.32, active: Math.PI + 0.72, omega: 0, pivot: null },
];

const GRAVITY = 560;       // 斜面の基準傾斜が生む加速度（盤 px/s²）
const SLOPE_GAIN = 9000;   // 地形の勾配(ワールド高/盤px)を加速度へ換算する係数
const SWAY_GAIN = 0.55;    // 左右方向は弱める。岩肌の凹凸で軌道が揺らぐ程度に留める
const GRAD_STEP = 6;       // 勾配を測る中央差分の幅（盤 px）
const FALL_ACCEL_MAX = 2600;
const MAX_SPEED = 1250;
// 1 回の物理積分で岩球が進んでよい距離。速度ではなく移動量から分割数を決め、
// 一時的な高速度や描画フレームの揺れでも岩壁をまたいでしまわないようにする。
const PHYSICS_TRAVEL_PER_STEP = BALL_R * 0.55;
const PHYSICS_MIN_STEPS = 3;
const PHYSICS_MAX_STEPS = 12;
const COLLISION_SLOP = 0.35; // 接触面からの微小な離隔。連続反射を防ぐ。
const FLIP_SPEED = 19;     // フリッパーの角速度（rad/s）
const FLIPPER_R = 11;      // フリッパーの当たり半径（盤 px）
const SURFACE_CAP = 1500;  // フリッパー面が球へ渡せる速度の上限（盤 px/s）
const WALL_BOUNCE = 0.72;

/* ============================================================
   ゲーム状態と HUD
   ============================================================ */

const keys = { left: false, right: false };   // 入力はキー / ボタン / ポインターすべてここへ集約する
const keySources = { left: new Set(), right: new Set() };
const pointers = new Map();

// 同じフリッパーを複数の操作で押している間は、どれか一つを離しても戻さない。
// キーボード、盤面タップ、画面ボタンのいずれも最終的には keys だけを物理側へ渡す。
const setFlipperInput = (side, source, pressed) => {
  if (side !== 'left' && side !== 'right') return;
  if (pressed) keySources[side].add(source);
  else keySources[side].delete(source);
  keys[side] = keySources[side].size > 0;
};

const el = (selector) => document.querySelector(selector);
const ui = {
  score: el('#score'), high: el('#high-score'), multiplier: el('#multiplier'), balls: el('#balls'),
  modeBadge: el('#mode-badge'), announcer: el('#announcer'), combo: el('#combo'), flash: el('#flash'),
  launch: el('#launch'), bridge: el('#bridge'), flipperLeft: el('#flipper-left'), flipperRight: el('#flipper-right'),
  pauseButton: el('#pause'), sound: el('#sound'),
  title: el('#title-screen'), pause: el('#pause-screen'), gameover: el('#gameover-screen'), final: el('#final-score'),
  idolPanel: el('#idol-status'), idolHint: el('#idol-hint'),
  ropePanel: el('#rope-status'), ropeValue: el('#rope-value'), ropeBar: el('#rope-bar'), ropeHint: el('#rope-hint'),
  torrentTrack: el('.torrent-track'), torrentBar: el('#torrent-bar'), torrentValue: el('#torrent-value'),
  explorationPanel: el('#exploration-status'), explorationCount: el('#exploration-count'), explorationStage: el('#exploration-stage'),
  explorationGoal: el('#exploration-goal'), explorationCondition: el('#exploration-condition'), explorationReward: el('#exploration-reward'),
};

let mode = 'title';   // title / play / paused / over
let demoMode = false;
let score = 0;
let highScore = Number(localStorage.getItem('x-pinball-opus-high') || 0);
let lives = 3;
let multiplier = 1;      // 遺跡ゲートで上がる基礎倍率
let floodFactor = 1;     // 鉄砲水モード中だけ基礎倍率へ掛かる係数
let balls = [];
let charging = false;
let charge = 0;
let gameTime = 0;
let launchPointerId = null;
let bridgePointerId = null;
let announceTimer = 0;
let demoRestartAt = 0;
let autoDemoTimer = 0;

// 自動確認用の読み取り記録。ゲーム進行には使わず、実際に通った通常経路の
// 結果だけを残す。検証 API からゲーム状態を書き換える近道はここへ作らない。
const verificationState = {
  run: 0,
  entries: 0,
  bridgeRescues: 0,
  floodStarts: 0,
  explorationRewards: 0,
  events: [],
};

const resetVerification = () => {
  verificationState.run += 1;
  verificationState.entries = 0;
  verificationState.bridgeRescues = 0;
  verificationState.floodStarts = 0;
  verificationState.explorationRewards = 0;
  verificationState.events.length = 0;
};

const recordVerification = (type, detail = {}) => {
  verificationState.events.push({
    type,
    at: Number(gameTime.toFixed(3)),
    ...detail,
  });
  // 長時間のデモでも状態 API を軽く保つ。
  if (verificationState.events.length > 20) verificationState.events.shift();
};

const syncActionControls = () => {
  const canPause = mode === 'play' || mode === 'paused';
  ui.pauseButton.disabled = !canPause;
  ui.pauseButton.textContent = mode === 'paused' ? 'RESUME' : 'PAUSE';
  ui.pauseButton.setAttribute('aria-pressed', String(mode === 'paused'));
  ui.pauseButton.setAttribute('aria-label', mode === 'paused' ? 'ゲームを再開' : 'ゲームを一時停止');
  ui.sound.setAttribute('aria-pressed', String(!muted));
};

// 実際に得点へ掛かる倍率。基礎倍率（IDOL）と鉄砲水の係数を一箇所で合成し、
// HUD の表示と加点が別々の値を見ることがないようにする。
const SCORE_MULTIPLIER_MAX = 16;
const scoreMultiplier = () => Math.min(SCORE_MULTIPLIER_MAX, multiplier * floodFactor);

const updateHud = () => {
  ui.score.textContent = String(score).padStart(7, '0');
  ui.high.textContent = String(highScore).padStart(7, '0');
  ui.multiplier.textContent = `×${scoreMultiplier()}`;
  ui.modeBadge.textContent = demoMode ? 'AUTOPILOT MODE' : 'PLAYER MODE';
  ui.modeBadge.classList.toggle('demo', demoMode);
  ui.balls.replaceChildren(...Array.from({ length: 3 }, (_, i) => {
    const node = document.createElement('i');
    if (i >= lives) node.className = 'lost';
    return node;
  }));
};

// 得点はここに集約する。倍率の掛け方とハイスコア更新を一箇所に閉じ込める。
// 遠征踏破のような固定報酬だけは applyMultiplier=false で、表示どおりの点数を加える。
const addScore = (points, applyMultiplier = true) => {
  score += Math.round(points * (applyMultiplier ? scoreMultiplier() : 1));
  if (score > highScore) {
    highScore = score;
    try { localStorage.setItem('x-pinball-opus-high', String(highScore)); } catch (_) { /* 保存できなくても進行は妨げない */ }
  }
  updateHud();
};

const announce = (text) => {
  ui.announcer.textContent = text;
  ui.announcer.classList.remove('show');
  void ui.announcer.offsetWidth;   // アニメーションを毎回頭から流し直す
  ui.announcer.classList.add('show');
  clearTimeout(announceTimer);
  announceTimer = setTimeout(() => ui.announcer.classList.remove('show'), 950);
};

/* ============================================================
   効果音（WebAudio。合成のみで外部アセットは使わない）
   ============================================================ */

let muted = false;
let audio = null;
let noiseBuffer = null;

const ensureAudio = () => {
  if (muted) return null;
  try {
    if (!audio) audio = new AudioContext();
    if (audio.state === 'suspended') audio.resume();
    return audio;
  } catch (_) { return null; }
};

const tone = (freq, duration = 0.07, type = 'sawtooth', gain = 0.035, sweep = 1) => {
  const ac = ensureAudio();
  if (!ac) return;
  const osc = ac.createOscillator();
  const amp = ac.createGain();
  const now = ac.currentTime;
  osc.type = type;
  osc.frequency.setValueAtTime(freq, now);
  osc.frequency.exponentialRampToValueAtTime(Math.max(30, freq * sweep), now + duration);
  amp.gain.setValueAtTime(gain, now);
  amp.gain.exponentialRampToValueAtTime(0.0001, now + duration);
  osc.connect(amp).connect(ac.destination);
  osc.start(now);
  osc.stop(now + duration);
};

const noise = (duration = 0.08, gain = 0.025, freq = 900) => {
  const ac = ensureAudio();
  if (!ac) return;
  if (!noiseBuffer) {
    noiseBuffer = ac.createBuffer(1, ac.sampleRate, ac.sampleRate);
    const data = noiseBuffer.getChannelData(0);
    for (let i = 0; i < data.length; i += 1) data[i] = Math.random() * 2 - 1;
  }
  const source = ac.createBufferSource();
  const amp = ac.createGain();
  const filter = ac.createBiquadFilter();
  source.buffer = noiseBuffer;
  filter.type = 'bandpass';
  filter.frequency.value = freq;
  amp.gain.setValueAtTime(gain, ac.currentTime);
  amp.gain.exponentialRampToValueAtTime(0.0001, ac.currentTime + duration);
  source.connect(filter).connect(amp).connect(ac.destination);
  source.start();
  source.stop(ac.currentTime + duration);
};

// 岩がぶつかる音。強さは衝突速度から決め、画面揺れも同じ強さから出す。
const rockHit = (power) => {
  const p = clamp(power, 0, 1);
  if (p < 0.08) return;
  noise(0.05 + p * 0.09, 0.012 + p * 0.03, 380 + p * 520);
  tone(70 + Math.random() * 40, 0.09 + p * 0.08, 'triangle', 0.012 + p * 0.026, 0.45);
  shakeView(0.12 + p * 0.75);
};

/* ============================================================
   衝突判定
   ============================================================ */

// 直近の衝突法線。押し戻しまで済ませ、反発の掛け方は呼び出し側で決める。
const hitNormal = { nx: 0, ny: 0, depth: 0 };

const capBallSpeed = (ball) => {
  const speed = Math.hypot(ball.vx, ball.vy);
  if (speed <= MAX_SPEED) return;
  ball.vx *= MAX_SPEED / speed;
  ball.vy *= MAX_SPEED / speed;
};

const segmentHit = (ball, ax, ay, bx, by, radius) => {
  const dx = bx - ax;
  const dy = by - ay;
  const length2 = dx * dx + dy * dy || 1e-6;
  const t = clamp(((ball.x - ax) * dx + (ball.y - ay) * dy) / length2, 0, 1);
  const px = ax + dx * t;
  const py = ay + dy * t;
  const ox = ball.x - px;
  const oy = ball.y - py;
  const distance = Math.hypot(ox, oy);
  const minimum = ball.r + radius;
  if (distance >= minimum) return false;

  let nx;
  let ny;
  if (distance < 1e-4) {
    // 中心が線分に乗ってしまった場合は、進行方向と逆側へ逃がす。
    // 常に同じ側を選ぶと、壁を横切った高速球をさらに外へ押し出してしまう。
    const length = Math.sqrt(length2);
    nx = -dy / length;
    ny = dx / length;
    if (ball.vx * nx + ball.vy * ny > 0) {
      nx = -nx;
      ny = -ny;
    }
  } else {
    nx = ox / distance;
    ny = oy / distance;
  }
  const depth = minimum - distance;
  ball.x += nx * (depth + COLLISION_SLOP);
  ball.y += ny * (depth + COLLISION_SLOP);
  hitNormal.nx = nx;
  hitNormal.ny = ny;
  hitNormal.depth = depth;
  return true;
};

// 円の当たり判定。線分版と同じく押し戻しまで済ませ、hitNormal へ法線を残す。
const circleHit = (ball, cx, cy, radius) => {
  const ox = ball.x - cx;
  const oy = ball.y - cy;
  const distance = Math.hypot(ox, oy);
  const minimum = ball.r + radius;
  if (distance >= minimum) return false;

  let nx;
  let ny;
  if (distance < 1e-4) {
    // 中心が完全に重なった場合も、入射方向の反対へ逃がして反射を成立させる。
    const speed = Math.hypot(ball.vx, ball.vy);
    nx = speed > 1e-4 ? -ball.vx / speed : 0;
    ny = speed > 1e-4 ? -ball.vy / speed : 1;
  } else {
    nx = ox / distance;
    ny = oy / distance;
  }
  ball.x = cx + nx * (minimum + COLLISION_SLOP);
  ball.y = cy + ny * (minimum + COLLISION_SLOP);
  hitNormal.nx = nx;
  hitNormal.ny = ny;
  hitNormal.depth = minimum - distance;
  return true;
};

// 法線方向の速度だけ反転させる。跳ね返った強さ（0〜1 目安）を返す。
const reflect = (ball, nx, ny, bounce) => {
  const along = ball.vx * nx + ball.vy * ny;
  if (along >= 0) return 0;
  ball.vx -= (1 + bounce) * along * nx;
  ball.vy -= (1 + bounce) * along * ny;
  capBallSpeed(ball);
  return Math.min(1, -along / 600);
};

/* ============================================================
   遺跡ゲート（IDOL ターゲット）

   盤奥の高台の縁に石柱を 4 基立て、I / D / O / L を灯していく。
   当たり判定・得点・石柱の発光・黄金像の起立・HUD は、すべて idolState
   ひとつを見て更新する。描画側の状態を別に持たせると、点灯と見た目が
   ずれたときに原因を追えなくなる。
   ============================================================ */

// 石柱の配置。盤 y は 72〜300 の帯に収め、中央の 2 基の間は球の直径(40px)より
// 広く空けて、奥の空間へ抜ける経路を必ず残す。左右対称（x の和が 720）。
const IDOL_R = 24;                 // 石柱の当たり半径（盤 px）
const IDOL_BOUNCE = 1.02;          // バンパー相当。入射より強く弾き返す
const IDOL_HIT_SCORE = 1500;       // 未点灯の石柱を灯した
const IDOL_REHIT_SCORE = 250;      // 点灯済みの石柱への再命中
const IDOL_AWAKE_SCORE = 12000;    // 4 基そろえた
const IDOL_MULTIPLIER_MAX = 8;
const IDOL_HIT_COOLDOWN = 0.18;    // 同じ石柱の連続判定を抑える秒数
// 3D の boulderPool と同じ上限。通常球を含め、画面上の岩球をこの数より増やさない。
const ECHO_BOULDER_TOTAL_MAX = 3;
const ECHO_BOULDER_SPREAD = [
  { x: -38, y: 42, vx: -210, vy: 215 },
  { x: 38, y: 54, vx: 210, vy: 260 },
];

const idolState = {
  targets: [
    { mark: 'I', x: 192, y: 204 },
    { mark: 'D', x: 296, y: 176 },
    { mark: 'O', x: 424, y: 176 },
    { mark: 'L', x: 528, y: 204 },
  ].map((target, i) => ({
    ...target,
    lit: false,
    hits: 0,
    hitAt: -9,
    glow: 0,      // 点灯の追従値（0〜1）。石柱の emissive に使う
    flash: 0,     // 命中直後の閃光（0〜1）
    phase: i * 1.7,
    node: el(`#idol-status i[data-mark="${target.mark}"]`),
    pillar: null,
    glyph: null,
  })),
  litCount: 0,
  awake: false,
  cycles: 0,    // 4 基そろえた回数
  rise: 0,      // 黄金像の起立の追従値（0〜1）
  echoBoulders: 0, // 今回の覚醒で追加された ECHO BOULDER 数
  echoCycle: 0,    // 同じ覚醒中に報酬を二重発行しないための識別子
};

const syncIdolHud = () => {
  idolState.targets.forEach((target) => {
    if (target.node) target.node.classList.toggle('lit', target.lit);
  });
  if (ui.idolPanel) ui.idolPanel.classList.toggle('awake', idolState.awake);
  if (ui.idolHint) {
    ui.idolHint.textContent = idolState.awake
      ? `GOLD AWAKENED ×${idolState.cycles}`
      : `AWAKEN THE GOLD ${idolState.litCount}/${idolState.targets.length}`;
  }
  if (explorationState.stage === 0) syncExplorationHud();
};

// full=true でゲーム全体の初期化（4 基そろえた回数も戻す）。
const resetIdol = (full = false) => {
  idolState.targets.forEach((target) => {
    target.lit = false;
    target.hits = 0;
    target.hitAt = -9;
    target.flash = 0;
  });
  idolState.litCount = 0;
  idolState.awake = false;
  idolState.echoBoulders = 0;
  idolState.echoCycle = 0;
  if (full) {
    idolState.cycles = 0;
    idolState.targets.forEach((target) => { target.glow = 0; });
    idolState.rise = 0;
  }
  syncIdolHud();
};

const awakenIdol = (sourceBall) => {
  idolState.awake = true;
  idolState.cycles += 1;
  multiplier = Math.min(IDOL_MULTIPLIER_MAX, multiplier + 1);
  addScore(IDOL_AWAKE_SCORE);   // 倍率を上げてから加点する
  const echoCount = releaseEchoBoulders(sourceBall);
  announce(echoCount > 0 ? `ECHO BOULDERS ×${echoCount}` : 'THE IDOL AWAKENS');
  tone(180, 0.55, 'triangle', 0.055, 4.2);
  tone(268, 0.65, 'sine', 0.04, 3.1);
  noise(0.42, 0.032, 1500);
  shakeView(1.45);
  // 増水は最後に足す。100% に届いた場合は鉄砲水の実況で上書きさせる。
  registerHit(TORRENT_AWAKE_GAIN);
  syncExplorationProgress();
};

const updateIdolTarget = (ball, target) => {
  if (!circleHit(ball, target.x, target.y, IDOL_R)) return;
  const power = reflect(ball, hitNormal.nx, hitNormal.ny, IDOL_BOUNCE);
  target.flash = 1;
  // サブステップで同じ接触を何度も拾うので、得点は時間で間引く。
  if (gameTime - target.hitAt < IDOL_HIT_COOLDOWN) return;
  target.hitAt = gameTime;
  target.hits += 1;
  rockHit(0.3 + power * 0.5);

  if (target.lit) {
    tone(620, 0.12, 'square', 0.024, 1.3);
    registerHit(TORRENT_HIT_GAIN);
    addScore(IDOL_REHIT_SCORE);
    return;
  }
  target.lit = true;
  idolState.litCount += 1;
  tone(300 + idolState.litCount * 90, 0.2, 'square', 0.032, 2.4);
  registerHit(TORRENT_LIT_GAIN);
  addScore(IDOL_HIT_SCORE);
  if (idolState.litCount >= idolState.targets.length) awakenIdol(ball);
  else announce(`GATE ${target.mark}`);
  syncIdolHud();
};

// 石柱の発光と黄金像の起立。idolState だけを見て毎フレーム追従させる。
const updateIdolVisuals = (dt, time) => {
  for (let i = 0; i < idolState.targets.length; i += 1) {
    const target = idolState.targets[i];
    target.flash = Math.max(0, target.flash - dt * 3.4);
    target.glow += ((target.lit ? 1 : 0) - target.glow) * Math.min(1, dt * 6);
    if (!target.pillar) continue;
    const pulse = target.lit ? 0.72 + Math.sin(time * 3.6 + target.phase) * 0.28 : 0.1;
    target.pillar.material.emissiveIntensity = 0.06 + target.glow * 0.55 + target.flash * 1.5;
    target.glyph.material.emissiveIntensity = pulse * (0.5 + target.glow * 1.6) + target.flash * 2.4;
    target.glyph.rotation.y = time * (0.3 + target.glow * 1.2);
    target.glyph.position.y = target.glyph.userData.baseY + target.glow * 0.55;
  }

  idolState.rise += ((idolState.awake ? 1 : 0) - idolState.rise) * Math.min(1, dt * 2.4);
  if (idolStatue) {
    idolStatue.position.y = idolStatueBaseY + idolState.rise * 5.6;
    idolStatue.rotation.y = Math.PI * 0.25 + time * (0.2 + idolState.rise * 1.4);
    idolStatue.scale.setScalar(1 + idolState.rise * 0.34);
    idolStatue.material.emissiveIntensity = 0.5 + idolState.rise * 2.8;
  }
  if (idolStatueLight) {
    idolStatueLight.intensity = idolState.rise * (620 + Math.sin(time * 2.4) * 90);
    idolStatueLight.distance = 60 + idolState.rise * 90;
  }
};

/* ============================================================
   蔓の吊り橋（ROPE BRIDGE）

   左右フリッパーの同時押しで、谷底の縁の手前に蔓の橋を巻き上げる。
   落ちてくる球を受け止めて盤面へ跳ね返す救済だが、縄は 3 回で切れる。

   当たり判定・耐久・HUD・3D の踏板は、すべて bridgeState ひとつを見て
   更新する。石柱（IDOL）と同じく、描画側に別の状態を持たせない。
   ============================================================ */

// 橋を張る位置。DRAIN_Y(1058) の手前で受け止める。両端の盤 x は
// 左右のアウトレーン壁（y=1000 でおよそ x=165 / x=527）へ架かる位置に合わせる。
const BRIDGE_X0 = 158;
const BRIDGE_X1 = 534;
const BRIDGE_Y = 1000;
const BRIDGE_SAG = 18;          // 中央のたわみ（谷側 +y）
const BRIDGE_R = 8;             // 縄の当たり半径（盤 px）
const BRIDGE_USES = 3;          // 縄の耐久。巻き上げるたびに 1 減る
const BRIDGE_SPAN = 0.62;       // 1 回の巻き上げで橋が張られている秒数
const BRIDGE_BOUNCE = 0.86;
const BRIDGE_LIFT = 660;        // 受け止めた球へ最低限与える奥向きの速度（盤 px/s）
const BRIDGE_SAVE_SCORE = 2500;
const BRIDGE_SAVE_COOLDOWN = 0.25;   // 同じ球の連続判定を抑える秒数
const BRIDGE_ARM_Y = 790;            // この位置より谷側へ落ちた岩球だけを救出対象にする
const BRIDGE_ARM_SPEED = 110;        // 横移動中の岩球へ縄を無駄打ちしないための最低落下速度
const BRIDGE_FLOOD_SCORE = 4500;     // 鉄砲水中の救出は危険に見合う追加得点を与える
const BRIDGE_FLOOD_TIME = 1.3;       // 同上。濁流の得点時間を少しだけ延長する

// 橋の縄の形。当たり判定の線分も 3D の踏板もここから作り、見た目と判定をずらさない。
const bridgePoint = (t) => ({
  x: BRIDGE_X0 + (BRIDGE_X1 - BRIDGE_X0) * t,
  y: BRIDGE_Y + Math.sin(Math.PI * t) * BRIDGE_SAG,
});

const BRIDGE_SPANS = 4;
const bridgeSpans = Array.from({ length: BRIDGE_SPANS }, (_, i) => ({
  a: bridgePoint(i / BRIDGE_SPANS),
  b: bridgePoint((i + 1) / BRIDGE_SPANS),
}));

const bridgeState = {
  uses: BRIDGE_USES,   // 残りの耐久回数
  timer: 0,            // 張っている残り秒。0 なら当たり判定を持たない
  deploys: 0,          // 巻き上げた回数
  saves: 0,            // 受け止めた回数
  floodSaves: 0,       // 鉄砲水中に受け止めた回数
  expeditionSaved: false, // 探索の第二段階へ反映済みか（救出そのものは複数回できる）
  windowOpen: false,   // 落下中の岩球が橋を張る時機にいるか
  status: 'ready',     // ready / empty / armed / missed / saved / flood-save / snapped
  lastScore: 0,        // 直近の救出の基礎報酬。HUD の表示内容と得点を対応させる
  raise: 0,            // 踏板のせり上がりの追従値（0〜1）
  flash: 0,            // 受け止めた直後の閃光（0〜1）
};

let bridgeGroup = null;          // 3D の踏板と縄。せり上がりで動かす
const bridgeDeckMats = [];       // 同上の材質。透過で出し入れする
let dualFlipLatched = false;     // 同時押しの立ち上がりだけを拾うラッチ

const syncBridgeHud = () => {
  if (ui.ropeValue) ui.ropeValue.textContent = String(bridgeState.uses);
  if (ui.ropeBar) ui.ropeBar.style.width = `${(bridgeState.uses / BRIDGE_USES) * 100}%`;
  if (ui.ropePanel) {
    ui.ropePanel.classList.toggle('frayed', bridgeState.uses === 1);
    ui.ropePanel.classList.toggle('broken', bridgeState.uses <= 0 && bridgeState.timer <= 0);
    ui.ropePanel.classList.toggle('armed', bridgeState.status === 'armed');
    ui.ropePanel.classList.toggle('saved', bridgeState.status === 'saved');
    ui.ropePanel.classList.toggle('flood-save', bridgeState.status === 'flood-save');
    ui.ropePanel.classList.toggle('missed', bridgeState.status === 'missed');
  }
  if (ui.ropeHint) {
    if (bridgeState.status === 'armed') ui.ropeHint.textContent = 'VINES READY — CATCH THE FALL';
    else if (bridgeState.status === 'saved') ui.ropeHint.textContent = `VINES SAVED THE ROCK +${bridgeState.lastScore.toLocaleString()}`;
    else if (bridgeState.status === 'flood-save') ui.ropeHint.textContent = `FLOOD RESCUE +${bridgeState.lastScore.toLocaleString()} / +${BRIDGE_FLOOD_TIME.toFixed(1)}s`;
    else if (bridgeState.uses <= 0) ui.ropeHint.textContent = 'ROPE SNAPPED';
    else if (bridgeState.status === 'missed') ui.ropeHint.textContent = 'FALL MISSED — ROPE LOST';
    else if (bridgeState.status === 'empty') ui.ropeHint.textContent = 'NO FALL — WAIT FOR THE DROP';
    else if (bridgeState.windowOpen) ui.ropeHint.textContent = 'DROP NOW — VINES CAN REACH';
    else ui.ropeHint.textContent = `WATCH THE FALL ×${bridgeState.uses}`;
  }
  if (ui.bridge) {
    ui.bridge.disabled = bridgeState.uses <= 0;
    ui.bridge.classList.toggle('ready', bridgeState.uses > 0 && mode === 'play');
    ui.bridge.classList.toggle('window', bridgeState.uses > 0 && bridgeState.windowOpen && bridgeState.timer <= 0);
  }
  if (explorationState.stage === 1) syncExplorationHud();
};

// full=true でゲーム全体の初期化。縄の耐久は球をまたいで残すので、
// 球ごとのリセット（resetRound）では張り直しの状態だけを戻す。
const resetBridge = (full = false) => {
  bridgeState.timer = 0;
  dualFlipLatched = false;
  bridgeState.windowOpen = false;
  bridgeState.status = 'ready';
  bridgeState.lastScore = 0;
  if (full) {
    bridgeState.uses = BRIDGE_USES;
    bridgeState.deploys = 0;
    bridgeState.saves = 0;
    bridgeState.floodSaves = 0;
    bridgeState.expeditionSaved = false;
    bridgeState.raise = 0;
    bridgeState.flash = 0;
  }
  syncBridgeHud();
};

// 谷底へ落ちつつある岩球だけを、橋を張る対象として返す。早過ぎる巻き上げは
// 耐久を消費させず、HUD で「待つべきだった」ことを明示する。
const bridgeRescueCandidate = () => balls.find((ball) => (
  ball.alive && !ball.lane && !ball.launchGuide && !ball.draining
  && ball.y >= BRIDGE_ARM_Y && ball.y < DRAIN_Y + ball.r
  && ball.vy >= BRIDGE_ARM_SPEED
  && ball.x >= BRIDGE_X0 - ball.r - 34 && ball.x <= BRIDGE_X1 + ball.r + 34
));

const refreshBridgeWindow = () => {
  const windowOpen = bridgeState.timer <= 0 && Boolean(bridgeRescueCandidate());
  if (bridgeState.windowOpen === windowOpen) return;
  bridgeState.windowOpen = windowOpen;
  if (bridgeState.status === 'ready' || bridgeState.status === 'empty') syncBridgeHud();
};

// 巻き上げ。落下に合わせて成功した展開だけが耐久を使う。耐久切れ、張っている最中、
// または早過ぎる入力は同じ経路で空振りにして、ボタンとキーボードで差を作らない。
const haulBridge = () => {
  if (mode !== 'play') return false;
  if (bridgeState.uses <= 0) {
    bridgeState.status = 'snapped';
    syncBridgeHud();
    announce('THE ROPE IS GONE');
    tone(90, 0.18, 'square', 0.02, 0.35);
    return false;
  }
  if (bridgeState.timer > 0) return false;
  if (!bridgeRescueCandidate()) {
    bridgeState.status = 'empty';
    bridgeState.windowOpen = false;
    syncBridgeHud();
    announce('NO FALL TO CATCH');
    tone(118, 0.12, 'square', 0.018, 0.68);
    return false;
  }

  bridgeState.uses -= 1;
  bridgeState.deploys += 1;
  bridgeState.timer = BRIDGE_SPAN;
  bridgeState.status = 'armed';
  bridgeState.windowOpen = false;
  syncBridgeHud();
  announce(bridgeState.uses > 0 ? 'ROPE BRIDGE' : 'LAST ROPE');
  tone(140, 0.26, 'sawtooth', 0.038, 3.4);
  noise(0.2, 0.026, 620);
  shakeView(0.55);
  return true;
};

// 落ちてきた球を橋で受け止める。張っていない間は線分そのものを持たない。
const updateBridgeHit = (ball) => {
  if (bridgeState.timer <= 0) return;
  for (let i = 0; i < bridgeSpans.length; i += 1) {
    const span = bridgeSpans[i];
    if (!segmentHit(ball, span.a.x, span.a.y, span.b.x, span.b.y, BRIDGE_R)) continue;
    reflect(ball, hitNormal.nx, hitNormal.ny, BRIDGE_BOUNCE);
    // 反発だけでは斜面の重力に負けてそのまま落ち直すので、盤面へ戻る最低速度を与える。
    if (ball.vy > -BRIDGE_LIFT) ball.vy = -BRIDGE_LIFT;
    bridgeState.flash = 1;
    // サブステップで同じ接触を何度も拾うので、得点は時間で間引く。
    if (gameTime - ball.bridgeAt < BRIDGE_SAVE_COOLDOWN) return;
    ball.bridgeAt = gameTime;
    bridgeState.saves += 1;
    const floodRescue = torrentState.flood;
    const rescueScore = floodRescue ? BRIDGE_FLOOD_SCORE : BRIDGE_SAVE_SCORE;
    bridgeState.lastScore = rescueScore;
    bridgeState.status = floodRescue ? 'flood-save' : 'saved';
    verificationState.bridgeRescues += 1;
    recordVerification('bridge-rescue', { flood: floodRescue, points: rescueScore });
    if (floodRescue) {
      bridgeState.floodSaves += 1;
      torrentState.bridgeRescues += 1;
      torrentState.timer = Math.min(FLOOD_SPAN + BRIDGE_FLOOD_TIME * 2, torrentState.timer + BRIDGE_FLOOD_TIME);
    }
    registerHit(TORRENT_SAVE_GAIN);
    addScore(rescueScore);
    announce(floodRescue ? 'FLOODLINE RESCUE' : 'CAUGHT BY THE VINES');
    tone(330, 0.22, 'triangle', 0.036, 2.6);
    noise(0.16, 0.022, 900);
    shakeView(0.8);
    // 探索の救出試練は最初の成功だけを達成事実にする。以後の救出は得点と
    // 濁流連鎖へ寄与するが、段階表示や達成報酬を重複させない。
    if (!bridgeState.expeditionSaved) {
      bridgeState.expeditionSaved = true;
      syncExplorationProgress();
    }
    syncBridgeHud();
    syncTorrentHud();
    return;
  }
};

// 踏板のせり上がりと縄の発光。bridgeState だけを見て毎フレーム追従させる。
const updateBridgeVisuals = (dt, time) => {
  const target = bridgeState.timer > 0 ? 1 : 0;
  // 巻き上げは速く、落とすのはゆっくり。縄が谷底へ垂れ戻る間も姿が見える。
  bridgeState.raise += (target - bridgeState.raise) * Math.min(1, dt * (target > 0 ? 16 : 4.2));
  bridgeState.flash = Math.max(0, bridgeState.flash - dt * 3);
  if (!bridgeGroup) return;

  const raise = bridgeState.raise;
  bridgeGroup.visible = raise > 0.012;
  if (!bridgeGroup.visible) return;
  bridgeGroup.position.y = -7.5 * (1 - raise);
  const sway = Math.sin(time * 6.2) * 0.05 * raise;
  bridgeGroup.rotation.z = sway;
  for (let i = 0; i < bridgeDeckMats.length; i += 1) {
    const mat = bridgeDeckMats[i];
    mat.opacity = Math.min(1, raise * 1.3);
    if (mat.emissive) mat.emissiveIntensity = 0.25 + raise * 0.85 + bridgeState.flash * 2.2;
  }
};

/* ============================================================
   増水率（TORRENT）と鉄砲水（FLASH FLOOD）

   石柱への命中と岩壁の反射で谷の増水率が上がり、100% で鉄砲水が起きる。
   鉄砲水の間は谷の奥から手前へ濁流が流れ、球は手前（谷底）へ押されるが、
   そのぶん得点倍率が上がる。攻め続けるほど自分の足場が危うくなる仕掛け。

   IDOL / ROPE BRIDGE と同じく、当たり判定・HUD・3D の水流はすべて
   torrentState ひとつを見て更新し、描画側に別の状態を持たせない。
   ============================================================ */

const TORRENT_MAX = 100;              // 増水率の上限（%）。ここで鉄砲水へ移る
const TORRENT_HIT_GAIN = 9;           // 点灯済みの石柱への命中
const TORRENT_LIT_GAIN = 14;          // 未点灯の石柱を灯した
const TORRENT_AWAKE_GAIN = 30;        // 4 基そろえた
const TORRENT_SAVE_GAIN = 10;         // 吊り橋で受け止めた
const TORRENT_WALL_GAIN = 2.0;        // 岩壁の反射（弱い接触では加算しない）
const TORRENT_WALL_POWER = 4.6;       // 同上。衝突の強さ(0〜1)に比例して上乗せする
const TORRENT_WALL_MIN = 0.08;        // 加算対象とする衝突の強さの下限
const TORRENT_WALL_COOLDOWN = 0.12;   // 同じ球の壁反射を数える間隔（秒）
const TORRENT_DECAY = 1.2;            // 何もしない間に引いていく増水率（%/秒）

const FLOOD_SPAN = 8;                 // 鉄砲水の継続秒数
const FLOOD_FACTOR = 2;               // 鉄砲水中に基礎倍率へ掛ける係数
const FLOOD_PUSH = 380;               // 濁流が球へ与える手前(+y)方向の加速度（盤 px/s²）
const FLOOD_SWAY = 150;               // 同上。左右へ揺さぶる加速度の振幅
const FLOOD_SCORE = 6000;             // 鉄砲水へ移った瞬間の加点

const COMBO_SPAN = 2.2;               // この秒数だけ命中が途切れたら連鎖を切る
const COMBO_BOOST = 0.05;             // 連鎖 1 段ごとに増水量へ上乗せする割合
const COMBO_BOOST_MAX = 12;           // 上乗せを頭打ちにする連鎖数

const torrentState = {
  level: 0,        // 増水率（0〜TORRENT_MAX）
  flood: false,    // 鉄砲水モードか
  timer: 0,        // 鉄砲水の残り秒
  floods: 0,       // 鉄砲水へ移った回数
  bridgeRescues: 0, // 鉄砲水中に吊り橋で救出した回数
  combo: 0,        // 連続命中の段数
  comboAt: -9,     // 最後に命中した時刻。COMBO_SPAN を過ぎたら切る
  flow: 0,         // 水流メッシュの追従値（0〜1）
  flash: 0,        // 画面全体の閃光（0〜1）
};

/* ============================================================
   峡谷探索の段階

   目標の達成事実は IDOL / ROPE BRIDGE / TORRENT の各状態だけに置く。
   ここはその事実を「どこまで踏査が進んだか」へ写す状態である。IDOL、橋、
   鉄砲水の個別報酬は各ギミックへ残し、三試練をすべて越えたときだけ固定の
   遠征達成報酬を発行する。rewarded を同一ゲーム中のラッチにすることで、
   複数の岩球が同時に当たっても二重加点しない。
   ============================================================ */

const EXPEDITION_COMPLETE_SCORE = 30000;
const explorationState = {
  stage: 0,          // 到達済みの最大段階（0〜3）。進行表示は次の段でこの値を読む
  advancedAt: -1,    // 最後に段階が進んだゲーム内時刻。状態確認と演出の重複防止用
  rewarded: false,   // 三試練達成報酬をこのゲームですでに発行したか
  rewardPoints: 0,   // 実際に加算した固定報酬。HUD と得点計算の同期確認に使う
  rewardedAt: -1,
};

let explorationAdvanceTimer = 0;

const explorationHudContent = () => {
  if (explorationState.stage === 0) {
    return {
      stage: '第一踏査', goal: '黄金像を目覚めさせる',
      condition: `遺跡ゲートを撃ち抜き I・D・O・L を灯せ　${idolState.litCount} / ${idolState.targets.length}`,
      reward: '報酬　基礎倍率 +1 ・ 12,000 × 実効倍率',
    };
  }
  if (explorationState.stage === 1) {
    return {
      stage: '第二踏査', goal: '蔓の救出',
      condition: `落下表示で両フリップ　救出 ${bridgeState.expeditionSaved ? '1 / 1' : '0 / 1'}　ROPE ${bridgeState.uses} / ${BRIDGE_USES}`,
      reward: '報酬　2,500 × 実効倍率 ・ 増水 +10（鉄砲水中は延長救出）',
    };
  }
  if (explorationState.stage === 2) {
    return {
      stage: '第三踏査', goal: '鉄砲水を起こす',
      condition: '連鎖をつなぎ TORRENT を100%へ',
      reward: '報酬　8秒間 ×2 ・ 6,000 × 実効倍率',
    };
  }
  return {
    stage: '峡谷踏査完了', goal: '遺跡・蔓・鉄砲水を制覇',
    condition: '三つの試練を越えた。次の遠征でも谷は応える',
    reward: explorationState.rewarded
      ? `達成報酬　${explorationState.rewardPoints.toLocaleString()}点（固定）`
      : `達成報酬　${EXPEDITION_COMPLETE_SCORE.toLocaleString()}点（固定）`,
  };
};

const syncExplorationHud = (advanced = false) => {
  if (!ui.explorationPanel) return;
  const { stage, goal, condition, reward } = explorationHudContent();
  ui.explorationCount.textContent = `${explorationState.stage} / 3`;
  ui.explorationStage.textContent = stage;
  ui.explorationGoal.textContent = goal;
  ui.explorationCondition.textContent = condition;
  ui.explorationReward.textContent = reward;
  ui.explorationPanel.classList.remove('stage-0', 'stage-1', 'stage-2', 'stage-3', 'complete');
  ui.explorationPanel.classList.add(`stage-${explorationState.stage}`);
  ui.explorationPanel.classList.toggle('complete', explorationState.stage === 3);
  ui.explorationPanel.classList.toggle('rewarded', explorationState.rewarded);
  ui.explorationPanel.querySelectorAll('.exploration-steps i').forEach((step, index) => {
    step.classList.toggle('done', index < explorationState.stage);
  });
  if (!advanced) return;
  ui.explorationPanel.classList.remove('advanced');
  void ui.explorationPanel.offsetWidth;
  ui.explorationPanel.classList.add('advanced');
  clearTimeout(explorationAdvanceTimer);
  explorationAdvanceTimer = setTimeout(() => ui.explorationPanel.classList.remove('advanced'), 900);
};

// 判定順は必ず IDOL → ROPE BRIDGE → TORRENT。後段を先に達成していても、
// 前段を越えるまでは踏査を進めず、三つの達成事実がそろったときだけ完了にする。
const explorationStageFromSources = () => {
  if (idolState.cycles < 1) return 0;
  if (!bridgeState.expeditionSaved) return 1;
  if (torrentState.floods < 1) return 2;
  return 3;
};

const awardExplorationCompletion = () => {
  if (explorationState.stage !== 3 || explorationState.rewarded) return false;
  explorationState.rewarded = true;
  explorationState.rewardPoints = EXPEDITION_COMPLETE_SCORE;
  explorationState.rewardedAt = gameTime;
  verificationState.explorationRewards += 1;
  recordVerification('exploration-reward', { points: EXPEDITION_COMPLETE_SCORE });
  addScore(explorationState.rewardPoints, false);
  announce(`CANYON EXPEDITION +${explorationState.rewardPoints.toLocaleString()}`);
  tone(392, 0.42, 'triangle', 0.055, 3.2);
  tone(587, 0.68, 'sine', 0.045, 2.3);
  noise(0.3, 0.035, 1700);
  shakeView(2.1);
  return true;
};

const syncExplorationProgress = () => {
  const stage = explorationStageFromSources();
  const advanced = stage > explorationState.stage;
  if (advanced) {
    explorationState.stage = stage;
    explorationState.advancedAt = gameTime;
  }
  const rewarded = awardExplorationCompletion();
  if (advanced || rewarded) syncExplorationHud(true);
  return advanced || rewarded;
};

// 球の入れ替えでは探索を戻さない。新規ゲーム開始時だけ、既存ギミックの full reset と
// 同じ境界で初期化する。
const resetExploration = () => {
  explorationState.stage = 0;
  explorationState.advancedAt = -1;
  explorationState.rewarded = false;
  explorationState.rewardPoints = 0;
  explorationState.rewardedAt = -1;
  clearTimeout(explorationAdvanceTimer);
  explorationAdvanceTimer = 0;
  if (ui.explorationPanel) ui.explorationPanel.classList.remove('advanced');
  syncExplorationHud();
};

let torrentFlow = null;         // 3D の水流メッシュ
let torrentFlowMat = null;      // 同上の材質。透過で出し入れする
let torrentFlowMap = null;      // 同上のテクスチャ。offset を送って流れを出す
let torrentFlowBaseY = null;    // 各頂点の基準ワールド y（波はここからの相対で動かす）
let torrentFlowWave = null;     // 各頂点の波の位相（盤座標から作る）

const syncTorrentHud = () => {
  const percent = Math.round(torrentState.level);
  if (ui.torrentBar) ui.torrentBar.style.width = `${(torrentState.level / TORRENT_MAX) * 100}%`;
  if (ui.torrentValue) {
    ui.torrentValue.textContent = torrentState.flood
      ? `FLASH FLOOD ${torrentState.timer.toFixed(1)}s`
      : `${percent}%`;
  }
  if (ui.torrentTrack) ui.torrentTrack.classList.toggle('flood', torrentState.flood);
};

const syncComboHud = () => {
  if (!ui.combo) return;
  ui.combo.textContent = torrentState.combo > 1
    ? `CANYON CHAIN ${torrentState.combo} // ×${scoreMultiplier()}`
    : '';
  ui.combo.classList.toggle('active', torrentState.combo > 1);
};

// 鉄砲水へ移る。増水率は上限に張り付かせたまま、残り時間で戻りを測る。
const startFlood = () => {
  torrentState.level = TORRENT_MAX;
  torrentState.flood = true;
  torrentState.timer = FLOOD_SPAN;
  torrentState.floods += 1;
  verificationState.floodStarts += 1;
  recordVerification('flood-start', { number: torrentState.floods });
  torrentState.flash = 1;
  floodFactor = FLOOD_FACTOR;
  addScore(FLOOD_SCORE);   // 倍率を上げてから加点する
  syncTorrentHud();
  syncComboHud();
  announce('FLASH FLOOD');
  tone(60, 1.1, 'sawtooth', 0.07, 3.6);
  tone(210, 0.8, 'triangle', 0.04, 0.35);
  noise(0.9, 0.05, 420);
  shakeView(2.3);
  syncExplorationProgress();
};

// 鉄砲水の終わり。増水率は 0 へ戻し、次の 100% までまた溜め直させる。
const endFlood = (quiet = false) => {
  const wasFlood = torrentState.flood;
  torrentState.flood = false;
  torrentState.timer = 0;
  torrentState.level = 0;
  floodFactor = 1;
  updateHud();
  syncTorrentHud();
  syncComboHud();
  if (wasFlood && !quiet) {
    announce('THE WATER RECEDES');
    tone(150, 0.5, 'sine', 0.03, 0.4);
    noise(0.4, 0.02, 300);
  }
};

// 連鎖だけ切る。球を失っても谷の水位は変わらないが、打ち続けた流れは切れる。
const resetCombo = () => {
  torrentState.combo = 0;
  torrentState.comboAt = -9;
  syncComboHud();
};

// 増水率ごと初期化する。鉄砲水は残り時間で終わるのが常道なので、
// ここを呼ぶのはゲーム開始とゲームオーバーだけにする。
// full=true でゲーム全体の初期化。
const resetTorrent = (full = false) => {
  endFlood(true);
  resetCombo();
  if (full) {
    torrentState.floods = 0;
    torrentState.bridgeRescues = 0;
    torrentState.flow = 0;
    torrentState.flash = 0;
  }
  syncTorrentHud();
  syncComboHud();
};

// ギミックへの命中をまとめて受ける入口。連鎖を伸ばし、増水率を上げる。
// 鉄砲水の最中は上限に張り付いているので、増水はせず連鎖だけ伸ばす。
const registerHit = (gain) => {
  if (mode !== 'play') return;
  torrentState.combo += 1;
  torrentState.comboAt = gameTime;
  syncComboHud();
  if (torrentState.flood || gain <= 0) return;

  const boost = 1 + Math.min(torrentState.combo, COMBO_BOOST_MAX) * COMBO_BOOST;
  torrentState.level = Math.min(TORRENT_MAX, torrentState.level + gain * boost);
  if (torrentState.level >= TORRENT_MAX) startFlood();
};

// 濁流が球を押す力。鉄砲水の最中だけ、手前(+y)への加速と左右の揺さぶりを足す。
const applyFlood = (ball, dt) => {
  if (!torrentState.flood) return;
  ball.vy += FLOOD_PUSH * dt;
  ball.vx += Math.sin(ball.y * 0.011 + gameTime * 2.3) * FLOOD_SWAY * dt;
};

// 水流メッシュ。盤を覆う格子を地表からわずかに浮かせ、
// 頂点の波とテクスチャ送りで奥から手前への流れを出す。
const FLOW_X0 = -60;
const FLOW_X1 = BOARD_W + 60;
const FLOW_Y0 = 40;
const FLOW_Y1 = 1140;
const FLOW_SEG_X = 22;
const FLOW_SEG_Y = 38;
// 水面は地表を薄く覆うだけにする。ここを厚くすると石柱もフリッパーも水没し、
// 鉄砲水の間だけ盤が読めなくなる。
const FLOW_LIFT = 0.15;
const FLOW_RISE = 0.55;   // 鉄砲水で持ち上がる水位

const buildTorrentFlow = () => {
  const cols = FLOW_SEG_X + 1;
  const rows = FLOW_SEG_Y + 1;
  const positions = new Float32Array(cols * rows * 3);
  const uvs = new Float32Array(cols * rows * 2);
  const baseY = new Float32Array(cols * rows);
  const wave = new Float32Array(cols * rows);
  const v = new THREE.Vector3();

  for (let r = 0; r < rows; r += 1) {
    const ty = r / FLOW_SEG_Y;
    const by = FLOW_Y0 + (FLOW_Y1 - FLOW_Y0) * ty;
    for (let c = 0; c < cols; c += 1) {
      const tx = c / FLOW_SEG_X;
      const bx = FLOW_X0 + (FLOW_X1 - FLOW_X0) * tx;
      const i = r * cols + c;
      boardToWorld(bx, by, FLOW_LIFT, v);
      positions[i * 3] = v.x;
      positions[i * 3 + 1] = v.y;
      positions[i * 3 + 2] = v.z;
      baseY[i] = v.y;
      // v が大きいほど手前。テクスチャの送りもこの向きに合わせる。
      uvs[i * 2] = tx;
      uvs[i * 2 + 1] = ty;
      wave[i] = by * 0.021 + bx * 0.006;
    }
  }

  const indices = [];
  for (let r = 0; r < FLOW_SEG_Y; r += 1) {
    for (let c = 0; c < FLOW_SEG_X; c += 1) {
      const a = r * cols + c;
      const b = a + 1;
      const d = a + cols;
      const e = d + 1;
      indices.push(a, d, b, b, d, e);
    }
  }

  const geo = keep(new THREE.BufferGeometry());
  geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geo.setAttribute('uv', new THREE.BufferAttribute(uvs, 2));
  geo.setIndex(indices);
  geo.computeVertexNormals();

  torrentFlowMap = createTorrentTexture();
  torrentFlowMat = keep(new THREE.MeshStandardMaterial({
    map: torrentFlowMap,
    color: 0x9fe4f2,
    emissive: 0x1c6c82,
    emissiveIntensity: 0.5,
    roughness: 0.22,
    metalness: 0.16,
    transparent: true,
    opacity: 0,
    // 地表のすぐ上を覆うので、深度書き込みを切って岩肌を消さないようにする。
    depthWrite: false,
    side: THREE.DoubleSide,
  }));

  const mesh = new THREE.Mesh(geo, torrentFlowMat);
  mesh.renderOrder = 2;
  mesh.visible = false;
  mesh.receiveShadow = false;
  scene.add(mesh);

  torrentFlow = mesh;
  torrentFlowBaseY = baseY;
  torrentFlowWave = wave;
  return mesh;
};

// 水流の高さ・透過・テクスチャ送りと、画面全体の閃光。
// torrentState だけを見て毎フレーム追従させる。HUD もここで送る。
const updateTorrentVisuals = (dt, time) => {
  syncTorrentHud();

  // 鉄砲水の最中は水面を出し切る。それ以外は増水率ぶんだけ薄く這わせ、
  // 100% が近づいていることを盤の上でも見せる。
  const target = torrentState.flood ? 1 : (torrentState.level / TORRENT_MAX) * 0.22;
  torrentState.flow += (target - torrentState.flow) * Math.min(1, dt * (target > torrentState.flow ? 5.5 : 2.2));
  torrentState.flash = Math.max(0, torrentState.flash - dt * 1.9);

  if (ui.flash) ui.flash.style.opacity = String((torrentState.flash * 0.8).toFixed(3));

  if (!torrentFlow) return;
  const flow = torrentState.flow;
  torrentFlow.visible = flow > 0.012;
  if (!torrentFlow.visible) return;

  // 透かしておく。濁流の下でも岩肌と盤のパーツが読めるようにする。
  torrentFlowMat.opacity = Math.min(0.62, flow * 0.68);
  torrentFlowMat.emissiveIntensity = 0.35 + flow * 0.8;
  // offset.y を減らすと模様は uv の大きい側＝手前へ動く。奥から手前へ流れて見える。
  torrentFlowMap.offset.y -= dt * (0.28 + flow * 1.15);
  torrentFlowMap.offset.x = Math.sin(time * 0.6) * 0.02;

  // 水位と波。増水率が低いうちは地表すれすれで、鉄砲水で一気に持ち上がる。
  const pos = torrentFlow.geometry.attributes.position;
  const array = pos.array;
  const lift = flow * FLOW_RISE;
  const amp = 0.08 + flow * 0.2;
  for (let i = 0; i < torrentFlowBaseY.length; i += 1) {
    array[i * 3 + 1] = torrentFlowBaseY[i] + lift
      + Math.sin(torrentFlowWave[i] - time * 3.4) * amp
      + Math.sin(torrentFlowWave[i] * 2.3 - time * 5.1) * amp * 0.35;
  }
  pos.needsUpdate = true;
};

/* ============================================================
   斜面の重力と球の積分
   ============================================================ */

// 地形の勾配から加速度を作る。奥ほど高い斜面なので基本は手前(+y)へ転がり、
// 岩肌の起伏で左右に揺さぶられ、谷底の縁では落差ぶんだけ一気に加速する。
const applySlope = (ball, dt) => {
  const gx = (terrainHeight(ball.x + GRAD_STEP, ball.y) - terrainHeight(ball.x - GRAD_STEP, ball.y)) / (2 * GRAD_STEP);
  const gy = (terrainHeight(ball.x, ball.y + GRAD_STEP) - terrainHeight(ball.x, ball.y - GRAD_STEP)) / (2 * GRAD_STEP);
  ball.vx += -SLOPE_GAIN * gx * SWAY_GAIN * dt;
  ball.vy += clamp(GRAVITY - SLOPE_GAIN * gy, 0, FALL_ACCEL_MAX) * dt;
};

// フリッパーとの衝突。面の角度で法線が決まり、角速度ぶんの面の速度を球へ渡す。
const updateFlipperHit = (ball, flipper) => {
  const ex = flipper.x + Math.cos(flipper.angle) * flipper.length;
  const ey = flipper.y + Math.sin(flipper.angle) * flipper.length;
  if (!segmentHit(ball, flipper.x, flipper.y, ex, ey, FLIPPER_R)) return;

  const { nx, ny } = hitNormal;
  // 接触点の腕。回転の接線速度は根本ほど遅く、先端ほど速い。
  const rx = ball.x - flipper.x;
  const ry = ball.y - flipper.y;
  let svx = -flipper.omega * ry;
  let svy = flipper.omega * rx;
  const surface = Math.hypot(svx, svy);
  if (surface > SURFACE_CAP) {
    svx *= SURFACE_CAP / surface;
    svy *= SURFACE_CAP / surface;
  }

  // 面から見た相対速度で反発させ、最後に面の速度を戻す。
  const rvx = ball.vx - svx;
  const rvy = ball.vy - svy;
  const along = rvx * nx + rvy * ny;
  if (along >= 0) return;
  // 振り上げ中はよく弾き、静止中は受け止める。転がってきた球が跳ね回らない。
  const bounce = Math.abs(flipper.omega) > 0.5 ? 0.78 : 0.34;
  ball.vx = rvx - (1 + bounce) * along * nx + svx;
  ball.vy = rvy - (1 + bounce) * along * ny + svy;
  capBallSpeed(ball);
  rockHit(Math.min(1, (-along + surface * 0.35) / 900));
  if (surface > 200) tone(150 + Math.random() * 90, 0.1, 'square', 0.028, 1.7);
};

const updateBall = (ball, dt) => {
  if (!ball.alive) return;
  if (ball.draining) {
    // 即座に消すと最大接近が1フレームで終わる。排出口の縁でわずかに静止させ、
    // 岩球がレンズを覆ってから残機処理へ進む。物理衝突はこの間だけ止める。
    const progress = clamp((gameTime - ball.drainAt) / DRAIN_TERROR_SPAN, 0, 1);
    ball.y = DRAIN_Y - 2 + progress * 3;
    ball.vx = 0;
    ball.vy = 0;
    if (progress >= 1) ball.alive = false;
    return;
  }
  if (ball.lane) {
    // 発射待機。盤へ進入するまでの経路は空けてあるので、ここから真上へ打ち出せる。
    ball.x = LANE_X;
    ball.y = LANE_Y;
    ball.px = ball.x;
    ball.py = ball.y;
    return;
  }

  applySlope(ball, dt);
  applyFlood(ball, dt);

  // 発射峰の途中だけは、岩肌の細かな勾配に負けて右側へ戻らないよう左向きの
  // 最低速度を保つ。盤面へ入った後は通常の地形・衝突物理だけへ完全に戻す。
  if (ball.launchGuide) {
    ball.vx = Math.min(ball.vx, -LAUNCH_MIN_SPEED);
    ball.vy = clamp(ball.vy, -120, 160);
  }
  capBallSpeed(ball);

  ball.x += ball.vx * dt;
  ball.y += ball.vy * dt;
  // 岩肌の転がり抵抗。dt に依存しないよう指数減衰で掛ける。
  ball.vx *= Math.pow(0.9975, dt * 60);
  ball.vy *= Math.pow(0.9986, dt * 60);

  for (let i = 0; i < walls.length; i += 1) {
    const wall = walls[i];
    if (!segmentHit(ball, wall.a[0], wall.a[1], wall.b[0], wall.b[1], 0)) continue;
    const power = reflect(ball, hitNormal.nx, hitNormal.ny, wall.bounce == null ? WALL_BOUNCE : wall.bounce);
    rockHit(power * 0.6);
    // 岩壁を強く叩くほど谷が増水する。サブステップで同じ接触を何度も拾うので、
    // 石柱の得点と同じく時間で間引く。
    if (power >= TORRENT_WALL_MIN && gameTime - ball.wallAt >= TORRENT_WALL_COOLDOWN) {
      ball.wallAt = gameTime;
      registerHit(TORRENT_WALL_GAIN + power * TORRENT_WALL_POWER);
    }
    // 漏斗の継ぎ目で 2 本の岩壁を同じサブステップに反射すると、速度が不自然に
    // 増幅する。最初に解決した接触だけを採用し、次の積分で残りを判定する。
    break;
  }
  for (let i = 0; i < idolState.targets.length; i += 1) updateIdolTarget(ball, idolState.targets[i]);
  updateBridgeHit(ball);
  for (let i = 0; i < flippers.length; i += 1) updateFlipperHit(ball, flippers[i]);

  // 投入峰から盤面へ抜けた瞬間だけ、カメラと演出を盤面状態へ切り替える。
  if (ball.launchGuide && ball.x <= LAUNCH_ENTRY_X) {
    ball.launchGuide = false;
    ball.entered = true;
    verificationState.entries += 1;
    recordVerification('boulder-entered', { echo: ball.echo });
    announce('INTO THE CANYON');
    tone(210, 0.22, 'triangle', 0.035, 2.2);
  }

  // 左右は人工的な盤端で落とさず、盤外の地形勾配へ球を流す。
  // 極端に遠くへ抜けた場合だけ安全弁として落球扱いにする。
  if (ball.y - ball.r > DRAIN_Y || ball.x < -420 || ball.x > BOARD_W + 420) {
    ball.draining = true;
    ball.drainAt = gameTime;
    // サイドアウトでも最後は視界の内側へ寄せ、失敗演出を必ず見せる。
    ball.x = clamp(ball.x, 90, 630);
  }
};

/* ============================================================
   ラウンド進行
   ============================================================ */

const makeBall = (x = LANE_X, y = LANE_Y, lane = true, vx = 0, vy = 0, echo = false) => ({
  x, y, px: x, py: y, vx, vy, r: BALL_R, lane, entered: !lane, alive: true, born: gameTime,
  launchGuide: false,
  draining: false, drainAt: -1,
  echo,
  bridgeAt: -9,   // 吊り橋で受け止めた最後の時刻。サブステップの二重加点を防ぐ
  wallAt: -9,     // 岩壁で増水を数えた最後の時刻。同上
});

// IDOL 完成時の報酬。追加球も通常球と同じ balls 配列へ入れることで、物理、得点、
// 排出、残機・ゲームオーバー判定を特別扱いせずに共有する。boulderPool の数を上限に
// するため、描画用メッシュが足りない球を生成することもない。
const releaseEchoBoulders = (sourceBall) => {
  if (!sourceBall || idolState.echoCycle === idolState.cycles) return 0;
  idolState.echoCycle = idolState.cycles;
  const maxBalls = Math.min(ECHO_BOULDER_TOTAL_MAX, boulderPool.length);
  const available = Math.max(0, maxBalls - balls.length);
  const echoCount = Math.min(available, ECHO_BOULDER_SPREAD.length);

  for (let i = 0; i < echoCount; i += 1) {
    const spread = ECHO_BOULDER_SPREAD[i];
    balls.push(makeBall(
      clamp(sourceBall.x + spread.x, BALL_R, BOARD_W - BALL_R),
      sourceBall.y + spread.y,
      false,
      sourceBall.vx * 0.35 + spread.vx,
      Math.max(sourceBall.vy * 0.35, 0) + spread.vy,
      true,
    ));
  }
  idolState.echoBoulders = echoCount;
  return echoCount;
};

const resetRound = () => {
  balls = [makeBall()];
  charging = false;
  charge = 0;
  flippers.forEach((flipper) => { flipper.angle = flipper.rest; flipper.omega = 0; });
  // 点灯は球をまたいで残す。1 球で 4 基そろえるのは実質不可能で、
  // 毎球リセットすると倍率が一度も上がらない。
  // 起立させ切った後だけ石柱を伏せ直し、次の段の倍率を狙わせる。
  if (idolState.awake) resetIdol();
  // 縄の耐久は球をまたいで残す。張り直しの状態だけ戻す。
  resetBridge();
  // 増水率と鉄砲水は球をまたいで残す。谷の水位は球の生死とは関わりなく、
  // 鉄砲水は残り時間で終わらせる。球ごとに戻すのは打ち続けた連鎖だけ。
  resetCombo();
  ui.launch.classList.add('visible');
};

const launchBall = (forcedCharge = null) => {
  if (mode !== 'play') return false;
  const ball = balls.find((item) => item.lane && item.alive);
  if (!ball) return false;
  const power = forcedCharge == null ? charge : clamp(forcedCharge, 0, 1);
  ball.lane = false;
  ball.entered = false;
  ball.launchGuide = true;
  // 砲のように打ち上げず、右側岩山の留め具を外して左へ転がす。
  // power は最初のひと押しだけに使い、その後は地形勾配へ任せる。
  ball.vx = -175 - power * 125;
  ball.vy = 18 + power * 42;
  recordVerification('boulder-launched', { power: Number(power.toFixed(3)) });
  charging = false;
  charge = 0;
  ui.launch.classList.remove('visible');
  announce('ROCK RELEASED');
  tone(72, 0.24, 'sawtooth', 0.05, 2.8);
  noise(0.3, 0.045, 210);
  shakeView(0.65);
  return true;
};

const gameOver = () => {
  mode = 'over';
  ui.final.textContent = `FINAL SCORE ${String(score).padStart(7, '0')}`;
  ui.gameover.classList.add('visible');
  ui.launch.classList.remove('visible');
  bridgeState.timer = 0;
  syncBridgeHud();
  resetTorrent();
  syncActionControls();
  announce('SWALLOWED BY THE RAVINE');
  tone(96, 0.9, 'sawtooth', 0.07, 0.2);
  noise(0.7, 0.045, 180);
  shakeView(2.2);
  if (demoMode) demoRestartAt = gameTime + 2.4;
};

const drain = () => {
  lives -= 1;
  updateHud();
  tone(130, 0.4, 'sawtooth', 0.055, 0.22);
  noise(0.35, 0.03, 240);
  shakeView(1.3);
  if (lives <= 0) {
    gameOver();
    return;
  }
  announce('LOST TO THE VALLEY');
  resetRound();
};

const startGame = (useDemo = false) => {
  ensureAudio();
  demoMode = useDemo;
  mode = 'play';
  score = 0;
  lives = 3;
  multiplier = 1;
  gameTime = 0;
  demoRestartAt = 0;
  resetVerification();
  recordVerification(useDemo ? 'demo-start' : 'game-start');
  releaseAllKeys();
  ui.title.classList.remove('visible');
  ui.pause.classList.remove('visible');
  ui.gameover.classList.remove('visible');
  resetIdol(true);
  resetBridge(true);
  resetTorrent(true);
  resetExploration();
  resetRound();
  updateHud();
  syncActionControls();
  announce(demoMode ? 'AUTOPILOT ONLINE' : 'THE CANYON AWAKES');
  tone(110, 0.35, 'sawtooth', 0.06, 4);
};

const togglePause = (forceResume = false) => {
  if (mode === 'play') {
    mode = 'paused';
    ui.pause.classList.add('visible');
    keys.left = false;
    keys.right = false;
    charging = false;
    dualFlipLatched = false;
    syncBridgeHud();
  } else if (mode === 'paused' || forceResume) {
    mode = 'play';
    ui.pause.classList.remove('visible');
    syncBridgeHud();
  }
  syncActionControls();
};

/* ============================================================
   毎フレームの進行
   ============================================================ */

const updateGame = (dt) => {
  if (mode === 'over') {
    // ゲームオーバー中も時計だけは進める。デモの自動再開がここで測られる。
    gameTime += dt;
    if (demoMode && demoRestartAt > 0 && gameTime >= demoRestartAt) startGame(true);
    return;
  }
  if (mode !== 'play') return;
  gameTime += dt;
  if (charging) charge = clamp(charge + dt * 0.72, 0, 1);

  // 無操作デモ。通常プレイと同じ keys / launchBall() を使い、経路を分けない。
  if (demoMode) {
    const laneBall = balls.find((ball) => ball.alive && ball.lane);
    if (laneBall && gameTime - laneBall.born > 0.7) launchBall(0.85);
    const danger = balls.filter((ball) => ball.alive && !ball.lane && ball.y > 660);
    const pulse = Math.sin(gameTime * 11) > -0.15;
    keys.left = pulse && danger.some((ball) => ball.x < 390);
    keys.right = pulse && danger.some((ball) => ball.x > 330);
  }

  // 左右フリッパーの同時押しで吊り橋を巻き上げる。押しっぱなしで連続発動しないよう、
  // 立ち上がりだけをラッチで拾う（Xピンボールsol の dualFlipLatched と同じ方式）。
  if (keys.left && keys.right) {
    if (!dualFlipLatched) {
      dualFlipLatched = true;
      haulBridge();
    }
  } else {
    dualFlipLatched = false;
  }

  refreshBridgeWindow();

  // 張っている時間を減らす。切れた瞬間に HUD の文言を戻す。
  if (bridgeState.timer > 0) {
    bridgeState.timer = Math.max(0, bridgeState.timer - dt);
    if (bridgeState.timer === 0) {
      if (bridgeState.status === 'armed' || bridgeState.status === 'saved' || bridgeState.status === 'flood-save') {
        bridgeState.status = bridgeState.uses <= 0 ? 'snapped' : (bridgeState.status === 'armed' ? 'missed' : 'ready');
        if (bridgeState.status === 'snapped' || bridgeState.status === 'missed') {
          announce(bridgeState.status === 'snapped' ? 'THE LAST ROPE SNAPS' : 'THE VINES FALL BACK');
        }
      }
      syncBridgeHud();
    }
  }

  // 鉄砲水の残り時間。切れたら通常状態へ戻し、増水率を 0 から溜め直させる。
  if (torrentState.flood) {
    torrentState.timer = Math.max(0, torrentState.timer - dt);
    if (torrentState.timer === 0) endFlood();
  } else if (torrentState.level > 0) {
    // 攻め続けないと谷の水は引く。連鎖が切れると 100% には届かない。
    torrentState.level = Math.max(0, torrentState.level - TORRENT_DECAY * dt);
  }

  // 連続命中。間隔が空いたら連鎖を切り、#combo の表示も消す。
  if (torrentState.combo > 0 && gameTime - torrentState.comboAt > COMBO_SPAN) {
    torrentState.combo = 0;
    syncComboHud();
  }

  // フリッパーは角速度を一定に保って動かす。lerp だと 1 フレーム目だけ
  // 角速度が跳ね上がり、球への伝達が dt 依存になってしまう。
  flippers.forEach((flipper) => {
    const target = keys[flipper.side] ? flipper.active : flipper.rest;
    const step = clamp(target - flipper.angle, -FLIP_SPEED * dt, FLIP_SPEED * dt);
    flipper.omega = dt > 0 ? step / dt : 0;
    flipper.angle += step;
  });

  // 高速時の貫通を防ぐため、固定回数ではなく 1 ステップの移動量から分割する。
  const fastest = balls.reduce((max, ball) => Math.max(max, Math.hypot(ball.vx, ball.vy)), 0);
  const steps = clamp(
    Math.ceil(Math.max(fastest, MAX_SPEED * 0.55) * dt / PHYSICS_TRAVEL_PER_STEP),
    PHYSICS_MIN_STEPS,
    PHYSICS_MAX_STEPS,
  );
  for (let i = 0; i < steps; i += 1) {
    for (let b = 0; b < balls.length; b += 1) updateBall(balls[b], dt / steps);
  }
  balls = balls.filter((ball) => ball.alive);
  if (balls.length === 0) drain();
};

/* ============================================================
   入力（キーボード / 画面ボタン / ポインターを keys へ集約）
   ============================================================ */

let inputAbort = null;

const releaseAllKeys = () => {
  keySources.left.clear();
  keySources.right.clear();
  keys.left = false;
  keys.right = false;
  pointers.clear();
  charging = false;
  dualFlipLatched = false;
};

const keyInput = (event, pressed) => {
  if (event.repeat) return;
  if (pressed && (event.key === 'p' || event.key === 'P' || event.key === 'Escape') && (mode === 'play' || mode === 'paused')) {
    togglePause();
    return;
  }
  if (pressed && event.key === 'Enter' && (mode === 'title' || mode === 'over')) {
    startGame(false);
    return;
  }
  if (mode !== 'play' || demoMode) return;
  if (event.key === 'ArrowLeft' || event.key === 'a' || event.key === 'A') {
    setFlipperInput('left', 'keyboard-left', pressed);
    event.preventDefault();
  }
  if (event.key === 'ArrowRight' || event.key === 'd' || event.key === 'D') {
    setFlipperInput('right', 'keyboard-right', pressed);
    event.preventDefault();
  }
  if (event.key === ' ' || event.key === 'ArrowDown') {
    if (balls.some((ball) => ball.lane)) {
      if (pressed) { charging = true; charge = 0; } else launchBall();
    }
    event.preventDefault();
  }
};

const releasePointer = (event) => {
  const input = pointers.get(event.pointerId);
  if (!input) return;
  pointers.delete(event.pointerId);
  // タップでも次の描画フレームで最低一度は押下状態を通す。
  // これにより短い画面ボタン操作もキーボードと同じ物理入力になる。
  requestAnimationFrame(() => setFlipperInput(input.side, input.source, false));
};

const bindInput = () => {
  inputAbort = new AbortController();
  const opt = { signal: inputAbort.signal };

  window.addEventListener('keydown', (event) => keyInput(event, true), opt);
  window.addEventListener('keyup', (event) => keyInput(event, false), opt);
  window.addEventListener('blur', releaseAllKeys, opt);

  // 盤面のタップ / ドラッグ。画面の左右半分でフリッパーを分ける。
  canvas.addEventListener('pointerdown', (event) => {
    if (mode !== 'play' || demoMode) return;
    ensureAudio();
    const side = event.clientX < window.innerWidth / 2 ? 'left' : 'right';
    const source = `canvas:${event.pointerId}`;
    setFlipperInput(side, source, true);
    pointers.set(event.pointerId, { side, source });
    canvas.setPointerCapture(event.pointerId);
  }, opt);
  canvas.addEventListener('pointerup', releasePointer, opt);
  canvas.addEventListener('pointercancel', releasePointer, opt);

  // タッチ端末では、盤面を覆う HUD の下でも左右を確実に選べる明示ボタンを使う。
  // クリック（キーボード起動）は短い押下として同じ keys 状態へ流す。
  const bindFlipperButton = (button, side) => {
    let lastPointerAt = 0;
    const pulse = () => {
      const source = `button-key-${side}`;
      setFlipperInput(side, source, true);
      requestAnimationFrame(() => setFlipperInput(side, source, false));
    };
    button.addEventListener('pointerdown', (event) => {
      if (mode !== 'play' || demoMode) return;
      event.preventDefault();
      event.stopPropagation();
      ensureAudio();
      lastPointerAt = performance.now();
      const source = `button-${side}:${event.pointerId}`;
      setFlipperInput(side, source, true);
      pointers.set(event.pointerId, { side, source });
      button.setPointerCapture(event.pointerId);
    }, opt);
    const release = (event) => {
      event.preventDefault();
      event.stopPropagation();
      releasePointer(event);
    };
    button.addEventListener('pointerup', release, opt);
    button.addEventListener('pointercancel', release, opt);
    button.addEventListener('click', () => {
      if (mode !== 'play' || demoMode || performance.now() - lastPointerAt < 550) return;
      pulse();
    }, opt);
  };
  bindFlipperButton(ui.flipperLeft, 'left');
  bindFlipperButton(ui.flipperRight, 'right');

  // 発射ボタンは押している間ためて、離した強さで打ち出す。
  ui.launch.addEventListener('pointerdown', (event) => {
    event.preventDefault();
    event.stopPropagation();
    ensureAudio();
    charging = true;
    charge = 0;
    launchPointerId = event.pointerId;
    ui.launch.setPointerCapture(event.pointerId);
  }, opt);
  ui.launch.addEventListener('pointerup', (event) => {
    if (launchPointerId !== event.pointerId) return;
    event.preventDefault();
    event.stopPropagation();
    launchPointerId = null;
    launchBall();
  }, opt);
  ui.launch.addEventListener('pointercancel', (event) => {
    if (launchPointerId !== event.pointerId) return;
    launchPointerId = null;
    charging = false;
    charge = 0;
  }, opt);
  // ポインターを持たない環境（キーボード操作 / 自動テスト）向けの保険。
  ui.launch.addEventListener('click', () => { if (balls.some((ball) => ball.lane)) launchBall(0.5); }, opt);

  // 吊り橋ボタン。専用の経路は作らず、左右フリッパーの同時押しとして keys へ流す。
  // 巻き上げの判定は updateGame のラッチ 1 箇所だけに残す。
  let bridgePointerAt = 0;
  const bridgePress = (down, source = 'bridge-button') => {
    if (mode !== 'play' || demoMode) return;
    setFlipperInput('left', source, down);
    setFlipperInput('right', source, down);
  };
  ui.bridge.addEventListener('pointerdown', (event) => {
    event.preventDefault();
    event.stopPropagation();
    ensureAudio();
    bridgePointerAt = performance.now();
    bridgePointerId = event.pointerId;
    bridgePress(true, `bridge:${event.pointerId}`);
    ui.bridge.setPointerCapture(event.pointerId);
  }, opt);
  const releaseBridgePointer = (event) => {
    if (bridgePointerId !== event.pointerId) return;
    event.preventDefault();
    event.stopPropagation();
    bridgePointerId = null;
    bridgePress(false, `bridge:${event.pointerId}`);
  };
  ui.bridge.addEventListener('pointerup', releaseBridgePointer, opt);
  ui.bridge.addEventListener('pointercancel', releaseBridgePointer, opt);
  // キーボードでボタンを起動した場合も、物理入力と同じ keys の同時押しへ流す。
  ui.bridge.addEventListener('click', () => {
    if (mode !== 'play' || demoMode || performance.now() - bridgePointerAt < 550) return;
    bridgePress(true, 'bridge-key');
    requestAnimationFrame(() => bridgePress(false, 'bridge-key'));
  }, opt);

  el('#start').addEventListener('click', () => startGame(false), opt);
  el('#demo-start').addEventListener('click', () => startGame(true), opt);
  el('#restart').addEventListener('click', () => startGame(false), opt);
  el('#resume').addEventListener('click', () => togglePause(true), opt);
  ui.pauseButton.addEventListener('click', () => {
    if (mode !== 'play' && mode !== 'paused') return;
    ensureAudio();
    togglePause();
  }, opt);
  ui.sound.addEventListener('click', () => {
    muted = !muted;
    ui.sound.textContent = muted ? 'SOUND OFF' : 'SOUND ON';
    syncActionControls();
    if (!muted) tone(420, 0.08, 'square', 0.025, 1.4);
  }, opt);
};

/* ============================================================
   盤面の 3D パーツ（岩の縁石とフリッパー）
   ============================================================ */

// 2D の衝突線分を岩の縁石として見せる。地形が傾いているので、
// 一本の長い箱ではなく短い岩塊を地表に沿って並べる。
const buildRails = () => {
  const mat = keep(new THREE.MeshStandardMaterial({
    color: 0x7a6446, roughness: 0.95, metalness: 0.03, flatShading: true,
  }));
  const geo = keep(new THREE.BoxGeometry(1, 1, 1));
  const group = new THREE.Group();
  const v = new THREE.Vector3();

  walls.forEach(({ a, b }) => {
    const dx = b[0] - a[0];
    const dy = b[1] - a[1];
    const length = Math.hypot(dx, dy);
    const chunks = Math.max(2, Math.round(length / 46));
    const angle = Math.atan2(dy, dx);
    for (let i = 0; i < chunks; i += 1) {
      const t = (i + 0.5) / chunks;
      const bx = a[0] + dx * t;
      const by = a[1] + dy * t;
      // 低いアクション視点でもガードの連なりが読める高さにする。
      const h = 3.4 + Math.sin(bx * 0.031 + by * 0.019) * 0.7 + Math.sin(by * 0.047) * 0.35;
      const block = new THREE.Mesh(geo, mat);
      boardToWorld(bx, by, h * 0.5 - 0.7, v);
      block.position.copy(v);
      block.rotation.y = -angle;
      block.scale.set((length / chunks) * SCALE * 1.12, h, 1.15);
      block.castShadow = true;
      block.receiveShadow = true;
      group.add(block);
    }
  });
  scene.add(group);
  return group;
};

// 遺跡ゲートの石柱。当たり半径 IDOL_R をそのまま柱の太さにして、
// 2D の判定と見た目がずれないようにする。発光は updateIdolVisuals が動かす。
const buildIdolGates = () => {
  const group = new THREE.Group();
  const v = new THREE.Vector3();
  const PILLAR_H = 5.4;
  const radius = IDOL_R * SCALE;

  idolState.targets.forEach((target) => {
    // 石柱は個別に発光させるので、材質も石柱ごとに持たせる。
    const pillarMat = keep(new THREE.MeshStandardMaterial({
      color: 0x9a855f, emissive: 0xff9c30, emissiveIntensity: 0.06,
      roughness: 0.88, metalness: 0.06, flatShading: true,
    }));
    const pillar = new THREE.Mesh(keep(new THREE.CylinderGeometry(radius * 0.82, radius, PILLAR_H, 8, 1)), pillarMat);
    // 斜面に立つので、中心を地表より少し沈めて足元を浮かせない。
    boardToWorld(target.x, target.y, PILLAR_H / 2 - 0.9, v);
    pillar.position.copy(v);
    pillar.castShadow = true;
    pillar.receiveShadow = true;
    group.add(pillar);

    // 柱頭の紋章環。点灯するとせり上がり、回りながら強く光る。
    const glyphMat = keep(new THREE.MeshStandardMaterial({
      color: 0x6d5732, emissive: 0xffc247, emissiveIntensity: 0.1,
      roughness: 0.42, metalness: 0.7,
    }));
    const glyph = new THREE.Mesh(keep(new THREE.TorusGeometry(radius * 0.82, radius * 0.2, 6, 12)), glyphMat);
    glyph.position.set(v.x, v.y + PILLAR_H / 2 + 0.5, v.z);
    glyph.rotation.x = Math.PI / 2;
    glyph.userData.baseY = glyph.position.y;
    group.add(glyph);

    target.pillar = pillar;
    target.glyph = glyph;
  });

  scene.add(group);
  return group;
};

// 蔓の吊り橋。踏板も縄も当たり判定と同じ bridgePoint() から並べ、
// 見た目と判定をずらさない。せり上がりと透過は updateBridgeVisuals が動かす。
// 両端の岩の杭だけは常設にして、橋が架かる位置を落ちる前から見せる。
const buildRopeBridge = () => {
  const group = new THREE.Group();
  const v = new THREE.Vector3();

  const plankMat = keep(new THREE.MeshStandardMaterial({
    color: 0x6d5030, roughness: 0.93, metalness: 0.03, flatShading: true,
    transparent: true, opacity: 0,
  }));
  const ropeMat = keep(new THREE.MeshStandardMaterial({
    color: 0x9a8046, emissive: 0x2f6d78, emissiveIntensity: 0.25,
    roughness: 0.72, metalness: 0.12, transparent: true, opacity: 0,
  }));
  bridgeDeckMats.push(plankMat, ropeMat);

  const boxGeo = keep(new THREE.BoxGeometry(1, 1, 1));

  // 踏板。橋に沿う向きを局所 +X に合わせるので rotation.y = -angle。
  const PLANKS = 22;
  for (let i = 0; i < PLANKS; i += 1) {
    const t = (i + 0.5) / PLANKS;
    const p = bridgePoint(t);
    const ahead = bridgePoint(Math.min(1, t + 0.02));
    const behind = bridgePoint(Math.max(0, t - 0.02));
    const plank = new THREE.Mesh(boxGeo, plankMat);
    boardToWorld(p.x, p.y, 0.35, v);
    plank.position.copy(v);
    plank.rotation.y = -Math.atan2(ahead.y - behind.y, ahead.x - behind.x);
    plank.scale.set(((BRIDGE_X1 - BRIDGE_X0) / PLANKS) * SCALE * 0.74, 0.22, BRIDGE_R * 2.6 * SCALE);
    plank.castShadow = true;
    group.add(plank);
  }

  // 左右の蔓。踏板の外側を通し、たわみに沿って短い棒でつなぐ。
  const ROPE_CHUNKS = 12;
  [-1, 1].forEach((side) => {
    for (let i = 0; i < ROPE_CHUNKS; i += 1) {
      const a = bridgePoint(i / ROPE_CHUNKS);
      const b = bridgePoint((i + 1) / ROPE_CHUNKS);
      const rope = new THREE.Mesh(boxGeo, ropeMat);
      boardToWorld((a.x + b.x) / 2, (a.y + b.y) / 2 + side * BRIDGE_R * 1.2, 0.95, v);
      rope.position.copy(v);
      rope.rotation.y = -Math.atan2(b.y - a.y, b.x - a.x);
      rope.scale.set(Math.hypot(b.x - a.x, b.y - a.y) * SCALE * 1.06, 0.17, 0.17);
      group.add(rope);
    }
  });

  group.visible = false;
  scene.add(group);
  bridgeGroup = group;

  // 常設の杭。せり上がりでは動かさないので、group とは別に置く。
  const postMat = keep(new THREE.MeshStandardMaterial({ color: 0x7d6949, roughness: 0.9, metalness: 0.05, flatShading: true }));
  const posts = new THREE.Group();
  [0, 1].forEach((end) => {
    const p = bridgePoint(end);
    const post = new THREE.Mesh(keep(new THREE.CylinderGeometry(0.34, 0.46, 3.2, 7)), postMat);
    boardToWorld(p.x, p.y, 0.9, v);
    post.position.copy(v);
    post.castShadow = true;
    posts.add(post);
  });
  scene.add(posts);
  return group;
};

// フリッパー。盤角 angle は +x から +y(谷側) へ測るので、
// 局所 +X をその向きへ合わせるには rotation.y = -angle にする。
const buildFlippers = () => {
  const stone = keep(new THREE.MeshStandardMaterial({ color: 0x9d8862, roughness: 0.76, metalness: 0.08, flatShading: true }));
  const band = keep(new THREE.MeshStandardMaterial({ color: 0xc79331, roughness: 0.34, metalness: 0.82, emissive: 0x2e1c05, emissiveIntensity: 0.7 }));
  const group = new THREE.Group();
  const v = new THREE.Vector3();

  flippers.forEach((flipper) => {
    const pivot = new THREE.Group();
    boardToWorld(flipper.x, flipper.y, 0.55, v);
    pivot.position.copy(v);

    const length = flipper.length * SCALE;
    const width = FLIPPER_R * 2 * SCALE;

    const arm = new THREE.Mesh(keep(new THREE.BoxGeometry(length, 0.85, width)), stone);
    arm.position.x = length / 2;
    arm.castShadow = true;
    arm.receiveShadow = true;
    pivot.add(arm);

    // 打面の金帯。球が当たる側（斜面の上手）は左右で局所 z の符号が逆になる。
    const edge = new THREE.Mesh(keep(new THREE.BoxGeometry(length * 0.9, 0.3, 0.2)), band);
    edge.position.set(length / 2, 0.5, (flipper.side === 'left' ? -1 : 1) * FLIPPER_R * SCALE);
    pivot.add(edge);

    const hub = new THREE.Mesh(keep(new THREE.CylinderGeometry(width * 0.6, width * 0.72, 1.6, 10)), stone);
    hub.position.y = -0.15;
    hub.castShadow = true;
    pivot.add(hub);

    flipper.pivot = pivot;
    group.add(pivot);
  });
  scene.add(group);
  return group;
};

/* ============================================================
   リサイズ
   ============================================================ */

const resize = () => {
  if (!renderer) return;
  const width = Math.max(1, stage ? stage.clientWidth : window.innerWidth);
  const height = Math.max(1, stage ? stage.clientHeight : window.innerHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.8));
  renderer.setSize(width, height, false);
  camera.aspect = width / height;
  const overviewAxis = new THREE.Vector3(0, -Math.sin(OVERVIEW_PITCH), -Math.cos(OVERVIEW_PITCH));
  const overviewUp = new THREE.Vector3(0, Math.cos(OVERVIEW_PITCH), -Math.sin(OVERVIEW_PITCH));
  const actionAxis = new THREE.Vector3(0, -Math.sin(ACTION_PITCH), -Math.cos(ACTION_PITCH));
  const actionUp = new THREE.Vector3(0, Math.cos(ACTION_PITCH), -Math.sin(ACTION_PITCH));
  view.overviewDistance = fitDistance(camera.aspect, overviewAnchor, overviewAxis, overviewUp, OVERVIEW_FOV, OVERVIEW_HEAD);
  // アクション視点では盤面全体を収めない。左右フリッパー直近の距離を優先する。
  // 極端に縦長の画面だけ、左右が完全に見切れない最低限の距離を足す。
  const actionFit = fitDistance(camera.aspect, actionAnchor, actionAxis, actionUp, ACTION_FOV, ACTION_HEAD);
  const portraitRelief = camera.aspect < 0.75 ? (0.75 - camera.aspect) * actionFit * 0.55 : 0;
  view.actionDistance = ACTION_DISTANCE + portraitRelief;
  camera.updateProjectionMatrix();
  view.distance = THREE.MathUtils.lerp(view.overviewDistance, view.actionDistance, view.cameraBlend);
};

/* ============================================================
   ループ（開始 / 停止に集約）
   ============================================================ */

let raf = 0;
let lastAt = 0;
let elapsed = 0;
let frameCount = 0;
let externalBall = false;
const ballWorld = new THREE.Vector3();
const ballBoard = { x: BOARD_W * 0.5, y: BOARD_H * 0.62 };
const spinAxis = new THREE.Vector3(0, 0, 1);
let prevBallX = ballBoard.x;
let prevBallY = ballBoard.y;

// 物理が入るまでの仮の軌道。setBall() が呼ばれた時点で使わなくなる。
const idleTrack = (time) => {
  const t = time * 0.24;
  ballBoard.x = BOARD_W / 2 + Math.sin(t) * 250;
  ballBoard.y = BOARD_H * 0.52 + Math.cos(t * 0.73) * 330;
};

// 進行方向に直交する軸まわりに、転がった距離ぶんだけ回す。
const spinBoulder = (mesh, dx, dz) => {
  const travel = Math.hypot(dx, dz);
  if (travel <= 1e-5) return;
  spinAxis.set(dz, 0, -dx).normalize();
  mesh.rotateOnWorldAxis(spinAxis, travel / BALL_WORLD_R);
};

const updateBoulders = (time) => {
  if (balls.length > 0) {
    for (let i = 0; i < boulderPool.length; i += 1) {
      const mesh = boulderPool[i];
      const ball = balls[i];
      mesh.visible = Boolean(ball);
      if (!ball) continue;
      boardToWorld(ball.x, ball.y, BALL_WORLD_R, ballWorld);
      mesh.position.copy(ballWorld);
      spinBoulder(mesh, (ball.x - ball.px) * SCALE, (ball.y - ball.py) * SCALE);
      ball.px = ball.x;
      ball.py = ball.y;
    }
    ballBoard.x = balls[0].x;
    ballBoard.y = balls[0].y;
    prevBallX = ballBoard.x;
    prevBallY = ballBoard.y;
    view.focusX = (ballBoard.x - BOARD_W / 2) * SCALE;

    flippers.forEach((flipper) => { if (flipper.pivot) flipper.pivot.rotation.y = -flipper.angle; });
    return;
  }

  // 盤上に球がない間（タイトル / ゲームオーバー）は仮軌道で岩球を転がしておく。
  if (!externalBall) idleTrack(time);
  for (let i = 0; i < boulderPool.length; i += 1) boulderPool[i].visible = i === 0;
  boardToWorld(ballBoard.x, ballBoard.y, BALL_WORLD_R, ballWorld);
  boulderPool[0].position.copy(ballWorld);
  spinBoulder(boulderPool[0], (ballBoard.x - prevBallX) * SCALE, (ballBoard.y - prevBallY) * SCALE);
  prevBallX = ballBoard.x;
  prevBallY = ballBoard.y;
  view.focusX = (ballBoard.x - BOARD_W / 2) * SCALE;
  flippers.forEach((flipper) => { if (flipper.pivot) flipper.pivot.rotation.y = -flipper.angle; });
};

const updateMist = (dt) => {
  const pos = mistPoints.geometry.attributes.position;
  const speeds = mistPoints.userData.speeds;
  const array = pos.array;
  for (let i = 0; i < speeds.length; i += 1) {
    const yi = i * 3 + 1;
    array[yi] += speeds[i] * dt;
    if (array[yi] > 4) array[yi] = -18 - rand() * 10;
  }
  pos.needsUpdate = true;
};

const frame = (timestamp) => {
  raf = requestAnimationFrame(frame);
  const dt = lastAt ? Math.min(0.05, (timestamp - lastAt) / 1000) : 0.016;
  lastAt = timestamp;
  elapsed += dt;
  frameCount += 1;

  updateGame(dt);
  updateBoulders(elapsed);
  updateIdolVisuals(dt, elapsed);
  updateBridgeVisuals(dt, elapsed);
  updateTorrentVisuals(dt, elapsed);
  updateMist(dt);
  updateCamera(dt, elapsed);
  skyDome.position.copy(camera.position);
  sunSprite.position.set(-42, 62, -34).normalize().multiplyScalar(420).add(camera.position);

  renderer.render(scene, camera);
};

const startLoop = () => {
  if (raf || !ready) return;
  lastAt = 0;
  raf = requestAnimationFrame(frame);
};

const stopLoop = () => {
  if (!raf) return;
  cancelAnimationFrame(raf);
  raf = 0;
};

// タブを離れている間は描画を止める。復帰時は lastAt=0 から測り直すので dt は飛ばない。
const onVisibility = () => {
  if (document.hidden) {
    if (mode === 'play') togglePause();
    releaseAllKeys();
    stopLoop();
  } else {
    startLoop();
  }
};

/* ============================================================
   後始末
   ============================================================ */

let disposed = false;
let resizeObserver = null;

const disposeAll = () => {
  if (disposed) return;
  disposed = true;
  stopLoop();
  ready = false;
  if (resizeObserver) {
    resizeObserver.disconnect();
    resizeObserver = null;
  }
  window.removeEventListener('resize', resize);
  document.removeEventListener('visibilitychange', onVisibility);
  if (inputAbort) {
    inputAbort.abort();
    inputAbort = null;
  }
  clearTimeout(announceTimer);
  clearTimeout(explorationAdvanceTimer);
  explorationAdvanceTimer = 0;
  clearTimeout(autoDemoTimer);
  autoDemoTimer = 0;
  if (audio) {
    audio.close();
    audio = null;
  }
  textureBin.forEach((texture) => texture.dispose());
  disposables.forEach((item) => item.dispose());
  textureBin.length = 0;
  disposables.length = 0;
  if (renderer) renderer.dispose();
};

/* ============================================================
   初期化
   ============================================================ */

const init = () => {
  buildRenderer();
  buildScene();
  buildLights();
  buildSky();
  buildDistantRidges();
  buildTerrain();
  buildRuins();
  buildAbyss();
  buildRails();
  buildIdolGates();
  buildRopeBridge();
  buildTorrentFlow();
  buildFlippers();
  for (let i = 0; i < 3; i += 1) {
    const mesh = buildBoulder();
    mesh.visible = i === 0;
    boulderPool.push(mesh);
  }
  buildCameraRig();

  resize();

  // three.js がテクスチャを GPU へ送るのは、そのメッシュを初めて描いた時点。
  // 水流は鉄砲水が起きるまで隠してあるので、送られるころには元になった
  // Canvas をブラウザが破棄していて、真っ黒(α=0)のまま送られてしまう。
  // transparent な材質では α=0 は完全な消失になり、濁流が一切見えなくなる。
  // Canvas が生きているこの時点で一度だけ描いて、先に送っておく。
  torrentFlow.visible = true;
  renderer.render(scene, camera);   // opacity は 0 のままなので画面には出ない
  torrentFlow.visible = false;

  ready = true;

  updateHud();
  syncActionControls();
  syncIdolHud();
  syncBridgeHud();
  syncTorrentHud();
  syncComboHud();
  bindInput();

  // Xピンボール共通の自動描画確認入口。通常表示ではタイトル画面を保ち、
  // ?demo=1 のときだけ、初期描画後に通常の startGame() 経路から開始する。
  if (new URLSearchParams(window.location.search).get('demo') === '1') {
    autoDemoTimer = setTimeout(() => {
      autoDemoTimer = 0;
      if (!disposed) startGame(true);
    }, 120);
  }

  if (window.ResizeObserver && stage) {
    resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(stage);
  }
  window.addEventListener('resize', resize);

  document.addEventListener('visibilitychange', onVisibility);
  window.addEventListener('pagehide', disposeAll, { once: true });

  startLoop();
  if (loadError) loadError.classList.add('hidden');
};

try {
  init();
} catch (error) {
  console.error('[Xピンボールopus] 3D ステージの初期化に失敗しました', error);
  if (loadError) {
    loadError.classList.remove('hidden');
    loadError.textContent = '3D 渓谷を初期化できませんでした。WebGL が有効か確認してください。';
  }
  disposeAll();
}

/* ============================================================
   3D ステージ層の読み取り / 操作 API
   後続ステップ（物理・ギミック・自動確認）から呼ぶ。
   ============================================================ */

const countScene = () => {
  let objects = 0;
  let triangles = 0;
  if (scene) {
    scene.traverse((obj) => {
      objects += 1;
      const geo = obj.geometry;
      if (geo && geo.index) triangles += geo.index.count / 3;
      else if (geo && geo.attributes && geo.attributes.position && obj.isMesh) triangles += geo.attributes.position.count / 3;
    });
  }
  return { objects, triangles: Math.round(triangles) };
};

window.XPinballOpusStage = {
  isReady: () => ready,
  isRunning: () => raf !== 0,
  start: startLoop,
  stop: stopLoop,
  dispose: disposeAll,
  boardToWorld: (bx, by, lift = 0) => {
    const v = boardToWorld(bx, by, lift, new THREE.Vector3());
    return { x: v.x, y: v.y, z: v.z };
  },
  terrainHeight,
  // 2D 物理側から毎フレーム球位置を渡す。渡し始めると仮軌道は止まる。
  setBall: (bx, by) => {
    externalBall = true;
    ballBoard.x = bx;
    ballBoard.y = by;
    view.focusX = (bx - BOARD_W / 2) * SCALE;
  },
  clearBall: () => { externalBall = false; },
  shake: (amount) => {
    view.shake = Math.min(2.6, view.shake + amount);
    view.shakeSeed = Math.random() * 100;
  },
  getInfo: () => {
    const counts = countScene();
    return {
      ready,
      running: raf !== 0,
      disposed,
      loop: { ready, running: raf !== 0, disposed },
      revision: THREE.REVISION,
      frames: frameCount,
      elapsed: Number(elapsed.toFixed(2)),
      size: renderer ? { width: renderer.domElement.width, height: renderer.domElement.height, pixelRatio: renderer.getPixelRatio() } : null,
      camera: camera ? {
        fov: camera.fov,
        aspect: Number(camera.aspect.toFixed(4)),
        distance: Number(view.distance.toFixed(2)),
        blend: Number(view.cameraBlend.toFixed(3)),
        dangerRush: Number(view.dangerRush.toFixed(3)),
        mode: view.cameraBlend > 0.5 ? 'action' : 'overview',
        position: { x: Number(camera.position.x.toFixed(2)), y: Number(camera.position.y.toFixed(2)), z: Number(camera.position.z.toFixed(2)) },
      } : null,
      lights: scene ? scene.children.filter((o) => o.isLight).map((o) => o.type) : [],
      fog: scene && scene.fog ? { color: `#${scene.fog.color.getHexString()}`, near: scene.fog.near, far: scene.fog.far } : null,
      shadowMap: renderer ? renderer.shadowMap.enabled : false,
      objects: counts.objects,
      triangles: counts.triangles,
      ball: { x: Math.round(ballBoard.x), y: Math.round(ballBoard.y), external: externalBall },
      shake: Number(view.shake.toFixed(3)),
      board: { w: BOARD_W, h: BOARD_H, scale: SCALE },
      // 3D の描画状態と、同じ通常経路を通過した盤上ギミックの要約を並べる。
      // 詳細は XPinballOpus.getState() に残し、ここでは自動確認の判定に必要な
      // 事実だけを公開する。読み取り専用であり、盤面状態は変更しない。
      game: {
        explorationStage: explorationState.stage,
        idolAwake: idolState.awake,
        bridgeRescues: bridgeState.saves,
        floodStarts: torrentState.floods,
        boulderEntries: verificationState.entries,
        verification: verificationSnapshot().checks,
      },
    };
  },
};

/* ============================================================
   盤の読み取り / 操作 API
   自動確認から通常プレイで起きたギミックを判定できるようにする。
   操作は発射・フリッパー入力・ポーズの既存経路だけを呼び、状態を直接変更しない。
   ============================================================ */

const verificationSnapshot = () => ({
  run: verificationState.run,
  entries: verificationState.entries,
  bridgeRescues: verificationState.bridgeRescues,
  floodStarts: verificationState.floodStarts,
  explorationRewards: verificationState.explorationRewards,
  checks: {
    boulderEntered: verificationState.entries > 0,
    bridgeRescued: verificationState.bridgeRescues > 0,
    floodStarted: verificationState.floodStarts > 0,
    explorationRewardedOnce: verificationState.explorationRewards === 1,
  },
  events: verificationState.events.map((event) => ({ ...event })),
});

// 両フリッパー同時押しを、画面の吊り橋ボタンと同じ入力経路へ流す。
// 成功や救出を強制しないので、橋を張る時機と物理判定は通常プレイと共通になる。
const tapBridgeFromApi = () => {
  if (mode !== 'play' || demoMode) return false;
  const source = 'api-bridge';
  setFlipperInput('left', source, true);
  setFlipperInput('right', source, true);
  requestAnimationFrame(() => {
    setFlipperInput('left', source, false);
    setFlipperInput('right', source, false);
  });
  return true;
};

window.XPinballOpus = {
  getState: () => ({
    mode,
    demoMode,
    score,
    highScore,
    lives,
    multiplier: scoreMultiplier(),
    baseMultiplier: multiplier,
    charging,
    charge: Number(charge.toFixed(3)),
    gameTime: Number(gameTime.toFixed(2)),
    flippers: flippers.map((flipper) => ({
      side: flipper.side,
      angle: Number(flipper.angle.toFixed(3)),
      omega: Number(flipper.omega.toFixed(2)),
      pressed: keys[flipper.side],
    })),
    balls: balls.map((ball) => ({
      x: Math.round(ball.x), y: Math.round(ball.y),
      vx: Math.round(ball.vx), vy: Math.round(ball.vy),
      lane: ball.lane, entered: ball.entered, alive: ball.alive, draining: ball.draining,
    })),
    idol: {
      litCount: idolState.litCount,
      total: idolState.targets.length,
      awake: idolState.awake,
      cycles: idolState.cycles,
      rise: Number(idolState.rise.toFixed(3)),
      radius: IDOL_R,
      targets: idolState.targets.map((target) => ({
        mark: target.mark,
        x: target.x,
        y: target.y,
        lit: target.lit,
        hits: target.hits,
      })),
    },
    bridge: {
      uses: bridgeState.uses,
      max: BRIDGE_USES,
      up: bridgeState.timer > 0,
      timer: Number(bridgeState.timer.toFixed(3)),
      deploys: bridgeState.deploys,
      saves: bridgeState.saves,
      raise: Number(bridgeState.raise.toFixed(3)),
      latched: dualFlipLatched,
      spans: bridgeSpans.map((span) => ({
        a: { x: Math.round(span.a.x), y: Math.round(span.a.y) },
        b: { x: Math.round(span.b.x), y: Math.round(span.b.y) },
      })),
    },
    torrent: {
      level: Number(torrentState.level.toFixed(2)),
      percent: Math.round(torrentState.level),
      max: TORRENT_MAX,
      flood: torrentState.flood,
      timer: Number(torrentState.timer.toFixed(3)),   // 鉄砲水モードの残時間（秒）
      span: FLOOD_SPAN,
      floods: torrentState.floods,
      factor: floodFactor,
      push: torrentState.flood ? FLOOD_PUSH : 0,
      combo: torrentState.combo,
      comboAt: Number(torrentState.comboAt.toFixed(2)),
      flow: Number(torrentState.flow.toFixed(3)),
      flash: Number(torrentState.flash.toFixed(3)),
    },
    exploration: {
      stage: explorationState.stage,
      total: 3,
      completed: explorationState.stage === 3,
      advancedAt: Number(explorationState.advancedAt.toFixed(3)),
      rewarded: explorationState.rewarded,
      rewardPoints: explorationState.rewardPoints,
      rewardedAt: Number(explorationState.rewardedAt.toFixed(3)),
      sources: {
        idolAwakened: idolState.cycles > 0,
        bridgeRescued: bridgeState.expeditionSaved,
        floodStarted: torrentState.floods > 0,
      },
    },
    rocks: {
      active: balls.length,
      maximum: ECHO_BOULDER_TOTAL_MAX,
      enteredNow: balls.filter((ball) => ball.entered).length,
      entering: balls.filter((ball) => ball.launchGuide).length,
      entries: verificationState.entries,
    },
    verification: verificationSnapshot(),
  }),
  getVerification: verificationSnapshot,
  startGame: () => startGame(false),
  startDemo: () => startGame(true),
  launch: (power = 1) => launchBall(power),
  pause: () => togglePause(),
  press: (side, down) => {
    if (side !== 'left' && side !== 'right' || mode !== 'play' || demoMode) return false;
    setFlipperInput(side, `api-${side}`, Boolean(down));
    return true;
  },
  tapBridge: tapBridgeFromApi,
};
