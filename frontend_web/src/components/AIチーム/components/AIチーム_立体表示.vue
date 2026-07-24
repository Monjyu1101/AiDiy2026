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
import {
  type エージェント,
  type エージェント状態,
  状態情報,
} from '../AIチーム_型';

type 実行状態 = {
  group: THREE.Group;
  目的地: THREE.Vector3;
  位相: number;
  速度: number;
  状態更新時刻: number;
};

const props = defineProps<{
  エージェント一覧: エージェント[];
  選択中ID: string;
  要員読込中: boolean;
  要員読込エラー: string;
}>();

const emit = defineEmits<{
  select: [id: string];
  retry: [];
  stateChange: [
    id: string,
    state: エージェント状態,
    work: string,
    comment: string,
  ];
}>();

const stageRef = ref<HTMLElement | null>(null);
const canvasRef = ref<HTMLCanvasElement | null>(null);
const エージェント一覧 = computed(() => props.エージェント一覧);
const 選択中ID = computed(() => props.選択中ID);
const 要員読込中 = computed(() => props.要員読込中);
const 要員読込エラー = computed(() => props.要員読込エラー);
const ホバー中ID = ref('');
const シミュレーション中 = ref(true);
const 速度倍率 = ref(1);
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
const 掲示板注視点 = new THREE.Vector3();
const 実行状態一覧 = new Map<string, 実行状態>();
const 掲示板一覧: THREE.Group[] = [];
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

const エリア位置 = (状態: エージェント状態, index = 0): THREE.Vector3 => {
  if (状態 === '作業中') {
    const 席 = [
      [-6.35, 0.66, -3.15],
      [-6.2, 0.66, -0.95],
      [-4.05, 0.66, -3.65],
      [-3.45, 0.66, -1.15],
    ];
    return new THREE.Vector3(...席[index % 席.length] as [number, number, number]);
  }
  if (状態 === '相談中') {
    const 席 = [
      [-0.75, 0.66, 5.1],
      [0.7, 0.66, 4.45],
      [1.4, 0.66, 5.85],
    ];
    return new THREE.Vector3(...席[index % 席.length] as [number, number, number]);
  }
  if (状態 === '瞑想中') {
    const 席 = [
      [5.2, 0.66, -1.95],
      [6.0, 0.66, -1.35],
    ];
    return new THREE.Vector3(...席[index % 席.length] as [number, number, number]);
  }
  if (状態 === '召喚中') return new THREE.Vector3(0.3, 0.66, 5.35);
  const 移動先 = [
    [-5.0, 0.66, -2.35],
    [0.3, 0.66, 5.35],
    [5.6, 0.66, -2.2],
  ];
  return new THREE.Vector3(
    ...(移動先[Math.floor(Math.random() * 移動先.length)] as [number, number, number]),
  );
};

const 机を作る = (x: number, z: number, rotation = 0) => {
  if (!scene) return;
  const group = new THREE.Group();
  group.position.set(x, 0, z);
  group.rotation.y = rotation;

  const 木材 = マテリアル(0x243649, { roughness: 0.72 });
  const 金属 = マテリアル(0x607a91, { metalness: 0.65, roughness: 0.32 });
  const 画面 = マテリアル(0x163a52, {
    emissive: 0x2dcfff,
    emissiveIntensity: 1.15,
    roughness: 0.2,
  });
  group.add(メッシュ(ジオメトリ(new THREE.BoxGeometry(2.2, 0.16, 1.05)), 木材, [0, 1.0, 0]));
  group.add(メッシュ(ジオメトリ(new THREE.BoxGeometry(0.1, 0.85, 0.1)), 金属, [-0.82, 0.52, -0.32]));
  group.add(メッシュ(ジオメトリ(new THREE.BoxGeometry(0.1, 0.85, 0.1)), 金属, [0.82, 0.52, -0.32]));
  group.add(メッシュ(ジオメトリ(new THREE.BoxGeometry(1.15, 0.72, 0.08)), 画面, [0, 1.54, -0.23]));
  group.add(メッシュ(ジオメトリ(new THREE.BoxGeometry(0.09, 0.42, 0.09)), 金属, [0, 1.18, -0.22]));
  scene.add(group);
};

