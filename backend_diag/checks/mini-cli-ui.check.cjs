const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {createRequire}=require('node:module'),req=createRequire(path.join(__dirname,'../ui/package.json'));
const vue=req('vue'),{parse,compileScript}=req('@vue/compiler-sfc'),{transformSync}=req('esbuild');
const {source,render}=require('./ui-components.cjs');
const flush=async()=>{for(let i=0;i<20;i++)await Promise.resolve();await vue.nextTick();};
const descendants=node=>[node,...node.children.flatMap(descendants)];
const text=node=>node.text+node.children.map(text).join('');
function compile(name,{globals={},modules={},inline=true}={}){
 const {descriptor}=parse(source(name),{filename:name});const compiled=compileScript(descriptor,{id:name,inlineTemplate:inline,genDefaultAs:'component'}),module={exports:{}};
 vm.runInNewContext(transformSync(compiled.content+'\nmodule.exports=component;',{format:'cjs'}).code,{module,exports:module.exports,URLSearchParams,AbortController,...globals,require:id=>id==='vue'?vue:modules[id]||{}});return module.exports;
}
function mount(component,props){
 const make=(tag,text='')=>({tag,text,children:[],props:{},style:{},parent:null});
 const renderer=vue.createRenderer({createElement:tag=>make(tag),createText:text=>make('#text',text),createComment:text=>make('#comment',text),setText:(node,value)=>node.text=value,setElementText:(node,value)=>{node.text=value;node.children=[];},parentNode:node=>node.parent,nextSibling:node=>node.parent?.children[node.parent.children.indexOf(node)+1]||null,patchProp:(node,key,_old,value)=>node.props[key]=value,insert(node,parent,anchor){if(node.parent)node.parent.children.splice(node.parent.children.indexOf(node),1);node.parent=parent;const index=anchor?parent.children.indexOf(anchor):-1;parent.children.splice(index<0?parent.children.length:index,0,node);},remove(node){node.parent?.children.splice(node.parent.children.indexOf(node),1);}});
 const root=make('root'),app=renderer.createApp({render:()=>vue.h(component,props())});app.mount(root);return {root,app,nodes:()=>descendants(root),button:label=>descendants(root).find(n=>n.tag==='button'&&(n.props['aria-label']===label||text(n)===label))};
}
test('実Vueタイトル欄: ミニ→最小化→最大化→終了の順、クリックと復帰は独立する',async()=>{
 const calls=[],window=new EventTarget();window.aidiyWindow={isMaximized:async()=>false,minimize:async()=>calls.push('minimize'),maximize:async()=>calls.push('maximize'),close:async()=>calls.push('close')};
 const props=vue.reactive({connected:true,compact:false,switching:false,onMini:()=>calls.push('mini'),onRestore:()=>calls.push('restore')});
 const ui=mount(compile('ウィンドウ/ステータスバー.vue',{globals:{window}}),()=>props);
 try{await flush();assert.deepEqual(ui.nodes().filter(n=>n.tag==='button').map(n=>n.props['aria-label']),['ミニ表示','最小化','最大化','終了']);ui.button('ミニ表示').props.onClick();assert.deepEqual(calls,['mini']);for(const label of ['最小化','最大化','終了'])ui.button(label).props.onClick();await flush();assert.deepEqual(calls,['mini','minimize','maximize','close']);props.compact=true;await flush();assert.deepEqual(ui.nodes().filter(n=>n.tag==='button').map(n=>n.props['aria-label']),['通常表示','最小化','終了']);ui.button('通常表示').props.onClick();assert.equal(calls.at(-1),'restore');props.compact=false;props.connected=false;await flush();assert.equal(ui.button('ミニ表示').props.disabled,true);}finally{ui.app.unmount();}
 const css=source('style.css');assert.match(css,/\.panel-brand\.desktop\{-webkit-app-region:drag\}/);assert.match(css,/\.panel-brand button,\.window-actions\{-webkit-app-region:no-drag\}/);
});
test('実App状態: 全7タブからミニへ移行し元のタブへ復帰、ミニ中はポート監視を維持する',async()=>{
 const {起動ミニ表示を作成}=await import('../ui/src/ウィンドウ/起動ミニ表示.mjs');const displays=[],switches=[],noop=()=>{};
 const methods={接続:noop,終了:noop,中止:noop,切断:noop,表示を離れる:noop,読込:async()=>{},一覧:vue.ref(null),実行中:vue.ref(false)};
 const modules={
  './導入状況/導入状況状態.mjs':{導入状況状態を作成:()=>({})},'./導入状況/導入操作状態.mjs':{導入操作状態を作成:()=>methods},
  './キー設定共通/キー設定状態.mjs':{キー設定状態を作成:()=>({終了:noop})},'./ウィンドウ/Tools接続.mjs':{Tools接続を作成:()=>methods},
  './起動/起動状態.mjs':{起動状態を作成:()=>({表示:(...args)=>displays.push(args),終了:noop})},'./アプリ起動/アプリ状態.mjs':{アプリ状態を作成:()=>({})},
  './アプリ起動/CLI状態.mjs':{CLI状態を作成:()=>methods},'./ウィンドウ/起動ミニ表示.mjs':{起動ミニ表示を作成:options=>起動ミニ表示を作成({...options,切替:async value=>{switches.push(value);return true;}})},
  './AIモデル/AIモデル状態.mjs':{AIモデル状態を作成:()=>methods},'./設定モデル/設定モデル状態.mjs':{設定モデル状態を作成:()=>methods},
 };
 const app=compile('App.vue',{inline:false,modules,globals:{location:{hash:'',pathname:'/',search:''},history:{replaceState(){}},window:{},fetch:async()=>{throw Error('unexpected request');}}});
 const scope=vue.effectScope();let state;const warn=console.warn;console.warn=()=>{};try{state=scope.run(()=>app.setup({}, {expose(){}}));}finally{console.warn=warn;}
 try{state.connected.value=true;await flush();for(const tab of ['install','keys','integrations','trials','manual','start','apps']){state.tab.value=tab;await flush();assert.equal(state.ミニ表示.value,false);await state.ミニ.変更(true);await flush();assert.equal(state.tab.value,tab);assert.equal(state.ミニ表示.value,true);assert.deepEqual(displays.at(-1),[true,false]);await state.ミニ.変更(false);await flush();assert.equal(state.tab.value,tab);assert.equal(state.ミニ表示.value,false);}assert.equal(switches.length,14);await state.ミニ.変更(true);state.connected.value=false;await flush();assert.equal(state.ミニ表示.value,false);}finally{scope.stop();}
 const appSource=source('App.vue');for(const tab of ['install','keys','integrations','trials','manual'])assert.ok(appSource.includes(`v-show="tab==='${tab}'&&!ミニ表示"`));assert.match(appSource,/v-if="ミニ表示" :is="起動ミニパネル"/);
});
test('実Vue CLI行: アイコンと名称帯、未選択disabled、確認取消・連打は実行しない',async()=>{
 const {CLI状態を作成}=await import('../ui/src/アプリ起動/CLI状態.mjs');const アプリ={フォルダ:vue.ref(''),処理中:vue.ref(''),選択中:vue.ref(false)};let approved=false,count=0,prompts=0,release;
 const state=CLI状態を作成({アプリ,確認:()=>{prompts++;return approved;},api:async route=>route==='api/CLI起動'?{対象:[{id:'copilot',名前:'GitHub Copilot CLI',モード:'YOLO',利用可能:true}]}:(count++,new Promise(resolve=>release=resolve))});
 const ui=mount(compile('アプリ起動/ミニCLI起動.vue'),()=>({state,appState:アプリ,online:true}));
 try{await flush();const cli=()=>ui.nodes().find(n=>n.props['data-cli']==='copilot');assert.equal(cli().props.disabled,true);assert.equal(text(cli()),'Copilot');assert.equal(descendants(cli()).find(n=>n.tag==='img').props.src,'CLI_copilot.png');assert.match(cli().props.title,/YOLO.*モデル指定なし/);アプリ.フォルダ.value='/project';await flush();assert.equal(cli().props.disabled,false);cli().props.onClick();await flush();assert.equal(prompts,1);assert.equal(count,0);approved=true;cli().props.onClick();cli().props.onClick();await flush();assert.equal(count,1);assert.equal(prompts,2);assert.equal(cli().props.disabled,true);release({通知:'Term 起動受付'});await flush();assert.equal(cli().props.disabled,false);assert.match(text(ui.root),/Term 起動受付/);}finally{ui.app.unmount();}
 const panel=source('起動/起動ミニパネル.vue');assert.ok(panel.indexOf(':is="ミニアプリ起動"')<panel.indexOf(':is="ミニCLI起動"'));assert.ok(panel.indexOf(':is="ミニCLI起動"')<panel.indexOf('class="mini-services"'));
});
test('CLIの名前やエラーは安全なテキストとして表示する',async()=>{
 const state={項目:vue.ref([{id:'copilot',名前:'<script>bad</script>',モード:'YOLO'}]),読込中:vue.ref(false),処理中:vue.ref(''),通知:vue.ref('<script>error</script>'),失敗:vue.ref(true),読込(){},切断(){}};
 const html=await render('アプリ起動/ミニCLI起動.vue',{state,appState:{フォルダ:vue.ref('/project'),処理中:vue.ref(''),選択中:vue.ref(false)},online:true});assert.doesNotMatch(html,/<script>/);assert.match(html,/&lt;script&gt;error/);assert.match(html,/class="mini-cli-message error"/);
});


