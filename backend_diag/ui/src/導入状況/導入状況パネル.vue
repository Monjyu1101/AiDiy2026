<script setup>
import { watch, nextTick } from 'vue';
import 状態バッジ from '../共通表示/状態バッジ.vue';
import { 導入状況表示を作成 } from './導入状況表示.mjs';
import './導入状況.css';

const props = defineProps(['項目', '結果', '確認中', '接続済み', '確認済み', '書込中', '書込済み', '表示中']);
defineEmits(['確認', '書込']);
const { 選択ID, 折り畳み, 分類, 状態, 選択項目, 詳細項目, 参照箇所, 開閉 } = 導入状況表示を作成(props);
// 演出中は左の一覧を結果が出た項目へ追従スクロールし、右の詳細は先頭から表示する。
watch(()=>props.表示中,async id=>{if(!id)return;await nextTick();document.querySelector('#list .item.selected')?.scrollIntoView({block:'center'});const detail=document.querySelector('#detail');if(detail)detail.scrollTop=0;});
</script>
<template>
<section class="panel" aria-label="導入状況"><div class="panel-heading"><h2>導入状況</h2><div class="panel-actions"><button id="install-run" :disabled="!接続済み || 確認中 || 書込中" @click="$emit('確認')">{{確認中?'確認中…':'状況確認'}}</button><button id="install-write" :disabled="!接続済み || !確認済み || 確認中 || 書込中" title="直前の確認結果を _AIDIY/aidiy_diag/install_info.json に保存します" @click="$emit('書込')">{{書込中?'書込中…':書込済み?'書込済':'書込'}}</button></div></div>

<main><aside aria-label="診断項目"><nav id="list"><details open><summary>導入状況</summary><template v-for="group in 分類" :key="group"><details :open="!折り畳み.has(group)" @toggle="開閉(group,$event)"><summary>{{group}} · {{項目.filter(e=>(e.menuGroup || 'その他拡張')===group).length}}</summary><button v-for="item in 項目.filter(e=>(e.menuGroup || 'その他拡張')===group)" :key="item.id" class="item" :class="{selected:選択ID===item.id}" :aria-pressed="選択ID===item.id" @click="選択ID=item.id"><span>{{item.name}}</span><component :is="状態バッジ" :state="状態(item.id)"/></button></details></template></details></nav></aside>
<article id="detail" aria-live="polite"><template v-if="選択項目"><span class="eyebrow">導入状況 / {{選択項目.menuGroup || 'その他拡張'}}</span><h2>{{選択項目.name}}</h2><component :is="状態バッジ" class="status" :state="状態(選択項目.id)"/><p>{{選択項目.description}}</p><dl><template v-for="[label,value] in 詳細項目" :key="label"><dt>{{label}}</dt><dd>{{value}}</dd></template></dl><h3>ソースの参照箇所</h3><ul><li v-for="source in 参照箇所" :key="source">{{source}}</li></ul></template><div v-else class="welcome"><span class="eyebrow">READ-ONLY DIAGNOSTICS</span><h2>導入状況</h2><p>ベース・CLI群・その他拡張からプログラムを選ぶと、利用用途と検出結果を表示します。</p><p>「状況確認」でパスとバージョンを確認します。インストール、ログイン、AI への問い合わせは行いません。</p></div></article></main></section>
</template>
