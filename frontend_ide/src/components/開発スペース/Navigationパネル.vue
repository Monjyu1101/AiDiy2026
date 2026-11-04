<!-- COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
Licensed under "AiDiy 公開利用ライセンス v1.1".
Commercial use requires prior written consent from all copyright holders.
See LICENSE for full terms. Thank you for keeping the rules.
https://github.com/monjyu1101/AiDiy2026 -->
<script setup>
import {ref,computed,nextTick,onBeforeUnmount,watch,onMounted} from 'vue';
import {DEFAULT_NAVIGATION_GOAL} from './Navigation既定値.js';
import StatusBar from '../共通表示/状態バー.vue';
import TerminalWelcome from '../ターミナル/開始表示.vue';
import ModalDialog from '../../dialog/共通ダイアログ.vue';
import {createPanelWindow} from '../ファイル閲覧/パネル別窓.js';
const props=defineProps({standalone:Boolean,startedAt:Number,allDisplays:Boolean,project:Object,instance:{type:String,required:true}});
const emit=defineEmits(['closed']);
const title=computed(()=>props.standalone?'AiDiy Navigator':'AiDiy IDE / Navigator '+props.instance.slice(5));
const native=!!window.aidiyWindow;
const visible=ref(false),detached=ref(false),panel=ref(),goal=ref(DEFAULT_NAVIGATION_GOAL),result=ref(null),job=ref(null),error=ref(''),submitting=ref(false),copied=ref(false);
const selection=ref({provider:'aidiy_hermes',model:'same'}),modelOpen=ref(false),chosenProvider=ref('aidiy_hermes'),chosenModel=ref('same'),savingModel=ref(false),modelChoice=ref('same');
const modelItems=ref([]),catalogBusy=ref(false),catalogNotice=ref('');let catalogVersion=0;
const toolsState=ref({connected:false,mode:'online'});
const availability=ref({available:false,reason:'実行環境を確認しています…'});
const history=ref(false),historyItems=ref([]);
const scored=value=>Number.isInteger(value)&&value>=0&&value<=100;
const progressStyle=value=>scored(value)?{'--progress-width':value+'%','--progress-fill':`hsl(${value*1.2} 65% 23%)`,'--progress-accent':`hsl(${value*1.2} 65% 72%)`}: {'--progress-width':'0%','--progress-fill':'#263445','--progress-accent':'#b3c5d8'};
// APIの旧版・不正応答を数値のない成功表示へ流さない。保存済み結果を画面で補完しない。
function verifiedResult(value){
 if(value===null)return null;
 if(value?.schemaVersion!==3||!scored(value.overall?.progress)||!Array.isArray(value.items)||value.items.some(item=>!scored(item?.progress)))throw Error('Navigator結果の形式または数値評価を確認できません。最新版へ更新し、「＋ 新規」からナビを再作成してください。');
 const next=value.items.find(item=>item.progress<100);
 if(value.nextItemId!==(next?.id??null)||(next?typeof value.nextPrompt!=='string'||!value.nextPrompt.trim():value.nextPrompt!==''))throw Error('おすすめプロンプトの対象が一致しません。「＋ 新規」からナビを再作成してください。');
 return value;
}
// 総合値・理由はAIの検証済み回答をそのまま表示する。旧形式を補完しない。
const overall=computed(()=>result.value?.overall);
const nextItem=computed(()=>result.value?.items.find(item=>item.progress<100));
const recommendedPrompt=computed(()=>result.value&&nextItem.value?result.value.nextPrompt:'');
const matchesResult=computed(()=>!!result.value&&goal.value.trim()===result.value.goal);
const canEvaluate=computed(()=>!busy.value&&availability.value.available&&matchesResult.value);
let draftInitialized=false,draftEdited=false,pendingGoal=null;
function editGoal(){draftEdited=true;}
// 応答を失った開始要求はGETで状態を確認するまで再送しない。
const reconciling=ref(false);
const busy=computed(()=>savingModel.value||submitting.value||reconciling.value||job.value?.status==='running');
let windowPanel,timer,disposed=false,version=0,request;