const 瞑想スペースを作る = (x: number, z: number) => {
  if (!scene) return;
  const group = new THREE.Group();
  group.position.set(x, 0, z);
  const 台座 = マテリアル(0x252943, { roughness: 0.82 });
  const 敷物 = マテリアル(0x5a527f, { roughness: 0.94 });
  const 光 = マテリアル(0xffcf73, {
    emissive: 0xf0a33c,
    emissiveIntensity: 0.8,
    roughness: 0.35,
  });
  group.add(メッシュ(ジオメトリ(new THREE.CylinderGeometry(1.75, 1.9, 0.16, 40)), 台座, [0, 0.08, 0]));
  const cushion = メッシュ(
    ジオメトリ(new THREE.CylinderGeometry(0.72, 0.78, 0.22, 32)),
    敷物,
    [0, 0.28, 0],
  );
  cushion.scale.z = 0.78;
  group.add(cushion);
  const meditationRing = メッシュ(
    ジオメトリ(new THREE.TorusGeometry(1.28, 0.035, 10, 48)),
    光,
    [0, 0.2, 0],
  );
  meditationRing.rotation.x = Math.PI / 2;
  group.add(meditationRing);
  for (let index = 0; index < 5; index += 1) {
    const light = メッシュ(
      ジオメトリ(new THREE.SphereGeometry(0.055, 10, 8)),
      光,
      [
        Math.cos((index / 5) * Math.PI * 2) * 1.28,
        0.26,
        Math.sin((index / 5) * Math.PI * 2) * 1.28,
      ],
    );
    group.add(light);
  }
  scene.add(group);
};

const 観葉植物を作る = (x: number, z: number, scale = 1) => {
  if (!scene) return;
  const group = new THREE.Group();
  group.position.set(x, 0, z);
  group.scale.setScalar(scale);
  const 鉢 = マテリアル(0xb76f50);
  const 葉 = マテリアル(0x4fd19a, { roughness: 0.9 });
  group.add(メッシュ(ジオメトリ(new THREE.CylinderGeometry(0.35, 0.28, 0.62, 16)), 鉢, [0, 0.3, 0]));
  for (let i = 0; i < 6; i += 1) {
    const leaf = メッシュ(ジオメトリ(new THREE.SphereGeometry(0.34, 12, 8)), 葉, [
      Math.cos(i) * 0.25,
      0.83 + (i % 2) * 0.22,
      Math.sin(i) * 0.25,
    ]);
    leaf.scale.set(0.65, 1.3, 0.5);
    group.add(leaf);
  }
  scene.add(group);
};

