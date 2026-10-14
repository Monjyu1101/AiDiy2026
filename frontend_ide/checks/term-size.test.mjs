// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import vm from 'node:vm';
import * as completion from '../src/terminal-completion.js';
const require=createRequire(import.meta.url),vue=require('vue');
const {parse,compileScript,compileStyle}=require('@vue/compiler-sfc'),{transformSync}=require('esbuild');
const {descriptor}=parse(readFileSync(new URL('../src/components/TermPanel.vue',import.meta.url),'utf8'));
const flush=async()=>{for(let i=0;i<12;i++)await Promise.resolve();};

// 実Vueのsetupと実FitAddonを通す。文字セルの測定・描画・WebSocketだけを代替する。
async function fixture(t){
 const mounted=[],unmounted=[],observers=new Set(),sockets=[],packets=[],resources={terminals:0,disposed:0};
 const container=new EventTarget();container.clientWidth=344;container.clientHeight=76;
 const window={getComputedStyle:element=>({getPropertyValue:key=>key==='height'?String(element.clientHeight):key==='width'?String(element.clientWidth):'0'})};
 const fitModule={exports:{}};
 vm.runInNewContext(readFileSync(require.resolve('@xterm/addon-fit'),'utf8'),{window,module:fitModule,exports:fitModule.exports});
 let terminal;
 class Terminal{
  cols=80;rows=24;options={scrollback:5000};listeners={};buffer={active:{}};
  _core={_renderService:{dimensions:{css:{cell:{width:8,height:17}}},clear(){}}};
  constructor(){terminal=this;resources.terminals++;}
  open(parent){this.element={parentElement:parent};} loadAddon(addon){addon.activate(this);} attachCustomKeyEventHandler(){} reset(){} clear(){} focus(){} dispose(){resources.disposed++;}
  resize(cols,rows){this.cols=cols;this.rows=rows;this.listeners.Resize?.({cols,rows});}
 }
 for(const event of ['Data','Key','Resize','CursorMove','Scroll','Render'])Terminal.prototype['on'+event]=function(callback){this.listeners[event]=callback;return{dispose:()=>delete this.listeners[event]};};
 class Socket{
  static OPEN=1;readyState=1;
  constructor(){sockets.push(this);} send(data){packets.push(JSON.parse(data));} close(){this.readyState=3;this.onclose?.();}
  receive(message){this.onmessage({data:JSON.stringify(message)});}
 }
 class ResizeObserver{
  constructor(callback){this.callback=callback;observers.add(this);} observe(target){this.target=target;} disconnect(){observers.delete(this);}
 }
 const modules={'@xterm/xterm':{Terminal},'@xterm/addon-fit':fitModule.exports,'@xterm/xterm/css/xterm.css':{},'./StatusBar.vue':{},'./TerminalWelcome.vue':{},'../terminal-completion.js':completion};
 const script=compileScript(descriptor,{id:'TermPanel',genDefaultAs:'component'}),module={exports:{}};
 vm.runInNewContext(transformSync(script.content+'\nmodule.exports=component;',{format:'cjs'}).code,{
  module,URL,WebSocket:Socket,ResizeObserver,location:{href:'http://localhost/'},
  require(id){if(id==='vue')return{...vue,onMounted:callback=>mounted.push(callback),onBeforeUnmount:callback=>unmounted.push(callback)};if(id in modules)return modules[id];throw Error(id);},
 });
 const props=vue.reactive({base:'/',visible:true}),scope=vue.effectScope(),state=scope.run(()=>module.exports.setup(props,{expose(){}}));
 state.container.value=vue.markRaw(container);
 t.after(()=>{for(const callback of unmounted)callback();scope.stop();});
 for(const callback of mounted)await callback();
 sockets[0].onopen();sockets[0].receive({type:'ready',project:'/fixture',shell:'bash',completion:false});
 return{state,props,terminal,container,sockets,packets,resources,observers,resize(height,width=344){container.clientHeight=height;container.clientWidth=width;for(const observer of observers)observer.callback();}};
}