async function api(method='GET',body){
 const response=await fetch('/api/navigation?instance='+encodeURIComponent(props.instance),{method,cache:'no-store',headers:body?{'content-type':'application/json'}:undefined,body:body?JSON.stringify(body):undefined,signal:AbortSignal.any([...(request?[request.signal]:[]),AbortSignal.timeout(15000)])});
 const data=await response.json();if(!response.ok)throw Error(data.error||'Navigatorを取得できません。');return data;
}
async function refresh(){
 const generation=version;
 try{if(props.standalone){try{const r=await fetch('/api/connection',{signal:AbortSignal.timeout(3000)});if(r.ok)toolsState.value=await r.json();else toolsState.value.connected=false;}catch{toolsState.value.connected=false;}}const data=await api();if(disposed||generation!==version)return;job.value=data.job;reconciling.value=false;result.value=verifiedResult(data.result);availability.value=data.availability||{available:true,reason:""};selection.value=data.selection||selection.value;if(!draftInitialized){draftInitialized=true;if(!draftEdited&&data.result)goal.value=data.result.goal;}if(pendingGoal&&data.job?.id===pendingGoal.id&&data.job.status!=='running'){if(data.job.status==='complete'&&goal.value===pendingGoal.text&&!draftEdited)goal.value=data.result.goal;pendingGoal=null;}}
 catch(e){if(!disposed&&generation===version&&e.name!=='AbortError')error.value=e.message;}
 finally{if(!disposed&&generation===version&&visible.value){clearTimeout(timer);timer=setTimeout(refresh,job.value?.status==='running'?2000:5000);}}
}
async function open(){
 visible.value=true;request=new AbortController();void refresh();await nextTick();if(!props.standalone)await pin();
}
onMounted(open);
async function pin(){
 await nextTick();
 windowPanel??=createPanelWindow({element:()=>panel.value,title:'Navigator '+props.instance.slice(5),kind:'panel-navigation',className:'navigation-window',changed:value=>detached.value=value,closed:()=>{visible.value=false;clearTimeout(timer);emit('closed');},report:message=>error.value=message});
 return windowPanel.pin();
}
function close(){if(detached.value)windowPanel.dismiss();else{visible.value=false;emit('closed');}clearTimeout(timer);}
async function navigate(action='navigate'){
 if(busy.value||!availability.value.available||(action==='evaluate'&&!canEvaluate.value))return;
 if(!goal.value.trim()){error.value='開発目標を入力してください。';return;}
 const submittedGoal=goal.value;draftEdited=false;submitting.value=true;error.value='';copied.value=false;const generation=++version;clearTimeout(timer);
 try{const data=await api('POST',{goal:submittedGoal,action});if(generation===version){job.value=data.job;pendingGoal={id:data.job.id,text:submittedGoal};}}
 catch(e){if(generation===version){error.value=e.message;reconciling.value=true;}}
 finally{if(generation===version){submitting.value=false;void refresh();}}
}
async function toggleHistory(){if(busy.value)return;history.value=!history.value;if(history.value)try{const r=await fetch('/api/navigation?instance='+encodeURIComponent(props.instance)+'&list=1',{cache:'no-store'});const data=await r.json();if(!r.ok)throw Error(data.error);historyItems.value=data.items;}catch(e){error.value=e.message;}}
async function selectHistory(id){if(busy.value)return;submitting.value=true;try{const data=await api('POST',{action:id?'select':'new',id});result.value=verifiedResult(data.result);job.value=data.job;availability.value=data.availability||availability.value;goal.value=data.result?.goal||DEFAULT_NAVIGATION_GOAL;draftInitialized=true;draftEdited=false;pendingGoal=null;selection.value=data.selection||selection.value;history.value=false;error.value='';}catch(e){error.value=e.message;}finally{submitting.value=false;}}
async function loadModels(){const version=++catalogVersion;catalogBusy.value=true;try{const r=await fetch('/api/navigation?instance='+encodeURIComponent(props.instance)+'&catalog='+encodeURIComponent(chosenProvider.value));const data=await r.json();if(!r.ok)throw Error(data.error);if(version===catalogVersion){modelItems.value=data.items;catalogNotice.value=data.notice||'';if(modelChoice.value==='__custom__'&&data.items.some(item=>item.id===chosenModel.value))modelChoice.value=chosenModel.value;}}catch(e){if(version===catalogVersion)error.value=e.message;}finally{if(version===catalogVersion)catalogBusy.value=false;}}
watch(chosenProvider,()=>{if(modelOpen.value){modelItems.value=[];void loadModels();}});
function chooseModel(){chosenProvider.value=selection.value.provider;chosenModel.value=selection.value.model;modelChoice.value=['same','auto'].includes(selection.value.model)?selection.value.model:'__custom__';modelOpen.value=!modelOpen.value;if(modelOpen.value)void loadModels();}
async function saveModel(){if(busy.value)return;savingModel.value=true;error.value='';try{const data=await api('PUT',{provider:chosenProvider.value,model:modelChoice.value==='__custom__'?chosenModel.value:modelChoice.value});selection.value=data.selection;modelOpen.value=false;}catch(e){error.value=e.message;}finally{savingModel.value=false;}}
async function copy(){try{await panel.value.ownerDocument.defaultView.navigator.clipboard.writeText(recommendedPrompt.value);copied.value=true;}catch{error.value='コピーできません。プロンプトを選択してコピーしてください。';}}

