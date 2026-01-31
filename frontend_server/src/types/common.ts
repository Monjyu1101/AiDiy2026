// -*- coding: utf-8 -*-

// ------------------------------------------------
// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
// This software is licensed under the MIT License.
// https://github.com/monjyu1101
// Thank you for keeping the rules.
// ------------------------------------------------

/**
 * 統一APIレスポンス形式
 */
export interface ApiResponse<T = any> {
  status: 'OK' | 'NG'
  message: string
  data?: T
  error?: Record<string, any>
}

/**
 * モード定義
 */
export type EditMode = 'create' | 'edit' | 'view'

/**
 * メッセージタイプ
 */
export type MessageType = 'success' | 'error' | 'warning' | 'info'

/**
 * 監査フィールド（全テーブル共通）
 */
export interface AuditFields {
  登録日時: string
  登録利用者ID: string
  登録利用者名: string | null
  登録端末ID: string
  更新日時: string
  更新利用者ID: string
  更新利用者名: string | null
  更新端末ID: string
}

/**
 * ページネーション情報
 */
export interface PaginationInfo {
  currentPage: number
  pageSize: number
  totalCount: number
  totalPages: number
}

/**
 * ソート情報
 */
export interface SortInfo {
  key: string
  order: 'asc' | 'desc'
}

