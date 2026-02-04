// -*- coding: utf-8 -*-

// ------------------------------------------------
// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
// This software is licensed under the MIT License.
// https://github.com/monjyu1101
// Thank you for keeping the rules.
// ------------------------------------------------

import type { C利用者 } from './entities'

/**
 * Auth Store State
 */
export interface AuthState {
  token: string
  user: C利用者 | null
  authChecked: boolean
}

/**
 * Login Result
 */
export interface LoginResult {
  success: boolean
  message?: string
}

