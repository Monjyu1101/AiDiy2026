// -*- coding: utf-8 -*-

// -------------------------------------------------------------------------
// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101
// -------------------------------------------------------------------------

import axios from 'axios'
import type { InternalAxiosRequestConfig } from 'axios'
import { CORE_BASE_URL } from '@/api/config'

const apiClient = axios.create({
  baseURL: CORE_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      localStorage.removeItem('avatar_session_id')
      window.dispatchEvent(new Event('auth-expired'))
    }
    return Promise.reject(error)
  },
)

export default apiClient
