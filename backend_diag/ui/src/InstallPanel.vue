<script setup>
import { ref, computed } from 'vue';
import StatusBadge from './StatusBadge.vue';
const props=defineProps(['entries','results','busy','connected']);defineEmits(['run']);
const selected=ref(null),collapsed=ref(new Set(['その他拡張']));
const groups=['ベース','CLI群','その他拡張'];
const state=id=>props.results.find(r=>r.id===id)?.状態 || '未確認';
const entry=computed(()=>props.entries.find(e=>e.id===selected.value));
const result=computed(()=>props.results.find(r=>r.id===selected.value));
const fields=computed(()=>{const e=entry.value,r=result.value;if(!e)return [];return [['利用区分',({base:'実行・依存管理のベース',cli:'選択した LLM CLI 連携',integration:'本体から利用する機能別の拡張'})[e.usageTier]],['機能カテゴリ',e.category],['必要性',e.diagnosticsRequired?'診断アプリの起動に必須':e.wholeSystemRequired?'Python バックエンド利用時の基盤':'該当機能を選択して使用する場合に確認'],['必要バージョン',e.minimumVersion?`${e.minimumVersion} 以降（ソースの要件）`:''],['検出パス',r?.パス || '—'],['バージョン',r?.バージョン || '—'],['確認結果',r?.説明 || 'まだ確認していません。'],['確認日時',r?.確認日時?new Date(r.確認日時).toLocaleString():'—'],['検出コマンド',e.commands.join(' / ')],['利用機能',(e.required_by || []).join('、')],['注意事項',e.notes]].filter(([,v])=>v);});
const references=computed(()=>entry.value?.evidence?.length?[...new Set(entry.value.evidence.map(e=>`${e.path}:${e.line}`))]:entry.value?.sources || []);
function toggle(group,event){const next=new Set(collapsed.value);event.target.open?next.delete(group):next.add(group);collapsed.value=next;}
</script>
<template>
<section class="panel" aria-label="インストール状況"><div class="panel-heading"><h2>現在のインストール状況</h2><button id="install-run" :disabled="!connected || busy" @click="$emit('run')">{{busy?'確認中…':'インストール確認'}}</button></div>

<main><aside aria-label="診断項目"><nav id="list"><details open><summary>インストール確認</summary><template v-for="group in groups" :key="group"><details :open="!collapsed.has(group)" @toggle="toggle(group,$event)"><summary>{{group}} · {{entries.filter(e=>(e.menuGroup || 'その他拡張')===group).length}}</summary><button v-for="item in entries.filter(e=>(e.menuGroup || 'その他拡張')===group)" :key="item.id" class="item" :class="{selected:selected===item.id}" :aria-pressed="selected===item.id" @click="selected=item.id"><span>{{item.name}}</span><StatusBadge :state="state(item.id)"/></button></details></template></details></nav></aside>
<article id="detail" aria-live="polite"><template v-if="entry"><span class="eyebrow">インストール確認 / {{entry.menuGroup || 'その他拡張'}}</span><h2>{{entry.name}}</h2><StatusBadge class="status" :state="state(entry.id)"/><p>{{entry.description}}</p><dl><template v-for="[label,value] in fields" :key="label"><dt>{{label}}</dt><dd>{{value}}</dd></template></dl><h3>ソースの参照箇所</h3><ul><li v-for="source in references" :key="source">{{source}}</li></ul></template><div v-else class="welcome"><span class="eyebrow">READ-ONLY DIAGNOSTICS</span><h2>インストール確認</h2><p>ベース・CLI群・その他拡張からプログラムを選ぶと、利用用途と検出結果を表示します。</p><p>「インストール確認」でパスとバージョンを確認します。インストール、ログイン、AI への問い合わせは行いません。</p></div></article></main></section>
</template>
