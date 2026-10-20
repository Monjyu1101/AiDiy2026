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
test('実Vue CLI行: 確認なしで即時起動し、連打・処理中を排他、成功通知を隠して失敗を表示する',async()=>{
 const {CLI状態を作成}=await import('../ui/src/アプリ起動/CLI状態.mjs');const アプリ={フォルダ:vue.ref(''),処理中:vue.ref(''),選択中:vue.ref(false)};
 const launches=[];let prompts=0,release;
 const state=CLI状態を作成({アプリ,確認:()=>{prompts++;return false;},api:async(route,method,_signal,format,body)=>{
  if(route==='api/CLI起動')return {対象:[{id:'copilot',名前:'GitHub Copilot CLI',モード:'YOLO',利用可能:true}]};
  assert.equal(route,'api/CLI起動/開始');launches.push({method,format,body});return new Promise((resolve,reject)=>release={resolve,reject});
 }});
 const ui=mount(compile('アプリ起動/ミニCLI起動.vue'),()=>({state,appState:アプリ,online:true}));
 const cli=()=>ui.nodes().find(n=>n.props['data-cli']==='copilot'),message=()=>ui.nodes().find(n=>n.props.class?.includes('mini-cli-message'));
 try{
  await flush();assert.equal(cli().props.disabled,true);assert.equal(text(cli()),'');assert.equal(cli().props['aria-label'],'GitHub Copilot CLI をTermで起動（YOLO）');assert.equal(descendants(cli()).find(n=>n.tag==='img').props.src,'CLI_copilot.svg');assert.match(cli().props.title,/YOLO.*モデル指定なし/);
  アプリ.フォルダ.value='/日本語 path & ;';await flush();assert.equal(cli().props.disabled,false);
  cli().props.onClick();cli().props.onClick();assert.equal(prompts,0);assert.equal(launches.length,1);
  assert.deepEqual(launches[0],{method:'POST',format:'json',body:{対象:'copilot',フォルダ:'/日本語 path & ;',自動承認確認:true}});
  await flush();assert.equal(cli().props.disabled,true);assert.equal(state.処理中.value,'copilot');assert.equal(アプリ.処理中.value,'cli:copilot');assert.ok(message());assert.match(text(message()),/起動中/);
  release.resolve({通知:'Term 起動受付'});await flush();assert.equal(cli().props.disabled,false);assert.equal(state.通知.value,'Term 起動受付');assert.doesNotMatch(text(ui.root),/Term 起動受付/);assert.equal(message(),undefined);
  cli().props.onClick();release.reject(Error('Term を開始できません'));await flush();assert.equal(launches.length,2);assert.equal(prompts,0);assert.equal(cli().props.disabled,false);assert.match(text(message()),/Term を開始できません/);assert.match(message().props.class,/error/);
  cli().props.onClick();await flush();assert.equal(cli().props.disabled,true);assert.doesNotMatch(text(ui.root),/Term を開始できません/);release.resolve({通知:'再試行の起動受付'});await flush();assert.equal(message(),undefined);assert.doesNotMatch(text(ui.root),/再試行の起動受付/);
  アプリ.選択中.value=true;await flush();assert.equal(cli().props.disabled,true);アプリ.選択中.value=false;アプリ.処理中.value='code';await flush();assert.equal(cli().props.disabled,true);
 }finally{ui.app.unmount();}
 const panel=source('起動/起動ミニパネル.vue');assert.ok(panel.indexOf(':is="ミニアプリ起動"')<panel.indexOf(':is="ミニCLI起動"'));assert.ok(panel.indexOf(':is="ミニCLI起動"')<panel.indexOf('class="mini-services"'));
});
test('実Vue AiDiy行: 6アプリは確認なしで起動し、成功説明を隠してフォルダ・処理中・失敗を残す',async()=>{
 const {アプリ状態を作成}=await import('../ui/src/アプリ起動/アプリ状態.mjs'),icons=await import('../ui/src/アプリ起動/アプリアイコン.mjs');
 const ids=['avatar','ide','term','code','live','discord'],launches=[];let release,prompts=0;
 const state=アプリ状態を作成({api:async(route,method,_signal,format,body)=>{
  if(route==='api/アプリ起動')return {対象:ids.map(id=>({id,名前:id}))};
  assert.equal(route,'api/アプリ起動/開始');launches.push({method,format,body});return new Promise((resolve,reject)=>release={resolve,reject});
 }});
 const ui=mount(compile('アプリ起動/ミニアプリ起動.vue',{modules:{'./アプリアイコン.mjs':icons},globals:{confirm:()=>{prompts++;return false;}}}),()=>({state,online:true}));
 const buttons=()=>ui.nodes().filter(n=>n.props['data-app']),button=id=>buttons().find(n=>n.props['data-app']===id),message=()=>ui.nodes().find(n=>n.props.class?.includes('mini-app-message'));
 try{
  await flush();assert.equal(buttons().length,6);assert.ok(buttons().every(n=>n.props.disabled));assert.match(text(message()),/SELECT YOUR PROJECT/);
  state.フォルダ.value='/日本語 project & ;';await flush();assert.equal(text(message()),state.フォルダ.value);
  for(const [index,id] of ids.entries()){
   button(id).props.onClick();button(id).props.onClick();assert.equal(launches.length,index+1);assert.equal(prompts,0);
   assert.deepEqual(launches.at(-1),{method:'POST',format:'json',body:{対象:id,フォルダ:'/日本語 project & ;'}});
   await flush();assert.ok(buttons().every(n=>n.props.disabled));assert.match(text(message()),/起動中/);
   const notification=id+' の起動結果の説明';release.resolve({通知:notification,起動済み:index%2===1});await flush();
   assert.equal(state.結果.value[id].通知,notification);assert.equal(text(message()),state.フォルダ.value);assert.equal(message().props.title,state.フォルダ.value);assert.doesNotMatch(text(ui.root),/起動結果の説明/);assert.ok(buttons().every(n=>!n.props.disabled));
  }
  button('code').props.onClick();release.reject(Error('Code を開始できません'));await flush();assert.equal(text(message()),'Code を開始できません');assert.match(message().props.class,/error/);assert.ok(buttons().every(n=>!n.props.disabled));
  button('code').props.onClick();await flush();assert.match(text(message()),/起動中/);assert.doesNotMatch(text(ui.root),/Code を開始できません/);release.resolve({通知:'Code の再試行を受け付けました'});await flush();assert.equal(text(message()),state.フォルダ.value);assert.doesNotMatch(message().props.class,/error/);
  state.フォルダ.value='';await flush();assert.match(text(message()),/SELECT YOUR PROJECT/);assert.ok(buttons().every(n=>n.props.disabled));assert.equal(prompts,0);
 }finally{ui.app.unmount();}
});
test('CLIの名前やエラーは安全なテキストとして表示する',async()=>{
 const state={項目:vue.ref([{id:'copilot',名前:'<script>bad</script>',モード:'YOLO'}]),読込中:vue.ref(false),処理中:vue.ref(''),通知:vue.ref('<script>error</script>'),失敗:vue.ref(true),読込(){},切断(){}};
 const html=await render('アプリ起動/ミニCLI起動.vue',{state,appState:{フォルダ:vue.ref('/project'),処理中:vue.ref(''),選択中:vue.ref(false)},online:true});assert.doesNotMatch(html,/<script>/);assert.match(html,/&lt;script&gt;error/);assert.match(html,/class="mini-cli-message error"/);
});