test('アイコンは上段AiDiy6種＋Hermes、下段外部CLI6種の2行。Hermesの確認・排他も維持する',async()=>{
 const {CLI状態を作成}=await import('../ui/src/アプリ起動/CLI状態.mjs');const icons=await import('../ui/src/アプリ起動/アプリアイコン.mjs');
 const ids=['claude','codex','copilot','agy','grok','opencode','aidiy_hermes'],apps=['avatar','ide','term','code','live','discord'];let approved=false,prompts=0,release;const launches=[],appLaunches=[];
 const app={項目:vue.ref(apps.map((id,i)=>({id,名前:['Avatar','IDE','Term','Code','Live','Discord'][i]}))),結果:vue.ref({}),フォルダ:vue.ref(''),処理中:vue.ref(''),選択中:vue.ref(false),読込(){},起動:id=>appLaunches.push(id)};
 const state=CLI状態を作成({アプリ:app,確認:()=>{prompts++;return approved;},api:async(route,_method,_signal,_format,body)=>route==='api/CLI起動'?{対象:ids.map(id=>({id,名前:id,モード:'YOLO',利用可能:true}))}:(launches.push(body),new Promise(resolve=>release=resolve))});
 const upper=mount(compile('アプリ起動/ミニアプリ起動.vue',{modules:{'./アプリアイコン.mjs':icons}}),()=>({state:app,cliState:state,online:true}));
 const lower=mount(compile('アプリ起動/ミニCLI起動.vue'),()=>({state,appState:app,online:true}));
 const upperButtons=()=>upper.nodes().filter(n=>n.tag==='button'),lowerButtons=()=>lower.nodes().filter(n=>n.props['data-cli']),hermes=()=>upper.nodes().find(n=>n.props['data-cli']==='aidiy_hermes');
 try{await flush();assert.equal(upperButtons().length,7);assert.deepEqual(upperButtons().map(text),['Avatar','IDE','Term','Code','Live','Discord','Hermes']);assert.deepEqual(lowerButtons().map(text),['Claude','Codex','Copilot','Agy','Grok','OpenCode']);assert.equal(lowerButtons().length,6);assert.ok(!lowerButtons().some(n=>n.props['data-cli']==='aidiy_hermes'));assert.equal(hermes().props.disabled,true);
  for(const button of [...upperButtons(),...lowerButtons()]){const img=descendants(button).find(n=>n.tag==='img');assert.equal(img.props.width,'36');assert.equal(img.props.height,'36');assert.equal(button.children[0].props.class,'mini-icon-frame');}
  app.フォルダ.value='/project';await flush();assert.equal(hermes().props.disabled,false);hermes().props.onClick();await flush();assert.equal(prompts,1);assert.equal(launches.length,0);approved=true;hermes().props.onClick();hermes().props.onClick();await flush();assert.equal(prompts,2);assert.equal(launches.length,1);assert.deepEqual(launches[0],{対象:'aidiy_hermes',フォルダ:'/project',自動承認確認:true});assert.equal(hermes().props.disabled,true);assert.equal(appLaunches.length,0);release({通知:'Hermes Term 起動受付'});await flush();assert.equal(hermes().props.disabled,false);
  state.項目.value=state.項目.value.filter(item=>item.id!=='aidiy_hermes');await flush();assert.equal(upperButtons().length,6);assert.equal(lowerButtons().length,6);assert.equal(hermes(),undefined);
 }finally{upper.app.unmount();lower.app.unmount();}
 const css=source('起動/起動ミニ.css');assert.match(css,/\.mini-app-buttons\{display:grid;grid-template-columns:repeat\(7,minmax\(0,1fr\)\)/);assert.match(css,/\.mini-cli-buttons\{display:grid;grid-template-columns:repeat\(6,minmax\(0,1fr\)\)/);assert.match(css,/\.mini-services\{display:grid;grid-template-columns:repeat\(6,minmax\(0,1fr\)\)/);assert.match(css,/\.mini-icon-frame\{[^}]*width:40px;height:40px/);assert.match(css,/\.mini-icon-frame img\{[^}]*width:36px;height:36px;object-fit:contain/);
});
