<!--
  -*- coding: utf-8 -*-

  -------------------------------------------------------------------------
  COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
  Licensed under "AiDiy 公開利用ライセンス v1.1".
  Commercial use requires prior written consent from all copyright holders.
  See LICENSE for full terms. Thank you for keeping the rules.
  https://github.com/monjyu1101/AiDiy2026
  -------------------------------------------------------------------------
-->

<script setup lang="ts">
import { computed, markRaw, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import AiTeamConversation from '../dialog/AIチーム_会話要求.vue';
import {
  type エージェント,
  type エージェント状態,
  type チーム目標,
} from '../AIチーム_型';
import {
  type NPC個体,
  type 造形ヘルパー,
  NPC群を更新,
  NPCを配置,
} from '../AIチーム_NPC制御';
// 草原の小物は毎回同じ配置にしたいので、NPC と同じシード付き擬似乱数で座標を決める
import { 乱数を作る } from '../AIチーム_NPC型';

type 実行状態 = {
  group: THREE.Group;
  目的地: THREE.Vector3;
  位相: number;
  速度: number;
  割当状態: エージェント状態;
  次自由行動時刻: number;
  /** うさぎ穴にはまっている残り秒。0 より大きいあいだは動けず、あたふたする */
  はまり残り: number;
  /** 這い出た直後に同じ穴へ落ち直さないための猶予秒 */
  穴無視残り: number;
  /** はまっている穴の中心（這い出る向きを決めるのに使う） */
  はまった穴: THREE.Vector3;
};

const props = defineProps<{
  エージェント一覧: エージェント[];
  選択中ID: string;
  要員読込中: boolean;
  要員読込エラー: string;
  チーム目標: チーム目標 | null;
}>();

const emit = defineEmits<{
  retry: [];
  目標クリック: [];
}>();

const stageRef = ref<HTMLElement | null>(null);
const canvasRef = ref<HTMLCanvasElement | null>(null);
const エージェント一覧 = computed(() => props.エージェント一覧);
const 選択中ID = computed(() => props.選択中ID);
const 要員読込中 = computed(() => props.要員読込中);
const 要員読込エラー = computed(() => props.要員読込エラー);
const 要員数 = computed(() => エージェント一覧.value.length);
const 稼働数 = computed(() => エージェント一覧.value.filter((agent) => agent.状態 === '作業中').length);
const 相談数 = computed(() => エージェント一覧.value.filter((agent) => ['相談中', '雑談中'].includes(agent.状態)).length);
const 瞑想数 = computed(() => エージェント一覧.value.filter((agent) => agent.状態 === '瞑想中').length);
const 休憩数 = computed(() => エージェント一覧.value.filter((agent) => ['移動中', '休憩中'].includes(agent.状態)).length);
// 一人称視点。要員のときは 一人称ID に要員 ID が入り、生き物のときは 一人称NPC に実体が入る。
// バッジに出す名前は 一人称ラベル で、空なら通常の俯瞰カメラ。Esc で解除する
const 一人称ID = ref('');
const 一人称ラベル = ref('');
// 視点を移しただけでは相手は自律行動のまま。矢印キーを押した時点で操作（憑依）へ切り替わる
const 憑依中 = ref(false);
const 会話対象 = ref<エージェント | null>(null);
const 会話ダイアログ表示 = ref(false);
// 時間の進み方は画面から変更せず、この規定値で固定する（1.0 倍が標準。0 にすると時間が止まる）
const 経過速度倍率 = 1;
const 現在時刻 = ref('');
const ラベル要素 = new Map<string, HTMLElement>();

let renderer: THREE.WebGLRenderer | null = null;
let scene: THREE.Scene | null = null;
let camera: THREE.PerspectiveCamera | null = null;
let controls: OrbitControls | null = null;
let resizeObserver: ResizeObserver | null = null;
let animationId = 0;
let 前フレーム時刻 = 0;
let 経過時間 = 0;
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
// 一人称視点に入る直前の俯瞰カメラ。Esc でここへ戻す
const 復帰カメラ位置 = new THREE.Vector3();
const 復帰注視点 = new THREE.Vector3();
const 一人称注視点 = new THREE.Vector3();
const 一人称体格 = new THREE.Box3();
const 掲示板注視点 = new THREE.Vector3();
// NPC飛行船が吊り下げて運ぶ「チーム目標」掲示板（常にカメラを向き、クリックで保守ダイアログ）
// 位置と向きは AIチーム_NPC動作_飛行船.ts 側が毎フレーム決める
const 目標掲示板 = {
  group: null as THREE.Group | null,
  板: null as THREE.Mesh | null,
  縁: null as THREE.Mesh | null,
  改善明滅: null as THREE.Mesh | null,
  改善ネオン芯: null as THREE.Group | null,
};
const 目標掲示板幅 = 13;
const 目標掲示板縦 = 4.6;
let 目標テクスチャ: THREE.CanvasTexture | null = null;
const 目標ホバー = ref(false);
const 実行状態一覧 = new Map<string, 実行状態>();
const 掲示板一覧: THREE.Group[] = [];
// NPC（ネコ・イヌ・馬・うさぎ・カモ・雲・蝶）。造形と動作は AIチーム_NPC制御.ts と AIチーム_NPC動作_*.ts で調整する
const NPC一覧: NPC個体[] = [];
const 破棄対象: Array<THREE.BufferGeometry | THREE.Material> = [];
const 破棄テクスチャ: THREE.Texture[] = [];

const 作業候補 = [
  '要件を小さなタスクに分解中',
  '既存コードの影響範囲を調査中',
  '実装案を組み立て中',
  'テストケースを追加中',
  'レビューコメントを整理中',
  '次のタスクを自主選択中',
];

const 雑談候補 = [
  'この実装、もう少し軽くできそう',
  '瞑想を終えたら一緒にレビューしよう',
  'さっきの発見、共有しておいたよ',
  '次はどのタスクを拾う？',
  '今日は集中できるBGMだね',
];

const マテリアル = (
  color: number,
  options: THREE.MeshStandardMaterialParameters = {},
): THREE.MeshStandardMaterial => {
  const material = new THREE.MeshStandardMaterial({
    color,
    roughness: 0.55,
    metalness: 0.18,
    ...options,
  });
  破棄対象.push(material);
  return material;
};

const ジオメトリ = <T extends THREE.BufferGeometry>(geometry: T): T => {
  破棄対象.push(geometry);
  return geometry;
};

// NPC動作モジュールへ渡す造形ヘルパー（生成物をこの画面の破棄リストへ載せる）
const NPC造形ヘルパー: 造形ヘルパー = {
  ジオメトリ,
  マテリアル,
  マテリアル登録: (material) => 破棄対象.push(material),
  テクスチャ登録: (texture) => 破棄テクスチャ.push(texture),
};

const メッシュ = (
  geometry: THREE.BufferGeometry,
  material: THREE.Material,
  position: [number, number, number],
): THREE.Mesh => {
  const mesh = new THREE.Mesh(geometry, material);
  mesh.position.set(...position);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  return mesh;
};

type エリアキー = '仕事' | '雑談' | '瞑想' | '休憩';

// 4エリアを xy=00/01/10/11 の正方グリッドに配置する（上から見て 左下=雑談 左上=仕事 右上=瞑想 右下=休憩）
// セルサイズと通路幅は 2 倍にしてあり、エリアの円（台座半径 = セルサイズ/2 - 1.4）も直径 2 倍になる
const セルサイズ = 16;
const 通路幅 = 2.8;
const グリッド間隔 = セルサイズ + 通路幅;
const 台座半径 = セルサイズ / 2 - 1.4;
// 要員が草原に立つ基準高さ（足元が y=0 になるモデルなので、わずかに浮かせて上下動の余地を作る）
const 要員基準Y = 0.06;
// 案内板を吊る高さと、エリア中心から案内板までの距離
const 掲示板高さ = 2.5;
const 掲示板オフセット = セルサイズ / 2 + 3.5;

const エリア座標: Record<エリアキー, { x: 0 | 1; y: 0 | 1; 色: number }> = {
  雑談: { x: 0, y: 0, 色: 0x8bb8ff },
  仕事: { x: 0, y: 1, 色: 0x5bd9ff },
  瞑想: { x: 1, y: 1, 色: 0xffcf73 },
  休憩: { x: 1, y: 0, 色: 0x7be3b0 },
};

const エリア中心 = (key: エリアキー): [number, number] => {
  const { x, y } = エリア座標[key];
  return [(x - 0.5) * グリッド間隔, (0.5 - y) * グリッド間隔];
};

// 状態からエリアを一意に決められるため、要員の移動先は座標計算だけで求まる
const 状態エリア: Record<エージェント状態, エリアキー> = {
  作業中: '仕事',
  相談中: '雑談',
  雑談中: '雑談',
  瞑想中: '瞑想',
  移動中: '休憩',
  休憩中: '休憩',
  召喚中: '雑談',
};

// エリア中心からの相対オフセット（座席）。indexで使い回す
// 広くなった円の中で要員が散らばるよう、エリア拡大に合わせて外側へ広げている
const 座席オフセット: [number, number][] = [
  [-3.2, -2.3],
  [3.2, -2.3],
  [-3.2, 2.6],
  [3.2, 2.6],
  [0, -4.1],
  [0, 4.4],
];

const エリア位置 = (状態: エージェント状態, index = 0): THREE.Vector3 => {
  const [cx, cz] = エリア中心(状態エリア[状態]);
  if (状態 === '召喚中') return new THREE.Vector3(cx, 要員基準Y, cz);
  const [ox, oz] = 座席オフセット[index % 座席オフセット.length];
  return new THREE.Vector3(cx + ox, 要員基準Y, cz + oz);
};

/** 指定されたエリア円内で自由行動するための目的地 */
const エリア内自由位置 = (状態: エージェント状態): THREE.Vector3 => {
  const [cx, cz] = エリア中心(状態エリア[状態]);
  if (状態 === '召喚中') return new THREE.Vector3(cx, 要員基準Y, cz);
  const 角度 = Math.random() * Math.PI * 2;
  const 距離 = 2.3 + Math.sqrt(Math.random()) * Math.max(0.5, 台座半径 - 4);
  return new THREE.Vector3(cx + Math.cos(角度) * 距離, 要員基準Y, cz + Math.sin(角度) * 距離);
};

const 指定エリア外 = (位置: THREE.Vector3, 状態: エージェント状態) => {
  const [cx, cz] = エリア中心(状態エリア[状態]);
  return Math.hypot(位置.x - cx, 位置.z - cz) > 台座半径 - 0.8;
};

// うさぎが掘った穴。多いと草原が穴だらけになるので、同時に存在する数を絞る
const うさぎ穴上限 = 6;
/** うさぎが掘り終えたときに呼ばれる。その場所へ うさぎ穴 NPC を置く */
const うさぎ穴を掘る = (位置: THREE.Vector3) => {
  if (!scene) return;
  if (NPC一覧.filter((npc) => npc.種別 === 'うさぎ穴').length >= うさぎ穴上限) return;
  NPC一覧.push(
    NPCを配置(scene, 'うさぎ穴', NPC造形ヘルパー, {
      位置: 位置.clone(),
      種: Math.floor(Math.random() * 1000000),
    }),
  );
};

/** 要員が踏み抜いた うさぎ穴。見つからなければ null */
const はまる穴を探す = (位置: THREE.Vector3): THREE.Group | null => {
  for (const npc of NPC一覧) {
    if (npc.種別 !== 'うさぎ穴') continue;
    const 半径 = (npc.group.userData.穴半径 as number) ?? 0;
    if (半径 <= 0) continue;
    if (Math.hypot(位置.x - npc.group.position.x, 位置.z - npc.group.position.z) < 半径) {
      return npc.group;
    }
  }
  return null;
};

// 草原の小物は数が多いため、ジオメトリとマテリアルを 1 組だけ作って共有する
type 共有部品 = {
  幹: THREE.CylinderGeometry;
  葉: THREE.SphereGeometry;
  葉小: THREE.SphereGeometry;
  茂み: THREE.SphereGeometry;
  石: THREE.DodecahedronGeometry;
  草: THREE.ConeGeometry;
  花芯: THREE.SphereGeometry;
  茎: THREE.CylinderGeometry;
  幹材: THREE.MeshStandardMaterial;
  葉材: THREE.MeshStandardMaterial[];
  茂み材: THREE.MeshStandardMaterial;
  石材: THREE.MeshStandardMaterial;
  草材: THREE.MeshStandardMaterial;
  花材: THREE.MeshStandardMaterial[];
  茎材: THREE.MeshStandardMaterial;
  木材: THREE.MeshStandardMaterial;
  濃木材: THREE.MeshStandardMaterial;
  布材: THREE.MeshStandardMaterial;
  金属材: THREE.MeshStandardMaterial;
};

let 部品: 共有部品 | null = null;

const 部品を用意 = (): 共有部品 => {
  if (部品) return 部品;
  部品 = {
    幹: ジオメトリ(new THREE.CylinderGeometry(0.16, 0.24, 1.7, 8)),
    葉: ジオメトリ(new THREE.SphereGeometry(1, 12, 10)),
    葉小: ジオメトリ(new THREE.SphereGeometry(0.7, 10, 8)),
    茂み: ジオメトリ(new THREE.SphereGeometry(0.55, 10, 8)),
    石: ジオメトリ(new THREE.DodecahedronGeometry(0.42, 0)),
    草: ジオメトリ(new THREE.ConeGeometry(0.11, 0.5, 5)),
    花芯: ジオメトリ(new THREE.SphereGeometry(0.075, 8, 6)),
    茎: ジオメトリ(new THREE.CylinderGeometry(0.014, 0.014, 0.3, 4)),
    幹材: マテリアル(0x8a6244, { roughness: 0.92, metalness: 0.02 }),
    葉材: [
      マテリアル(0x4f9e46, { roughness: 0.88, metalness: 0.02 }),
      マテリアル(0x63b356, { roughness: 0.88, metalness: 0.02 }),
      マテリアル(0x3d8a41, { roughness: 0.9, metalness: 0.02 }),
    ],
    茂み材: マテリアル(0x59a84c, { roughness: 0.9, metalness: 0.02 }),
    石材: マテリアル(0x9ba49f, { roughness: 0.85, metalness: 0.05 }),
    草材: マテリアル(0x74bb55, { roughness: 0.9, metalness: 0.02 }),
    花材: [
      マテリアル(0xffe066, { roughness: 0.7, metalness: 0.02 }),
      マテリアル(0xff9ec0, { roughness: 0.7, metalness: 0.02 }),
      マテリアル(0xfdfdfd, { roughness: 0.7, metalness: 0.02 }),
      マテリアル(0xc79bff, { roughness: 0.7, metalness: 0.02 }),
    ],
    茎材: マテリアル(0x4f9245, { roughness: 0.9, metalness: 0.02 }),
    木材: マテリアル(0xb5824a, { roughness: 0.82, metalness: 0.03 }),
    濃木材: マテリアル(0x8a5c33, { roughness: 0.86, metalness: 0.03 }),
    布材: マテリアル(0xf6f1e2, { roughness: 0.88, metalness: 0.0 }),
    金属材: マテリアル(0x9aa7ad, { roughness: 0.35, metalness: 0.7 }),
  };
  return 部品;
};

const 空を作る = () => {
  if (!scene) return;
  const canvas = document.createElement('canvas');
  canvas.width = 8;
  canvas.height = 256;
  const context = canvas.getContext('2d');
  if (context) {
    const gradient = context.createLinearGradient(0, 0, 0, canvas.height);
    gradient.addColorStop(0, '#2f7fc4');
    gradient.addColorStop(0.42, '#7dc0e8');
    gradient.addColorStop(0.72, '#c7e6f4');
    gradient.addColorStop(1, '#eaf6e6');
    context.fillStyle = gradient;
    context.fillRect(0, 0, canvas.width, canvas.height);
  }
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  破棄テクスチャ.push(texture);
  const skyMaterial = new THREE.MeshBasicMaterial({
    map: texture,
    side: THREE.BackSide,
    depthWrite: false,
    toneMapped: false,
  });
  破棄対象.push(skyMaterial);
  const sky = new THREE.Mesh(ジオメトリ(new THREE.SphereGeometry(118, 24, 16)), skyMaterial);
  sky.position.y = 8;
  scene.add(sky);

  // 太陽（見た目だけの発光球）
  const sunMaterial = new THREE.MeshBasicMaterial({ color: 0xfff6d8, toneMapped: false });
  破棄対象.push(sunMaterial);
  const sun = new THREE.Mesh(ジオメトリ(new THREE.SphereGeometry(2.4, 16, 12)), sunMaterial);
  sun.position.set(-52, 48, -68);
  scene.add(sun);

};

const 草地テクスチャを作る = (): THREE.Texture | null => {
  const canvas = document.createElement('canvas');
  canvas.width = 256;
  canvas.height = 256;
  const context = canvas.getContext('2d');
  if (!context) return null;
  context.fillStyle = '#69ab4f';
  context.fillRect(0, 0, canvas.width, canvas.height);
  const 乱数 = 乱数を作る(777);
  // 明暗の斑と草の筋を重ねて、単色に見えない芝生にする
  for (let index = 0; index < 900; index += 1) {
    const x = 乱数() * canvas.width;
    const y = 乱数() * canvas.height;
    const 明るさ = 乱数();
    context.fillStyle = 明るさ > 0.62
      ? 'rgba(139, 200, 106, 0.55)'
      : 明るさ > 0.3
        ? 'rgba(88, 154, 68, 0.5)'
        : 'rgba(60, 121, 55, 0.45)';
    context.fillRect(x, y, 1 + 乱数() * 3, 2 + 乱数() * 5);
  }
  for (let index = 0; index < 220; index += 1) {
    const x = 乱数() * canvas.width;
    const y = 乱数() * canvas.height;
    context.strokeStyle = 乱数() > 0.5 ? 'rgba(160, 214, 120, 0.4)' : 'rgba(66, 126, 58, 0.4)';
    context.lineWidth = 1;
    context.beginPath();
    context.moveTo(x, y);
    context.lineTo(x + (乱数() - 0.5) * 4, y - 4 - 乱数() * 5);
    context.stroke();
  }
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  texture.repeat.set(40, 40);
  破棄テクスチャ.push(texture);
  return texture;
};

const 草原を作る = () => {
  if (!scene) return;
  const 草地材 = マテリアル(0x74b155, { roughness: 0.95, metalness: 0.02 });
  const texture = 草地テクスチャを作る();
  if (texture) 草地材.map = texture;
  const ground = new THREE.Mesh(ジオメトリ(new THREE.CircleGeometry(104, 72)), 草地材);
  ground.rotation.x = -Math.PI / 2;
  ground.receiveShadow = true;
  scene.add(ground);

  // 遠景の丘（つぶした半球）で草原が続いている感じを出す
  const 丘材 = [
    マテリアル(0x5c9e52, { roughness: 0.96, metalness: 0.0 }),
    マテリアル(0x4c8b47, { roughness: 0.96, metalness: 0.0 }),
  ];
  const 丘 = ジオメトリ(new THREE.SphereGeometry(1, 16, 10, 0, Math.PI * 2, 0, Math.PI / 2));
  const 乱数 = 乱数を作る(31415);
  // なだらかな稜線にしたいので、遠くに低く広い丘を並べる
  for (let index = 0; index < 20; index += 1) {
    const 角度 = (index / 20) * Math.PI * 2 + 乱数() * 0.22;
    const 距離 = 82 + 乱数() * 14;
    const hill = new THREE.Mesh(丘, 丘材[index % 丘材.length]);
    hill.position.set(Math.cos(角度) * 距離, -0.6, Math.sin(角度) * 距離);
    hill.scale.set(19 + 乱数() * 13, 3.0 + 乱数() * 3.2, 16 + 乱数() * 11);
    scene.add(hill);
  }
};

const 木を作る = (x: number, z: number, scale = 1, seed = 1) => {
  if (!scene) return;
  const p = 部品を用意();
  const 乱数 = 乱数を作る(seed);
  const group = new THREE.Group();
  group.position.set(x, 0, z);
  group.scale.setScalar(scale);
  group.rotation.y = 乱数() * Math.PI * 2;

  const trunk = new THREE.Mesh(p.幹, p.幹材);
  trunk.position.y = 0.85;
  trunk.castShadow = true;
  trunk.receiveShadow = true;
  group.add(trunk);
  const 葉数 = 3 + Math.floor(乱数() * 2);
  for (let index = 0; index < 葉数; index += 1) {
    const leaf = new THREE.Mesh(index === 0 ? p.葉 : p.葉小, p.葉材[index % p.葉材.length]);
    leaf.position.set(
      (乱数() - 0.5) * 0.9,
      1.85 + index * 0.42 + 乱数() * 0.2,
      (乱数() - 0.5) * 0.9,
    );
    leaf.scale.setScalar(0.85 + 乱数() * 0.5);
    leaf.castShadow = true;
    leaf.receiveShadow = true;
    group.add(leaf);
  }
  scene.add(group);
};

const 茂みを作る = (x: number, z: number, scale = 1, seed = 2) => {
  if (!scene) return;
  const p = 部品を用意();
  const 乱数 = 乱数を作る(seed);
  const group = new THREE.Group();
  group.position.set(x, 0, z);
  group.scale.setScalar(scale);
  for (let index = 0; index < 3; index += 1) {
    const bush = new THREE.Mesh(p.茂み, index === 1 ? p.茂み材 : p.葉材[index % p.葉材.length]);
    bush.position.set((乱数() - 0.5) * 0.7, 0.34 + 乱数() * 0.14, (乱数() - 0.5) * 0.7);
    bush.scale.setScalar(0.8 + 乱数() * 0.5);
    bush.castShadow = true;
    bush.receiveShadow = true;
    group.add(bush);
  }
  scene.add(group);
};

const 花畑を作る = (x: number, z: number, 半径 = 1.6, 本数 = 10, seed = 3) => {
  if (!scene) return;
  const p = 部品を用意();
  const 乱数 = 乱数を作る(seed);
  const group = new THREE.Group();
  group.position.set(x, 0, z);
  for (let index = 0; index < 本数; index += 1) {
    const 角度 = 乱数() * Math.PI * 2;
    const 距離 = 乱数() * 半径;
    const fx = Math.cos(角度) * 距離;
    const fz = Math.sin(角度) * 距離;
    const stem = new THREE.Mesh(p.茎, p.茎材);
    stem.position.set(fx, 0.15, fz);
    group.add(stem);
    const flower = new THREE.Mesh(p.花芯, p.花材[Math.floor(乱数() * p.花材.length)]);
    flower.position.set(fx, 0.3, fz);
    // 平たくして、棒付きの球ではなく花びららしく見せる
    const 大きさ = 1.1 + 乱数() * 0.7;
    flower.scale.set(大きさ, 大きさ * 0.42, 大きさ);
    group.add(flower);
    if (乱数() > 0.45) {
      const blade = new THREE.Mesh(p.草, p.草材);
      blade.position.set(fx + (乱数() - 0.5) * 0.4, 0.24, fz + (乱数() - 0.5) * 0.4);
      blade.rotation.set((乱数() - 0.5) * 0.3, 乱数() * 3, (乱数() - 0.5) * 0.3);
      group.add(blade);
    }
  }
  scene.add(group);
};

const 石を置く = (x: number, z: number, scale = 1, seed = 4) => {
  if (!scene) return;
  const p = 部品を用意();
  const 乱数 = 乱数を作る(seed);
  const rock = new THREE.Mesh(p.石, p.石材);
  rock.position.set(x, 0.16 * scale, z);
  rock.scale.set(scale, scale * 0.62, scale * 0.9);
  rock.rotation.set(乱数(), 乱数() * 3, 乱数());
  rock.castShadow = true;
  rock.receiveShadow = true;
  scene.add(rock);
};

const 小道を作る = () => {
  if (!scene) return;
  const 土材 = マテリアル(0xcbb185, { roughness: 0.95, metalness: 0.0 });
  const 縦 = new THREE.Mesh(ジオメトリ(new THREE.PlaneGeometry(通路幅 + 0.5, グリッド間隔 * 2.05)), 土材);
  縦.rotation.x = -Math.PI / 2;
  縦.position.y = 0.012;
  縦.receiveShadow = true;
  const 横 = new THREE.Mesh(ジオメトリ(new THREE.PlaneGeometry(グリッド間隔 * 2.05, 通路幅 + 0.5)), 土材);
  横.rotation.x = -Math.PI / 2;
  横.position.y = 0.012;
  横.receiveShadow = true;
  scene.add(縦, 横);
};

const 作業テントを作る = (x: number, z: number, color: number) => {
  if (!scene) return;
  const p = 部品を用意();
  const group = new THREE.Group();
  group.position.set(x, 0, z);
  // エリア色を落ち着いた帆布色へ寄せ、面ごとに陰影を付けて布のテントらしく見せる
  const 天幕 = マテリアル(
    new THREE.Color(color).lerp(new THREE.Color(0x2c6379), 0.74).getHex(),
    { roughness: 0.98, metalness: 0.0, side: THREE.DoubleSide, flatShading: true },
  );
  const 支柱 = ジオメトリ(new THREE.CylinderGeometry(0.08, 0.08, 2.7, 8));
  const 柱位置: [number, number][] = [
    [-4.4, -3.4],
    [4.4, -3.4],
    [-4.4, 3.6],
    [4.4, 3.6],
  ];
  柱位置.forEach(([px, pz]) => {
    group.add(メッシュ(支柱, p.木材, [px, 1.35, pz]));
  });
  const roof = メッシュ(ジオメトリ(new THREE.ConeGeometry(6.4, 2.2, 4)), 天幕, [0, 3.8, 0]);
  roof.rotation.y = Math.PI / 4;
  group.add(roof);
  group.add(メッシュ(ジオメトリ(new THREE.SphereGeometry(0.13, 10, 8)), p.木材, [0, 4.98, 0]));
  group.add(メッシュ(ジオメトリ(new THREE.BoxGeometry(8.95, 0.1, 0.1)), p.濃木材, [0, 2.68, -3.4]));
  group.add(メッシュ(ジオメトリ(new THREE.BoxGeometry(8.95, 0.1, 0.1)), p.濃木材, [0, 2.68, 3.6]));
  scene.add(group);
};

const 作業机を作る = (x: number, z: number, rotation = 0) => {
  if (!scene) return;
  const p = 部品を用意();
  const group = new THREE.Group();
  group.position.set(x, 0, z);
  group.rotation.y = rotation;

  const 画面 = マテリアル(0x21455c, {
    emissive: 0x49d2ff,
    emissiveIntensity: 0.95,
    roughness: 0.25,
  });
  group.add(メッシュ(ジオメトリ(new THREE.BoxGeometry(2.2, 0.14, 1.05)), p.木材, [0, 0.94, 0]));
  group.add(メッシュ(ジオメトリ(new THREE.BoxGeometry(0.12, 0.86, 0.12)), p.濃木材, [-0.9, 0.5, -0.35]));
  group.add(メッシュ(ジオメトリ(new THREE.BoxGeometry(0.12, 0.86, 0.12)), p.濃木材, [0.9, 0.5, -0.35]));
  group.add(メッシュ(ジオメトリ(new THREE.BoxGeometry(0.12, 0.86, 0.12)), p.濃木材, [-0.9, 0.5, 0.35]));
  group.add(メッシュ(ジオメトリ(new THREE.BoxGeometry(0.12, 0.86, 0.12)), p.濃木材, [0.9, 0.5, 0.35]));
  group.add(メッシュ(ジオメトリ(new THREE.BoxGeometry(1.1, 0.68, 0.07)), 画面, [0, 1.42, -0.2]));
  group.add(メッシュ(ジオメトリ(new THREE.BoxGeometry(0.1, 0.34, 0.1)), p.金属材, [0, 1.1, -0.2]));
  group.add(メッシュ(ジオメトリ(new THREE.BoxGeometry(0.5, 0.03, 0.24)), p.金属材, [0.05, 1.02, 0.28]));
  // 切り株の椅子
  const stump = メッシュ(ジオメトリ(new THREE.CylinderGeometry(0.3, 0.34, 0.52, 12)), p.濃木材, [0, 0.26, 1.15]);
  group.add(stump);
  scene.add(group);
};

const 雑談スペースを作る = (x: number, z: number, color: number) => {
  if (!scene) return;
  const p = 部品を用意();
  const group = new THREE.Group();
  group.position.set(x, 0, z);
  const 傘布 = マテリアル(color, { roughness: 0.92, metalness: 0.0, side: THREE.DoubleSide });

  // 丸テーブルとパラソル
  group.add(メッシュ(ジオメトリ(new THREE.CylinderGeometry(1.6, 1.6, 0.12, 28)), p.木材, [0, 0.78, 0]));
  group.add(メッシュ(ジオメトリ(new THREE.CylinderGeometry(0.14, 0.18, 0.78, 12)), p.濃木材, [0, 0.39, 0]));
  group.add(メッシュ(ジオメトリ(new THREE.CylinderGeometry(0.055, 0.055, 3.0, 8)), p.木材, [0, 1.5, 0]));
  const 傘 = メッシュ(ジオメトリ(new THREE.ConeGeometry(2.3, 1.2, 10)), 傘布, [0, 2.86, 0]);
  group.add(傘);
  group.add(メッシュ(ジオメトリ(new THREE.SphereGeometry(0.09, 10, 8)), p.木材, [0, 3.52, 0]));

  // 丸太スツール（要員の立ち位置の内側に並べる）
  const 丸太 = ジオメトリ(new THREE.CylinderGeometry(0.3, 0.32, 0.48, 12));
  [
    [-2.5, -1.1],
    [2.5, -1.1],
    [-2.5, 1.6],
    [2.5, 1.6],
    [0, -2.7],
    [0, 3.0],
  ].forEach(([sx, sz]) => {
    group.add(メッシュ(丸太, p.濃木材, [sx, 0.24, sz]));
  });

  // マグカップ 3 つ
  const カップ = ジオメトリ(new THREE.CylinderGeometry(0.09, 0.08, 0.16, 10));
  group.add(メッシュ(カップ, p.布材, [-0.5, 0.92, 0.3]));
  group.add(メッシュ(カップ, p.布材, [0.55, 0.92, -0.18]));
  group.add(メッシュ(カップ, p.布材, [0.1, 0.92, 0.72]));
  scene.add(group);
};

const 瞑想スペースを作る = (x: number, z: number, seed = 5) => {
  if (!scene) return;
  const p = 部品を用意();
  const group = new THREE.Group();
  group.position.set(x, 0, z);
  const 敷石 = マテリアル(0xb9b3a2, { roughness: 0.92, metalness: 0.03 });
  const 座布 = マテリアル(0xd8a25c, { roughness: 0.9, metalness: 0.0 });

  group.add(メッシュ(ジオメトリ(new THREE.CylinderGeometry(1.7, 1.8, 0.1, 36)), 敷石, [0, 0.05, 0]));
  const cushion = メッシュ(ジオメトリ(new THREE.CylinderGeometry(0.66, 0.72, 0.2, 24)), 座布, [0, 0.2, 0]);
  cushion.scale.z = 0.82;
  group.add(cushion);
  // 縁を小石で囲む
  const 乱数 = 乱数を作る(seed);
  for (let index = 0; index < 9; index += 1) {
    const 角度 = (index / 9) * Math.PI * 2;
    const rock = new THREE.Mesh(p.石, p.石材);
    rock.position.set(Math.cos(角度) * 1.62, 0.12, Math.sin(角度) * 1.62);
    rock.scale.setScalar(0.34 + 乱数() * 0.22);
    rock.rotation.set(乱数(), 乱数() * 3, 乱数());
    rock.castShadow = true;
    rock.receiveShadow = true;
    group.add(rock);
  }
  scene.add(group);
};

const 石灯籠を作る = (x: number, z: number) => {
  if (!scene) return;
  const 石 = マテリアル(0xa8a294, { roughness: 0.9, metalness: 0.04 });
  const 灯 = マテリアル(0xfff0c4, {
    emissive: 0xffc861,
    emissiveIntensity: 1.1,
    roughness: 0.4,
  });
  const group = new THREE.Group();
  group.position.set(x, 0, z);
  group.add(メッシュ(ジオメトリ(new THREE.CylinderGeometry(0.26, 0.32, 0.6, 8)), 石, [0, 0.3, 0]));
  group.add(メッシュ(ジオメトリ(new THREE.CylinderGeometry(0.14, 0.14, 0.5, 8)), 石, [0, 0.85, 0]));
  group.add(メッシュ(ジオメトリ(new THREE.BoxGeometry(0.42, 0.34, 0.42)), 灯, [0, 1.25, 0]));
  const 笠 = メッシュ(ジオメトリ(new THREE.ConeGeometry(0.42, 0.3, 8)), 石, [0, 1.56, 0]);
  group.add(笠);
  scene.add(group);
};

const ベンチを作る = (x: number, z: number, rotation = 0) => {
  if (!scene) return;
  const p = 部品を用意();
  const group = new THREE.Group();
  group.position.set(x, 0, z);
  group.rotation.y = rotation;
  group.add(メッシュ(ジオメトリ(new THREE.BoxGeometry(1.9, 0.1, 0.62)), p.木材, [0, 0.46, 0]));
  group.add(メッシュ(ジオメトリ(new THREE.BoxGeometry(1.9, 0.5, 0.09)), p.木材, [0, 0.74, -0.28]));
  const 脚 = ジオメトリ(new THREE.BoxGeometry(0.1, 0.46, 0.5));
  group.add(メッシュ(脚, p.濃木材, [-0.78, 0.23, 0]));
  group.add(メッシュ(脚, p.濃木材, [0.78, 0.23, 0]));
  scene.add(group);
};

const ハンモックを作る = (x: number, z: number) => {
  if (!scene) return;
  const p = 部品を用意();
  const group = new THREE.Group();
  group.position.set(x, 0, z);
  const 布 = マテリアル(0x7be3b0, { roughness: 0.9, metalness: 0.0, side: THREE.DoubleSide });
  const 支柱 = ジオメトリ(new THREE.CylinderGeometry(0.09, 0.11, 1.7, 8));
  group.add(メッシュ(支柱, p.濃木材, [-1.5, 0.85, 0]));
  group.add(メッシュ(支柱, p.濃木材, [1.5, 0.85, 0]));
  // 上半分を開いた半円筒を吊って、たわんだ布に見せる
  const hammock = メッシュ(
    ジオメトリ(new THREE.CylinderGeometry(0.52, 0.52, 2.4, 16, 1, true, 0, Math.PI)),
    布,
    [0, 0.95, 0],
  );
  hammock.rotation.z = Math.PI / 2;
  hammock.rotation.x = Math.PI;
  group.add(hammock);
  const 吊り紐 = ジオメトリ(new THREE.CylinderGeometry(0.02, 0.02, 0.75, 6));
  group.add(メッシュ(吊り紐, p.木材, [-1.4, 1.3, 0]), メッシュ(吊り紐, p.木材, [1.4, 1.3, 0]));
  scene.add(group);
};

// 炎は出さず、石で囲った薪だけを置く（焚き火跡）
const 焚き火跡を作る = (x: number, z: number) => {
  if (!scene) return;
  const p = 部品を用意();
  const group = new THREE.Group();
  group.position.set(x, 0, z);
  for (let index = 0; index < 7; index += 1) {
    const 角度 = (index / 7) * Math.PI * 2;
    const rock = new THREE.Mesh(p.石, p.石材);
    rock.position.set(Math.cos(角度) * 0.62, 0.1, Math.sin(角度) * 0.62);
    rock.scale.setScalar(0.3);
    rock.castShadow = true;
    group.add(rock);
  }
  const 薪 = ジオメトリ(new THREE.CylinderGeometry(0.07, 0.07, 0.9, 6));
  for (let index = 0; index < 3; index += 1) {
    const log = メッシュ(薪, p.濃木材, [0, 0.14, 0]);
    log.rotation.set(Math.PI / 2.4, (index / 3) * Math.PI, 0);
    group.add(log);
  }
  scene.add(group);
};

const 道標を作る = (x: number, z: number) => {
  if (!scene) return;
  const p = 部品を用意();
  const group = new THREE.Group();
  group.position.set(x, 0, z);
  group.add(メッシュ(ジオメトリ(new THREE.CylinderGeometry(0.09, 0.11, 2.3, 8)), p.濃木材, [0, 1.15, 0]));
  // 4エリアの方向へ矢印板を向ける
  const 板 = ジオメトリ(new THREE.BoxGeometry(1.0, 0.2, 0.05));
  (Object.keys(エリア座標) as エリアキー[]).forEach((key, index) => {
    const [cx, cz] = エリア中心(key);
    const 矢印 = メッシュ(板, p.木材, [0, 1.95 - index * 0.32, 0]);
    矢印.rotation.y = Math.atan2(cx - x, cz - z);
    矢印.position.x = Math.sin(矢印.rotation.y) * 0.44;
    矢印.position.z = Math.cos(矢印.rotation.y) * 0.44;
    group.add(矢印);
  });
  group.add(メッシュ(ジオメトリ(new THREE.ConeGeometry(0.14, 0.22, 8)), p.濃木材, [0, 2.4, 0]));
  scene.add(group);
};

const 池を作る = (x: number, z: number, radius = 2.4, seed = 9) => {
  if (!scene) return;
  const p = 部品を用意();
  const 乱数 = 乱数を作る(seed);
  const group = new THREE.Group();
  group.position.set(x, 0, z);
  const 水 = マテリアル(0x5fb3d4, {
    roughness: 0.18,
    metalness: 0.35,
    transparent: true,
    opacity: 0.88,
  });
  const 岸 = マテリアル(0xc4b48c, { roughness: 0.95, metalness: 0.02 });
  const bank = メッシュ(ジオメトリ(new THREE.CylinderGeometry(radius + 0.35, radius + 0.5, 0.12, 36)), 岸, [0, 0.02, 0]);
  bank.castShadow = false;
  group.add(bank);
  const water = メッシュ(ジオメトリ(new THREE.CircleGeometry(radius, 36)), 水, [0, 0.09, 0]);
  water.rotation.x = -Math.PI / 2;
  water.castShadow = false;
  group.add(water);
  // 岸辺の石と葦
  for (let index = 0; index < 7; index += 1) {
    const 角度 = (index / 7) * Math.PI * 2 + 乱数();
    const rock = new THREE.Mesh(p.石, p.石材);
    rock.position.set(Math.cos(角度) * (radius + 0.4), 0.12, Math.sin(角度) * (radius + 0.4));
    rock.scale.setScalar(0.4 + 乱数() * 0.3);
    rock.rotation.set(乱数(), 乱数() * 3, 乱数());
    rock.castShadow = true;
    group.add(rock);
  }
  for (let index = 0; index < 12; index += 1) {
    const 角度 = 乱数() * Math.PI * 2;
    const reed = new THREE.Mesh(p.草, p.草材);
    reed.position.set(
      Math.cos(角度) * (radius + 0.15 + 乱数() * 0.5),
      0.34,
      Math.sin(角度) * (radius + 0.15 + 乱数() * 0.5),
    );
    reed.scale.set(0.8, 2.1 + 乱数(), 0.8);
    group.add(reed);
  }
  scene.add(group);
};

const 柵を作る = (x: number, z: number, rotation = 0, 本数 = 4) => {
  if (!scene) return;
  const p = 部品を用意();
  const group = new THREE.Group();
  group.position.set(x, 0, z);
  group.rotation.y = rotation;
  const 杭 = ジオメトリ(new THREE.CylinderGeometry(0.06, 0.07, 1, 6));
  const 横板 = ジオメトリ(new THREE.BoxGeometry(1.5, 0.1, 0.05));
  for (let index = 0; index < 本数; index += 1) {
    group.add(メッシュ(杭, p.濃木材, [index * 1.5, 0.5, 0]));
    if (index < 本数 - 1) {
      group.add(メッシュ(横板, p.木材, [index * 1.5 + 0.75, 0.72, 0]));
      group.add(メッシュ(横板, p.木材, [index * 1.5 + 0.75, 0.42, 0]));
    }
  }
  scene.add(group);
};

const 地面パッチを作る = (
  x: number,
  z: number,
  radius: number,
  color: number,
  種類: '芝' | 'デッキ' | '砂利' | '石畳',
) => {
  if (!scene) return;
  const 下地色 = 種類 === 'デッキ' ? 0xb5824a : 種類 === '砂利' ? 0xd9c9a3 : 種類 === '石畳' ? 0xbdb7a6 : 0x86bd63;
  const 下地 = マテリアル(下地色, { roughness: 0.93, metalness: 0.02 });
  const patch = メッシュ(
    ジオメトリ(new THREE.CylinderGeometry(radius, radius + 0.12, 0.12, 48)),
    下地,
    [x, 0.03, z],
  );
  patch.castShadow = false;
  scene.add(patch);

  if (種類 === 'デッキ') {
    const 板 = マテリアル(0x9c6a3c, { roughness: 0.88, metalness: 0.02 });
    // 板の長さを円の弦から求め、丸いデッキの継ぎ目に見えるようにする
    const 本数 = 6;
    const 間隔 = radius / (本数 + 1);
    for (let index = -本数; index <= 本数; index += 1) {
      const オフセット = index * 間隔;
      const 長さ = Math.sqrt(Math.max(radius * radius - オフセット * オフセット, 0)) * 1.94;
      const plank = メッシュ(
        ジオメトリ(new THREE.BoxGeometry(長さ, 0.02, 0.07)),
        板,
        [x, 0.095, z + オフセット],
      );
      plank.castShadow = false;
      scene.add(plank);
    }
  }

  const ringMaterial = new THREE.MeshBasicMaterial({
    color,
    transparent: true,
    opacity: 0.42,
    side: THREE.DoubleSide,
  });
  破棄対象.push(ringMaterial);
  const ring = メッシュ(
    ジオメトリ(new THREE.RingGeometry(radius - 0.14, radius + 0.02, 48)),
    ringMaterial,
    [x, 0.095, z],
  );
  ring.rotation.x = -Math.PI / 2;
  ring.castShadow = false;
  scene.add(ring);
};

// チーム目標のテキストを大きな板に描く（神の声のように読ませたいので余白と行間を広く取る）
const 目標テクスチャへ描く = (canvas: HTMLCanvasElement) => {
  const context = canvas.getContext('2d');
  if (!context) return;
  const 目標 = props.チーム目標;
  const 本文 = String(目標?.チーム目標 ?? '').trim() || 'チーム目標が未登録です';
  const パス = String(目標?.CODE_BASE_PATH ?? '').trim();
  const 更新 = String(目標?.更新日時 ?? '').trim();

  context.clearRect(0, 0, canvas.width, canvas.height);
  const 背景 = context.createLinearGradient(0, 0, 0, canvas.height);
  背景.addColorStop(0, '#fffdf0');
  背景.addColorStop(1, '#e3f0e2');
  context.fillStyle = 背景;
  context.fillRect(0, 0, canvas.width, canvas.height);
  context.strokeStyle = 'rgba(120, 160, 120, 0.55)';
  context.lineWidth = 10;
  context.strokeRect(5, 5, canvas.width - 10, canvas.height - 10);
  context.fillStyle = 'rgba(96, 150, 108, 0.9)';
  context.fillRect(0, 0, canvas.width, 12);
  context.fillRect(0, canvas.height - 12, canvas.width, 12);

  context.textBaseline = 'alphabetic';
  context.font = '700 40px "Yu Gothic", "Meiryo", sans-serif';
  context.fillStyle = '#4a7c59';
  context.fillText('TEAM GOAL  /  チーム目標', 60, 78);
  if (パス) {
    context.font = '600 34px "Yu Gothic", "Meiryo", sans-serif';
    context.fillStyle = '#7a6a3c';
    context.textAlign = 'right';
    context.fillText(パス, canvas.width - 60, 78);
    context.textAlign = 'left';
  }
  context.fillStyle = 'rgba(120, 160, 120, 0.45)';
  context.fillRect(60, 100, canvas.width - 120, 3);

  // 本文は板幅に合わせて折り返す（最大 4 行。溢れたら末尾を … にする）
  context.font = '700 66px "Yu Gothic", "Meiryo", sans-serif';
  context.fillStyle = '#2f3a2f';
  const 最大幅 = canvas.width - 130;
  const 行: string[] = [];
  本文.split(/\r?\n/).forEach((段落) => {
    let 現在行 = '';
    Array.from(段落).forEach((文字) => {
      const 候補 = 現在行 + 文字;
      if (context.measureText(候補).width > 最大幅 && 現在行) {
        行.push(現在行);
        現在行 = 文字;
      } else {
        現在行 = 候補;
      }
    });
    行.push(現在行);
  });
  const 最大行数 = 4;
  const 表示行 = 行.slice(0, 最大行数);
  if (行.length > 最大行数 && 表示行.length > 0) {
    表示行[表示行.length - 1] = `${表示行[表示行.length - 1].slice(0, -1)}…`;
  }
  // 本文の描画域は y=130〜470（下の最終更新行に重ならない範囲）
  const 行高 = 84;
  const 開始Y = 130 + (最大行数 - 表示行.length) * (行高 / 2) + 行高 * 0.72;
  表示行.forEach((行文字, index) => {
    context.fillText(行文字, 65, 開始Y + index * 行高);
  });

  context.font = '600 30px "Yu Gothic", "Meiryo", sans-serif';
  context.fillStyle = 'rgba(90, 110, 90, 0.8)';
  context.fillText(更新 ? `最終更新 ${更新}` : 'クリックで保守', 62, canvas.height - 34);
  context.textAlign = 'right';
  context.fillText('クリックで保守', canvas.width - 62, canvas.height - 34);
  context.textAlign = 'left';
};

const 目標掲示板を作る = () => {
  if (!scene) return;
  const canvas = document.createElement('canvas');
  canvas.width = 1536;
  canvas.height = 544;
  目標テクスチャへ描く(canvas);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.minFilter = THREE.LinearFilter;
  破棄テクスチャ.push(texture);
  目標テクスチャ = texture;
  目標テクスチャ.userData.canvas = canvas;

  const group = new THREE.Group();
  // 初期位置は飛行船が最初の更新で上書きする
  group.position.set(0, 10, 0);
  group.name = 'team-goal-board';

  const 板材 = new THREE.MeshBasicMaterial({ map: texture, toneMapped: false });
  破棄対象.push(板材);
  const 板 = new THREE.Mesh(
    ジオメトリ(new THREE.PlaneGeometry(目標掲示板幅, 目標掲示板縦)),
    板材,
  );
  板.name = 'team-goal-panel';
  板.userData.目標掲示板 = true;
  group.add(板);
  目標掲示板.板 = 板;

  // 光の縁取り（神の声らしさ）
  const 縁材 = new THREE.MeshBasicMaterial({
    color: 0xfff6d0,
    transparent: true,
    opacity: 0.42,
    side: THREE.DoubleSide,
    depthWrite: false,
  });
  破棄対象.push(縁材);
  const 縁 = new THREE.Mesh(
    ジオメトリ(new THREE.PlaneGeometry(目標掲示板幅 + 0.7, 目標掲示板縦 + 0.7)),
    縁材,
  );
  縁.position.z = -0.05;
  group.add(縁);
  目標掲示板.縁 = 縁;

  // 改善ループ中は、掲示板全体へ薄いピンクの明滅を重ねる。
  const 改善明滅材 = new THREE.MeshBasicMaterial({
    color: 0xff1493,
    transparent: true,
    opacity: 0,
    side: THREE.DoubleSide,
    depthWrite: false,
    toneMapped: false,
    blending: THREE.AdditiveBlending,
  });
  破棄対象.push(改善明滅材);
  const 改善明滅 = new THREE.Mesh(
    ジオメトリ(new THREE.PlaneGeometry(目標掲示板幅, 目標掲示板縦)),
    改善明滅材,
  );
  改善明滅.position.z = 0.035;
  改善明滅.visible = Boolean(props.チーム目標?.改善ループ);
  改善明滅.renderOrder = 2;
  group.add(改善明滅);
  目標掲示板.改善明滅 = 改善明滅;

  // ネオン管の白い発光芯。外側のピンクの縁と重ねて、光のにじみを作る。
  const ネオン芯材 = new THREE.MeshBasicMaterial({
    color: 0xffeaf6,
    transparent: true,
    opacity: 0,
    depthWrite: false,
    toneMapped: false,
    blending: THREE.AdditiveBlending,
  });
  破棄対象.push(ネオン芯材);
  const ネオン芯 = new THREE.Group();
  const 横芯形状 = ジオメトリ(new THREE.BoxGeometry(目標掲示板幅 + 0.42, 0.1, 0.06));
  const 縦芯形状 = ジオメトリ(new THREE.BoxGeometry(0.1, 目標掲示板縦 + 0.42, 0.06));
  [-1, 1].forEach((方向) => {
    const 横芯 = new THREE.Mesh(横芯形状, ネオン芯材);
    横芯.position.set(0, 方向 * (目標掲示板縦 / 2 + 0.2), 0.065);
    ネオン芯.add(横芯);
    const 縦芯 = new THREE.Mesh(縦芯形状, ネオン芯材);
    縦芯.position.set(方向 * (目標掲示板幅 / 2 + 0.2), 0, 0.065);
    ネオン芯.add(縦芯);
  });
  ネオン芯.visible = Boolean(props.チーム目標?.改善ループ);
  ネオン芯.renderOrder = 3;
  group.add(ネオン芯);
  目標掲示板.改善ネオン芯 = ネオン芯;

  scene.add(group);
  目標掲示板.group = group;
};

const 目標掲示板を更新 = () => {
  const canvas = 目標テクスチャ?.userData.canvas as HTMLCanvasElement | undefined;
  if (!目標テクスチャ || !canvas) return;
  目標テクスチャへ描く(canvas);
  目標テクスチャ.needsUpdate = true;
};

const 掲示板を作る = (
  title: string,
  englishTitle: string,
  messages: [string, string],
  position: [number, number],
  color: number,
) => {
  if (!scene) return;
  const canvas = document.createElement('canvas');
  canvas.width = 1024;
  canvas.height = 512;
  const context = canvas.getContext('2d');
  if (!context) return;

  // 草原になじむ木札の案内板（木目の下地 + エリア色の帯）
  const accent = `#${color.toString(16).padStart(6, '0')}`;
  context.fillStyle = '#e6d3ab';
  context.fillRect(0, 0, canvas.width, canvas.height);
  context.strokeStyle = 'rgba(150, 111, 62, 0.22)';
  context.lineWidth = 3;
  for (let y = 24; y < canvas.height; y += 34) {
    context.beginPath();
    context.moveTo(0, y);
    context.bezierCurveTo(280, y - 9, 700, y + 9, canvas.width, y);
    context.stroke();
  }
  context.fillStyle = accent;
  context.fillRect(0, 0, canvas.width, 14);
  context.fillRect(0, canvas.height - 14, canvas.width, 14);
  context.fillRect(54, 96, 132, 8);
  context.font = '700 42px "Yu Gothic", "Meiryo", sans-serif';
  context.fillStyle = '#7a5a2c';
  context.fillText(englishTitle, 54, 78);
  context.font = '700 82px "Yu Gothic", "Meiryo", sans-serif';
  context.fillStyle = '#3f2f16';
  context.fillText(title, 54, 196);
  context.fillStyle = 'rgba(122, 90, 44, 0.32)';
  context.fillRect(54, 232, 910, 3);
  context.font = '500 37px "Yu Gothic", "Meiryo", sans-serif';
  context.fillStyle = '#5b4423';
  context.fillText(messages[0], 54, 310);
  context.fillText(messages[1], 54, 374);
  context.font = '600 25px "Yu Gothic", "Meiryo", sans-serif';
  context.fillStyle = 'rgba(122, 90, 44, 0.72)';
  context.fillText('MEADOW AREA BOARD  /  LIVE', 54, 452);

  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.minFilter = THREE.LinearFilter;
  texture.needsUpdate = true;
  破棄テクスチャ.push(texture);

  const group = new THREE.Group();
  group.position.set(position[0], 掲示板高さ, position[1]);
  group.name = 'area-board';
  const frameMaterial = マテリアル(0x8a5c33, {
    metalness: 0.04,
    roughness: 0.85,
  });
  const screenMaterial = new THREE.MeshBasicMaterial({
    map: texture,
    toneMapped: false,
  });
  破棄対象.push(screenMaterial);
  group.add(
    メッシュ(ジオメトリ(new THREE.BoxGeometry(3.3, 1.85, 0.14)), frameMaterial, [0, 0, 0]),
    メッシュ(ジオメトリ(new THREE.PlaneGeometry(3.08, 1.63)), screenMaterial, [0, 0, 0.08]),
  );
  // 木札を吊る横木（横向きに寝かせる）と縄
  const 横木 = メッシュ(ジオメトリ(new THREE.CylinderGeometry(0.055, 0.055, 3.9, 8)), frameMaterial, [0, 1.3, 0]);
  横木.rotation.z = Math.PI / 2;
  group.add(横木);
  const 縄材 = マテリアル(0xcdb182, { roughness: 0.95, metalness: 0.0 });
  const 縄 = ジオメトリ(new THREE.CylinderGeometry(0.02, 0.02, 0.4, 6));
  group.add(メッシュ(縄, 縄材, [-1.2, 1.11, 0]), メッシュ(縄, 縄材, [1.2, 1.11, 0]));
  scene.add(group);
  掲示板一覧.push(group);
};

const エージェントモデルを作る = (agent: エージェント): THREE.Group => {
  const group = new THREE.Group();
  group.userData.agentId = agent.id;

  // 上着は要員色、下半身と装備は共通色で人型のシルエットを作る
  const 上着 = マテリアル(agent.色, {
    emissive: agent.色,
    emissiveIntensity: 0.06,
    metalness: 0.1,
    roughness: 0.62,
  });
  const 濃色 = マテリアル(0x3c4a5c, { metalness: 0.12, roughness: 0.72 });
  const 肌 = マテリアル(0xf3ddc4, { metalness: 0.02, roughness: 0.78 });
  const 髪 = マテリアル(0x4a3b32, { metalness: 0.05, roughness: 0.8 });
  const 白 = マテリアル(0xf7fbff, { metalness: 0.04, roughness: 0.5 });
  const 目 = マテリアル(0x23303d, { metalness: 0.05, roughness: 0.35 });
  const 発光 = マテリアル(0xffffff, {
    emissive: agent.色,
    emissiveIntensity: 1.5,
    roughness: 0.2,
  });

  // 脚（歩行アニメーション用に前後へ振る）
  const 脚形 = ジオメトリ(new THREE.CapsuleGeometry(0.11, 0.42, 4, 8));
  const 靴形 = ジオメトリ(new THREE.BoxGeometry(0.2, 0.1, 0.3));
  const leftLeg = new THREE.Group();
  leftLeg.name = 'leftLeg';
  leftLeg.position.set(-0.15, 0.62, 0);
  leftLeg.add(メッシュ(脚形, 濃色, [0, -0.3, 0]), メッシュ(靴形, 髪, [0, -0.57, 0.05]));
  const rightLeg = new THREE.Group();
  rightLeg.name = 'rightLeg';
  rightLeg.position.set(0.15, 0.62, 0);
  rightLeg.add(メッシュ(脚形, 濃色, [0, -0.3, 0]), メッシュ(靴形, 髪, [0, -0.57, 0.05]));

  // 胴（上着 + 襟 + 胸の要員色ランプ）
  const body = new THREE.Group();
  body.name = 'body';
  body.add(メッシュ(ジオメトリ(new THREE.CapsuleGeometry(0.28, 0.42, 5, 14)), 上着, [0, 0.95, 0]));
  body.add(メッシュ(ジオメトリ(new THREE.CylinderGeometry(0.3, 0.34, 0.14, 14)), 濃色, [0, 0.66, 0]));
  body.add(メッシュ(ジオメトリ(new THREE.CylinderGeometry(0.14, 0.17, 0.1, 12)), 白, [0, 1.24, 0]));
  body.add(メッシュ(ジオメトリ(new THREE.SphereGeometry(0.055, 10, 8)), 発光, [0, 1.06, 0.27]));

  // 腕（肩を支点に振る）
  const 腕形 = ジオメトリ(new THREE.CapsuleGeometry(0.085, 0.36, 4, 8));
  const 手形 = ジオメトリ(new THREE.SphereGeometry(0.1, 10, 8));
  const leftArm = new THREE.Group();
  leftArm.name = 'leftArm';
  leftArm.position.set(-0.36, 1.19, 0);
  leftArm.rotation.z = 0.16;
  leftArm.add(メッシュ(腕形, 上着, [0, -0.22, 0]), メッシュ(手形, 肌, [0, -0.46, 0]));
  const rightArm = new THREE.Group();
  rightArm.name = 'rightArm';
  rightArm.position.set(0.36, 1.19, 0);
  rightArm.rotation.z = -0.16;
  rightArm.add(メッシュ(腕形, 上着, [0, -0.22, 0]), メッシュ(手形, 肌, [0, -0.46, 0]));

  // 頭（顔・髪・目・アンテナ）
  const head = new THREE.Group();
  head.name = 'head';
  head.position.set(0, 1.34, 0);
  const 顔 = メッシュ(ジオメトリ(new THREE.SphereGeometry(0.27, 20, 16)), 肌, [0, 0.27, 0]);
  顔.scale.set(1, 1.06, 0.96);
  head.add(顔);
  const 前髪 = メッシュ(
    ジオメトリ(new THREE.SphereGeometry(0.285, 18, 14, 0, Math.PI * 2, 0, Math.PI / 1.9)),
    髪,
    [0, 0.29, 0],
  );
  前髪.scale.set(1, 0.92, 1);
  head.add(前髪);
  const 目形 = ジオメトリ(new THREE.SphereGeometry(0.037, 10, 8));
  head.add(メッシュ(目形, 目, [-0.095, 0.28, 0.235]), メッシュ(目形, 目, [0.095, 0.28, 0.235]));
  head.add(メッシュ(ジオメトリ(new THREE.CylinderGeometry(0.014, 0.014, 0.2, 6)), 濃色, [0.1, 0.55, 0]));
  head.add(メッシュ(ジオメトリ(new THREE.SphereGeometry(0.055, 10, 8)), 発光, [0.1, 0.67, 0]));

  const ringMaterial = new THREE.MeshBasicMaterial({
    color: agent.色,
    transparent: true,
    opacity: 0.4,
    side: THREE.DoubleSide,
    depthWrite: false,
  });
  破棄対象.push(ringMaterial);
  const ring = メッシュ(ジオメトリ(new THREE.RingGeometry(0.42, 0.5, 32)), ringMaterial, [0, 0.02, 0]);
  ring.rotation.x = -Math.PI / 2;
  ring.castShadow = false;
  ring.name = 'ring';

  group.add(leftLeg, rightLeg, body, leftArm, rightArm, head, ring);
  group.position.copy(エリア位置(agent.状態));
  group.traverse((object) => {
    object.userData.agentId = agent.id;
    if (object instanceof THREE.Mesh && object.name !== 'ring') {
      object.castShadow = true;
      object.receiveShadow = true;
    }
  });
  return group;
};

const エージェントを追加 = (agent: エージェント, index: number) => {
  if (!scene || 実行状態一覧.has(agent.id)) return;
  const group = エージェントモデルを作る(agent);
  const startPosition = エリア位置(agent.状態, index);
  group.position.copy(startPosition);
  scene.add(group);
  実行状態一覧.set(agent.id, {
    group: markRaw(group),
    目的地: startPosition.clone(),
    位相: Math.random() * Math.PI * 2,
    速度: 0.65 + Math.random() * 0.2,
    割当状態: agent.状態,
    次自由行動時刻: 経過時間 + 2 + Math.random() * 4,
    はまり残り: 0,
    穴無視残り: 0,
    はまった穴: new THREE.Vector3(),
  });
};

const エージェント表示を同期 = () => {
  if (!scene) return;
  const currentIds = new Set(エージェント一覧.value.map((agent) => agent.id));
  実行状態一覧.forEach((runtime, id) => {
    if (currentIds.has(id)) return;
    scene?.remove(runtime.group);
    実行状態一覧.delete(id);
    ラベル要素.delete(id);
  });
  エージェント一覧.value.forEach((agent, index) => {
    エージェントを追加(agent, index);
  });
};

const シーンを作る = () => {
  if (!canvasRef.value || !stageRef.value) return;

  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x9fd4ea);
  // 遠景の丘がうっすら霞むように、空色寄りのフォグを薄くかける
  scene.fog = new THREE.Fog(0xcfe8ee, 74, 146);

  camera = new THREE.PerspectiveCamera(42, 1, 0.1, 220);
  // 空と稜線が見える低めの視点から始める
  camera.position.set(30, 18, 30);

  renderer = new THREE.WebGLRenderer({
    canvas: canvasRef.value,
    antialias: true,
    alpha: false,
    powerPreference: 'high-performance',
  });
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.28;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.8));

  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.075;
  controls.enablePan = false;
  controls.minDistance = 12;
  controls.maxDistance = 78;
  controls.minPolarAngle = 0.28;
  controls.maxPolarAngle = Math.PI / 2.22;
  controls.target.set(0, 1.5, 0);
  controls.update();

  // 昼の草原の光（空色の環境光 + 温かい太陽光）
  scene.add(new THREE.HemisphereLight(0xdff1ff, 0x6f9c52, 1.15));
  const keyLight = new THREE.DirectionalLight(0xfff3d6, 2.5);
  keyLight.position.set(-24, 30, -18);
  keyLight.castShadow = true;
  keyLight.shadow.mapSize.set(2048, 2048);
  keyLight.shadow.camera.left = -32;
  keyLight.shadow.camera.right = 32;
  keyLight.shadow.camera.top = 32;
  keyLight.shadow.camera.bottom = -32;
  keyLight.shadow.camera.far = 110;
  keyLight.shadow.normalBias = 0.02;
  scene.add(keyLight);
  const fillLight = new THREE.DirectionalLight(0xd7ecff, 0.5);
  fillLight.position.set(18, 14, 21);
  scene.add(fillLight);

  空を作る();
  草原を作る();
  小道を作る();

  // 4エリアはグリッド座標から中心を求めて、草原の地面パッチとして配置する
  const パッチ種類: Record<エリアキー, '芝' | 'デッキ' | '砂利' | '石畳'> = {
    仕事: 'デッキ',
    雑談: '砂利',
    瞑想: '石畳',
    休憩: '芝',
  };
  (Object.keys(エリア座標) as エリアキー[]).forEach((key) => {
    const [cx, cz] = エリア中心(key);
    地面パッチを作る(cx, cz, 台座半径, エリア座標[key].色, パッチ種類[key]);
  });

  {
    // 仕事エリア: 日除けテントの下に、座席位置と同じ並びで机を置く
    const [cx, cz] = エリア中心('仕事');
    作業テントを作る(cx, cz, エリア座標.仕事.色);
    座席オフセット.forEach(([ox, oz]) => {
      作業机を作る(cx + ox, cz + oz - 0.1, 0);
    });
    茂みを作る(cx + 5.4, cz + 5.0, 1, 101);
    花畑を作る(cx - 5.4, cz + 5.0, 1.6, 12, 102);
    石を置く(cx - 5.6, cz - 4.8, 0.95, 103);
  }
  {
    // 雑談エリア: パラソル付きの丸テーブルと丸太スツール
    const [cx, cz] = エリア中心('雑談');
    雑談スペースを作る(cx, cz, エリア座標.雑談.色);
    木を作る(cx - 5.2, cz + 4.8, 1.05, 111);
    茂みを作る(cx + 5.3, cz - 4.9, 0.95, 112);
    花畑を作る(cx + 5.0, cz + 5.0, 1.8, 14, 113);
    ベンチを作る(cx - 5.4, cz - 1.2, Math.PI / 2);
  }
  {
    // 瞑想エリア: 石畳の座と灯籠、静かな小石まわり
    const [cx, cz] = エリア中心('瞑想');
    瞑想スペースを作る(cx - 2.9, cz - 0.6, 121);
    瞑想スペースを作る(cx + 2.9, cz - 0.6, 122);
    瞑想スペースを作る(cx, cz + 3.4, 123);
    石灯籠を作る(cx - 5.2, cz - 4.4);
    石灯籠を作る(cx + 5.2, cz - 4.4);
    石灯籠を作る(cx, cz - 5.4);
    石を置く(cx + 5.2, cz + 4.6, 1.15, 124);
    茂みを作る(cx - 5.3, cz + 4.7, 0.9, 125);
  }
  {
    // 休憩エリア: ハンモック・ベンチ・焚き火
    const [cx, cz] = エリア中心('休憩');
    ハンモックを作る(cx, cz - 2.2);
    ベンチを作る(cx - 5.0, cz - 0.4, Math.PI / 2);
    ベンチを作る(cx + 5.0, cz - 0.4, -Math.PI / 2);
    ベンチを作る(cx - 1.9, cz + 5.2, Math.PI);
    焚き火跡を作る(cx, cz + 2.0);
    木を作る(cx + 5.4, cz + 5.2, 1.05, 131);
    花畑を作る(cx - 5.2, cz - 5.0, 1.7, 12, 132);
  }

  // 4エリアの外周に木立・茂み・花・石を散らして「草原の中にいる」感じを作る
  {
    const 乱数 = 乱数を作る(50607);
    // 斜め方向はエリア中心が最も遠いので、その外周（対角の中心距離 + 台座半径）を基準に散らす
    const 内側 = (グリッド間隔 / 2) * Math.SQRT2 + 台座半径;
    const エリア中心一覧 = (Object.keys(エリア座標) as エリアキー[]).map((key) => エリア中心(key));
    // エリアの円の中に小物が乗らないようにする
    const エリア内 = (x: number, z: number) =>
      エリア中心一覧.some(([cx, cz]) => Math.hypot(x - cx, z - cz) < 台座半径 + 1);
    // 1つ目の池はカモの住処。奥に置くとカモが見えないため、中央通路の南端（z=19.3）と
    // 掲示板（z=20.9）を避けたうえで手前へ寄せている
    const 池位置: [number, number, number][] = [
      [0, 24, 3.4],
      [31, 5, 2.6],
    ];
    // 案内板や池の手前に木を置くと隠れてしまうため、その周囲は木立を避ける
    const 避ける位置: [number, number, number][] = [
      ...(Object.keys(エリア座標) as エリアキー[]).map((key) => {
        const [cx, cz] = エリア中心(key);
        const 北側 = key === '仕事' || key === '瞑想';
        return [cx, cz + (北側 ? -1 : 1) * 掲示板オフセット, 5.2] as [number, number, number];
      }),
      ...池位置.map(([px, pz, pr]) => [px, pz, pr + 2.6] as [number, number, number]),
    ];
    const 近すぎる = (x: number, z: number) =>
      避ける位置.some(([ax, az, ar]) => Math.hypot(x - ax, z - az) < ar);
    for (let index = 0; index < 44; index += 1) {
      const 角度 = (index / 44) * Math.PI * 2 + 乱数() * 0.16;
      const 距離 = 内側 + 1.5 + 乱数() * 21;
      const x = Math.cos(角度) * 距離;
      const z = Math.sin(角度) * 距離;
      if (エリア内(x, z)) continue;
      const 種 = 乱数();
      if (種 > 0.52) {
        if (近すぎる(x, z)) 花畑を作る(x, z, 1.8, 12, 400 + index);
        else 木を作る(x, z, 1.05 + 乱数() * 0.85, 200 + index);
      } else if (種 > 0.3) 茂みを作る(x, z, 0.85 + 乱数() * 0.7, 300 + index);
      else if (種 > 0.14) 花畑を作る(x, z, 1.6 + 乱数(), 10 + Math.floor(乱数() * 8), 400 + index);
      else 石を置く(x, z, 0.9 + 乱数() * 0.9, 500 + index);
    }
    // 十字の通路沿い（エリアの間）にも小さな彩りを置く
    for (let index = 0; index < 16; index += 1) {
      const 軸 = index % 4;
      const 段 = Math.floor(index / 4);
      const 距離 = 8 + 段 * 4.6;
      const 横 = (段 % 2 === 0 ? 1 : -1) * (通路幅 / 2 + 1.7);
      const [x, z] =
        軸 === 0 ? [距離, 横] : 軸 === 1 ? [-距離, 横] : 軸 === 2 ? [横, 距離] : [横, -距離];
      if (エリア内(x, z)) continue;
      花畑を作る(x, z, 1.1, 8, 600 + index);
    }
    // 4本の小道が交わる中心に道標、草原には池と柵を置いて風景に変化を付ける
    道標を作る(0, 0);
    目標掲示板を作る();
    池位置.forEach(([px, pz, pr], index) => 池を作る(px, pz, pr, 901 + index));
    柵を作る(-34, 8, Math.PI / 2, 6);
    柵を作る(32, -14, Math.PI / 2.4, 5);
    柵を作る(-11, 34, 0.15, 6);

    // --- NPC（ネコ・イヌ・馬・うさぎ・カモ・雲・蝶）---
    // 池は避けて歩くよう禁止円として渡す
    const NPC禁止円 = 池位置.map(
      ([px, pz, pr]) => [px, pz, pr + 1.2] as [number, number, number],
    );
    // 飛行船は 4 エリアの上空を旋回し、チーム目標の掲示板を吊り下げて運ぶ
    NPC一覧.push(
      NPCを配置(
        scene,
        '飛行船',
        NPC造形ヘルパー,
        { 位置: new THREE.Vector3(0, 0, 0), 種: 851 },
        { 吊り下げ物: 目標掲示板.group },
      ),
      NPCを配置(scene, 'ネコ', NPC造形ヘルパー, {
        位置: new THREE.Vector3(-6.5, 0, 5.5),
        禁止円: NPC禁止円,
      }),
      NPCを配置(scene, 'イヌ', NPC造形ヘルパー, {
        位置: new THREE.Vector3(7.5, 0, -5),
        禁止円: NPC禁止円,
      }),
    );
    // カメラから見て4エリアの向こう側を放牧エリアにする。白馬は離れたときだけ黒馬を追う
    const 黒馬 = NPCを配置(scene, '黒馬', NPC造形ヘルパー, {
      位置: new THREE.Vector3(0, 0, 0),
      種: 910,
    });
    const 白馬 = NPCを配置(
      scene,
      '白馬',
      NPC造形ヘルパー,
      { 位置: new THREE.Vector3(0, 0, 0), 種: 911 },
      { 追跡対象: 黒馬.group, 追従開始距離: 14, 追従終了距離: 7 },
    );
    NPC一覧.push(黒馬, 白馬);

    // うさぎは雑談エリアと休憩エリアの2つを遊び場にして、ぴょんぴょん跳ね回る。
    // 馬と同じ距離制御（追従開始 / 追従終了のヒステリシス）で、黒うさぎが主体に動き白うさぎが追う。
    {
      const [雑談x, 雑談z] = エリア中心('雑談');
      const [休憩x, 休憩z] = エリア中心('休憩');
      const 遊び場 = [
        { x: 雑談x, z: 雑談z, 半径: 台座半径 - 1.0 },
        { x: 休憩x, z: 休憩z, 半径: 台座半径 - 1.0 },
      ];
      // エリアの中央に置いた大きな備品には乗り上げないようにする
      const うさぎ禁止円: [number, number, number][] = [
        [雑談x, 雑談z, 2.2],
        [休憩x, 休憩z - 2.2, 2.0],
        [休憩x, 休憩z + 2.0, 1.1],
      ];
      const 黒うさぎ = NPCを配置(
        scene,
        '黒うさぎ',
        NPC造形ヘルパー,
        { 位置: new THREE.Vector3(雑談x + 3.2, 0, 雑談z + 3.4), 種: 930, 禁止円: うさぎ禁止円 },
        { 遊び場, 穴を掘る: うさぎ穴を掘る },
      );
      const 白うさぎ = NPCを配置(
        scene,
        '白うさぎ',
        NPC造形ヘルパー,
        { 位置: new THREE.Vector3(雑談x + 4.4, 0, 雑談z + 2.2), 種: 931, 禁止円: うさぎ禁止円 },
        {
          遊び場,
          穴を掘る: うさぎ穴を掘る,
          追跡対象: 黒うさぎ.group,
          追従開始距離: 5,
          追従終了距離: 2,
        },
      );
      NPC一覧.push(黒うさぎ, 白うさぎ);
    }

    // カモの親子。1つ目の池を住処にして、親カモが岸の散歩と水浴びを繰り返す。
    // 子カモは「これ以上親へ近づかない距離」を 0.5m から 0.2m 刻みで持たせてあり、
    // 親が離れるとそれぞれ自分の距離まで詰めるので、近い順の縦一列になる。
    // NPC群を更新 は配列順に進めるため、親を先に push して子が最新位置を見られるようにする。
    {
      const [池x, 池z, 池半径] = 池位置[0];
      const 水場 = { x: 池x, z: 池z, 半径: 池半径 };
      const カモ大 = NPCを配置(
        scene,
        'カモ大',
        NPC造形ヘルパー,
        { 位置: new THREE.Vector3(池x + 池半径 + 1.4, 0, 池z), 種: 920 },
        { 水場 },
      );
      NPC一覧.push(カモ大);
      for (let index = 0; index < 5; index += 1) {
        NPC一覧.push(
          NPCを配置(
            scene,
            'カモ小',
            NPC造形ヘルパー,
            {
              位置: new THREE.Vector3(
                池x + 池半径 + 1.4 + 0.5 + index * 0.2,
                0,
                池z + 0.1 * (index % 2 === 0 ? 1 : -1),
              ),
              種: 921 + index,
            },
            { 水場, 親: カモ大.group, 最小距離: 0.5 + index * 0.2 },
          ),
        );
      }
    }

    [
      [-5, 6, 0xfff0a0],
      [6.5, -7, 0xffc0dd],
      [1.5, 13, 0xc8f0ff],
      [-13, -2, 0xd8ffc0],
    ].forEach(([bx, bz, 色], index) => {
      NPC一覧.push(
        NPCを配置(
          scene!,
          '蝶',
          NPC造形ヘルパー,
          { 位置: new THREE.Vector3(bx, 1.5, bz), 種: 701 + index },
          { 色 },
        ),
      );
    });
    const 雲乱数 = 乱数を作る(20260725);
    for (let index = 0; index < 9; index += 1) {
      const 角度 = (index / 9) * Math.PI * 2 + 雲乱数() * 0.5;
      const 距離 = 48 + 雲乱数() * 32;
      NPC一覧.push(
        NPCを配置(scene, '雲', NPC造形ヘルパー, {
          位置: new THREE.Vector3(
            Math.cos(角度) * 距離,
            21 + 雲乱数() * 12,
            Math.sin(角度) * 距離,
          ),
          種: 801 + index,
        }),
      );
    }
  }

  {
    const [cx, cz] = エリア中心('仕事');
    掲示板を作る(
      '仕事エリア',
      'WORK AREA',
      ['担当タスクと進捗を共有', '集中して成果を積み上げる'],
      [cx, cz - 掲示板オフセット],
      0x5bd9ff,
    );
  }
  {
    const [cx, cz] = エリア中心('雑談');
    掲示板を作る(
      '雑談エリア',
      'CHAT AREA',
      ['発見・相談・アイデアを交換', '仲間との対話から次を見つける'],
      [cx, cz + 掲示板オフセット],
      0x8bb8ff,
    );
  }
  {
    const [cx, cz] = エリア中心('瞑想');
    掲示板を作る(
      '瞑想エリア',
      'MEDITATION AREA',
      ['静かに思考と文脈を整理', '自分の判断で次の行動を選ぶ'],
      [cx, cz - 掲示板オフセット],
      0xffcf73,
    );
  }
  {
    const [cx, cz] = エリア中心('休憩');
    掲示板を作る(
      '休憩エリア',
      'REST AREA',
      ['肩の力を抜いてひと休み', '次の集中に向けて英気を養う'],
      [cx, cz + 掲示板オフセット],
      0x7be3b0,
    );
  }

  resizeObserver = new ResizeObserver(サイズ更新);
  resizeObserver.observe(stageRef.value);
  サイズ更新();
  現在時刻.value = new Date().toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' });
  前フレーム時刻 = performance.now();
  animationId = requestAnimationFrame(描画);
};

