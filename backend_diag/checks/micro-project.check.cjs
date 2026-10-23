const test=require('node:test'),assert=require('node:assert/strict'),path=require('node:path'),vm=require('node:vm');
const {createRequire}=require('node:module'),req=createRequire(path.join(__dirname,'../ui/package.json'));
const vue=req('vue'),{parse,compileScript}=req('@vue/compiler-sfc'),{transformSync}=req('esbuild');
const {source}=require('./ui-components.cjs');
const {閉じた幅}=require('../起動/マイクロ表示.cjs');
const flush=async()=>{for(let i=0;i<20;i++)await Promise.resolve();await vue.nextTick();};
const nodes=node=>[node,...node.children.flatMap(nodes)];
async function fixture(){
 const modules={'./アプリアイコン.mjs':await import('../ui/src/アプリ起動/アプリアイコン.mjs'),'./アイコン移動.mjs':await import('../ui/src/アプリ起動/アイコン移動.mjs'),'./円周配置.cjs':require('../ui/src/アプリ起動/円周配置.cjs')};
 const window=new EventTarget(),calls=[];
 window.aidiyWindow={expandMicro:async(...args)=>{calls.push(args);return true;}};
 const {descriptor}=parse(source('アプリ起動/マイクロランチャー.vue'));
 const compiled=compileScript(descriptor,{id:'micro-project',inlineTemplate:true,genDefaultAs:'component'}),module={exports:{}};
 vm.runInNewContext(transformSync(compiled.content+'\nmodule.exports=component;',{format:'cjs'}).code,{module,exports:module.exports,window,document:{documentElement:{classList:{add(){},remove(){}}}},setTimeout,clearTimeout,require:id=>id==='vue'?vue:modules[id]||{}});
 const make=(tag,text='')=>({tag,text,children:[],props:{},style:{},parent:null,querySelector(){return null;}});
 const renderer=vue.createRenderer({createElement:make,createText:text=>make('#text',text),createComment:text=>make('#comment',text),setText:(n,t)=>n.text=t,setElementText:(n,t)=>{n.text=t;n.children=[];},parentNode:n=>n.parent,nextSibling:n=>n.parent?.children[n.parent.children.indexOf(n)+1]||null,patchProp:(n,k,_old,v)=>n.props[k]=v,insert(n,p){n.parent=p;p.children.push(n);},remove(n){n.parent?.children.splice(n.parent.children.indexOf(n),1);}});
 const appState={フォルダ:vue.ref('/work/project'),項目:vue.ref([]),処理中:vue.ref(''),選択中:vue.ref(false),読込(){}},cliState={項目:vue.ref([]),読込(){}};
 const root=make('root'),app=renderer.createApp({render:()=>vue.h(module.exports,{appState,cliState,online:true})});app.mount(root);
 return {app,root,appState,calls,label:()=>nodes(root).find(n=>n.props.class==='micro-project'),core:()=>nodes(root).find(n=>n.props.class==='micro-core')};
}

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
  assert.equal(f.label().style.display,'none','展開メニューに名前を重ねない');
  f.core().props.onClick({detail:0});await flush();
  assert.notEqual(f.label().style.display,'none','収納時は名前を戻す');
 }finally{f.app.unmount();}
});

test('長名は1行省略し、名前の領域が閉じたnative窓からはみ出さない',()=>{
 const css=req('postcss').parse(source('アプリ起動/マイクロランチャー.css')),d={};
 css.walkRules(r=>{if(r.selector==='.micro-project')r.walkDecls(v=>d[v.prop]=v.value);});
 assert.equal(d['text-overflow'],'ellipsis');assert.equal(d['white-space'],'nowrap');assert.equal(d.overflow,'hidden');
 assert.equal(d['pointer-events'],'auto');assert.equal(d['-webkit-app-region'],'no-drag');
 assert.equal(d.top,'calc(50% + 38px)');assert.ok(閉じた幅/2+38+parseFloat(d.height)<閉じた幅);assert.ok(parseFloat(d.width)<閉じた幅);
 assert.match(require('node:fs').readFileSync(path.join(__dirname,'../起動/electron-main.cjs'),'utf8'),/value==='micro'\?\{width:閉じた幅,height:閉じた幅\}/);
});