const 盤面を作る = (
  x: number,
  z: number,
  radius: number,
  color: number,
  ringEnabled = true,
) => {
  if (!scene) return;
  const baseMaterial = マテリアル(0x142334, {
    metalness: 0.48,
    roughness: 0.62,
  });
  const topMaterial = マテリアル(0x1a2e3f, {
    roughness: 0.82,
  });
  const areaMaterial = new THREE.MeshBasicMaterial({
    color,
    transparent: true,
    opacity: 0.075,
    side: THREE.DoubleSide,
    depthWrite: false,
  });
  破棄対象.push(areaMaterial);
  const base = メッシュ(
    ジオメトリ(new THREE.CylinderGeometry(radius, radius + 0.18, 0.58, 48)),
    baseMaterial,
    [x, -0.34, z],
  );
  const top = メッシュ(
    ジオメトリ(new THREE.CylinderGeometry(radius - 0.12, radius - 0.12, 0.08, 48)),
    topMaterial,
    [x, -0.01, z],
  );
  const area = メッシュ(
    ジオメトリ(new THREE.CircleGeometry(radius, 48)),
    areaMaterial,
    [x, 0.052, z],
  );
  area.rotation.x = -Math.PI / 2;
  scene.add(base, top, area);
  if (ringEnabled) {
    const ringMaterial = new THREE.MeshBasicMaterial({
      color,
      transparent: true,
      opacity: 0.3,
      side: THREE.DoubleSide,
    });
    破棄対象.push(ringMaterial);
    const ring = メッシュ(
      ジオメトリ(new THREE.RingGeometry(radius - 0.1, radius, 48)),
      ringMaterial,
      [x, 0.058, z],
    );
    ring.rotation.x = -Math.PI / 2;
    scene.add(ring);
  }
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

  const accent = `#${color.toString(16).padStart(6, '0')}`;
  context.fillStyle = '#0d1d2a';
  context.fillRect(0, 0, canvas.width, canvas.height);
  context.fillStyle = accent;
  context.fillRect(0, 0, 18, canvas.height);
  context.fillRect(54, 72, 118, 7);
  context.font = '700 44px "Yu Gothic", "Meiryo", sans-serif';
  context.fillStyle = accent;
  context.fillText(englishTitle, 54, 55);
  context.font = '700 82px "Yu Gothic", "Meiryo", sans-serif';
  context.fillStyle = '#eefaff';
  context.fillText(title, 54, 178);
  context.fillStyle = 'rgba(128, 168, 187, 0.35)';
  context.fillRect(54, 221, 910, 2);
  context.font = '500 37px "Yu Gothic", "Meiryo", sans-serif';
  context.fillStyle = '#a9c4d1';
  context.fillText(messages[0], 54, 302);
  context.fillText(messages[1], 54, 368);
  context.font = '600 25px "Yu Gothic", "Meiryo", sans-serif';
  context.fillStyle = 'rgba(138, 175, 191, 0.68)';
  context.fillText('TEAM AREA BOARD  /  LIVE', 54, 450);

  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.minFilter = THREE.LinearFilter;
  texture.needsUpdate = true;
  破棄テクスチャ.push(texture);

  const group = new THREE.Group();
  group.position.set(position[0], 3.35, position[1]);
  group.name = 'area-board';
  const frameMaterial = マテリアル(0x23394a, {
    metalness: 0.62,
    roughness: 0.34,
  });
  const screenMaterial = new THREE.MeshBasicMaterial({
    map: texture,
    toneMapped: false,
  });
  破棄対象.push(screenMaterial);
  group.add(
    メッシュ(ジオメトリ(new THREE.BoxGeometry(4.25, 2.38, 0.18)), frameMaterial, [0, 0, 0]),
    メッシュ(ジオメトリ(new THREE.PlaneGeometry(4.0, 2.12)), screenMaterial, [0, 0, 0.1]),
  );
  const glowMaterial = new THREE.MeshBasicMaterial({
    color,
    transparent: true,
    opacity: 0.28,
    side: THREE.DoubleSide,
  });
  破棄対象.push(glowMaterial);
  const glow = メッシュ(
    ジオメトリ(new THREE.RingGeometry(0.72, 0.79, 40)),
    glowMaterial,
    [0, -1.52, 0],
  );
  glow.rotation.x = -Math.PI / 2;
  group.add(glow);
  scene.add(group);
  掲示板一覧.push(group);
};