const サイズ更新 = () => {
  if (!renderer || !camera || !stageRef.value) return;
  const width = Math.max(stageRef.value.clientWidth, 1);
  const height = Math.max(stageRef.value.clientHeight, 1);
  renderer.setSize(width, height, false);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
};

const 描画 = (時刻: number) => {
  if (!renderer || !scene || !camera) return;
  const rawDelta = Math.min((時刻 - 前フレーム時刻) / 1000, 0.05);
  前フレーム時刻 = 時刻;
  const delta = rawDelta * 経過速度倍率;
  経過時間 += delta;

  エージェント一覧.value.forEach((agent, index) => {
    const runtime = 実行状態一覧.get(agent.id);
    if (!runtime) return;
    const group = runtime.group;

    // --- うさぎ穴 ---
    // 歩いていて穴を踏み抜くと、しばらく抜け出せずにあたふたする
    if (delta > 0 && runtime.穴無視残り > 0) runtime.穴無視残り -= delta;
    if (delta > 0 && runtime.はまり残り <= 0 && runtime.穴無視残り <= 0) {
      const 穴 = はまる穴を探す(group.position);
      if (穴) {
        runtime.はまり残り = 2.4 + Math.random() * 1.8;
        runtime.はまった穴.copy(穴.position);
      }
    }
    const はまり中 = runtime.はまり残り > 0;
    if (はまり中 && delta > 0) {
      runtime.はまり残り -= delta;
      if (runtime.はまり残り <= 0) {
        // 這い上がって穴の外へ。すぐ落ち直さないよう猶予を置き、あわてて歩き出す
        const 逃げ = group.position.clone().sub(runtime.はまった穴);
        逃げ.y = 0;
        if (逃げ.lengthSq() < 1e-4) 逃げ.set(Math.random() - 0.5, 0, Math.random() - 0.5);
        逃げ.setLength(1.25);
        group.position.copy(runtime.はまった穴).add(逃げ);
        group.position.y = 要員基準Y;
        runtime.穴無視残り = 5;
        runtime.目的地.copy(エリア内自由位置(agent.状態));
        runtime.速度 = 0.85;
        runtime.次自由行動時刻 = Number.POSITIVE_INFINITY;
      }
    }

    // 憑依した要員だけは、行き先を自分で決めずに矢印キーで動く（見ているだけなら自律行動のまま）
    const 操作中 = 憑依中.value && 一人称ID.value === agent.id;
    // 要員状況の状態を正とし、表示位置が違うエリアなら指定エリアへの移動を優先する
    if (!操作中 && !はまり中 && (runtime.割当状態 !== agent.状態 || 指定エリア外(group.position, agent.状態))) {
      runtime.割当状態 = agent.状態;
      runtime.目的地.copy(エリア位置(agent.状態, index));
      runtime.速度 = 1.35;
      runtime.次自由行動時刻 = Number.POSITIVE_INFINITY;
    }
    const direction = runtime.目的地.clone().sub(group.position);
    direction.y = 0;
    const distance = direction.length();
    const 歩行中 = 操作中
      ? 前進速さ !== 0
      : !はまり中 && delta > 0 && distance > 0.06;
    if (操作中) {
      // 移動そのものは 一人称を進める が行う。ここでは行き先を足元へ寄せておき、
      // 解除した瞬間に元の場所へ走り出さないようにする
      runtime.目的地.copy(group.position);
      runtime.次自由行動時刻 = 経過時間 + 1;
    } else if (歩行中) {
      direction.normalize();
      group.position.addScaledVector(direction, Math.min(distance, delta * runtime.速度));
      group.rotation.y = THREE.MathUtils.lerp(group.rotation.y, Math.atan2(direction.x, direction.z), 0.08);
    } else if (!はまり中 && delta > 0) {
      if (!Number.isFinite(runtime.次自由行動時刻)) {
        runtime.次自由行動時刻 = 経過時間 + 1 + Math.random() * 3;
      } else if (経過時間 >= runtime.次自由行動時刻) {
        if (Math.random() < 0.34) {
          // ときどきその場にとどまる
          runtime.目的地.copy(group.position);
          runtime.次自由行動時刻 = 経過時間 + 3 + Math.random() * 7;
        } else {
          // 割り当てられた同じエリア内の別地点へ歩く
          runtime.目的地.copy(エリア内自由位置(agent.状態));
          runtime.速度 = 0.42 + Math.random() * 0.42;
          runtime.次自由行動時刻 = Number.POSITIVE_INFINITY;
        }
      }
    }

    const bob = Math.sin(時刻 * 0.0027 + runtime.位相);
    // 歩行中は足の運びに合わせて上下に弾ませ、立ち止まると呼吸だけにする
    const 歩調 = Math.sin(時刻 * 0.0105 + runtime.位相);
    // 穴にはまっているあいだは腰まで沈める。地面に隠れて下半身が見えなくなり、落ちて見える
    const あたふた = Math.sin(時刻 * 0.024 + runtime.位相);
    group.position.y = はまり中
      ? 要員基準Y - 0.62 + Math.abs(あたふた) * 0.16
      : 要員基準Y + (歩行中 ? Math.abs(歩調) * 0.05 : bob * 0.022);
    if (はまり中) group.rotation.y += あたふた * 0.05;
    const ring = group.getObjectByName('ring') as THREE.Mesh | undefined;
    if (ring) {
      ring.rotation.z += rawDelta * (agent.状態 === '作業中' ? 0.45 : 0.85);
      const material = ring.material as THREE.MeshBasicMaterial;
      material.opacity = agent.状態 === '召喚中' ? 0.8 : 0.24 + (bob + 1) * 0.07;
    }
    const leftArm = group.getObjectByName('leftArm');
    const rightArm = group.getObjectByName('rightArm');
    const leftLeg = group.getObjectByName('leftLeg');
    const rightLeg = group.getObjectByName('rightLeg');
    const 腕振り = 歩行中
      ? 歩調 * 0.5
      : agent.状態 === '作業中'
        ? 0.42 + Math.sin(時刻 * 0.006 + runtime.位相) * 0.16
        : agent.状態 === '瞑想中'
          ? 0.2 + bob * 0.03
          : bob * 0.1;
    if (leftArm && rightArm) {
      if (はまり中) {
        // 両手を頭の上へ突き上げ、左右交互にばたばたと振って助けを求める
        leftArm.rotation.x = -2.7 + あたふた * 0.5;
        rightArm.rotation.x = -2.7 - あたふた * 0.5;
        leftArm.rotation.z = 0.32 + あたふた * 0.3;
        rightArm.rotation.z = -0.32 + あたふた * 0.3;
      } else {
        leftArm.rotation.x = 腕振り;
        rightArm.rotation.x = -腕振り;
        leftArm.rotation.z = 0.16;
        rightArm.rotation.z = -0.16;
      }
    }
    if (leftLeg && rightLeg) {
      const 脚振り = はまり中 ? あたふた * 0.7 : 歩行中 ? 歩調 * 0.55 : 0;
      leftLeg.rotation.x = -脚振り;
      rightLeg.rotation.x = 脚振り;
    }
    const head = group.getObjectByName('head');
    if (head) {
      head.rotation.y = はまり中
        ? Math.sin(時刻 * 0.019 + runtime.位相) * 0.55
        : ['相談中', '雑談中'].includes(agent.状態)
          ? Math.sin(時刻 * 0.0016 + runtime.位相) * 0.4
          : bob * 0.06;
      // はまっているあいだは助けを求めるように上を向く
      head.rotation.x = はまり中
        ? -0.28
        : agent.状態 === '瞑想中'
          ? 0.22
          : agent.状態 === '作業中'
            ? 0.14
            : 0;
    }
  });

  // 一人称視点のあいだは OrbitControls を止める（カメラは NPC 更新のあとで合わせる）
  if (!一人称ラベル.value) controls?.update();
  掲示板一覧.forEach((board, index) => {
    board.position.y = 掲示板高さ + Math.sin(時刻 * 0.0012 + index * 1.8) * 0.07;
    掲示板注視点.set(camera!.position.x, board.position.y, camera!.position.z);
    board.lookAt(掲示板注視点);
    const scale = THREE.MathUtils.clamp(board.position.distanceTo(camera!.position) / 46, 0.85, 1.15);
    board.scale.setScalar(scale);
  });

  // 掲示板の位置と向きは飛行船（NPC）が運ぶ。ここでは光の縁の演出だけ行う
  const 改善ループ中 = Boolean(props.チーム目標?.改善ループ);
  // ゆっくりした明滅へ、ごく短い瞬断を混ぜてネオン管らしい点灯の揺らぎを作る。
  const 瞬断 = Math.sin(時刻 * 0.021) + Math.sin(時刻 * 0.0137) > 1.72 ? 0.2 : 1;
  const ネオン強度 = (0.72 + (Math.sin(時刻 * 0.0045) + 1) * 0.14) * 瞬断;
  if (目標掲示板.縁) {
    const 縁材 = 目標掲示板.縁.material as THREE.MeshBasicMaterial;
    縁材.color.setHex(改善ループ中 ? 0xff1493 : 0xfff6d0);
    const 目標値 = 目標ホバー.value
      ? 0.85
      : 改善ループ中
        ? 0.18 + ネオン強度 * 0.78
        : 0.34 + (Math.sin(時刻 * 0.0016) + 1) * 0.06;
    縁材.opacity = THREE.MathUtils.lerp(縁材.opacity, 目標値, 改善ループ中 ? 0.32 : 0.12);
  }
  if (目標掲示板.改善明滅) {
    目標掲示板.改善明滅.visible = 改善ループ中;
    if (改善ループ中) {
      const 明滅材 = 目標掲示板.改善明滅.material as THREE.MeshBasicMaterial;
      明滅材.opacity = 0.025 + ネオン強度 * 0.085;
    }
  }
  if (目標掲示板.改善ネオン芯) {
    目標掲示板.改善ネオン芯.visible = 改善ループ中;
    if (改善ループ中) {
      const 芯材 = (目標掲示板.改善ネオン芯.children[0] as THREE.Mesh)
        .material as THREE.MeshBasicMaterial;
      芯材.opacity = 0.28 + ネオン強度 * 0.72;
      const 芯拡大 = 1 + ネオン強度 * 0.004;
      目標掲示板.改善ネオン芯.scale.setScalar(芯拡大);
    }
  }

  // NPC はそれぞれの動作モジュールが自分で動く。寿命が尽きた うさぎ穴 はここで一覧から消える
  // 放牧地のような「見る側の位置で決まる配置」は俯瞰カメラを基準にする。
  // 一人称でその生き物に乗って動くと配置ごと引きずられてしまうため
  const 俯瞰位置 = 一人称ラベル.value ? 復帰カメラ位置 : camera.position;
  NPC群を更新(NPC一覧, { 経過時間, delta, 時刻, camera: camera!, 俯瞰位置 });
  // 操作対象が動いたあとにカメラを合わせる。追えなくなったら俯瞰へ戻す
  if (一人称ラベル.value && !一人称を進める(delta, 時刻)) 一人称を解除();
  ラベル位置を更新();
  renderer.render(scene, camera);
  animationId = requestAnimationFrame(描画);
};

