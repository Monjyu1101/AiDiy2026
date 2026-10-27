const test=require('node:test'),assert=require('node:assert/strict'),path=require('node:path'),vm=require('node:vm');
const {createRequire}=require('node:module'),req=createRequire(path.join(__dirname,'../ui/package.json'));
const vue=req('vue'),{parse,compileScript}=req('@vue/compiler-sfc'),{transformSync}=req('esbuild');
const {source}=require('./ui-components.cjs');
const {閉じた幅}=require('../起動/マイクロ表示.cjs');
const flush=async()=>{for(let i=0;i<20;i++)await Promise.resolve();await vue.nextTick();};
const nodes=node=>[node,...node.children.flatMap(nodes)];
async function fixture({switching=false}={}){
 const modules={'./アプリアイコン.mjs':await import('../ui/src/アプリ起動/アプリアイコン.mjs'),'./アイコン移動.mjs':await import('../ui/src/アプリ起動/アイコン移動.mjs'),'./円周配置.cjs':require('../ui/src/アプリ起動/円周配置.cjs')};
 const window=new EventTarget(),calls=[],sizes=[];
 window.aidiyWindow={resizeMicroLabel:async height=>{sizes.push(height);return true;},expandMicro:async(...args)=>{calls.push(args);return true;}};
 const {descriptor}=parse(source('アプリ起動/マイクロランチャー.vue'));
 const compiled=compileScript(descriptor,{id:'micro-project',inlineTemplate:true,genDefaultAs:'component'}),module={exports:{}};
 vm.runInNewContext(transformSync(compiled.content+'\nmodule.exports=component;',{format:'cjs'}).code,{module,exports:module.exports,window,document:{documentElement:{classList:{add(){},remove(){}}}},setTimeout,clearTimeout,require:id=>id==='vue'?vue:modules[id]||{}});
 const make=(tag,text='')=>({tag,_text:text,get text(){return this._text+this.children.filter(n=>n.tag!=='#comment').map(n=>n.text).join('');},set text(value){this._text=value;},children:[],props:{},style:{},parent:null,querySelector(){return null;},getBoundingClientRect(){return {height:Math.max(18,Math.ceil(this.text.length/10)*18)};}});
 const renderer=vue.createRenderer({createElement:make,createText:text=>make('#text',text),createComment:text=>make('#comment',text),setText:(n,t)=>n.text=t,setElementText:(n,t)=>{n.text=t;n.children=[];},parentNode:n=>n.parent,nextSibling:n=>n.parent?.children[n.parent.children.indexOf(n)+1]||null,patchProp:(n,k,_old,v)=>n.props[k]=v,insert(n,p){n.parent=p;p.children.push(n);},remove(n){n.parent?.children.splice(n.parent.children.indexOf(n),1);}});
 const appState={フォルダ:vue.ref('/work/project'),項目:vue.ref([]),処理中:vue.ref(''),選択中:vue.ref(false),読込(){}},cliState={項目:vue.ref([]),読込(){}};
 const state={進捗表示:vue.ref(null)};
 const root=make('root'),app=renderer.createApp({render:()=>vue.h(module.exports,{appState,cliState,state,online:true,switching})});app.mount(root);
 return {app,root,appState,cliState,state,calls,sizes,label:()=>nodes(root).find(n=>n.props.class==='micro-project'),core:()=>nodes(root).find(n=>n.props.class==='micro-core')};
}

test('VS Codeを含む6アプリ・7CLI・エディターの14個をアイコン表示へ渡す',async()=>{
 const f=await fixture();
 try{
  f.appState.項目.value=['avatar','ide','term','code','live','discord'].map(id=>({id,名前:id}));
  f.cliState.項目.value=['claude','codex','copilot','agy','grok','opencode','aidiy_hermes'].map(id=>({id,名前:id,利用可能:true}));
  f.cliState.項目.value.push({id:'vscode',名前:'VS Code',種類:'editor',利用可能:true});
  await flush();
  assert.equal(nodes(f.root).filter(n=>n.props.class==='micro-app').length,14);
  assert.ok(nodes(f.root).some(n=>n.tag==='img'&&n.props.src==='CLI_vscode.svg'));
  f.core().props.onClick({detail:0});await flush();assert.deepEqual(f.calls.at(-1),[true,14]);
 }finally{f.app.unmount();}
});