test('ミニの説明文を省き、右側のCLI再確認とその無効化条件は維持する',async()=>{
 let reads=0;const online=vue.ref(true),state={項目:vue.ref([]),読込中:vue.ref(false),処理中:vue.ref(''),通知:vue.ref(''),失敗:vue.ref(false),読込(){reads++;},切断(){}};
 const ui=mount(compile('アプリ起動/ミニCLI起動.vue'),()=>({state,appState:{フォルダ:vue.ref('/project'),処理中:vue.ref(''),選択中:vue.ref(false)},online:online.value}));
 const refresh=()=>ui.nodes().find(n=>n.props['aria-label']==='利用可能なCLIを再確認');
 try{
  await flush();assert.equal(reads,1);assert.doesNotMatch(text(ui.root),/外部CLI\s*[·・]\s*自動承認/);assert.equal(text(refresh()),'↻');assert.equal(refresh().props.disabled,false);
  refresh().props.onClick();assert.equal(reads,2);
  state.読込中.value=true;await flush();assert.equal(refresh().props.disabled,true);state.読込中.value=false;
  state.処理中.value='copilot';await flush();assert.equal(refresh().props.disabled,true);state.処理中.value='';
  online.value=false;await flush();assert.equal(refresh().props.disabled,true);
 }finally{ui.app.unmount();}
 assert.match(source('起動/起動ミニ.css'),/\.mini-cli-heading\{display:flex;align-items:center;justify-content:flex-end;/);
});


test('アイコンは上段AiDiy6種＋Hermes、下段外部CLI6種。Hermesも確認なし・排他・成功非表示',async()=>{
 const {CLI状態を作成}=await import('../ui/src/アプリ起動/CLI状態.mjs');const icons=await import('../ui/src/アプリ起動/アプリアイコン.mjs');
 const ids=['claude','codex','copilot','agy','grok','opencode','aidiy_hermes'],apps=['avatar','ide','term','code','live','discord'];let prompts=0,release;const launches=[],appLaunches=[];
 const app={項目:vue.ref(apps.map((id,i)=>({id,名前:['Avatar','IDE','Term','Code','Live','Discord'][i]}))),結果:vue.ref({}),フォルダ:vue.ref(''),処理中:vue.ref(''),選択中:vue.ref(false),読込(){},起動:id=>appLaunches.push(id)};
 const state=CLI状態を作成({アプリ:app,確認:()=>{prompts++;return false;},api:async(route,_method,_signal,_format,body)=>route==='api/CLI起動'?{対象:ids.map(id=>({id,名前:id,モード:'YOLO',利用可能:true}))}:(launches.push(body),new Promise((resolve,reject)=>release={resolve,reject}))});
 const upper=mount(compile('アプリ起動/ミニアプリ起動.vue',{modules:{'./アプリアイコン.mjs':icons}}),()=>({state:app,cliState:state,online:true}));
 const lower=mount(compile('アプリ起動/ミニCLI起動.vue'),()=>({state,appState:app,online:true}));
 const upperButtons=()=>upper.nodes().filter(n=>n.tag==='button'),lowerButtons=()=>lower.nodes().filter(n=>n.props['data-cli']),hermes=()=>upper.nodes().find(n=>n.props['data-cli']==='aidiy_hermes');
 try{await flush();assert.equal(upperButtons().length,7);assert.deepEqual(upperButtons().map(n=>n.props['data-app']||n.props['data-cli']),[...apps,'aidiy_hermes']);assert.deepEqual(lowerButtons().map(n=>n.props['data-cli']),ids.filter(id=>id!=='aidiy_hermes'));assert.equal(lowerButtons().length,6);assert.ok(!lowerButtons().some(n=>n.props['data-cli']==='aidiy_hermes'));assert.equal(hermes().props.disabled,true);
  assert.ok([...upper.nodes(),...lower.nodes()].every(n=>!n.props.class?.includes('mini-icon-caption')));
  for(const button of [...upperButtons(),...lowerButtons()]){
   const img=descendants(button).find(n=>n.tag==='img'),appId=button.props['data-app'],cliId=button.props['data-cli'];
   assert.equal(img.props.width,'40');assert.equal(img.props.height,'40');assert.equal(button.children[0].props.class,'mini-icon-frame');assert.equal(text(button),'');
   const name=appId?app.項目.value.find(item=>item.id===appId).名前:state.項目.value.find(item=>item.id===cliId).名前;
   assert.ok(button.props['aria-label'].includes(name));assert.ok(button.props.title.includes(name));
   assert.equal(img.props.src,appId?icons.アプリアイコン[appId]:cliId==='aidiy_hermes'?'CLI_aidiy_hermes.svg':'CLI_'+cliId+'.svg');
  }
  app.フォルダ.value='/project';await flush();assert.equal(hermes().props.disabled,false);
  hermes().props.onClick();hermes().props.onClick();lowerButtons()[0].props.onClick();assert.equal(prompts,0);assert.equal(launches.length,1);assert.deepEqual(launches[0],{対象:'aidiy_hermes',フォルダ:'/project',自動承認確認:true});
  await flush();assert.ok([...upperButtons(),...lowerButtons()].every(n=>n.props.disabled));assert.equal(appLaunches.length,0);
  release.resolve({通知:'Hermes Term 起動受付'});await flush();assert.equal(hermes().props.disabled,false);assert.doesNotMatch(text(upper.root)+text(lower.root),/Hermes Term 起動受付/);assert.equal(lower.nodes().find(n=>n.props.class?.includes('mini-cli-message')),undefined);
  hermes().props.onClick();release.reject(Error('Hermes の起動に失敗しました'));await flush();assert.equal(prompts,0);assert.equal(launches.length,2);assert.match(text(lower.root),/Hermes の起動に失敗しました/);assert.equal(hermes().props.disabled,false);
  state.項目.value=state.項目.value.filter(item=>item.id!=='aidiy_hermes');await flush();assert.equal(upperButtons().length,6);assert.equal(lowerButtons().length,6);assert.equal(hermes(),undefined);
 }finally{upper.app.unmount();lower.app.unmount();}
 const css=source('起動/起動ミニ.css');assert.match(css,/\.mini-app-buttons\{display:grid;grid-template-columns:repeat\(7,minmax\(0,1fr\)\)/);assert.match(css,/\.mini-cli-buttons\{display:grid;grid-template-columns:repeat\(6,minmax\(0,1fr\)\)/);assert.match(css,/\.mini-services\{display:grid;grid-template-columns:repeat\(6,minmax\(0,1fr\)\)/);assert.match(css,/\.mini-icon-frame\{[^}]*width:40px;height:40px/);assert.match(css,/\.mini-icon-frame img\{[^}]*width:40px;height:40px;object-fit:contain/);
});
