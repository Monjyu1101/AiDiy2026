// NPC飛行船の動作制御。
// 4エリアの上空をゆっくり旋回し、船底から「吊り下げ物」（チーム目標の掲示板）を下げて運ぶ。
// 旋回半径・高度・速さ・船体の大きさ・吊り下げ距離はここだけで調整する。

import * as THREE from 'three';

import { type NPC定義, type NPC個体, 乱数を作る } from './AIチーム_NPC型';

export type 飛行船設定 = {
  /** 旋回半径（配置位置を中心とする） */
  旋回半径: number;
  /** 飛行高度 */
  高度: number;
  /** 旋回の速さ（1秒あたりのラジアン） */
  旋回速度: number;
  /** 高度の揺れ幅 */
  上下幅: number;
  /** 旋回時のバンク角 */
  傾き: number;
  /** 船体の大きさ */
  船体長: number;
  船体径: number;
  /** 色（帯色は尾翼とプロペラにも使う） */
  船体色: number;
  帯色: number;
  /** プロペラの回転速度 */
  プロペラ速度: number;
  /** 吊り下げ物を船底から下げる距離 */
  吊り下げ距離: number;
  /** 吊り下げるオブジェクト（シーン直下に置いたものを渡す） */
  吊り下げ物: THREE.Object3D | null;
  /** 吊り下げ物を常にカメラへ向けるか（掲示板を読ませたいので既定 true） */
  吊り下げカメラ追従: boolean;
};

export const 飛行船既定設定: 飛行船設定 = {
  旋回半径: 16,
  高度: 15.5,
  旋回速度: 0.055,
  上下幅: 0.5,
  傾き: 0.1,
  船体長: 14,
  船体径: 3.4,
  船体色: 0xe8e2d4,
  帯色: 0xc2603f,
  プロペラ速度: 0.012,
  吊り下げ距離: 4.6,
  吊り下げ物: null,
  吊り下げカメラ追従: true,
};

export const 飛行船定義: NPC定義<飛行船設定> = {
  種別: '飛行船',
  既定設定: 飛行船既定設定,
  生成: (scene, ヘルパー, 配置, 設定): NPC個体 => {
    const { ジオメトリ, マテリアル } = ヘルパー;
    const 乱数 = 乱数を作る(配置.種 ?? 1);
    const 船体材 = マテリアル(設定.船体色, { roughness: 0.62, metalness: 0.18 });
    const 帯材 = マテリアル(設定.帯色, { roughness: 0.7, metalness: 0.1 });
    const 金具材 = マテリアル(0x9aa7ad, { roughness: 0.35, metalness: 0.7 });

    const group = new THREE.Group();

    // 船体（前後にとがった気球。長手を z 方向に置く）
    const 船体 = new THREE.Mesh(
      ジオメトリ(new THREE.SphereGeometry(設定.船体径 * 0.5, 20, 14)),
      船体材,
    );
    船体.scale.set(1, 0.92, 設定.船体長 / 設定.船体径);
    group.add(船体);
    // 胴のライン（帯）
    // 尾翼（垂直 + 水平）
    const 尾翼Z = 設定.船体長 * 0.36;
    const 垂直翼 = new THREE.Mesh(
      ジオメトリ(new THREE.BoxGeometry(0.11, 設定.船体径 * 0.46, 設定.船体径 * 0.5)),
      帯材,
    );
    垂直翼.position.set(0, 設定.船体径 * 0.3, 尾翼Z);
    group.add(垂直翼);
    const 水平翼 = new THREE.Mesh(
      ジオメトリ(new THREE.BoxGeometry(設定.船体径 * 1.05, 0.11, 設定.船体径 * 0.42)),
      帯材,
    );
    水平翼.position.set(0, 0, 尾翼Z);
    group.add(水平翼);

    // プロペラ（後方の左右）
    const プロペラ一覧: THREE.Group[] = [];
    [-1, 1].forEach((向き) => {
      const 軸 = new THREE.Group();
      軸.position.set(向き * 設定.船体径 * 0.52, -設定.船体径 * 0.22, 設定.船体長 * 0.3);
      const ハブ = new THREE.Mesh(
        ジオメトリ(new THREE.CylinderGeometry(0.1, 0.1, 0.3, 8)),
        金具材,
      );
      ハブ.rotation.x = Math.PI / 2;
      軸.add(ハブ);
      const 羽根形 = ジオメトリ(new THREE.BoxGeometry(0.1, 設定.船体径 * 0.62, 0.06));
      [0, Math.PI / 2].forEach((回転) => {
        const 羽根 = new THREE.Mesh(羽根形, 帯材);
        羽根.rotation.z = 回転;
        軸.add(羽根);
      });
      group.add(軸);
      プロペラ一覧.push(軸);
    });

    // 吊り下げ用のロープ。吊り下げ物の高さを測り、船体下端から上端までの長さだけにする
    if (設定.吊り下げ物) {
      const ロープ材 = マテリアル(0xcdb182, { roughness: 0.95, metalness: 0.0 });
      const 枠 = new THREE.Box3().setFromObject(設定.吊り下げ物);
      const 吊り下げ半高 = Math.max((枠.max.y - 枠.min.y) * 0.5, 0);
      const 船体下端 = 設定.船体径 * 0.46;
      const ロープ長 = Math.max(設定.吊り下げ距離 - 船体下端 - 吊り下げ半高, 0.2);
      const ロープ形 = ジオメトリ(new THREE.CylinderGeometry(0.04, 0.04, ロープ長, 6));
      [-1, 1].forEach((向き) => {
        const ロープ = new THREE.Mesh(ロープ形, ロープ材);
        ロープ.position.set(向き * 設定.船体径 * 0.3, -(船体下端 + ロープ長 * 0.5), 0);
        group.add(ロープ);
      });
    }

    group.traverse((object) => {
      if (object instanceof THREE.Mesh) object.castShadow = true;
    });
    scene.add(group);

    const 中心 = 配置.位置.clone();
    const 位相 = 乱数() * Math.PI * 2;

    return {
      種別: '飛行船',
      group,
      更新: ({ 経過時間, 時刻, camera }) => {
        const 角度 = 経過時間 * 設定.旋回速度 + 位相;
        const 高さ = 中心.y + 設定.高度 + Math.sin(時刻 * 0.0004 + 位相) * 設定.上下幅;
        group.position.set(
          中心.x + Math.cos(角度) * 設定.旋回半径,
          高さ,
          中心.z + Math.sin(角度) * 設定.旋回半径,
        );
        // 進行方向（円の接線）へ機首（-z）を向け、旋回の内側へ少し傾ける
        group.rotation.set(0, Math.PI - 角度, 設定.傾き);
        プロペラ一覧.forEach((軸, index) => {
          軸.rotation.z = 時刻 * 設定.プロペラ速度 * (index === 0 ? 1 : -1);
        });

        // 吊り下げ物は船底の真下へ運び、常にカメラを向かせる
        const 吊り下げ物 = 設定.吊り下げ物;
        if (吊り下げ物) {
          吊り下げ物.position.set(
            group.position.x,
            高さ - 設定.吊り下げ距離,
            group.position.z,
          );
          if (設定.吊り下げカメラ追従) {
            吊り下げ物.lookAt(camera.position.x, 吊り下げ物.position.y, camera.position.z);
          }
        }
      },
    };
  },
};