const ラベル位置を更新 = () => {
  if (!camera || !stageRef.value) return;
  const width = stageRef.value.clientWidth;
  const height = stageRef.value.clientHeight;
  エージェント一覧.value.forEach((agent) => {
    const element = ラベル要素.get(agent.id);
    const runtime = 実行状態一覧.get(agent.id);
    if (!element || !runtime) return;
    // 一人称視点で覗いている本人の名札は、目の前に張り付くので出さない
    if (agent.id === 一人称ID.value) {
      element.style.opacity = '0';
      return;
    }
    const projected = runtime.group.position.clone().add(new THREE.Vector3(0, 2.2, 0)).project(camera!);
    const visible = projected.z > -1 && projected.z < 1;
    element.style.transform = `translate(-50%, -100%) translate(${(projected.x * 0.5 + 0.5) * width}px, ${(-projected.y * 0.5 + 0.5) * height}px)`;
    element.style.opacity = visible ? '1' : '0';
  });
};

const ラベルRef設定 = (id: string, element: Element | null) => {
  if (element instanceof HTMLElement) ラベル要素.set(id, element);
  else ラベル要素.delete(id);
};

const 目標掲示板をヒットテスト = (clientX: number, clientY: number) => {
  if (!renderer || !camera || !目標掲示板.板) return false;
  const rect = renderer.domElement.getBoundingClientRect();
  pointer.x = ((clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);
  return raycaster.intersectObject(目標掲示板.板, false).length > 0;
};

// 草原そのものはクリックで反応させない。3D 側で操作できるのはチーム目標の掲示板だけで、
// 要員の選択・視点切替・会話は【要員状況】パネルから行う
const キャンバスクリック = (event: MouseEvent) => {
  if (目標掲示板をヒットテスト(event.clientX, event.clientY)) emit('目標クリック');
};

const 会話を開く = (id: string) => {
  const agent = エージェント一覧.value.find((item) => item.id === id);
  if (!agent) return;
  会話対象.value = agent;
  会話ダイアログ表示.value = true;
};

const キャンバスポインター移動 = (event: PointerEvent) => {
  目標ホバー.value = 目標掲示板をヒットテスト(event.clientX, event.clientY);
  if (renderer) {
    renderer.domElement.style.cursor = 目標ホバー.value ? 'pointer' : 'grab';
  }
};

const キャンバスポインター離脱 = () => {
  目標ホバー.value = false;
  if (renderer) renderer.domElement.style.cursor = 'grab';
};

// --- 一人称視点 ---
// 【要員状況】から要員や生き物を選ぶと、その目の高さへカメラを移して見ている方向を映す。
// 矢印キーの上下で前後移動、左右で向き変更。馬だけは上を押し続けると駆け足まで速くなる。
// Esc（または視点を戻す）で俯瞰へ戻る。

type 一人称移動設定 = {
  /** 押した直後の速さ（m/秒） */
  速さ: number;
  /** 押し続けたときの上限（加速しない相手は 速さ と同じ） */
  最高: number;
  /** 1 秒あたりの加速量。0 なら最初から最高速 */
  加速: number;
  /** 向きを変える速さ（ラジアン/秒） */
  旋回: number;
  /** モデルの正面。要員は +z、動物は -z を向いている */
  向き符号: 1 | -1;
  /** 1 歩の長さ（m）。頭の揺れをこの歩幅に合わせて刻む */
  歩幅: number;
  /** 1 歩ごとの頭の上下（m） */
  揺れ縦: number;
  /** 1 歩ごとの体の傾き（ラジアン）。カモは横に大きく振ってヨタヨタ歩きになる */
  揺れ横: number;
};

/**
 * 生き物ボタンの名前 → 一人称で操る NPC と移動の性格。
 * 目線 / 前オフセット を書かない相手は、体の大きさから自動で決める（鼻先の少し前に置く）。
 */
const 生き物視点表: Record<
  string,
  Omit<一人称移動設定, '向き符号'> & {
    種別: string;
    目線?: number;
    前オフセット?: number;
    /** 12m 先の注視点を目線から何 m 下げるか。大きいほど足元寄りを見る */
    見下ろし?: number;
  }
> = {
  // 馬だけは鼻先ではなく背中に乗った位置から見る。首の前後運動が目の前で見える
  馬: {
    種別: '黒馬',
    速さ: 2.4,
    最高: 8,
    加速: 2.2,
    旋回: 1.4,
    歩幅: 1.7,
    揺れ縦: 0.13,
    揺れ横: 0.045,
    目線: 3.05,
    前オフセット: -0.2,
  },
  イヌ: { 種別: 'イヌ', 速さ: 1.6, 最高: 1.6, 加速: 0, 旋回: 2.6, 歩幅: 0.42, 揺れ縦: 0.055, 揺れ横: 0.04 },
  ネコ: { 種別: 'ネコ', 速さ: 1.1, 最高: 1.1, 加速: 0, 旋回: 2.6, 歩幅: 0.28, 揺れ縦: 0.04, 揺れ横: 0.05 },
  うさぎ: { 種別: '黒うさぎ', 速さ: 1.4, 最高: 1.4, 加速: 0, 旋回: 2.8, 歩幅: 0.5, 揺れ縦: 0.012, 揺れ横: 0.02 },
  // カモは歩幅が小さいぶん揺れが速くなるので、横振りは控えめにして酔わないようにする。
  // 目線を下げて足元寄りを見ることで、後ろについてくる子カモが視界に入る
  カモ: {
    種別: 'カモ大',
    速さ: 0.8,
    最高: 0.8,
    加速: 0,
    旋回: 2.4,
    歩幅: 0.3,
    揺れ縦: 0.03,
    揺れ横: 0.035,
    目線: 0.3,
    見下ろし: 2.1,
  },
};

const 要員移動設定: 一人称移動設定 = {
  速さ: 1.5,
  最高: 1.5,
  加速: 0,
  旋回: 2.2,
  向き符号: 1,
  歩幅: 0.62,
  揺れ縦: 0.05,
  揺れ横: 0.022,
};

let 一人称NPC: NPC個体 | null = null;
let 一人称設定: 一人称移動設定 = 要員移動設定;
let 一人称目線 = 1.62;
let 一人称前オフセット = 0.3;
let 一人称見下ろし = 0.6;
// 水に浮くなどで沈むぶんの目線補正。境目でカクつかないよう毎フレーム滑らかに寄せる
let 一人称目線補正 = 0;
let 前進速さ = 0;
// 歩くリズムに合わせて頭を揺らすための位相。1 歩で π 進む
let 一人称揺れ位相 = 0;
// 前フレームの立ち位置。実際に動いた距離から揺れを刻む（自律行動でも憑依でも同じ扱いにする）
const 一人称前回位置 = new THREE.Vector3();
const 押しキー = new Set<string>();
// 草原の円（半径 104）からはみ出さないようにする
const 一人称行動半径 = 96;

const 一人称対象グループ = (): THREE.Group | null => {
  if (一人称ID.value) return 実行状態一覧.get(一人称ID.value)?.group ?? null;
  return 一人称NPC?.group ?? null;
};

/** 切り替えの共通処理。元の俯瞰カメラを控え、前の操作対象を自律行動へ戻す */
const 一人称を始める = (ラベル: string) => {
  if (!camera || !controls) return;
  if (!一人称ラベル.value) {
    復帰カメラ位置.copy(camera.position);
    復帰注視点.copy(controls.target);
  }
  一人称NPC?.手動操作?.(null);
  一人称NPC = null;
  一人称ID.value = '';
  一人称ラベル.value = ラベル;
  憑依中.value = false;
  前進速さ = 0;
  一人称揺れ位相 = 0;
  一人称目線補正 = 0;
  押しキー.clear();
  controls.enabled = false;
};

/** 切り替え直後に、揺れの基準となる立ち位置を合わせておく */
const 一人称の足元を記録 = () => {
  const group = 一人称対象グループ();
  if (group) 一人称前回位置.copy(group.position);
};

const 一人称へ入る = (id: string) => {
  const 要員 = エージェント一覧.value.find((agent) => agent.id === id);
  if (!camera || !controls || !要員 || !実行状態一覧.has(id)) return;
  一人称を始める(要員.名前);
  一人称ID.value = id;
  一人称設定 = 要員移動設定;
  一人称目線 = 1.62;
  一人称前オフセット = 0.3;
  一人称見下ろし = 0.6;
  一人称の足元を記録();
};

const 生き物視点へ入る = (名前: string) => {
  const 定義 = 生き物視点表[名前 as keyof typeof 生き物視点表];
  if (!camera || !controls || !定義) return;
  const npc = NPC一覧.find((item) => item.種別 === 定義.種別 && item.手動操作);
  if (!npc) return;
  一人称を始める(名前);
  一人称NPC = npc;
  一人称設定 = { ...定義, 向き符号: -1 };

  // 体の大きさから目線の高さと前へ出す距離を決める。
  // 回転したままだと軸に沿った箱にならないので、いったん向きを戻して自分の体だけを測る。
  const 元の向き = npc.group.rotation.y;
  npc.group.rotation.y = 0;
  npc.group.updateMatrixWorld(true);
  一人称体格.setFromObject(npc.group);
  npc.group.rotation.y = 元の向き;
  npc.group.updateMatrixWorld(true);

  const 頭頂 = 一人称体格.max.y - npc.group.position.y;
  // 動物の正面は -z。鼻先（min.z）より少し前へ出さないと、自分の鼻が視界をふさぐ
  const 鼻先まで = npc.group.position.z - 一人称体格.min.z;
  一人称目線 = 定義.目線 ?? Math.max(0.22, 頭頂 * 0.88);
  一人称前オフセット = 定義.前オフセット ?? Math.max(0.2, 鼻先まで + 0.1);
  一人称見下ろし = 定義.見下ろし ?? 0.6;
  一人称の足元を記録();
};

const 一人称を解除 = () => {
  if (!一人称ラベル.value) return;
  一人称NPC?.手動操作?.(null);
  一人称NPC = null;
  一人称ID.value = '';
  一人称ラベル.value = '';
  憑依中.value = false;
  押しキー.clear();
  前進速さ = 0;
  if (!camera || !controls) return;
  controls.enabled = true;
  camera.position.copy(復帰カメラ位置);
  controls.target.copy(復帰注視点);
  controls.update();
};

/** 矢印キーで動かし、カメラを頭へ合わせる。対象を見失ったら false */
const 一人称を進める = (delta: number, 時刻: number) => {
  const group = 一人称対象グループ();
  if (!camera || !group) return false;

  // 足場や体勢で動きが変わる相手（跳ぶうさぎ、水面を滑るカモ）はここで性質を受け取る
  const 特性 = 一人称NPC?.移動特性?.() ?? {};
  const 速さ倍率 = 特性.速さ倍率 ?? 1;
  const 揺れ倍率 = 特性.揺れ倍率 ?? 1;
  const 目線補正 = 特性.目線補正 ?? 0;

  // 憑依していないあいだは相手の自律行動にまかせ、カメラだけ乗せてついていく
  if (憑依中.value) {
    const 旋回入力 = (押しキー.has('ArrowLeft') ? 1 : 0) - (押しキー.has('ArrowRight') ? 1 : 0);
    const 前後入力 = (押しキー.has('ArrowUp') ? 1 : 0) - (押しキー.has('ArrowDown') ? 1 : 0);
    // 穴にはまっている要員は、もがき終わるまで動かせない
    const はまり中 = (実行状態一覧.get(一人称ID.value)?.はまり残り ?? 0) > 0;

    group.rotation.y += 旋回入力 * 一人称設定.旋回 * delta;

    if (はまり中 || 前後入力 === 0) {
      前進速さ = 0;
    } else if (前後入力 > 0) {
      // 押し続けるほど速くなる（加速 0 の相手は最初から最高速のまま）
      前進速さ =
        一人称設定.加速 > 0
          ? Math.min(一人称設定.最高, Math.max(前進速さ, 一人称設定.速さ) + 一人称設定.加速 * delta)
          : 一人称設定.速さ;
    } else {
      前進速さ = -一人称設定.速さ * 0.45;
    }

    const 実速さ = 前進速さ * 速さ倍率;
    if (実速さ !== 0) {
      const 進x = 一人称設定.向き符号 * Math.sin(group.rotation.y);
      const 進z = 一人称設定.向き符号 * Math.cos(group.rotation.y);
      group.position.x += 進x * 実速さ * delta;
      group.position.z += 進z * 実速さ * delta;
      const 中心距離 = Math.hypot(group.position.x, group.position.z);
      if (中心距離 > 一人称行動半径) {
        group.position.x *= 一人称行動半径 / 中心距離;
        group.position.z *= 一人称行動半径 / 中心距離;
      }
    }

    // 見た目づくりには「進もうとしている速さ」を渡す。
    // 実際に進んだ量を渡すと、着地している間に跳ぶのをやめてしまう
    一人称NPC?.手動操作?.({
      速さ: Math.abs(前進速さ),
      全力: 前進速さ > 一人称設定.速さ * 1.6,
    });
  }

  const 前x = 一人称設定.向き符号 * Math.sin(group.rotation.y);
  const 前z = 一人称設定.向き符号 * Math.cos(group.rotation.y);

  // --- 頭の揺れ ---
  // 実際に動いた距離で刻むので、自律行動でついていくときも同じように揺れる。
  // 止まっているあいだも呼吸ぶんだけ動かして、視界が固まって見えないようにする。
  const 移動距離 = Math.hypot(
    group.position.x - 一人称前回位置.x,
    group.position.z - 一人称前回位置.z,
  );
  一人称前回位置.copy(group.position);
  const 速さ = delta > 0 ? 移動距離 / delta : 0;
  一人称揺れ位相 += (移動距離 / 一人称設定.歩幅) * Math.PI;
  const 勢い = 一人称設定.最高 > 一人称設定.速さ
    ? 0.55 + 0.45 * Math.min(1, 速さ / 一人称設定.最高)
    : 1;
  const 揺れ強さ = (速さ > 0.01 ? 勢い : 0) * 揺れ倍率;
  const 呼吸 = Math.sin(時刻 * 0.0022) * 0.008;
  const 縦揺れ = Math.abs(Math.sin(一人称揺れ位相)) * 一人称設定.揺れ縦 * 揺れ強さ + 呼吸;
  const 横傾き = Math.sin(一人称揺れ位相) * 一人称設定.揺れ横 * 揺れ強さ;
  // 水に浮くなど、体の沈みぶんだけ目線を下げる（境目で跳ねないよう滑らかに寄せる）
  一人称目線補正 = THREE.MathUtils.lerp(一人称目線補正, 目線補正, Math.min(1, delta * 4));
  const 目線 = 一人称目線 + 一人称目線補正;
  // カメラを前後に揺らすと「進んでは少し遅くなる」ように見えて速度が一定に感じられないため、
  // 前後の動きはカメラには入れない（馬の首など、体側の動きで見せる）

  camera.position.set(
    group.position.x + 前x * 一人称前オフセット,
    group.position.y + 目線 + 縦揺れ,
    group.position.z + 前z * 一人称前オフセット,
  );
  一人称注視点.set(
    group.position.x + 前x * 12,
    group.position.y + 目線 - 一人称見下ろし + 縦揺れ * 0.4,
    group.position.z + 前z * 12,
  );
  camera.lookAt(一人称注視点);
  // 体の傾きは lookAt のあとに足す（lookAt は上方向を +y に戻してしまうため）
  camera.rotateZ(横傾き);
  return true;
};

const 操作キー一覧 = ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'];

const キー押下 = (event: KeyboardEvent) => {
  if (!一人称ラベル.value) return;
  if (event.key === 'Escape') {
    一人称を解除();
    event.preventDefault();
    return;
  }
  if (操作キー一覧.includes(event.key)) {
    // 矢印キーを押した時点で、自律行動を止めて操作へ切り替える
    憑依中.value = true;
    押しキー.add(event.key);
    // 矢印キーで画面がスクロールしてしまわないようにする
    event.preventDefault();
  }
};

const キー解放 = (event: KeyboardEvent) => {
  if (操作キー一覧.includes(event.key)) 押しキー.delete(event.key);
};

// 画面から離れたときにキーが押しっぱなし扱いで残らないようにする
const キー全解放 = () => 押しキー.clear();

const カメラを戻す = () => {
  一人称を解除();
  if (!camera || !controls) return;
  camera.position.set(30, 18, 30);
  controls.target.set(0, 1.5, 0);
  controls.update();
};

watch(
  () => props.エージェント一覧.map((agent) => `${agent.id}:${agent.状態}`).join('|'),
  () => {
    エージェント表示を同期();
    props.エージェント一覧.forEach((agent, index) => {
      const runtime = 実行状態一覧.get(agent.id);
      if (!runtime || runtime.割当状態 === agent.状態) return;
      runtime.割当状態 = agent.状態;
      runtime.目的地.copy(エリア位置(agent.状態, index));
      runtime.速度 = 1.35;
      runtime.次自由行動時刻 = Number.POSITIVE_INFINITY;
    });
  },
  { flush: 'post' },
);

watch(
  () => [props.チーム目標?.CODE_BASE_PATH, props.チーム目標?.チーム目標, props.チーム目標?.更新日時],
  () => 目標掲示板を更新(),
);

// 【要員状況】パネルから呼ぶ入口。カメラと会話ダイアログはこの画面が持っているため、
// 親（AIチーム.vue）が要員のクリック / ダブルクリックをここへ中継する
defineExpose({ 一人称へ入る, 生き物視点へ入る, 会話を開く });

onMounted(() => {
  シーンを作る();
  エージェント表示を同期();
  window.addEventListener('keydown', キー押下);
  window.addEventListener('keyup', キー解放);
  window.addEventListener('blur', キー全解放);
});

onBeforeUnmount(() => {
  window.removeEventListener('keydown', キー押下);
  window.removeEventListener('keyup', キー解放);
  window.removeEventListener('blur', キー全解放);
  cancelAnimationFrame(animationId);
  resizeObserver?.disconnect();
  controls?.dispose();
  renderer?.dispose();
  破棄対象.forEach((item) => item.dispose());
  破棄テクスチャ.forEach((texture) => texture.dispose());
  実行状態一覧.clear();
  掲示板一覧.length = 0;
  目標掲示板.group = null;
  目標掲示板.板 = null;
  目標掲示板.縁 = null;
  目標掲示板.改善明滅 = null;
  目標掲示板.改善ネオン芯 = null;
  目標テクスチャ = null;
  // うさぎ穴のように自前で資源を持つ NPC を片付けてから一覧を空にする
  NPC一覧.forEach((npc) => npc.破棄?.());
  NPC一覧.length = 0;
  部品 = null;
  ラベル要素.clear();
  scene = null;
  camera = null;
  renderer = null;
});
</script>

<template>
  <main ref="stageRef" class="scene-stage">
    <canvas
      ref="canvasRef"
      class="scene-canvas"
      aria-label="ドラッグで360度回転できるAIチームの3D草原ワークスペース"
      @click="キャンバスクリック"
      @pointermove="キャンバスポインター移動"
      @pointerleave="キャンバスポインター離脱"
    ></canvas>

    <div v-if="要員読込中" class="viewer-message">
      <strong>要員一覧を読み込んでいます</strong>
      <span>backend_team に接続中...</span>
    </div>
    <div v-else-if="要員読込エラー" class="viewer-message error">
      <strong>要員一覧を表示できません</strong>
      <span>{{ 要員読込エラー }}</span>
      <button type="button" @click="emit('retry')">再試行</button>
    </div>
    <div v-else-if="エージェント一覧.length === 0" class="viewer-message">
      <strong>召喚済みの要員がいません</strong>
      <span>召喚要員を選択して、チーム空間へ呼び出してください。</span>
    </div>

    <div class="scene-titlebar">
      <span class="scene-title">【チーム空間】</span>
      <span class="scene-subtitle">草原フロア</span>
      <div class="scene-right">
        <span class="stat-chip">要員<b>{{ 要員数 }}</b></span>
        <span class="stat-chip active">作業中<b>{{ 稼働数 }}</b></span>
        <span class="stat-chip">雑談中<b>{{ 相談数 }}</b></span>
        <span class="stat-chip">瞑想中<b>{{ 瞑想数 }}</b></span>
        <span class="stat-chip">休憩中<b>{{ 休憩数 }}</b></span>
        <div class="scene-clock"><span>LIVE</span>{{ 現在時刻 }}</div>
      </div>
    </div>

    <!-- 名札は誰がどこにいるかを示すだけの表示。操作は【要員状況】パネル側で行う -->
    <div
      v-for="agent in エージェント一覧"
      :key="`label-${agent.id}`"
      :ref="(element) => ラベルRef設定(agent.id, element as Element | null)"
      class="world-label"
      :class="{
        selected: agent.id === 選択中ID,
        talking: ['相談中', '雑談中'].includes(agent.状態),
      }"
      :style="{ '--agent-color': agent.色CSS }"
    >
      <span class="world-name">{{ agent.名前 }}</span>
      <span class="world-role">{{ agent.役割 || '役割未設定' }}</span>
      <span v-if="['相談中', '雑談中'].includes(agent.状態) && agent.ひとこと" class="speech">
        {{ agent.ひとこと }}
      </span>
    </div>

    <div v-if="一人称ラベル" class="first-person-badge" :class="{ possessed: 憑依中 }">
      <span class="fp-eye">◉</span>
      <span class="fp-name">{{ 一人称ラベル }} {{ 憑依中 ? 'に憑依中' : 'の視点' }}</span>
      <template v-if="憑依中">
        <span class="fp-hint"><b>↑↓</b> 前後</span>
        <span class="fp-hint"><b>←→</b> 向き</span>
        <span v-if="一人称ラベル === '馬'" class="fp-hint"><b>↑長押し</b> 駆け足</span>
      </template>
      <span v-else class="fp-hint"><b>↑↓←→</b> で憑依</span>
      <span class="fp-hint"><b>ESC</b> で解除</span>
    </div>

    <!-- 一人称中の操作説明は下部中央のバッジに出すので、ここでは重ねて出さない -->
    <div class="camera-help">
      <template v-if="!一人称ラベル">
        <span><b>DRAG</b> 360° 回転</span>
        <span><b>WHEEL</b> ズーム</span>
        <span>要員状況をクリックでその人の視点</span>
      </template>
      <button type="button" @click="カメラを戻す">視点を戻す</button>
    </div>

    <component
      :is="AiTeamConversation"
      :is-open="会話ダイアログ表示"
      :エージェント="会話対象"
      :チーム目標="props.チーム目標"
      @close="会話ダイアログ表示 = false"
    />
  </main>