const エージェントモデルを作る = (agent: エージェント): THREE.Group => {
  const group = new THREE.Group();
  group.userData.agentId = agent.id;

  const 本体色 = マテリアル(agent.色, {
    emissive: agent.色,
    emissiveIntensity: 0.12,
    metalness: 0.52,
    roughness: 0.28,
  });
  const 暗色 = マテリアル(0x172432, { metalness: 0.72, roughness: 0.28 });
  const 発光 = マテリアル(0xdffcff, {
    emissive: agent.色,
    emissiveIntensity: 1.4,
    roughness: 0.1,
  });

  const body = メッシュ(ジオメトリ(new THREE.CapsuleGeometry(0.38, 0.62, 5, 12)), 本体色, [0, 0.72, 0]);
  body.name = 'body';
  const head = メッシュ(ジオメトリ(new THREE.SphereGeometry(0.43, 20, 14)), 暗色, [0, 1.62, 0]);
  const face = メッシュ(ジオメトリ(new THREE.BoxGeometry(0.54, 0.2, 0.04)), 発光, [0, 1.62, 0.39]);
  const leftArm = メッシュ(ジオメトリ(new THREE.CapsuleGeometry(0.1, 0.45, 4, 8)), 暗色, [-0.51, 0.85, 0]);
  const rightArm = メッシュ(ジオメトリ(new THREE.CapsuleGeometry(0.1, 0.45, 4, 8)), 暗色, [0.51, 0.85, 0]);
  leftArm.rotation.z = -0.18;
  rightArm.rotation.z = 0.18;
  leftArm.name = 'leftArm';
  rightArm.name = 'rightArm';

  const ringMaterial = new THREE.MeshBasicMaterial({
    color: agent.色,
    transparent: true,
    opacity: 0.48,
    side: THREE.DoubleSide,
  });
  破棄対象.push(ringMaterial);
  const ring = メッシュ(ジオメトリ(new THREE.RingGeometry(0.55, 0.63, 32)), ringMaterial, [0, 0.05, 0]);
  ring.rotation.x = -Math.PI / 2;
  ring.name = 'ring';

  group.add(body, head, face, leftArm, rightArm, ring);
  group.position.copy(エリア位置(agent.状態));
  group.traverse((object) => {
    object.userData.agentId = agent.id;
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
    状態更新時刻: 経過時間 + 8 + Math.random() * 8,
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
  scene.background = new THREE.Color(0x07111d);
  scene.fog = new THREE.FogExp2(0x07111d, 0.027);

  camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
  camera.position.set(19.5, 17, 23);

  renderer = new THREE.WebGLRenderer({
    canvas: canvasRef.value,
    antialias: true,
    alpha: false,
    powerPreference: 'high-performance',
  });
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.1;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.8));

  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.075;
  controls.enablePan = false;
  controls.minDistance = 10;
  controls.maxDistance = 42;
  controls.minPolarAngle = 0.28;
  controls.maxPolarAngle = Math.PI / 2.07;
  controls.target.set(0.15, 0.8, 0.45);
  controls.update();

  scene.add(new THREE.HemisphereLight(0x8ed8ff, 0x172033, 1.45));
  const keyLight = new THREE.DirectionalLight(0xffffff, 2.2);
  keyLight.position.set(7, 14, 8);
  keyLight.castShadow = true;
  keyLight.shadow.mapSize.set(2048, 2048);
  keyLight.shadow.camera.left = -12;
  keyLight.shadow.camera.right = 12;
  keyLight.shadow.camera.top = 12;
  keyLight.shadow.camera.bottom = -12;
  scene.add(keyLight);
  const accentLight = new THREE.PointLight(0x3fcfff, 28, 20, 2);
  accentLight.position.set(-5, 5, 3);
  scene.add(accentLight);

  盤面を作る(-5.0, -2.35, 4.65, 0x48c9ea, false);
  盤面を作る(0.3, 5.35, 4.05, 0x789cff);
  盤面を作る(5.6, -2.2, 4.05, 0xf3bd67);

  机を作る(-6.4, -3.7, 0);
  机を作る(-6.35, -1.1, 0);
  机を作る(-3.9, -3.75, 0);
  机を作る(-3.55, -1.0, 0);
  瞑想スペースを作る(5.6, -2.0);
  観葉植物を作る(-8.1, -2.25, 0.78);
  観葉植物を作る(-2.4, 5.6, 0.76);
  観葉植物を作る(8.1, -1.05, 0.78);

  const table = メッシュ(
    ジオメトリ(new THREE.CylinderGeometry(1.1, 1.1, 0.22, 32)),
    マテリアル(0x355064),
    [0.3, 0.48, 5.35],
  );
  scene.add(table);

  掲示板を作る(
    '仕事エリア',
    'WORK AREA',
    ['担当タスクと進捗を共有', '集中して成果を積み上げる'],
    [-5.0, -7.75],
    0x5bd9ff,
  );
  掲示板を作る(
    '雑談エリア',
    'CHAT AREA',
    ['発見・相談・アイデアを交換', '仲間との対話から次を見つける'],
    [0.3, 10.1],
    0x8bb8ff,
  );
  掲示板を作る(
    '瞑想エリア',
    'MEDITATION AREA',
    ['静かに思考と文脈を整理', '自分の判断で次の行動を選ぶ'],
    [5.6, -6.95],
    0xffcf73,
  );

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

const 次の状態へ = (agent: エージェント, index: number) => {
  const runtime = 実行状態一覧.get(agent.id);
  if (!runtime) return;
  const roll = Math.random();
  let nextState: エージェント状態;
  if (roll < 0.48) nextState = '作業中';
  else if (roll < 0.68) nextState = '相談中';
  else if (roll < 0.82) nextState = '瞑想中';
  else nextState = '移動中';

  runtime.状態更新時刻 = 経過時間 + 8 + Math.random() * 10;
  runtime.目的地.copy(エリア位置(nextState, index));

  let work = '';
  let comment = '';
  if (nextState === '作業中') {
    work = 作業候補[Math.floor(Math.random() * 作業候補.length)];
  } else if (nextState === '相談中') {
    work = '仲間とアイデア交換';
    comment = 雑談候補[Math.floor(Math.random() * 雑談候補.length)];
  } else if (nextState === '瞑想中') {
    work = '静かに思考と文脈を整理中';
    comment = '次の行動を見つめ直しています';
  } else {
    work = 'オフィスを気ままに散歩中';
  }
  emit('stateChange', agent.id, nextState, work, comment);
};

const 描画 = (時刻: number) => {
  if (!renderer || !scene || !camera) return;
  const rawDelta = Math.min((時刻 - 前フレーム時刻) / 1000, 0.05);
  前フレーム時刻 = 時刻;
  const delta = シミュレーション中.value ? rawDelta * 速度倍率.value : 0;
  経過時間 += delta;

  エージェント一覧.value.forEach((agent, index) => {
    const runtime = 実行状態一覧.get(agent.id);
    if (!runtime) return;
    if (delta > 0 && 経過時間 >= runtime.状態更新時刻) 次の状態へ(agent, index);

    const group = runtime.group;
    const direction = runtime.目的地.clone().sub(group.position);
    direction.y = 0;
    const distance = direction.length();
    if (delta > 0 && distance > 0.06) {
      direction.normalize();
      group.position.addScaledVector(direction, Math.min(distance, delta * runtime.速度));
      group.rotation.y = THREE.MathUtils.lerp(group.rotation.y, Math.atan2(direction.x, direction.z), 0.08);
    } else if (agent.状態 === '移動中' && distance <= 0.06) {
      runtime.目的地.copy(エリア位置('移動中', index));
    }

    const bob = Math.sin(時刻 * 0.0027 + runtime.位相);
    group.position.y = 0.66 + bob * 0.055;
    const ring = group.getObjectByName('ring') as THREE.Mesh | undefined;
    if (ring) {
      ring.rotation.z += rawDelta * (agent.状態 === '作業中' ? 0.45 : 0.85);
      const material = ring.material as THREE.MeshBasicMaterial;
      material.opacity = agent.状態 === '召喚中' ? 0.85 : 0.36 + (bob + 1) * 0.08;
    }
    const leftArm = group.getObjectByName('leftArm');
    const rightArm = group.getObjectByName('rightArm');
    if (leftArm && rightArm) {
      const activity = agent.状態 === '作業中' ? Math.sin(時刻 * 0.006 + runtime.位相) * 0.18 : bob * 0.08;
      leftArm.rotation.x = activity;
      rightArm.rotation.x = -activity;
    }
  });

  controls?.update();
  掲示板一覧.forEach((board, index) => {
    board.position.y = 3.35 + Math.sin(時刻 * 0.0012 + index * 1.8) * 0.08;
    掲示板注視点.set(camera!.position.x, board.position.y, camera!.position.z);
    board.lookAt(掲示板注視点);
    const scale = THREE.MathUtils.clamp(board.position.distanceTo(camera!.position) / 28, 0.92, 1.28);
    board.scale.setScalar(scale);
  });
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
    const projected = runtime.group.position.clone().add(new THREE.Vector3(0, 2.35, 0)).project(camera!);
    const visible = projected.z > -1 && projected.z < 1;
    element.style.transform = `translate(-50%, -100%) translate(${(projected.x * 0.5 + 0.5) * width}px, ${(-projected.y * 0.5 + 0.5) * height}px)`;
    element.style.opacity = visible ? '1' : '0';
    element.style.pointerEvents = visible ? 'auto' : 'none';
  });
};

