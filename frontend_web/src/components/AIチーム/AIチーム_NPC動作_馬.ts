// NPC馬の造形と周回動作。
// カメラから見て4エリアの向こう側を放牧エリアにし、黒馬・白馬が自由に行動する。
// 白馬は普段は独立して動き、黒馬から離れたときだけ走って追従する。

import * as THREE from 'three';

import type {
  NPC定義,
  NPC個体,
  NPC更新引数,
  NPC配置,
  手動操作状態,
  造形ヘルパー,
} from './AIチーム_NPC型';

type 馬状態 = '走る' | '歩く' | 'とどまる';

type 馬設定 = {
  役割: '先導' | '追従';
  体色: number;
  たてがみ色: number;
  蹄色: number;
  基準距離: number;
  放牧半径: number;
  追従開始距離: number;
  追従終了距離: number;
  追跡対象: THREE.Group | null;
};

const 共通設定: Omit<馬設定, '役割' | '体色' | 'たてがみ色' | '蹄色'> = {
  基準距離: 34,
  放牧半径: 10,
  追従開始距離: 14,
  追従終了距離: 7,
  追跡対象: null,
};

const 最小中心距離 = 27;

/** 首の付け根の基準姿勢。歩くリズムに合わせてこの前後に振る */
const 首基準角 = -0.46;
const 首基準Z = -0.72;

/** 俯瞰カメラから見て4エリアの向こう側にある放牧エリア中心 */
const 基準位置 = (俯瞰位置: THREE.Vector3, 設定: 馬設定) => {
  const カメラ方向 = new THREE.Vector3(俯瞰位置.x, 0, 俯瞰位置.z);
  if (カメラ方向.lengthSq() < 0.01) カメラ方向.set(0, 0, 1);
  return カメラ方向.normalize().multiplyScalar(-設定.基準距離);
};

/** 中央の4エリアへ近づきすぎない、基準位置周辺のランダムな目的地 */
const 放牧目的地 = (基準: THREE.Vector3, 設定: 馬設定, 広がり = 1) => {
  const 角度 = Math.random() * Math.PI * 2;
  const 距離 = (2 + Math.random() * (設定.放牧半径 - 2)) * 広がり;
  const 目的地 = 基準.clone().add(new THREE.Vector3(Math.cos(角度) * 距離, 0, Math.sin(角度) * 距離));
  if (目的地.length() < 最小中心距離) 目的地.setLength(最小中心距離);
  return 目的地;
};

const 馬体を作る = (ヘルパー: 造形ヘルパー, 設定: 馬設定) => {
  const { ジオメトリ, マテリアル } = ヘルパー;
  const 体材 = マテリアル(設定.体色, { roughness: 0.82, metalness: 0.01 });
  const 毛材 = マテリアル(設定.たてがみ色, { roughness: 0.95 });
  const 蹄材 = マテリアル(設定.蹄色, { roughness: 0.78 });
  const 目材 = マテリアル(0x151719, { roughness: 0.3 });
  const group = new THREE.Group();
  group.scale.setScalar(1.18);

  const 胴 = new THREE.Mesh(ジオメトリ(new THREE.CapsuleGeometry(0.48, 1.45, 6, 16)), 体材);
  胴.rotation.x = Math.PI / 2;
  胴.scale.x = 0.78;
  胴.position.y = 1.42;
  group.add(胴);

  const 首 = new THREE.Group();
  首.position.set(0, 1.62, 首基準Z);
  首.rotation.x = 首基準角;
  const 首本体 = new THREE.Mesh(ジオメトリ(new THREE.CapsuleGeometry(0.27, 0.78, 5, 12)), 体材);
  首本体.position.y = 0.42;
  首.add(首本体);
  const 頭 = new THREE.Mesh(ジオメトリ(new THREE.CapsuleGeometry(0.25, 0.42, 5, 12)), 体材);
  頭.rotation.x = Math.PI / 2;
  頭.position.set(0, 0.9, -0.25);
  頭.scale.set(0.9, 1, 0.82);
  首.add(頭);
  const 鼻先 = new THREE.Mesh(ジオメトリ(new THREE.SphereGeometry(0.22, 12, 8)), 体材);
  鼻先.position.set(0, 0.87, -0.59);
  鼻先.scale.set(1, 0.72, 1.18);
  首.add(鼻先);
  const 目形 = ジオメトリ(new THREE.SphereGeometry(0.045, 8, 6));
  [-1, 1].forEach((左右) => {
    const 目 = new THREE.Mesh(目形, 目材);
    目.position.set(左右 * 0.22, 1.03, -0.31);
    首.add(目);
    const 耳 = new THREE.Mesh(ジオメトリ(new THREE.ConeGeometry(0.09, 0.34, 6)), 体材);
    耳.position.set(左右 * 0.16, 1.25, -0.08);
    耳.rotation.z = 左右 * 0.12;
    首.add(耳);
  });
  const たてがみ = new THREE.Mesh(ジオメトリ(new THREE.BoxGeometry(0.11, 0.9, 0.44)), 毛材);
  たてがみ.position.set(0, 0.46, 0.2);
  たてがみ.rotation.x = 0.28;
  首.add(たてがみ);
  group.add(首);

  const 脚: THREE.Group[] = [];
  const 脚形 = ジオメトリ(new THREE.CapsuleGeometry(0.105, 0.72, 4, 8));
  const 蹄形 = ジオメトリ(new THREE.BoxGeometry(0.23, 0.16, 0.32));
  [-0.56, 0.56].forEach((前後) => {
    [-0.28, 0.28].forEach((左右) => {
      const 脚Group = new THREE.Group();
      脚Group.position.set(左右, 1.22, 前後);
      const 脚本体 = new THREE.Mesh(脚形, 体材);
      脚本体.position.y = -0.52;
      const 蹄 = new THREE.Mesh(蹄形, 蹄材);
      蹄.position.set(0, -1.01, -0.04);
      脚Group.add(脚本体, 蹄);
      group.add(脚Group);
      脚.push(脚Group);
    });
  });

  const 尾 = new THREE.Group();
  尾.position.set(0, 1.58, 0.93);
  // 馬の尾は通常、尻から後方へ出て自然に下へ垂れる
  尾.rotation.x = Math.PI * 0.73;
  const 尾本体 = new THREE.Mesh(ジオメトリ(new THREE.CapsuleGeometry(0.12, 0.82, 5, 10)), 毛材);
  尾本体.position.y = 0.43;
  尾.add(尾本体);
  group.add(尾);

  group.traverse((object) => {
    if (object instanceof THREE.Mesh) {
      object.castShadow = true;
      object.receiveShadow = true;
    }
  });
  return { group, 胴, 首, 脚, 尾 };
};

