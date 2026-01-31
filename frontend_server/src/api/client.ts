// -*- coding: utf-8 -*-

// ------------------------------------------------
// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
// This software is licensed under the MIT License.
// https://github.com/monjyu1101
// Thank you for keeping the rules.
// ------------------------------------------------

import axios from 'axios'
import type { InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '../stores/auth'

const apiClient = axios.create({
    baseURL: '/',
    headers: {
        'Content-Type': 'application/json',
    },
})

// リクエストインターセプター: トークン付与
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
    const authStore = useAuthStore()
    if (authStore.token) {
        config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
})

// レスポンスインターセプター: エラーハンドリング
apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response && error.response.status === 401) {
            const authStore = useAuthStore()
            authStore.logout()
        }
        return Promise.reject(error)
    }
)

export default apiClient

