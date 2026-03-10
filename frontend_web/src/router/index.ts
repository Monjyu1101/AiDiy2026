// -*- coding: utf-8 -*-

// -------------------------------------------------------------------------
// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101
// -------------------------------------------------------------------------

import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import ログイン from '../components/ログイン.vue'
import { coreRoutes } from './coreRouter'
import { appsRoutes } from './appsRouter'

// ベースルート (認証, リンク, X系)
const baseRoutes: RouteRecordRaw[] = [
    {
        path: '/ログイン',
        name: 'login',
        component: ログイン,
        meta: { title: 'ログイン' }
    },
    {
        path: '/ログアウト',
        name: 'logout',
        component: () => import('../components/ログアウト.vue'),
        meta: { requiresAuth: true, title: 'ログアウト' }
    },
    {
        path: '/リンク',
        name: 'リンク',
        component: () => import('../components/リンク.vue'),
        meta: { requiresAuth: true, title: 'リンク' }
    },
    {
        path: '/Xその他',
        name: 'その他',
        component: () => import('../components/Xその他.vue'),
        meta: { requiresAuth: true, title: 'その他' }
    },
    {
        path: '/Xその他/Xテトリス/ゲーム',
        name: 'Xテトリス',
        component: () => import('../components/Xテスト/Xテトリス.vue'),
        meta: { requiresAuth: true, title: 'Xテトリス' }
    },
    {
        path: '/Xその他/Xインベーダー/ゲーム',
        name: 'Xインベーダー',
        component: () => import('../components/Xテスト/Xインベーダー.vue'),
        meta: { requiresAuth: true, title: 'Xインベーダー' }
    },
    {
        path: '/Xその他/Xリバーシ/ゲーム',
        name: 'Xリバーシ',
        component: () => import('../components/Xテスト/Xリバーシ.vue'),
        meta: { requiresAuth: true, title: 'Xリバーシ' }
    },
    {
        path: '/Xその他/X自己紹介/表示',
        name: 'X自己紹介',
        component: () => import('../components/Xテスト/X自己紹介.vue'),
        meta: { requiresAuth: true, title: 'X自己紹介' }
    },
]

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        ...baseRoutes,
        ...coreRoutes,
        ...appsRoutes,
    ]
})

router.beforeEach(async (to, _from, next) => {
    // 日本語URLのリロード対応: エンコードされたパスが来た場合、デコードしてリダイレクト
    try {
        const decodedPath = decodeURIComponent(to.path)
        if (decodedPath !== to.path) {
            next({ path: decodedPath, query: to.query, hash: to.hash })
            return
        }
    } catch (e) {
        console.error('URL Decode Error:', e)
    }

    const authStore = useAuthStore()
    if (to.meta.requiresAuth) {
        if (!authStore.token) {
            next('/ログイン')
            return
        }
        await authStore.ensureAuth()
        if (!authStore.user) {
            next('/ログイン')
            return
        }
    }
    next()
})

const BASE_TITLE = 'AiDiy'
router.afterEach((to) => {
    const pageTitle = to.meta?.title || (typeof to.name === 'string' ? to.name : '')
    document.title = pageTitle ? `${BASE_TITLE} - ${pageTitle}` : BASE_TITLE
})

export default router
