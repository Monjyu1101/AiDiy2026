<!-- COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
Licensed under "AiDiy 公開利用ライセンス v1.1".
Commercial use requires prior written consent from all copyright holders.
See LICENSE for full terms. Thank you for keeping the rules.
https://github.com/monjyu1101/AiDiy2026 -->
<script setup>
import {ref,onMounted,onBeforeUnmount} from 'vue';
import StatusBar from '../共通表示/状態バー.vue';
const page=ref({url:'',title:'',loading:false,back:false,forward:false,error:''}),address=ref(''),surface=ref(),error=ref('');
let stop=()=>{},observer,disposed=false,editing=false;
function update(value){if(disposed||!value)return;page.value=value;if(!editing)address.value=value.url||'';}
async function action(name,value){
 const result=await window.aidiyWindow.browserAction(name,value).catch(e=>({ok:false,error:e.message}));
 if(disposed)return;if(!result?.ok){error.value=result?.error||'ブラウザを操作できません。';return;}
 error.value='';update(result);
}
function navigate(){editing=false;void action('navigate',address.value);}
function resize(){const rect=surface.value?.getBoundingClientRect();if(rect)void window.aidiyWindow.browserAction('bounds',{left:rect.left,top:rect.top,width:rect.width,height:rect.height}).catch(()=>{});}
onMounted(()=>{
 stop=window.aidiyWindow.onBrowserChanged(update);void action('state');
 observer=new ResizeObserver(resize);observer.observe(surface.value);resize();
});
onBeforeUnmount(()=>{disposed=true;stop();observer?.disconnect();});
</script>
<template>
 <main class="development-app browser-panel desktop-window" data-app="browser">
  <StatusBar title="AiDiy IDE / Browser" :connected="page.available===true" :status="page.available===false?'tools未接続':page.loading?'読み込み中':'ブラウザ'" desktop :clock-pulse="false" />
  <form class="browser-toolbar" @submit.prevent="navigate">
   <button type="button" aria-label="戻る" title="戻る" :disabled="!page.available||!page.back" @click="action('back')">←</button>
   <button type="button" aria-label="進む" title="進む" :disabled="!page.available||!page.forward" @click="action('forward')">→</button>
   <button type="button" :disabled="!page.available" :aria-label="page.loading?'読み込みを停止':'再読み込み'" :title="page.loading?'読み込みを停止':'再読み込み'" @click="action(page.loading?'stop':'reload')">{{ page.loading?'×':'⟳' }}</button>
   <button type="button" :disabled="!page.available" title="Google検索" aria-label="Google検索" @click="action('home')">⌂</button>
   <input v-model="address" :disabled="!page.available" aria-label="URLまたは検索語" placeholder="URLまたはGoogleで検索" spellcheck="false" @focus="editing=true" @blur="editing=false">
   <button type="submit" :disabled="!page.available">開く</button>
  </form>
  <p class="browser-page-title" :title="page.title">{{ page.loading?'読み込み中…':page.title||'Browser' }}<span v-if="page.session"> · session={{ page.session }}</span></p>
  <p v-if="error||page.error" class="error browser-error" role="status">{{ error||page.error }}</p>
  <div ref="surface" class="browser-surface"></div>
 </main>
</template>
<style scoped>
.browser-panel{height:100vh;display:flex;flex-direction:column;background:#080c1a;color:#dce6f4}
.browser-toolbar{display:flex;align-items:center;gap:5px;padding:7px 9px;border-bottom:1px solid #2c4055;flex:none}
.browser-toolbar button{padding:5px 9px;flex:none}.browser-toolbar input{flex:1;min-width:60px;background:#080f1b;color:#e2ecf8;border:1px solid #375067;border-radius:3px;padding:6px 9px;font:inherit}
.browser-page-title{margin:0;padding:3px 10px;font-size:11px;color:#9eb4c8;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;flex:none}
.browser-error{margin:0;padding:6px 10px;flex:none}.browser-surface{flex:1;min-height:0}
</style>
