<!-- COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
Licensed under "AiDiy 公開利用ライセンス v1.1". See LICENSE. -->
<script setup>
import {ref,computed,watch,onUnmounted} from 'vue';
import {Tools状態を作成} from './Tools状態.mjs';
import {Tools代表テスト} from './Tools代表テスト.mjs';
import './Tools.css';
const props=defineProps({api:Function,connected:Boolean,coreOnline:Boolean,toolsOnline:Boolean,visible:Boolean});
const ready=()=>props.connected&&props.coreOnline&&props.toolsOnline;
const state=Tools状態を作成({api:(...args)=>props.api(...args),利用可能:ready,代表テスト:Tools代表テスト});
const userId=ref(''),password=ref('');
const current=computed(()=>state.選択.value),fields=computed(()=>state.schema.value[current.value?.defaultsKey]||{});
const test=computed(()=>state.テスト定義(current.value?.id));
watch(()=>current.value?.id,id=>{const def=state.テスト定義(id);if(def&&!state.テスト条件.value[id])state.テスト条件.value[id]={...def.defaults};},{immediate:true});
async function login(){const secret=password.value;password.value='';await state.ログイン(userId.value,secret);}
watch(ready,value=>{if(!value){password.value='';state.切断();}},{flush:'sync'});
watch(()=>props.visible,value=>{if(!value)state.テスト中止();},{flush:'sync'});
onUnmounted(()=>{password.value='';state.終了();});
</script>
<template>
<section class="tools-panel panel" aria-label="Tools管理">
 <header class="tools-heading"><h2>Tools</h2><button v-if="state.認証済み.value" @click="state.ログアウト()">Coreからログアウト</button></header>
 <p class="tools-note">Coreの利用者IDでログインしてください。OFFでも登録は維持し「サービス外」として応答します。既定値の変更は次の実行から反映されます。状態欄は利用可否であり、機能テスト成功を意味しません。</p>
 <p v-if="!connected" role="status">先にDiagへ接続してください。</p>
 <p v-else-if="!coreOnline||!toolsOnline" role="status">システム起動で Core と Tools を起動してください。</p>
 <form v-else-if="!state.認証済み.value" class="tools-login" @submit.prevent="login">
  <label>利用者ID<input v-model="userId" autocomplete="username" :disabled="!!state.処理中.value" required></label>
  <label>パスワード<input v-model="password" type="password" autocomplete="off" :disabled="!!state.処理中.value" required></label>
  <button :disabled="!!state.処理中.value">{{state.処理中.value?'接続中…':'Coreへログイン'}}</button>
 </form>
 <p v-if="state.通知.value" class="tools-notice" role="status" aria-live="polite">{{state.通知.value}}</p>
 <div v-if="state.認証済み.value&&connected&&coreOnline&&toolsOnline" class="tools-columns">
  <section class="tools-list" aria-label="Tools一覧">
   <div class="tools-actions"><button :disabled="!!state.処理中.value" @click="state.再読込()">再読込</button><button :disabled="!!state.処理中.value||!Object.keys(state.有効変更.value).length" @click="state.有効保存()">オン・オフを保存</button></div>
   <p v-if="Object.keys(state.有効変更.value).length" class="tools-unsaved">オン・オフ：未保存の適用があります</p>
   <ul><li v-for="row in state.項目.value" :key="row.id" :class="{selected:row.id===state.選択ID.value}">
    <button class="tools-name" :aria-pressed="row.id===state.選択ID.value" @click="state.選択ID.value=row.id">{{row.label||row.id}}</button>
    <button class="tools-switch" :aria-pressed="row.enabled" :aria-label="`${row.label||row.id} ${row.enabled?'OFFにする':'ONにする'}`" :disabled="!!state.処理中.value||!row.available" @click="state.切替(row.id)">{{row.enabled?'ON':'OFF'}}</button>
    <button :disabled="!!state.処理中.value||!row.available||!row.enabled||!state.テスト定義(row.id)" :title="state.テスト定義(row.id)?.label||'代表機能テストは未対応です'" @click="state.テスト(row.id)">テスト</button>
    <span class="tools-status">{{!row.available?'サービス外（利用不可）':!row.enabled?'サービス外':row.status}}</span>
    <span v-if="state.結果.value[row.id]" class="tools-result" :title="state.結果.value[row.id].message">{{state.結果.value[row.id].status}}</span>
   </li></ul>
  </section>
  <section class="tools-detail" aria-label="既定値とテスト条件">
   <template v-if="current">
    <h3>{{current.label||current.id}}</h3><p class="tools-id">{{current.id}}</p>
    <h4>既定値</h4>
    <form v-if="Object.keys(fields).length" @submit.prevent="state.規定値設定(true)">
     <label v-for="(choices,name) in fields" :key="name">{{name}}<select v-model="state.編集値.value[current.defaultsKey][name]" :disabled="!!state.処理中.value||!current.available"><option v-for="choice in choices" :key="choice" :value="choice">{{choice}}</option></select></label>
     <div class="tools-actions"><button type="button" :disabled="!!state.処理中.value||!current.available" @click="state.規定値設定(false)">適用のみ</button><button :disabled="!!state.処理中.value||!current.available">既定値を保存</button></div>
     <p v-if="state.未保存規定値.value[current.defaultsKey]" class="tools-unsaved">実行時へ適用済み・ファイル未保存</p>
    </form>
    <p v-else>このToolには変更できる既定値はありません。</p>
    <h4>代表機能のテスト</h4>
    <p v-if="!current.available">この環境では利用できません。</p><p v-else-if="!current.enabled">OFF（サービス外）のため実行しません。専用ブラウザを終了する場合は、先にこのToolをONへ戻してください。</p>
    <template v-if="test"><p>{{test.label}}</p><p>{{test.description}}</p><label class="tools-test-option"><input v-model="state.テスト条件.value[current.id].headless" type="checkbox" :disabled="!!state.処理中.value||!current.available||!current.enabled">画面を表示しない（headless）</label><button :disabled="!!state.処理中.value||!current.available||!current.enabled" @click="state.テスト(current.id)">この条件でテスト</button><button v-if="test.close" :disabled="!!state.処理中.value||!current.available||!current.enabled" @click="state.テスト(current.id,true)">専用ブラウザを終了</button></template>
    <p v-else>このToolの代表機能テストは未対応です。状態の表示は機能テスト成功を意味しません。</p>
    <button v-if="state.処理中.value==='test'" @click="state.テスト中止()">待機を中止</button>
    <pre v-if="state.結果.value[current.id]" class="tools-test-output" aria-live="polite">{{state.結果.value[current.id].message}}</pre>
   </template><p v-else>Toolを選択してください。</p>
  </section>
 </div>
</section>
</template>