const 馬を生成 = (
  種別: string,
  scene: THREE.Scene,
  ヘルパー: 造形ヘルパー,
  配置: NPC配置,
  設定: 馬設定,
): NPC個体 => {
  const 部位 = 馬体を作る(ヘルパー, 設定);
  const { group } = 部位;
  let 状態: 馬状態 = 設定.役割 === '先導' ? '走る' : '歩く';
  let 状態残り = 1 + Math.random() * 3;
  let 歩調 = 0;
  let 目的地 = new THREE.Vector3(0, 0, -設定.基準距離);
  let 前回基準 = 目的地.clone();
  let 追従中 = false;
  group.position.copy(目的地).add(new THREE.Vector3(設定.役割 === '追従' ? 6 : 0, 配置.位置.y, 0));
  scene.add(group);

  const 次の自由行動 = (基準: THREE.Vector3) => {
    const くじ = Math.random();
    状態 = くじ < 0.3 ? '走る' : くじ < 0.76 ? '歩く' : 'とどまる';
    状態残り = 状態 === '走る' ? 3 + Math.random() * 6 : 状態 === '歩く' ? 5 + Math.random() * 10 : 2 + Math.random() * 7;
    if (状態 !== 'とどまる') 目的地 = 放牧目的地(基準, 設定, 状態 === '走る' ? 1.15 : 0.85);
  };

  /** 脚・胴・首・尾の動き。自律行動でも一人称操作でも、いまの速度から同じように作る */
  const 見た目を更新 = (速度: number, delta: number, 時刻: number) => {
    if (速度 > 0) 歩調 += delta * (状態 === '走る' ? 12.5 : 7.2);
    部位.脚.forEach((脚, index) => {
      const 対角位相 = index === 0 || index === 3 ? 0 : Math.PI;
      const 振幅 = 状態 === '走る' ? 0.72 : 状態 === '歩く' ? 0.42 : 0.03;
      脚.rotation.x = THREE.MathUtils.lerp(脚.rotation.x, Math.sin(歩調 + 対角位相) * 振幅, 0.32);
    });
    const 弾み = 速度 > 0 ? Math.abs(Math.sin(歩調 * 2)) * (状態 === '走る' ? 0.1 : 0.045) : 0;
    部位.胴.position.y = 1.42 + 弾み;
    部位.首.rotation.z = Math.sin(歩調 * 2) * (速度 > 0 ? 0.025 : 0.008);
    // 首は一歩ごとに前後へ大きく波打つ。走るほど深く伸び縮みする
    const 首振り = 状態 === '走る' ? 0.19 : 状態 === '歩く' ? 0.085 : 0.014;
    const 首波 = Math.sin(歩調);
    部位.首.rotation.x = THREE.MathUtils.lerp(部位.首.rotation.x, 首基準角 + 首波 * 首振り, 0.4);
    部位.首.position.z = THREE.MathUtils.lerp(
      部位.首.position.z,
      首基準Z + 首波 * (状態 === '走る' ? 0.11 : 状態 === '歩く' ? 0.05 : 0.008),
      0.4,
    );
    // 普段は静かに垂らし、間欠的に左右へ強く叩いて虫を払う
    const 尾叩き中 = Math.sin(時刻 * 0.00043 + (設定.役割 === '先導' ? 0 : 2.1)) > 0.68;
    const 尾振幅 = 尾叩き中 ? 0.62 : 0.035;
    const 尾速度 = 尾叩き中 ? 0.012 : 0.0018;
    部位.尾.rotation.y = THREE.MathUtils.lerp(
      部位.尾.rotation.y,
      Math.sin(時刻 * 尾速度) * 尾振幅,
      尾叩き中 ? 0.28 : 0.06,
    );
  };

  // 一人称視点で操作されているあいだは、位置と向きを画面側に任せて見た目だけ合わせる
  let 手動: 手動操作状態 | null = null;

  const 更新 = ({ delta, 時刻, 俯瞰位置 }: NPC更新引数) => {
    if (delta <= 0) return;

    if (手動) {
      状態 = 手動.速さ < 0.05 ? 'とどまる' : 手動.全力 ? '走る' : '歩く';
      状態残り = 1;
      追従中 = false;
      目的地.copy(group.position);
      前回基準.copy(基準位置(俯瞰位置, 設定));
      見た目を更新(手動.速さ, delta, 時刻);
      return;
    }

    const 基準 = 基準位置(俯瞰位置, 設定);
    const 基準移動量 = 基準.distanceTo(前回基準);
    前回基準.lerp(基準, Math.min(1, delta * 1.4));
    let 速度 = 0;

    const 基準からの距離 = group.position.distanceTo(基準);
    const 視点変更で帰還 = 基準移動量 > 2.5 || 基準からの距離 > 設定.放牧半径 * 1.7;
    if (視点変更で帰還) {
      状態 = '走る';
      状態残り = 2;
      // 視点回転中にランダム目的地を毎フレーム引き直すと蛇行するため、移動中の基準そのものを追う
      目的地.copy(基準);
    }

    if (設定.役割 === '追従' && 設定.追跡対象) {
      const 黒馬距離 = group.position.distanceTo(設定.追跡対象.position);
      if (黒馬距離 > 設定.追従開始距離) 追従中 = true;
      if (黒馬距離 < 設定.追従終了距離) 追従中 = false;
      if (追従中) {
        状態 = '走る';
        状態残り = 1.5;
        const 横ずれ = new THREE.Vector3(Math.sin(時刻 * 0.0007) * 2.2, 0, Math.cos(時刻 * 0.0009) * 2.2);
        目的地 = 設定.追跡対象.position.clone().add(横ずれ);
      }
    }

    状態残り -= delta;
    const 目的地到着 = group.position.distanceTo(目的地) < 0.7;
    if (!追従中 && (状態残り <= 0 || (目的地到着 && 状態 !== 'とどまる'))) 次の自由行動(基準);
    速度 = 状態 === '走る' ? (追従中 ? 5.4 : 4.4 + Math.random() * 0.35) : 状態 === '歩く' ? 1.25 + Math.random() * 0.25 : 0;

    if (速度 > 0) {
      const 向き = 目的地.clone().sub(group.position);
      向き.y = 0;
      const 距離 = 向き.length();
      if (距離 > 0.05) {
        向き.normalize();
        group.position.addScaledVector(向き, Math.min(距離, 速度 * delta));
        group.rotation.y = THREE.MathUtils.lerp(group.rotation.y, Math.atan2(向き.x, 向き.z) + Math.PI, 0.14);
      }
    }

    見た目を更新(速度, delta, 時刻);
  };

  return {
    種別,
    group,
    更新,
    手動操作: (状態指定: 手動操作状態 | null) => {
      手動 = 状態指定;
      if (!状態指定) {
        状態 = '歩く';
        状態残り = 0;
        目的地.copy(group.position);
      }
    },
  };
};

export const 黒馬定義: NPC定義<馬設定> = {
  種別: '黒馬',
  既定設定: { ...共通設定, 役割: '先導', 体色: 0x17191c, たてがみ色: 0x050607, 蹄色: 0x08090a },
  生成: (scene, ヘルパー, 配置, 設定) => 馬を生成('黒馬', scene, ヘルパー, 配置, 設定),
};

export const 白馬定義: NPC定義<馬設定> = {
  種別: '白馬',
  既定設定: { ...共通設定, 役割: '追従', 体色: 0xf2f0e8, たてがみ色: 0xd7d3c8, 蹄色: 0x8c8982 },
  生成: (scene, ヘルパー, 配置, 設定) => 馬を生成('白馬', scene, ヘルパー, 配置, 設定),
};
