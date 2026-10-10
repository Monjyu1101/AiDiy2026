// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
import { createApp } from 'vue';
import App from './App.vue';
import './style.css';
import './chat-presentation.css';
async function main(){
  const embedded=document.getElementById('development-config');
  const config=embedded?JSON.parse(embedded.textContent):await fetch('/development/config').then(r=>{if(!r.ok)throw Error('起動設定を取得できません。');return r.json();});
  document.title = `AiDiy ${config.linked ? 'IDE / ' : ''}${{code:'Code',live:'Live',ide:'IDE'}[config.kind]}`;
  createApp(App,{config}).mount('#app');
}
void main().catch(error=>{document.getElementById('app').textContent=error.message;});
