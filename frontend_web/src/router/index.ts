// -*- coding: utf-8 -*-

// -------------------------------------------------------------------------
// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
// -------------------------------------------------------------------------

import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import ログイン from '../components/ログイン.vue'
import { coreRoutes } from './coreRouter'
import { appsRoutes } from './appsRouter'

const buildStaticRedirectUrl = (targetPath: string): string => {
    const baseUrl = import.meta.env.BASE_URL || '/'
    const normalizedBaseUrl = baseUrl.endsWith('/') ? baseUrl : `${baseUrl}/`
    return new URL(targetPath.replace(/^\/+/, ''), new URL(normalizedBaseUrl, window.location.origin)).toString()
}

const createStaticAliasRoute = (
    aliasPath: string,
    targetPath: string,
    title: string,
): RouteRecordRaw => ({
    path: aliasPath,
    component: { render: () => null },
    beforeEnter: () => {
        window.location.replace(buildStaticRedirectUrl(targetPath))
        return false
    },
    meta: { title },
})

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
        path: '/メニュー',
        name: 'メニュー',
        component: () => import('../components/メニュー.vue'),
        meta: { requiresAuth: true, title: 'メニュー' }
    },
    {
        path: '/Xその他',
        name: 'その他',
        component: () => import('../components/Xその他.vue'),
        meta: { requiresAuth: true, title: 'その他' }
    },
    {
        path: '/Xビデオ',
        name: 'Xビデオ',
        component: () => import('../components/Xビデオ.vue'),
        meta: { requiresAuth: true, title: 'Xビデオ' }
    },
    {
        path: '/Xその他/Xテトリス/ゲーム',
        name: 'Xテトリス',
        component: () => import('../components/Xその他/Xテトリス.vue'),
        meta: { requiresAuth: true, title: 'Xテトリス' }
    },
    {
        path: '/Xその他/Xインベーダー/ゲーム',
        name: 'Xインベーダー',
        component: () => import('../components/Xその他/Xインベーダー.vue'),
        meta: { requiresAuth: true, title: 'Xインベーダー' }
    },
    {
        path: '/Xその他/Xリバーシ/ゲーム',
        name: 'Xリバーシ',
        component: () => import('../components/Xその他/Xリバーシ.vue'),
        meta: { requiresAuth: true, title: 'Xリバーシ' }
    },
    {
        path: '/Xその他/X立体リバーシ/ゲーム',
        name: 'X立体リバーシ',
        component: () => import('../components/Xその他/X立体リバーシ.vue'),
        meta: { requiresAuth: true, title: 'X立体リバーシ' }
    },
    {
        path: '/Xその他/X世界の絶景/表示',
        name: 'X世界の絶景',
        component: () => import('../components/Xその他/X世界の絶景.vue'),
        meta: { requiresAuth: true, title: 'X世界の絶景' }
    },
    {
        path: '/Xその他/X太陽系/表示',
        name: 'X太陽系',
        component: () => import('../components/Xその他/X太陽系.vue'),
        meta: { requiresAuth: true, title: 'X太陽系' }
    },
    {
        path: '/Xその他/X動画再生BGM/再生',
        name: 'X動画再生BGM',
        component: () => import('../components/Xその他/X動画再生BGM.vue'),
        meta: { requiresAuth: true, title: 'X動画再生BGM' }
    },
    {
        path: '/Xその他/X自己紹介/表示',
        name: 'X自己紹介',
        component: () => import('../components/Xその他/X自己紹介.vue'),
        meta: { requiresAuth: true, title: 'X自己紹介' }
    },
    createStaticAliasRoute(
        '/X自己紹介/aidiy紹介ビデオtake4/index.html',
        'X自己紹介/AiDiy紹介ビデオtake4/index.html',
        'X自己紹介'
    ),
    createStaticAliasRoute(
        '/X自己紹介/AiDiy自己紹介ビデオtake4/index.html',
        'X自己紹介/AiDiy紹介ビデオtake4/index.html',
        'X自己紹介'
    ),
    createStaticAliasRoute(
        '/X自己紹介/aidiy紹介アバター/index.html',
        'X自己紹介/AiDiy紹介アバター/index.html',
        'X自己紹介'
    ),
    createStaticAliasRoute(
        '/X自己紹介/aidiy紹介hermes/index.html',
        'X自己紹介/AiDiy紹介hermes/index.html',
        'X自己紹介'
    ),
    createStaticAliasRoute(
        '/Xビデオ/AiDiy紹介__all',
        'Xビデオ/AiDiy紹介__all_ja/index.html',
        'Xビデオ'
    ),
    createStaticAliasRoute(
        '/Xビデオ/AiDiy紹介__all_ja',
        'Xビデオ/AiDiy紹介__all_ja/index.html',
        'Xビデオ'
    ),
    createStaticAliasRoute(
        '/Xビデオ/AiDiy紹介_AIコア',
        'Xビデオ/AiDiy紹介_AIコア_ja/index.html',
        'Xビデオ'
    ),
    createStaticAliasRoute(
        '/Xビデオ/AiDiy紹介_AIコア_ja',
        'Xビデオ/AiDiy紹介_AIコア_ja/index.html',
        'Xビデオ'
    ),
    createStaticAliasRoute(
        '/Xビデオ/AiDiy紹介_backend',
        'Xビデオ/AiDiy紹介_backend_ja/index.html',
        'Xビデオ'
    ),
    createStaticAliasRoute(
        '/Xビデオ/AiDiy紹介_backend_ja',
        'Xビデオ/AiDiy紹介_backend_ja/index.html',
        'Xビデオ'
    ),
    createStaticAliasRoute(
        '/Xビデオ/AiDiy紹介_frontend',
        'Xビデオ/AiDiy紹介_frontend_ja/index.html',
        'Xビデオ'
    ),
    createStaticAliasRoute(
        '/Xビデオ/AiDiy紹介_frontend_ja',
        'Xビデオ/AiDiy紹介_frontend_ja/index.html',
        'Xビデオ'
    ),
    createStaticAliasRoute(
        '/Xビデオ/AiDiy紹介_avatar',
        'Xビデオ/AiDiy紹介_avatar_ja/index.html',
        'Xビデオ'
    ),
    createStaticAliasRoute(
        '/Xビデオ/AiDiy紹介_avatar_ja',
        'Xビデオ/AiDiy紹介_avatar_ja/index.html',
        'Xビデオ'
    ),
    createStaticAliasRoute(
        '/Xビデオ/AiDiy紹介_hermes',
        'Xビデオ/AiDiy紹介_hermes_ja/index.html',
        'Xビデオ'
    ),
    createStaticAliasRoute(
        '/Xビデオ/AiDiy紹介_hermes_ja',
        'Xビデオ/AiDiy紹介_hermes_ja/index.html',
        'Xビデオ'
    ),
    createStaticAliasRoute(
        '/Xビデオ/AiDiy紹介_tools',
        'Xビデオ/AiDiy紹介_tools_ja/index.html',
        'Xビデオ'
    ),
    createStaticAliasRoute(
        '/Xビデオ/AiDiy紹介_tools_ja',
        'Xビデオ/AiDiy紹介_tools_ja/index.html',
        'Xビデオ'
    ),
    createStaticAliasRoute(
        '/Xビデオ/AiDiy紹介_mcp',
        'Xビデオ/AiDiy紹介_tools_ja/index.html',
        'Xビデオ'
    ),
    createStaticAliasRoute(
        '/Xビデオ/AiDiy紹介_配車管理',
        'Xビデオ/AiDiy実装_配車管理_ja/index.html',
        'Xビデオ'
    ),
    createStaticAliasRoute(
        '/Xビデオ/AiDiy実装_配車管理',
        'Xビデオ/AiDiy実装_配車管理_ja/index.html',
        'Xビデオ'
    ),
    createStaticAliasRoute(
        '/Xビデオ/AiDiy実装_配車管理_ja',
        'Xビデオ/AiDiy実装_配車管理_ja/index.html',
        'Xビデオ'
    ),
    createStaticAliasRoute(
        '/Xビデオ/AiDiy紹介_生産管理',
        'Xビデオ/AiDiy実装_生産管理_ja/index.html',
        'Xビデオ'
    ),
    createStaticAliasRoute(
        '/Xビデオ/AiDiy実装_生産管理',
        'Xビデオ/AiDiy実装_生産管理_ja/index.html',
        'Xビデオ'
    ),
    createStaticAliasRoute(
        '/Xビデオ/AiDiy実装_生産管理_ja',
        'Xビデオ/AiDiy実装_生産管理_ja/index.html',
        'Xビデオ'
    ),
    createStaticAliasRoute(
        '/Xビデオ/AiDiy紹介_在庫管理',
        'Xビデオ/AiDiy実装_在庫管理_ja/index.html',
        'Xビデオ'
    ),
    createStaticAliasRoute(
        '/Xビデオ/AiDiy実装_在庫管理',
        'Xビデオ/AiDiy実装_在庫管理_ja/index.html',
        'Xビデオ'
    ),
    createStaticAliasRoute(
        '/Xビデオ/AiDiy実装_在庫管理_ja',
        'Xビデオ/AiDiy実装_在庫管理_ja/index.html',
        'Xビデオ'
    ),
    createStaticAliasRoute(
        '/Xビデオ/AiDiy紹介_webAiDiy',
        'Xビデオ/AiDiy実装_web_ja/index.html',
        'Xビデオ'
    ),
    createStaticAliasRoute(
        '/Xビデオ/AiDiy紹介_avatarAiDiy',
        'Xビデオ/AiDiy実装_avatar_ja/index.html',
        'Xビデオ'
    ),
    createStaticAliasRoute(
        '/Xビデオ/AiDiy実装_web版',
        'Xビデオ/AiDiy実装_web_ja/index.html',
        'Xビデオ'
    ),
    createStaticAliasRoute(
        '/Xビデオ/AiDiy実装_web_ja',
        'Xビデオ/AiDiy実装_web_ja/index.html',
        'Xビデオ'
    ),
    createStaticAliasRoute(
        '/Xビデオ/AiDiy実装_avatar版',
        'Xビデオ/AiDiy実装_avatar_ja/index.html',
        'Xビデオ'
    ),
    createStaticAliasRoute(
        '/Xビデオ/AiDiy実装_avatar_ja',
        'Xビデオ/AiDiy実装_avatar_ja/index.html',
        'Xビデオ'
    ),
    createStaticAliasRoute(
        '/Xビデオ/ニュース_20260521_anthropic2026前半',
        'Xビデオ/ニュース_20260521_anthropic2026前半_ja/index.html',
        'Xビデオ'
    ),
    createStaticAliasRoute(
        '/Xビデオ/ニュース_20260521_anthropic2026前半_ja',
        'Xビデオ/ニュース_20260521_anthropic2026前半_ja/index.html',
        'Xビデオ'
    ),
    createStaticAliasRoute(
        '/Xビデオ/ニュース_20260521_google2026前半',
        'Xビデオ/ニュース_20260521_google2026前半_ja/index.html',
        'Xビデオ'
    ),
    createStaticAliasRoute(
        '/Xビデオ/ニュース_20260521_google2026前半_ja',
        'Xビデオ/ニュース_20260521_google2026前半_ja/index.html',
        'Xビデオ'
    ),
    createStaticAliasRoute(
        '/Xビデオ/ニュース_20260521_openai2026前半',
        'Xビデオ/ニュース_20260521_openai2026前半_ja/index.html',
        'Xビデオ'
    ),
    createStaticAliasRoute(
        '/Xビデオ/ニュース_20260521_openai2026前半_ja',
        'Xビデオ/ニュース_20260521_openai2026前半_ja/index.html',
        'Xビデオ'
    ),
    createStaticAliasRoute(
        '/Xビデオ/活用事例_video_generation解説',
        'Xビデオ/解説_ビデオページ生成_ja/index.html',
        'Xビデオ'
    ),
    createStaticAliasRoute(
        '/Xビデオ/活用事例_ビデオページ生成解説_ja',
        'Xビデオ/解説_ビデオページ生成_ja/index.html',
        'Xビデオ'
    ),
    createStaticAliasRoute(
        '/Xビデオ/解説_ビデオページ生成_ja',
        'Xビデオ/解説_ビデオページ生成_ja/index.html',
        'Xビデオ'
    ),
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