watch(()=>props.startedAt,()=>{version++;request?.abort();close();windowPanel?.close();windowPanel=null;draftInitialized=false;draftEdited=false;pendingGoal=null;goal.value=DEFAULT_NAVIGATION_GOAL;result.value=null;job.value=null;error.value='';submitting.value=false;modelOpen.value=false;selection.value={provider:'aidiy_hermes',model:'same'};});
onBeforeUnmount(()=>{void fetch('/api/navigation?instance='+encodeURIComponent(props.instance),{method:'DELETE'}).catch(()=>{});disposed=true;version++;request?.abort();clearTimeout(timer);windowPanel?.close();});

</script>
<template>
 <section ref="panel" v-show="visible" class="navigation-panel" :class="{detached,standalone}" aria-label="Navigator">
  <StatusBar v-if="standalone" :title="title" :desktop="native" :connected="toolsState.connected" :mode="toolsState.mode" clock-pulse />
  <header class="navigation-local-header" v-else-if="!detached||!native"><span class="navigation-emblem" aria-hidden="true">◇</span><strong>{{title}}</strong><span class="navigation-header-space"></span><button v-if="!detached" aria-label="Navigatorを別窓にピン留め" title="別窓にピン留め" @click="pin">📌</button><button aria-label="Navigatorを閉じる" @click="close">×</button></header>
  <div class="component-toolbar navigation-project"><span :title="project?.path">プロジェクト: {{project?.name || project?.path}}</span><nav><small>読取専用</small><button :disabled="busy" @click="selectHistory()">＋ 新規</button><button :disabled="busy" :aria-expanded="history" @click="toggleHistory">{{history?'戻る':'一覧'}}</button></nav></div>
   <form class="navigation-goal-form" @submit.prevent="navigate()">
    <label :for="instance+'-goal'">目標</label>
    <textarea :id="instance+'-goal'" v-model="goal" maxlength="4000" rows="3" @input="editGoal" placeholder="目標を入力してください"></textarea>
    <div class="navigation-form-foot"><small>設定済みAIへ読取専用で調査を依頼します。ファイルは変更しません。</small><button type="submit" class="navigation-start" :disabled="busy||!availability.available">{{busy?'確認中…':'ナビ'}}</button><button type="button" class="navigation-evaluate" :disabled="!canEvaluate" title="保存済みの作業項目を変えずに採点" @click="navigate('evaluate')">評価</button></div>
    <p v-if="result&&!matchesResult" class="navigation-draft-note" role="status">入力が保存済みの目標と異なります。ナビを作成すると評価できます。</p>
   </form>
  <div v-if="history" class="navigation-history" role="list"><p v-if="!historyItems.length">このフォルダにナビ履歴はありません</p><button v-for="item in historyItems" :key="item.id" :disabled="busy" @click="selectHistory(item.id)"><time>{{new Date(item.updatedAt).toLocaleString()}}</time><span>{{item.goal}}</span></button></div>
  <div v-show="!history" class="navigation-display" :class="{running:submitting||job?.status==='running'}"><div class="navigation-content">
   <p v-if="!availability.available" role="status" class="navigation-unavailable">{{availability.reason}}</p>
   <p v-if="error" role="alert" class="navigation-error">{{error}}</p>
   <p v-if="job" role="status" aria-live="polite" :aria-busy="busy" :class="{'navigation-error':job.status==='failed'}">{{job.message}}</p>
   <template v-if="result">
    <div class="navigation-result-heading"><small>{{result.inferred?'仮の開発目標（AIの推測・編集できます）':'保存済みの目標'}}</small><h2>{{result.goal}}</h2><small>達成度はAIの推定です。根拠と実際の状態を確認してください。</small></div>
    <p v-if="!result.items.length">対象の作業項目はありません。</p>
    <ol class="navigation-items" :key="result.navigationId||result.requestId"><li v-for="item in result.items" :key="item.id"><details class="navigation-disclosure">
     <summary>
     <span class="navigation-progress" :style="progressStyle(item.progress)" role="progressbar" :aria-label="item.name" :aria-valuenow="item.progress" :aria-valuetext="item.progress+'%（AIの推定）'" aria-valuemin="0" aria-valuemax="100"><span class="navigation-fill" aria-hidden="true"></span><span class="navigation-disclosure-arrow" aria-hidden="true"></span><span class="navigation-name">{{item.name}}</span><strong>{{item.progress}}<small>%</small></strong></span>
     </summary><div class="navigation-reasons"><p>{{item.reason}}</p><div class="navigation-effort"><strong>工数比率 {{item.weight}}%</strong><span>{{item.weightReason}}</span></div>
     </div></details></li></ol>

   </template>
   <TerminalWelcome v-else-if="!busy" kind="navi" icon="/development/AiDiy.png" :started="draftEdited" />
  </div>
  </div>
    <section v-if="result&&!history" class="navigation-overall" aria-label="総合評価の詳細"><details :key="result.navigationId||result.requestId" class="navigation-disclosure">
     <summary>
     <span class="navigation-progress" :style="progressStyle(overall.progress)" role="progressbar" aria-label="総合評価" :aria-valuenow="overall.progress" :aria-valuetext="overall.progress+'%（AIの工数比率による加重評価）'" aria-valuemin="0" aria-valuemax="100"><span class="navigation-fill" aria-hidden="true"></span><span class="navigation-disclosure-arrow" aria-hidden="true"></span><span class="navigation-name">総合評価</span><strong>{{overall.progress}}<small>%</small></strong></span>
     </summary><div class="navigation-reasons"><small>AIが見積もった工数比率による総合評価。実測値ではありません。</small><p class="navigation-overall-reason">{{overall.reason}}</p></div></details>
    </section>
    <section v-if="result&&!history" class="navigation-next" aria-label="おすすめプロンプト(案)"><div><h2>おすすめプロンプト(案)</h2><button v-if="nextItem" @click="copy">{{copied?'コピーしました':'コピー'}}</button></div><p class="navigation-prompt"><span v-if="nextItem">{{recommendedPrompt}}</span><span v-else>{{result.items.length?'全項目が100%です。おすすめの追加作業はありません。':'作業項目がないため、おすすめプロンプトはありません。'}}</span></p><small>プロンプト案です。自動送信・作業実行はしません。</small></section>
  <footer class="navigation-model-footer">
   <div class="navigation-model-line composer-meta"><button type="button" :disabled="busy" :aria-expanded="modelOpen" @click="chooseModel"><span class="model-caption">モデル</span> ▾</button><span class="model-label" :title="selection.provider+' / '+selection.model">{{selection.provider}} / {{selection.model}}</span></div>
  </footer>
  <ModalDialog v-if="modelOpen" label="モデル選択" :locked="savingModel" @close="modelOpen=false">
   <h3>コードAIとモデル</h3><p>Navigatorは読取専用で調査します。この窓の選択だけを保存します。</p>
   <form class="navigation-model-picker" @submit.prevent="saveModel">
    <label>コードAI<select v-model="chosenProvider" :disabled="busy"><option value="aidiy_hermes">aidiy_hermes</option><option value="codex_cli">codex_cli</option><option value="copilot_cli">copilot_cli</option></select></label>
    <label>モデル<select class="navigation-model-choice" v-model="modelChoice" :disabled="busy"><option value="same">same（前回のモデル）</option><option value="auto">auto（自動選択）</option><option v-for="item in modelItems.filter(item=>!['same','auto'].includes(item.id))" :key="item.id" :value="item.id">{{item.label}}</option><option value="__custom__">一覧にないモデル ID を入力…</option></select></label>
    <input v-if="modelChoice==='__custom__'" v-model="chosenModel" maxlength="300" autocomplete="off" spellcheck="false" aria-label="モデル名" :disabled="busy" />
    <p v-if="catalogBusy">読み込み中…</p><p v-if="catalogNotice" role="status">{{catalogNotice}}</p><p v-if="error" role="alert" class="error">{{error}}</p>
    <div><button type="submit" :disabled="busy||(modelChoice==='__custom__'&&!chosenModel.trim())">選択する</button><button type="button" :disabled="busy" @click="modelOpen=false">閉じる</button></div>
   </form>
  </ModalDialog>
 </section>
