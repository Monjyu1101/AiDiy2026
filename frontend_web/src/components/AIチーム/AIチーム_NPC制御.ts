// NPC制御。種別ごとの動作モジュールを登録し、配置と毎フレーム更新の入口をまとめる。
//
// 画面（AIチーム_空間表示.vue）はこのファイルだけを使い、
// 個々の見た目や動きは AIチーム_NPC動作_*.ts 側で調整する。

import type * as THREE from 'three';

import { イヌ定義 } from './AIチーム_NPC動作_イヌ';
import { ネコ定義 } from './AIチーム_NPC動作_ネコ';
import { 蝶定義 } from './AIチーム_NPC動作_蝶';
import { 雲定義 } from './AIチーム_NPC動作_雲';
import { 飛行船定義 } from './AIチーム_NPC動作_飛行船';
import type { NPC個体, NPC更新引数, NPC配置, 造形ヘルパー } from './AIチーム_NPC型';

/** 種別 → 動作モジュールの登録表。NPC を増やすときはここへ 1 行追加する */
const NPC定義一覧 = {
  ネコ: ネコ定義,
  イヌ: イヌ定義,
  雲: 雲定義,
  蝶: 蝶定義,
  飛行船: 飛行船定義,
} as const;

export type NPC種別 = keyof typeof NPC定義一覧;
/** 種別ごとの設定型（上書きしたい項目だけ渡せる） */
export type NPC設定<T extends NPC種別> = (typeof NPC定義一覧)[T]['既定設定'];

export type { NPC個体, NPC更新引数, NPC配置, 造形ヘルパー };

/** NPC を 1 体つくってシーンへ追加する */
export const NPCを配置 = <T extends NPC種別>(
  scene: THREE.Scene,
  種別: T,
  ヘルパー: 造形ヘルパー,
  配置: NPC配置,
  上書き: Partial<NPC設定<T>> = {},
): NPC個体 => {
  const 定義 = NPC定義一覧[種別];
  const 設定 = { ...定義.既定設定, ...上書き };
  return 定義.生成(scene, ヘルパー, 配置, 設定 as never);
};

/** 配置済みの NPC をまとめて 1 フレーム進める */
export const NPC群を更新 = (一覧: NPC個体[], 引数: NPC更新引数): void => {
  一覧.forEach((npc) => npc.更新(引数));
};