test('Term: 数行の初期サイズ・縮小・拡大・最下行が実FitAddonとresize送信へ反映する',async t=>{
 const f=await fixture(t);
 assert.deepEqual(f.packets[0],{type:'start',cols:41,rows:4});
 assert.equal(f.terminal.rows*17<=f.container.clientHeight,true);
 for(const [height,rows] of [[51,3],[17,1],[85,5],[510,30],[76,4]]){
  f.resize(height);assert.deepEqual(f.packets.at(-1),{type:'resize',cols:41,rows});
  assert.ok(f.terminal.rows*17<=height);
 }
 const count=f.packets.length;f.resize(76);assert.equal(f.packets.length,count,'同じサイズは再送しない');
 f.resize(0);f.resize(76,0);assert.equal(f.packets.length,count,'0サイズはPTYへ送らない');
 f.resize(76);f.terminal.listeners.Data('日本語\r');assert.deepEqual(f.packets.at(-1),{type:'input',data:'日本語\r'});
});

test('Term: 小さな画面の入力・表示クリア・タブ往復・再起動でも同じ端末を維持する',async t=>{
 const f=await fixture(t);assert.equal(f.state.inputStarted.value,false);
 f.terminal.listeners.Key();await vue.nextTick();assert.equal(f.state.inputStarted.value,true);
 await f.state.clearDisplay();assert.equal(f.state.inputStarted.value,false);assert.equal(f.terminal.rows,4);
 const before=f.packets.length;f.props.visible=false;await vue.nextTick();f.resize(51);assert.equal(f.packets.length,before);
 f.props.visible=true;await flush();assert.equal(f.terminal.rows,3);
 f.container.dispatchEvent(new Event('paste'));await vue.nextTick();assert.equal(f.state.inputStarted.value,true);
 f.state.connect();f.sockets.at(-1).onopen();assert.deepEqual(f.packets.at(-1),{type:'start',cols:41,rows:3});
 assert.equal(f.state.inputStarted.value,false);assert.equal(f.resources.terminals,1);assert.equal(f.observers.size,1);
});

test('Term: 内側の領域を原点に補完候補を置き、最後の表示行で切り詰める',async t=>{
 const f=await fixture(t),text='PS X> codex';
 const line={length:f.terminal.cols,isWrapped:false,translateToString:()=>text,getCell:x=>({getChars:()=>text[x]||'',isItalic:()=>false})};
 const buffer=f.terminal.buffer.active={type:'normal',baseY:10,viewportY:10,cursorX:text.length,cursorY:3,getLine:row=>row===10+buffer.cursorY?line:undefined};
 f.container.getBoundingClientRect=()=>({left:108,top:216,width:344,height:f.container.clientHeight});
 f.container.querySelector=()=>({getBoundingClientRect:()=>({left:108,top:216,width:f.terminal.cols*8,height:f.terminal.rows*17})});
 f.sockets[0].receive({type:'ready',project:'/fixture',shell:'powershell',completion:true});
 f.state.updateCompletion();
 assert.equal(f.state.ghostRows.value.length,1);
 assert.equal(f.state.ghostRows.value[0].style.left,`${(text.length+1)*8}px`);
 assert.equal(f.state.ghostRows.value[0].style.top,'51px');
 assert.equal(f.state.ghostRows.value[0].style.height,'17px');
 assert.equal(f.state.ghostRows.value[0].text.length,f.terminal.cols-text.length-1);
 f.resize(51);buffer.cursorY=2;f.state.updateCompletion();
 assert.equal(f.state.ghostRows.value.length,1);assert.equal(f.state.ghostRows.value[0].style.top,'34px');
 f.props.visible=false;f.state.updateCompletion();assert.equal(f.state.ghostRows.value.length,0);
});

test('Term CSS: 高さ240以下だけ案内を畳み、余白なしの内側へfitする',()=>{
 const css=descriptor.styles[0].content,result=compileStyle({source:css,id:'data-v-term',scoped:true});
 assert.deepEqual(result.errors,[]);
 assert.match(css,/\.term-component\{[^}]*container:term-panel \/ size/);
 assert.match(css,/@container term-panel \(max-height:240px\)\{\s*\.term-welcome\{display:none\}\s*\.term-waiting \.term-screen\{flex:1;height:auto;max-height:none;border-top:0\}/);
 assert.match(css,/\.term-viewport\{[^}]*height:100%;[^}]*min-height:0/);
 assert.match(descriptor.template.content,/<div class="term-screen"[^>]*><div ref="container" class="term-viewport">/);
 assert.match(css,/\.term-error\{flex:none;max-height:1\.65em;overflow:auto/);
 assert.match(css,/\.term-meta>span:first-child\{[^}]*white-space:nowrap/);
});
