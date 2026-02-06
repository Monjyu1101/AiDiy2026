// -*- coding: utf-8 -*-

// ------------------------------------------------
// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
// This software is licensed under the MIT License.
// https://github.com/monjyu1101
// Thank you for keeping the rules.
// ------------------------------------------------

import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import ログイン from '../components/ログイン.vue'

const routes: RouteRecordRaw[] = [
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
        path: '/',
        name: 'dashboard',
        component: () => import('../components/C管理.vue'),
        meta: { requiresAuth: true, title: '管理' }
    },
    {
        path: '/C管理',
        name: '管理',
        component: () => import('../components/C管理.vue'),
        meta: { requiresAuth: true, title: '管理' }
    },
    {
        path: '/Mマスタ',
        name: 'マスタ',
        component: () => import('../components/Mマスタ.vue'),
        meta: { requiresAuth: true, title: 'マスタ' }
    },
    {
        path: '/Tトラン',
        name: 'トラン',
        component: () => import('../components/Tトラン.vue'),
        meta: { requiresAuth: true, title: 'トラン' }
    },
    {
        path: '/Sスケジュール',
        name: 'スケジュール',
        component: () => import('../components/Sスケジュール.vue'),
        meta: { requiresAuth: true, title: 'スケジュール' }
    },
    {
        path: '/Sスケジュール/S配車_週表示',
        name: 'S配車週表示',
        component: () => import('../components/Sスケジューラー/S配車_週表示.vue'),
        meta: { requiresAuth: true, title: 'S配車_週表示' }
    },
    {
        path: '/Sスケジュール/S配車_日表示',
        name: 'S配車日表示',
        component: () => import('../components/Sスケジューラー/S配車_日表示.vue'),
        meta: { requiresAuth: true, title: 'S配車_日表示' }
    },
    {
        path: '/Vビュー',
        name: 'ビュー',
        component: () => import('../components/Vビュー.vue'),
        meta: { requiresAuth: true, title: 'ビュー' }
    },
    {
        path: '/Vビュー/V商品推移表',
        name: 'V商品推移表',
        component: () => import('../components/Vビュー/V商品推移表.vue'),
        meta: { requiresAuth: true, title: '商品推移表' }
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
        path: '/AIコア',
        name: 'AIコア',
        component: () => import('../components/AIコア/AIコア.vue'),
        meta: { requiresAuth: true, title: 'AIコア' }
    },
    {
        path: '/C管理/C権限/一覧',
        name: 'C権限一覧',
        component: () => import('../components/C管理/C権限/C権限一覧.vue'),
        meta: { requiresAuth: true, title: 'C権限一覧' }
    },
    {
        path: '/C管理/C権限/編集',
        name: 'C権限編集',
        component: () => import('../components/C管理/C権限/C権限編集.vue'),
        meta: { requiresAuth: true, title: 'C権限編集' }
    },
    {
        path: '/C管理/C利用者/一覧',
        name: 'C利用者一覧',
        component: () => import('../components/C管理/C利用者/C利用者一覧.vue'),
        meta: { requiresAuth: true, title: 'C利用者一覧' }
    },
    {
        path: '/C管理/C利用者/編集',
        name: 'C利用者編集',
        component: () => import('../components/C管理/C利用者/C利用者編集.vue'),
        meta: { requiresAuth: true, title: 'C利用者編集' }
    },
    {
        path: '/C管理/C採番/一覧',
        name: 'C採番一覧',
        component: () => import('../components/C管理/C採番/C採番一覧.vue'),
        meta: { requiresAuth: true, title: 'C採番一覧' }
    },
    {
        path: '/C管理/C採番/編集',
        name: 'C採番編集',
        component: () => import('../components/C管理/C採番/C採番編集.vue'),
        meta: { requiresAuth: true, title: 'C採番編集' }
    },
    {
        path: '/Mマスタ/M配車区分/一覧',
        name: 'M配車区分一覧',
        component: () => import('../components/Mマスタ/M配車区分/M配車区分一覧.vue'),
        meta: { requiresAuth: true, title: 'M配車区分一覧' }
    },
    {
        path: '/Mマスタ/M配車区分/編集',
        name: 'M配車区分編集',
        component: () => import('../components/Mマスタ/M配車区分/M配車区分編集.vue'),
        meta: { requiresAuth: true, title: 'M配車区分編集' }
    },
    {
        path: '/Mマスタ/M車両/一覧',
        name: 'M車両一覧',
        component: () => import('../components/Mマスタ/M車両/M車両一覧.vue'),
        meta: { requiresAuth: true, title: 'M車両一覧' }
    },
    {
        path: '/Mマスタ/M車両/編集',
        name: 'M車両編集',
        component: () => import('../components/Mマスタ/M車両/M車両編集.vue'),
        meta: { requiresAuth: true, title: 'M車両編集' }
    },
    {
        path: '/Mマスタ/M商品/一覧',
        name: 'M商品一覧',
        component: () => import('../components/Mマスタ/M商品/M商品一覧.vue'),
        meta: { requiresAuth: true, title: 'M商品一覧' }
    },
    {
        path: '/Mマスタ/M商品/編集',
        name: 'M商品編集',
        component: () => import('../components/Mマスタ/M商品/M商品編集.vue'),
        meta: { requiresAuth: true, title: 'M商品編集' }
    },
    {
        path: '/Tトラン/T配車/一覧',
        name: 'T配車一覧',
        component: () => import('../components/Tトラン/T配車/T配車一覧.vue'),
        meta: { requiresAuth: true, title: 'T配車一覧' }
    },
    {
        path: '/Tトラン/T配車/編集',
        name: 'T配車編集',
        component: () => import('../components/Tトラン/T配車/T配車編集.vue'),
        meta: { requiresAuth: true, title: 'T配車編集' }
    },
    {
        path: '/Tトラン/T商品入庫/一覧',
        name: 'T商品入庫一覧',
        component: () => import('../components/Tトラン/T商品入庫/T商品入庫一覧.vue'),
        meta: { requiresAuth: true, title: 'T商品入庫一覧' }
    },
    {
        path: '/Tトラン/T商品入庫/編集',
        name: 'T商品入庫編集',
        component: () => import('../components/Tトラン/T商品入庫/T商品入庫編集.vue'),
        meta: { requiresAuth: true, title: 'T商品入庫編集' }
    },
    {
        path: '/Tトラン/T商品出庫/一覧',
        name: 'T商品出庫一覧',
        component: () => import('../components/Tトラン/T商品出庫/T商品出庫一覧.vue'),
        meta: { requiresAuth: true, title: 'T商品出庫一覧' }
    },
    {
        path: '/Tトラン/T商品出庫/編集',
        name: 'T商品出庫編集',
        component: () => import('../components/Tトラン/T商品出庫/T商品出庫編集.vue'),
        meta: { requiresAuth: true, title: 'T商品出庫編集' }
    },
    {
        path: '/Tトラン/T商品棚卸/一覧',
        name: 'T商品棚卸一覧',
        component: () => import('../components/Tトラン/T商品棚卸/T商品棚卸一覧.vue'),
        meta: { requiresAuth: true, title: 'T商品棚卸一覧' }
    },
    {
        path: '/Tトラン/T商品棚卸/編集',
        name: 'T商品棚卸編集',
        component: () => import('../components/Tトラン/T商品棚卸/T商品棚卸編集.vue'),
        meta: { requiresAuth: true, title: 'T商品棚卸編集' }
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
    }
]

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes
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