test('アイコンの下に1つだけプロジェクト名を表示し、Windows/POSIX・末尾区切り・変更・長名を扱う',async()=>{
 const f=await fixture();
 try{
  for(const [folder,name] of [['/work/プロジェクト/','プロジェクト'],['C:\\work\\AiDiy2026\\','AiDiy2026'],['\\\\server\\share\\project\\\\','project'],['/work/日本語 & <test>','日本語 & <test>'],['/work/'+ '長い名前'.repeat(50),'長い名前'.repeat(50)],['C:\\','C:'],['/','/'],['','']]){
   f.appState.フォルダ.value=folder;await vue.nextTick();
   assert.equal(f.label().text,name);assert.equal(f.label().props.title,name);
   assert.equal(nodes(f.root).filter(n=>n.props.class==='micro-project').length,1);
   assert.equal(f.label().props['data-micro-hit'],'');
   for(const event of ['onPointerdown','onPointermove','onPointerup','onPointercancel','onLostpointercapture'])assert.equal(typeof f.label().props[event],'function');
  }
  const image=nodes(f.core()).find(n=>n.tag==='img');assert.equal(image.props.src,'AiDiy.png');assert.equal(image.props.width,'40');assert.equal(image.props.height,'40');
  f.core().props.onClick({detail:0});await flush();
  assert.notEqual(f.label().style.display,'none','展開中も名前を表示したままにする');
  f.core().props.onClick({detail:0});await new Promise(resolve=>setTimeout(resolve,480));await flush();
  assert.notEqual(f.label().style.display,'none','収納後も名前を表示する');
 }finally{f.app.unmount();}
});

test('名前は透明な同幅領域で日本語・空白なし英字も折り返す',()=>{
 const css=req('postcss').parse(source('アプリ起動/マイクロランチャー.css')),d={};
 css.walkRules(r=>{if(r.selector==='.micro-project')r.walkDecls(v=>d[v.prop]=v.value);});
 assert.equal(d.background,'transparent');assert.equal(d['white-space'],'normal');assert.equal(d['overflow-wrap'],'anywhere');
 assert.equal(d.width,'120px');assert.equal(d['min-height'],'18px');assert.equal(d['text-overflow'],undefined);
 assert.equal(d['pointer-events'],'auto');assert.equal(d['-webkit-app-region'],'no-drag');
 assert.equal(d.top,'calc(var(--core-y,64px) + 48px)');assert.ok(parseFloat(d.width)<閉じた幅);
 const unfolded={};css.walkRules(r=>{if(r.selector==='.micro-launcher.unfolded .micro-project')r.walkDecls(v=>unfolded[v.prop]=v.value);});
 assert.equal(unfolded['-webkit-line-clamp'],'2');assert.equal(unfolded.overflow,'hidden');
});

test('ラベルの実測高さを送り、長名から短名へ戻しても縮める',async()=>{
 const f=await fixture();
 try{
  for(const name of ['short','日本語プロジェクト'.repeat(20),'unbrokenEnglishProjectName'.repeat(12),'','short']){
   f.appState.フォルダ.value='/work/'+name;await flush();
   assert.equal(f.sizes.at(-1),Math.max(18,Math.ceil(f.label().text.length/10)*18));
  }
 }finally{f.app.unmount();}
});

test('切替中もラベル高さを通知し、main側で完成画像に反映できる',async()=>{
 const f=await fixture({switching:true});
 try{f.appState.フォルダ.value='/work/'+'長い名称'.repeat(50);await flush();assert.equal(f.sizes.at(-1),Math.ceil(f.label().text.length/10)*18);}finally{f.app.unmount();}
});

 test('アイコン表示も短い進行状況を表示し、ランチャーの操作を妨げない',async()=>{
 const f=await fixture();
 try{
  f.state.進捗表示.value={種別:'stop',状態:'running',通知:'Tools を停止しています。'};await flush();
  const notice=nodes(f.root).find(n=>n.props.class==='micro-batch-status');
  assert.equal(notice.text,'停止中…');assert.equal(notice.props.title,'Tools を停止しています。');
  assert.equal(f.core().props.disabled,undefined);
  f.state.進捗表示.value=null;await flush();assert.equal(nodes(f.root).some(n=>n.props.class==='micro-batch-status'),false);
 }finally{f.app.unmount();}
});
