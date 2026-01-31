// -*- coding: utf-8 -*-

// ------------------------------------------------
// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
// This software is licensed under the MIT License.
// https://github.com/monjyu1101
// Thank you for keeping the rules.
// ------------------------------------------------

import type { C利用者 } from './entities'

/**
 * 認証関連
 */
export interface LoginRequest {
  利用者ID: string
  パスワード: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
}

export interface CurrentUserResponse extends C利用者 {
  権限名?: string
}

/**
 * C権限 API
 */
export interface C権限GetRequest {
  権限ID: string
}

export interface C権限CreateRequest {
  権限ID: string
  権限名: string
  権限備考?: string
}

export interface C権限UpdateRequest {
  権限ID: string
  権限名?: string
  権限備考?: string
}

export interface C権限DeleteRequest {
  権限ID: string
}

/**
 * C利用者 API
 */
export interface C利用者GetRequest {
  利用者ID: string
}

export interface C利用者CreateRequest {
  利用者ID: string
  利用者名: string
  パスワード: string
  権限ID: string
  利用者備考?: string
}

export interface C利用者UpdateRequest {
  利用者ID: string
  利用者名?: string
  パスワード?: string
  権限ID?: string
  利用者備考?: string
}

export interface C利用者DeleteRequest {
  利用者ID: string
}

/**
 * C採番 API
 */
export interface C採番GetRequest {
  採番ID: string
}

export interface C採番CreateRequest {
  採番ID: string
  最終採番値: number
  採番備考?: string
}

export interface C採番UpdateRequest {
  採番ID: string
  最終採番値?: number
  採番備考?: string
}

export interface C採番DeleteRequest {
  採番ID: string
}

export interface C採番次番取得Request {
  採番区分: string
  採番数?: number
}

export interface C採番次番取得Response {
  次番開始: number
  次番終了: number
  次番リスト: number[]
}

/**
 * テーブルカラム定義
 */
export interface TableColumn {
  key: string
  label: string
  width?: string
  sortable?: boolean
}

/**
 * フィルタ型定義ヘルパー
 */
export type FilterObject<T> = {
  [K in keyof T]?: string
}