</template>

<style scoped>
.scene-stage {
  min-width: 0;
  min-height: 420px;
  position: relative;
  overflow: hidden;
  background: linear-gradient(180deg, #7dc0e8, #cfe8dd);
}

.scene-stage::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: linear-gradient(0deg, rgba(20, 48, 30, 0.28), transparent 22%);
}

.scene-canvas {
  width: 100%;
  height: 100%;
  display: block;
  cursor: grab;
  touch-action: none;
}

.scene-canvas:active { cursor: grabbing; }

.viewer-message {
  position: absolute;
  top: 50%;
  left: 50%;
  z-index: 6;
  width: min(320px, calc(100% - 48px));
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 17px 20px;
  transform: translate(-50%, -50%);
  border: 1px solid rgba(91, 217, 255, 0.2);
  border-radius: 12px;
  color: #dcebf2;
  background: rgba(7, 20, 31, 0.91);
  text-align: center;
}

.viewer-message strong { font-size: 12px; }
.viewer-message span { color: #7995a5; font-size: 9px; line-height: 1.5; }
.viewer-message.error { border-color: rgba(255, 126, 182, 0.28); }
.viewer-message button {
  margin-top: 5px;
  padding: 5px 12px;
  border: 1px solid rgba(91, 217, 255, 0.3);
  border-radius: 6px;
  color: #9ceaff;
  background: rgba(91, 217, 255, 0.08);
  cursor: pointer;
}

.scene-titlebar {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 2;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 14px;
  height: 32px;
  box-sizing: border-box;
  /* 明るい空の上でも文字が読めるように、上端だけ濃い緑のグラデーションを敷く */
  background: linear-gradient(180deg, rgba(14, 42, 28, 0.62), transparent);
  pointer-events: none;
}

.scene-title {
  color: rgba(255, 255, 255, 0.88);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 1px;
  white-space: nowrap;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.6);
}

