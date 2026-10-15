<script setup>
import StatusBadge from '../StatusBadge.vue';
import { インストール表示を作成 } from './インストール表示.mjs';
import './インストール.css';

const props = defineProps(['項目', '結果', '確認中', '接続済み']);
defineEmits(['確認']);
const { 選択ID, 折り畳み, 分類, 状態, 選択項目, 詳細項目, 参照箇所, 開閉 } = インストール表示を作成(props);
</script>
<template>
<section class="panel" aria-label="インストール状況"><div class="panel-heading"><h2>現在のインストール状況</h2><button id="install-run" :disabled="!接続済み || 確認中" @click="$emit('確認')">{{確認中?'確認中…':'インストール確認'}}</button></div>

<main><aside aria-label="診断項目"><nav id="list"><details open><summary>インストール確認</summary><template v-for="group in 分類" :key="group"><details :open="!折り畳み.has(group)" @toggle="開閉(group,$event)"><summary>{{group}} · {{項目.filter(e=>(e.menuGroup || 'その他拡張')===group).length}}</summary><button v-for="item in 項目.filter(e=>(e.menuGroup || 'その他拡張')===group)" :key="item.id" class="item" :class="{selected:選択ID===item.id}" :aria-pressed="選択ID===item.id" @click="選択ID=item.id"><span>{{item.name}}</span><StatusBadge :state="状態(item.id)"/></button></details></template></details></nav></aside>
<article id="detail" aria-live="polite"><template v-if="選択項目"><span class="eyebrow">インストール確認 / {{選択項目.menuGroup || 'その他拡張'}}</span><h2>{{選択項目.name}}</h2><StatusBadge class="status" :state="状態(選択項目.id)"/><p>{{選択項目.description}}</p><dl><template v-for="[label,value] in 詳細項目" :key="label"><dt>{{label}}</dt><dd>{{value}}</dd></template></dl><h3>ソースの参照箇所</h3><ul><li v-for="source in 参照箇所" :key="source">{{source}}</li></ul></template><div v-else class="welcome"><span class="eyebrow">READ-ONLY DIAGNOSTICS</span><h2>インストール確認</h2><p>ベース・CLI群・その他拡張からプログラムを選ぶと、利用用途と検出結果を表示します。</p><p>「インストール確認」でパスとバージョンを確認します。インストール、ログイン、AI への問い合わせは行いません。</p></div></article></main></section>
</template>
