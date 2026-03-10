// -*- coding: utf-8 -*-

// -------------------------------------------------------------------------
// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101
// -------------------------------------------------------------------------

import type { AuditFields } from './common'

/**
 * CRITICAL: All ID fields are STRING type, not number!
 * バックエンドは文字列でIDを返します: {"権限ID": "1", "利用者ID": "USR001"}
 */

// ==================== C系（共通・管理） ====================

/**
 * C権限（権限マスタ）
 */
export interface C権限 extends AuditFields {
  権限ID: string  // STRING, not number!
  権限名: string
  権限備考: string | null
}

/**
 * C利用者（利用者マスタ）
 */
export interface C利用者 extends AuditFields {
  利用者ID: string  // STRING, not number!
  利用者名: string
  パスワード: string
  権限ID: string    // STRING, not number!
  利用者備考: string | null
}

/**
 * C採番（採番管理）
 */
export interface C採番 extends AuditFields {
  採番ID: string
  最終採番値: number
  採番備考: string | null
}

// ==================== M系（マスタ） ====================

/**
 * M車両（車両マスタ）
 */
export interface M車両 extends AuditFields {
  車両ID: string
  車両名: string
  車両備考: string | null
}

/**
 * M商品（商品マスタ）
 */
export interface M商品 extends AuditFields {
  商品ID: string
  商品名: string
  商品備考: string | null
}

/**
 * M配車区分（配車区分マスタ）
 */
export interface M配車区分 extends AuditFields {
  配車区分ID: string
  配車区分名: string
  配車区分備考: string | null
}

// ==================== T系（トランザクション） ====================

/**
 * T配車（配車トランザクション）
 */
export interface T配車 extends AuditFields {
  配車ID: string
  配車日: string
  車両ID: string
  配車区分ID: string
  配車備考: string | null
}

/**
 * T商品入庫（商品入庫トランザクション）
 */
export interface T商品入庫 extends AuditFields {
  入庫ID: string
  入庫日: string
  商品ID: string
  入庫数量: number
  入庫備考: string | null
}

/**
 * T商品出庫（商品出庫トランザクション）
 */
export interface T商品出庫 extends AuditFields {
  出庫ID: string
  出庫日: string
  商品ID: string
  出庫数量: number
  出庫備考: string | null
}

/**
 * T商品棚卸（商品棚卸トランザクション）
 */
export interface T商品棚卸 extends AuditFields {
  棚卸ID: string
  棚卸日: string
  商品ID: string
  棚卸数量: number
  棚卸備考: string | null
}

// ==================== V系（ビュー） ====================

/**
 * V利用者（利用者ビュー - JOIN結果）
 */
export interface V利用者 extends C利用者 {
  権限名: string
}

/**
 * V車両（車両ビュー）
 */
export interface V車両 extends M車両 {
  // 追加のビュー固有フィールドがあればここに定義
}

/**
 * V商品（商品ビュー）
 */
export interface V商品 extends M商品 {
  // 追加のビュー固有フィールドがあればここに定義
}

/**
 * V配車区分（配車区分ビュー）
 */
export interface V配車区分 extends M配車区分 {
  // 追加のビュー固有フィールドがあればここに定義
}

/**
 * V配車（配車ビュー）
 */
export interface V配車 extends T配車 {
  車両名?: string
  配車区分名?: string
}

/**
 * V商品入庫（商品入庫ビュー）
 */
export interface V商品入庫 extends T商品入庫 {
  商品名?: string
}

/**
 * V商品出庫（商品出庫ビュー）
 */
export interface V商品出庫 extends T商品出庫 {
  商品名?: string
}

/**
 * V商品棚卸（商品棚卸ビュー）
 */
export interface V商品棚卸 extends T商品棚卸 {
  商品名?: string
}

/**
 * V商品推移表（商品推移集計ビュー）
 */
export interface V商品推移表 {
  商品ID: string
  商品名: string
  入庫合計: number
  出庫合計: number
  棚卸合計: number
  在庫数: number
}

/**
 * V採番（採番ビュー）
 */
export interface V採番 extends C採番 {
  // 追加のビュー固有フィールドがあればここに定義
}

/**
 * V権限（権限ビュー）
 */
export interface V権限 extends C権限 {
  // 追加のビュー固有フィールドがあればここに定義
}