</template>
<style>
.navigation-display{position:relative;display:flex;flex:1;min-height:0;--stream:#00ffff}.navigation-history{flex:1;overflow:auto;padding:12px}.navigation-history>button{display:flex;width:100%;gap:16px;padding:12px;text-align:left}.navigation-history time{flex:none;color:#98a6b8}.navigation-project nav{display:flex;align-items:center;gap:8px;margin-left:auto;}
.navigation-panel.standalone{position:relative;inset:auto;width:100%;height:100%;max-height:none;max-width:none;border:0;border-radius:0;}
.navigation-model-footer{flex:none;padding:8px 10px;border-top:1px solid #395069;background:#101b2b}.navigation-model-line{display:flex;align-items:center;gap:8px;font-size:11px}.navigation-model-line>span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.navigation-model-picker{display:grid;gap:8px;max-height:50vh;overflow:auto}.navigation-model-picker label{display:grid;gap:4px}.navigation-model-picker select,.navigation-model-picker input{width:100%;box-sizing:border-box;font:inherit;background:#142235;color:#edf5ff;border:1px solid #47637b;padding:6px}.navigation-model-picker small{color:#b3c5d8}.navigation-model-picker>div{display:flex;gap:8px}
.navigation-panel{position:fixed;left:16px;top:var(--workspace-top,78px);bottom:auto;width:min(500px,calc(100vw - 32px));height:min(600px,calc(100vh - var(--workspace-top,78px) - 16px));box-sizing:border-box;z-index:42;display:flex;flex-direction:column;background:#0b1220;color:#e5edf8;border:1px solid #395069;border-radius:10px;box-shadow:0 12px 40px #0008;overflow:hidden;font-size:13px}
.navigation-panel .navigation-local-header{display:flex;align-items:center;gap:8px;padding:9px 12px;border-bottom:1px solid #29394f}.navigation-emblem{color:#7de2cf}.navigation-header-space{flex:1}.navigation-content{padding:14px;overflow:auto;min-height:0;flex:1}.navigation-goal-form label{display:block;font-weight:600;margin-bottom:8px}.navigation-goal-form textarea{box-sizing:border-box;width:100%;resize:vertical;min-height:48px;max-height:120px;background:#101e30;color:#edf5ff;border:1px solid #47637b;border-radius:7px;padding:10px;font:inherit}.navigation-form-foot{display:flex;gap:10px;align-items:center;margin-top:8px}.navigation-form-foot small{flex:1;color:#afc2d8;font-size:11px}.navigation-start{background:#165b64!important;color:#fff!important;padding:8px 20px!important}.navigation-content button:focus-visible,.navigation-panel .navigation-local-header button:focus-visible{outline:2px solid #8de8e0;outline-offset:2px}.navigation-content button:disabled{opacity:.55;cursor:default}.navigation-error{color:#ffb7ad}.navigation-result-heading{margin:22px 0 14px}.navigation-content h2{font-size:16px;line-height:1.5;margin:4px 0 8px}.navigation-result-heading small{color:#b3c5d8}.navigation-items{padding:0;list-style:none;margin:0}.navigation-items li{margin-bottom:8px;border:1px solid #32465d;border-radius:7px;overflow:hidden}.navigation-items .navigation-progress{border-width:0 0 0 3px;border-radius:0}.navigation-items .navigation-reasons>p{padding:0 9px;font-size:12px}.navigation-progress{position:relative;isolation:isolate;display:flex;align-items:center;gap:12px;overflow:hidden;border:1px solid #32465d;border-radius:7px;background:#142235;padding:11px}.navigation-fill{position:absolute;z-index:-1;inset:0 auto 0 0;width:var(--progress-width);background:var(--progress-fill)}.navigation-name{flex:1;overflow-wrap:anywhere}.navigation-progress strong{white-space:nowrap;color:var(--progress-accent)}.navigation-progress{border-left:3px solid var(--progress-accent);color:#f5f7fb;line-height:1.5}.navigation-name{min-width:0}.navigation-progress strong small{font-size:10px;margin-left:2px}.navigation-items .navigation-reasons>p{color:#b8cadc;line-height:1.6;margin:7px 3px;white-space:pre-wrap;overflow-wrap:anywhere}.navigation-next{margin-top:22px;padding:14px;border:1px solid #3e6b7b;border-radius:10px;background:linear-gradient(135deg,#122d3b,#172238)}.navigation-next>div{display:flex;justify-content:space-between;align-items:center;gap:8px}.navigation-next small{color:#afc5da}.navigation-prompt{white-space:pre-wrap;overflow-wrap:anywhere;line-height:1.8;user-select:text}.navigation-empty{text-align:center;padding:26px 8px;color:#b5c6db;line-height:1.7}.navigation-empty>span{font-size:36px;color:#7de2cf}
.navigation-window{height:100vh;display:flex;flex-direction:column}.navigation-window .navigation-panel{position:relative;inset:auto;width:100%;height:100%;min-height:0;flex:1;box-sizing:border-box;border-radius:0}.navigation-window.native-panel-window .navigation-panel{height:calc(100vh - 34px)}
</style>

<style>
.navigation-display{position:relative;display:flex;flex:1;min-height:0;--stream:#00ffff}.navigation-history{flex:1;overflow:auto;padding:12px}.navigation-history>button{display:flex;width:100%;gap:16px;padding:12px;text-align:left}.navigation-history time{flex:none;color:#98a6b8}.navigation-project nav{display:flex;align-items:center;gap:8px;margin-left:auto;}
.navigation-panel.standalone{position:relative;inset:auto;width:100%;height:100%;max-height:none;max-width:none;border:0;border-radius:0;}
.navigation-project{flex:none;justify-content:space-between}.navigation-project>span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.navigation-project small{flex:none;color:#a9b8cc}.navigation-panel .model-dialog{max-width:min(440px,calc(100vw - 40px));box-sizing:border-box}.navigation-model-picker{max-height:none}.navigation-model-footer{padding:8px 12px}.navigation-model-line .model-label{min-width:0}
</style>

<style>
.navigation-goal-form{flex:none;padding:10px 12px;border-bottom:1px solid #29394f;background:#0b1220}.navigation-goal-form label{margin-bottom:5px}.navigation-goal-form button:disabled{opacity:.55;cursor:default}.navigation-goal-form button:focus-visible{outline:2px solid #8de8e0;outline-offset:2px}.navigation-draft-note{font-size:11px;color:#f5cf85;margin:6px 0 0}.navigation-form-foot small{font-size:10px}.navigation-form-foot button{flex:none}.navigation-result-heading{margin:0 0 10px}.navigation-result-heading h2{font-size:14px}.navigation-content{padding:10px 12px}
</style>

<style>
.navigation-content > .terminal-welcome{box-sizing:border-box;padding:24px 0;min-height:100%}
</style>

<style>
.navigation-panel,.navigation-goal-form,.navigation-model-footer,.navigation-next{background:#000}
.navigation-goal-form textarea,.navigation-model-picker input,.navigation-model-picker select{background:#000}
.navigation-panel.standalone,.navigation-window{border:1px solid var(--aidiy-titlebar-background);box-sizing:border-box}
.navigation-window .navigation-panel{border:0}
.navigation-window .panel-window-title .panel-brand{grid-template-columns:minmax(0,1fr) auto minmax(0,1fr)}
.navigation-panel .panel-brand strong,.navigation-window .panel-brand strong{font-size:14px}
</style>

<style>
.navigation-panel .model-caption{padding:0 4px;font-size:11px;font-weight:400;line-height:calc(1.65em - 2px);background:#fff;color:#000}
.navigation-panel .composer-meta button{flex:none;padding:2px 6px;border-color:var(--border,#343943);font-size:10px;line-height:1.4}
</style>

<style>
.navigation-panel>.navigation-overall{flex:none;display:flex;flex-direction:column;min-height:0;max-height:25%;box-sizing:border-box;margin:0;padding:8px 12px;border-top:1px solid #395069;background:#000}.navigation-overall>.navigation-disclosure{min-height:0;overflow:auto}.navigation-overall .navigation-reasons>small{display:block;margin-top:4px;color:#b3c5d8;font-size:10px}
.navigation-panel>.navigation-next{flex:none;display:flex;flex-direction:column;min-height:0;max-height:30%;box-sizing:border-box;margin:0;padding:8px 12px;border:0;border-top:1px solid #3e6b7b;border-radius:0}
.navigation-panel>.navigation-next>div,.navigation-panel>.navigation-next>small{flex:none}
.navigation-panel>.navigation-next h2{font-size:13px;margin:0}
.navigation-panel>.navigation-next .navigation-prompt{min-height:0;overflow:auto;overflow-wrap:anywhere;margin:6px 0;line-height:1.5;font-size:12px}
.navigation-panel>.navigation-next>small{font-size:10px}
</style>

<style>
.navigation-overall-reason{margin:6px 0 0;color:#c5d7e6;font-size:12px;line-height:1.6;white-space:pre-wrap;overflow-wrap:anywhere}
.navigation-effort{display:grid;gap:3px;margin:7px 12px 10px;font-size:11px;line-height:1.5;color:#b8cadc;white-space:pre-wrap;overflow-wrap:anywhere}.navigation-effort strong{color:#d4e8f8}
</style>


<style>
.navigation-disclosure>summary{display:block;list-style:none;cursor:pointer}.navigation-disclosure>summary::-webkit-details-marker{display:none}.navigation-disclosure>summary:focus-visible{outline:2px solid #8de8e0;outline-offset:-2px}.navigation-disclosure-arrow{flex:none;width:1em;font-size:11px}.navigation-disclosure-arrow::before{content:'▶'}.navigation-disclosure[open]>summary .navigation-disclosure-arrow::before{content:'▽'}
.navigation-overall>.navigation-disclosure>summary{position:sticky;top:0;z-index:1;background:#000}
</style>