.scene-subtitle {
  color: rgba(255, 255, 255, 0.75);
  font-size: 10px;
  letter-spacing: 0.05em;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.6);
}

.scene-right {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 12px;
}

.scene-clock {
  color: #fff;
  font-size: 10px;
  letter-spacing: 0.05em;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.6);
}

.scene-clock span { margin-right: 7px; color: #5ce3a1; font-weight: 800; }

.stat-chip {
  display: flex;
  align-items: center;
  gap: 4px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 9px;
  letter-spacing: 0.03em;
  white-space: nowrap;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.6);
}

.stat-chip b {
  color: #fff;
  font-size: 11px;
  font-weight: 800;
}

.stat-chip.active b {
  color: #9dffce;
}

.world-label {
  position: absolute;
  top: 0;
  left: 0;
  z-index: 3;
  display: block;
  overflow: visible;
  padding: 4px 7px;
  border: 1px solid color-mix(in srgb, var(--agent-color) 35%, transparent);
  border-radius: 6px;
  color: #eaf7fb;
  background: rgba(7, 20, 31, 0.86);
  /* 名札は表示だけ。マウス操作は素通りさせて、名札越しでも視点をドラッグできるようにする */
  pointer-events: none;
  will-change: transform;
}

.world-label.selected {
  border-color: var(--agent-color);
  box-shadow: 0 0 18px color-mix(in srgb, var(--agent-color) 24%, transparent);
}

