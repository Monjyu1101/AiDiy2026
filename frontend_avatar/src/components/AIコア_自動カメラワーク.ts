// -*- coding: utf-8 -*-

// -------------------------------------------------------------------------
// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101
// -------------------------------------------------------------------------

import * as THREE from 'three'

export type 自動カメラワーク設定 = {
  基準半径: number
  半径: number
  最小半径: number
  最大半径: number
  注視Y: number
  角速度: number
  高さ振幅: number
  初期角度: number
}

export function 自動カメラワーク初期化(基準Y: number, 基準Z: number, modelSize: THREE.Vector3): 自動カメラワーク設定 {
  const baseRadius = Math.max(1.1, Math.abs(基準Z))
  return {
    基準半径: baseRadius,
    半径: baseRadius,
    最小半径: Math.max(0.12, baseRadius * 0.12),
    最大半径: baseRadius * 3.2,
    注視Y: 基準Y,
    // 約36秒で1周
    角速度: (Math.PI * 2) / 36,
    高さ振幅: Math.max(0.015, modelSize.y * 0.018),
    初期角度: 0,
  }
}

export function カメラ周回位置適用(
  camera: THREE.PerspectiveCamera,
  設定: 自動カメラワーク設定,
  angle: number,
  高さオフセット = 0,
): void {
  camera.position.x = Math.sin(angle) * 設定.半径
  camera.position.z = -Math.cos(angle) * 設定.半径
  camera.position.y = 設定.注視Y + 高さオフセット
  camera.lookAt(0, 設定.注視Y, 0)
  camera.updateProjectionMatrix()
}

export function 自動カメラワーク適用(
  camera: THREE.PerspectiveCamera,
  elapsed: number,
  設定: 自動カメラワーク設定,
  手動角度オフセット = 0,
  手動高さオフセット = 0,
): void {
  const angle = 設定.初期角度 + elapsed * 設定.角速度 + 手動角度オフセット
  const 高さオフセット = Math.sin(angle * 0.5) * 設定.高さ振幅 + 手動高さオフセット
  カメラ周回位置適用(camera, 設定, angle, 高さオフセット)
}

export function 手動カメラ周回適用(
  camera: THREE.PerspectiveCamera,
  設定: 自動カメラワーク設定,
  手動角度オフセット = 0,
  手動高さオフセット = 0,
): void {
  const angle = 設定.初期角度 + 手動角度オフセット
  カメラ周回位置適用(camera, 設定, angle, 手動高さオフセット)
}

export function カメラ距離倍率適用(
  設定: 自動カメラワーク設定,
  距離倍率: number,
): 自動カメラワーク設定 {
  設定.半径 = THREE.MathUtils.clamp(
    設定.基準半径 * 距離倍率,
    設定.最小半径,
    設定.最大半径,
  )
  return 設定
}
