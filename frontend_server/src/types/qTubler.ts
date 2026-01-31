// -*- coding: utf-8 -*-

// ------------------------------------------------
// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
// This software is licensed under the MIT License.
// https://github.com/monjyu1101
// Thank you for keeping the rules.
// ------------------------------------------------

/**
 * qTublerコンポーネントの型定義
 */

export interface Column {
  key: string
  label: string
  width?: string
  align?: 'left' | 'right' | 'center'
  sortable?: boolean
}