.world-name { display: block; color: var(--agent-color); font-size: 9px; font-weight: 800; }
.world-role {
  position: absolute;
  top: calc(100% + 6px);
  left: 50%;
  width: max-content;
  max-width: 180px;
  padding: 5px 8px;
  transform: translate(-50%, -4px);
  border: 1px solid color-mix(in srgb, var(--agent-color) 35%, transparent);
  border-radius: 6px;
  color: #d7eaf2;
  background: rgba(7, 20, 31, 0.94);
  font-size: 8px;
  opacity: 0;
  pointer-events: none;
}

/* 役割は選択中の要員だけ名札の下に出す（名札はマウスを受け取らないため hover では出せない） */
.world-label.selected .world-role { transform: translate(-50%, 0); opacity: 1; }

.speech {
  position: absolute;
  bottom: calc(100% + 7px);
  left: 50%;
  width: max-content;
  max-width: 155px;
  padding: 6px 8px;
  transform: translateX(-50%);
  border: 1px solid rgba(130, 177, 204, 0.22);
  border-radius: 8px;
  color: #bfd4df;
  background: rgba(11, 25, 38, 0.93);
  font-size: 8px;
}

.camera-help {
  position: absolute;
  right: 18px;
  bottom: 17px;
  z-index: 3;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 5px 9px;
  border-radius: 9px;
  color: #cfe3d4;
  background: rgba(16, 40, 27, 0.55);
  font-size: 8px;
}