const ラベルRef設定 = (id: string, element: Element | null) => {
  if (element instanceof HTMLElement) ラベル要素.set(id, element);
  else ラベル要素.delete(id);
};

const エージェントIDをヒットテスト = (clientX: number, clientY: number) => {
  if (!renderer || !camera) return;
  const rect = renderer.domElement.getBoundingClientRect();
  pointer.x = ((clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);
  const hits = raycaster.intersectObjects(
    [...実行状態一覧.values()].map((runtime) => runtime.group),
    true,
  );
  return hits[0]?.object.userData.agentId as string | undefined;
};

const キャンバスクリック = (event: MouseEvent) => {
  const id = エージェントIDをヒットテスト(event.clientX, event.clientY);
  if (id) emit('select', id);
};

const キャンバスポインター移動 = (event: PointerEvent) => {
  const id = エージェントIDをヒットテスト(event.clientX, event.clientY) ?? '';
  ホバー中ID.value = id;
  if (renderer) renderer.domElement.style.cursor = id ? 'pointer' : 'grab';
};

const キャンバスポインター離脱 = () => {
  ホバー中ID.value = '';
  if (renderer) renderer.domElement.style.cursor = 'grab';
};

const エージェントを選択 = (id: string) => {
  emit('select', id);
};

const カメラを戻す = () => {
  if (!camera || !controls) return;
  camera.position.set(19.5, 17, 23);
  controls.target.set(0.15, 0.8, 0.45);
  controls.update();
};

watch(
  () => props.エージェント一覧.map((agent) => agent.id).join('|'),
  () => エージェント表示を同期(),
  { flush: 'post' },
);

onMounted(() => {
  シーンを作る();
  エージェント表示を同期();
});

onBeforeUnmount(() => {
  cancelAnimationFrame(animationId);
  resizeObserver?.disconnect();
  controls?.dispose();
  renderer?.dispose();
  破棄対象.forEach((item) => item.dispose());
  破棄テクスチャ.forEach((texture) => texture.dispose());
  実行状態一覧.clear();
  掲示板一覧.length = 0;
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
      aria-label="ドラッグで360度回転できるAIチームの3Dワークスペース"
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

    <div class="scene-topbar">
      <div class="view-chip"><span class="view-icon">◎</span>チーム空間 / メインフロア</div>
      <div class="scene-clock"><span>LIVE</span>{{ 現在時刻 }}</div>
    </div>

    <button
      v-for="agent in エージェント一覧"
      :key="`label-${agent.id}`"
      :ref="(element) => ラベルRef設定(agent.id, element as Element | null)"
      type="button"
      class="world-label"
      :class="{
        selected: agent.id === 選択中ID,
        talking: agent.状態 === '相談中',
        hovered: agent.id === ホバー中ID,
      }"
      :style="{ '--agent-color': agent.色CSS }"
      @click.stop="エージェントを選択(agent.id)"
      @mouseenter="ホバー中ID = agent.id"
      @mouseleave="ホバー中ID = ''"
    >
      <span class="world-name">{{ agent.名前 }}</span>
      <span class="world-role">{{ agent.役割 || '役割未設定' }}</span>
      <span v-if="agent.状態 === '相談中' && agent.ひとこと" class="speech">
        {{ agent.ひとこと }}
      </span>
    </button>

    <div class="camera-help">
      <span><b>DRAG</b> 360° 回転</span>
      <span><b>WHEEL</b> ズーム</span>
      <button type="button" @click="カメラを戻す">視点を戻す</button>
    </div>

    <div class="scene-controls">
      <button
        type="button"
        class="play-button"
        :aria-label="シミュレーション中 ? '一時停止' : '再開'"
        @click="シミュレーション中 = !シミュレーション中"
      >
        {{ シミュレーション中 ? 'Ⅱ' : '▶' }}
      </button>
      <div class="speed-control">
        <span>時間速度</span>
        <input
          v-model.number="速度倍率"
          type="range"
          min="0.4"
          max="2"
          step="0.2"
          aria-label="エージェントの移動速度"
        />
        <b>{{ 速度倍率.toFixed(1) }}×</b>
      </div>
    </div>
  </main>
</template>

<style scoped>
.scene-stage {
  min-width: 0;
  min-height: 420px;
  position: relative;
  overflow: hidden;
  background: #07111d;
}

.scene-stage::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: linear-gradient(0deg, rgba(7, 17, 29, 0.45), transparent 25%);
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

.scene-topbar {
  position: absolute;
  top: 16px;
  right: 18px;
  left: 18px;
  z-index: 2;
  display: flex;
  justify-content: space-between;
  pointer-events: none;
}

.view-chip,
.scene-clock {
  padding: 7px 10px;
  border: 1px solid rgba(117, 184, 210, 0.16);
  border-radius: 8px;
  color: #8da9b9;
  background: rgba(8, 21, 33, 0.72);
  backdrop-filter: blur(10px);
  font-size: 9px;
  letter-spacing: 0.05em;
}

.view-chip {
  color: #fff;
  background: linear-gradient(135deg, rgba(108, 78, 196, 0.94), rgba(143, 104, 221, 0.9));
  border-color: rgba(93, 68, 168, 0.95);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.16),
    inset 0 -1px 0 rgba(44, 24, 101, 0.3);
}

.view-icon { margin-right: 6px; color: #5bd9ff; }
.scene-clock span { margin-right: 7px; color: #5ce3a1; font-weight: 800; }

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
  cursor: pointer;
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

.world-label:hover .world-role,
.world-label.hovered .world-role { transform: translate(-50%, 0); opacity: 1; }

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
  color: #698293;
  font-size: 8px;
}

.camera-help b { margin-right: 3px; color: #9bb3c0; }
.camera-help button {
  padding: 5px 8px;
  border: 1px solid rgba(117, 172, 196, 0.2);
  border-radius: 6px;
  color: #91a9b7;
  background: rgba(12, 28, 41, 0.7);
  cursor: pointer;
  font-size: 8px;
}

.scene-controls {
  position: absolute;
  bottom: 16px;
  left: 18px;
  z-index: 3;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 7px 10px;
  border: 1px solid rgba(117, 184, 210, 0.16);
  border-radius: 9px;
  background: rgba(8, 21, 33, 0.78);
}

.play-button {
  width: 25px;
  height: 25px;
  display: grid;
  place-items: center;
  border: 0;
  border-radius: 6px;
  color: #9aeed2;
  background: rgba(76, 213, 164, 0.13);
  cursor: pointer;
}

.speed-control {
  display: grid;
  grid-template-columns: auto 70px 28px;
  align-items: center;
  gap: 7px;
  color: #728c9c;
  font-size: 8px;
}

.speed-control input { width: 70px; margin: 0; accent-color: #62dfb0; }
.speed-control b { color: #aac0cb; font-size: 8px; }

@media (max-width: 760px) {
  .scene-stage { min-height: 520px; order: 1; }
  .camera-help span { display: none; }
}
</style>