.camera-help b { margin-right: 3px; color: #f0f7ee; }
.camera-help button {
  padding: 5px 8px;
  border: 1px solid rgba(196, 231, 200, 0.28);
  border-radius: 6px;
  color: #e3f3e2;
  background: rgba(30, 66, 44, 0.6);
  cursor: pointer;
  font-size: 8px;
}

/* 一人称視点中であることと、解除の仕方を画面下部中央で知らせる */
.first-person-badge {
  position: absolute;
  bottom: 15px;
  left: 50%;
  z-index: 4;
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 6px 13px;
  border: 1px solid rgba(196, 231, 200, 0.35);
  border-radius: 999px;
  transform: translateX(-50%);
  color: #eaf7ec;
  background: rgba(16, 40, 27, 0.72);
  font-size: 11px;
  pointer-events: none;
}

/* 憑依中は縁を明るくして、操作を握っていることを分かりやすくする */
.first-person-badge.possessed {
  border-color: rgba(123, 227, 176, 0.85);
  box-shadow: 0 0 14px rgba(123, 227, 176, 0.3);
}

.first-person-badge .fp-eye { color: #7be3b0; }
.first-person-badge.possessed .fp-eye { color: #ffe08a; }
.first-person-badge .fp-name { font-weight: 700; }
.first-person-badge .fp-hint { color: #b6d4c0; font-size: 9px; }
.first-person-badge .fp-hint b {
  margin-right: 3px;
  padding: 1px 4px;
  border-radius: 4px;
  color: #f0f7ee;
  background: rgba(123, 227, 176, 0.25);
}

@media (max-width: 760px) {
  .scene-stage { min-height: 520px; order: 1; }
  .camera-help span { display: none; }
}
</style>
