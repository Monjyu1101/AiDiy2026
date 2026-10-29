// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {EventEmitter} from 'node:events';
import vm from 'node:vm';
import {parse,compileScript,compileTemplate,compileStyle} from '@vue/compiler-sfc';
import * as vue from 'vue';
import {renderToString} from '@vue/server-renderer';
import {transformSync} from 'esbuild';
import * as addressTools from '../src/ブラウザ/URL表示.js';
import {browserGlassFrame,browserGlassMap} from '../src/ブラウザ/ガラス屈折.js';

test('Browser板ガラス: PNGと有界なDIP矩形だけを受け取り、切り抜きの位置を維持する',()=>{
 const input={src:'data:image/png;base64,aGVsbG8=',width:1200,height:100,x:8,y:0,captureWidth:1192,captureHeight:100,extra:'ignored'};
 assert.deepEqual(browserGlassFrame(input),{...Object.fromEntries(Object.entries(input).filter(([key])=>key!=='extra')),zoom:1});
 assert.equal(browserGlassFrame({...input,zoom:1.5}).zoom,1.5);
 assert.equal(browserGlassFrame({...input,zoom:Infinity}),null);
 for(const invalid of [null,{}, {...input,src:'https://example.test/image.png'},{...input,src:'data:image/svg+xml,<svg/>'},{...input,width:Infinity},{...input,width:1201},{...input,height:1001},{...input,x:-1},{...input,captureWidth:1200},{...input,captureHeight:101},{...input,captureHeight:0}])assert.equal(browserGlassFrame(invalid),null);
});

test('Browser板ガラス: 滑らかな内向きの変位マップを生成し、ノイズやぼかしを使わない',()=>{
 const map=(length,axis)=>decodeURIComponent(browserGlassMap(length,axis).split(',')[1]);
 const x=map(1200,'x'),y=map(100,'y');
 assert.match(x,/#ff8080/);assert.match(x,/#008080/);assert.match(x,/offset="1%"/);
 assert.match(y,/#80ff80/);assert.match(y,/#800080/);assert.match(y,/offset="12%"/);
 for(const source of [x,y,map(8,'x')]){assert.match(source,/linearGradient/);assert.doesNotMatch(source,/feTurbulence|feGaussianBlur|https?:\/\/(?!www\.w3\.org)/);}
});

test('Browser板ガラス: 実ピクセルを二軸変位し、12pxの四角い縁だけ描くSVGをコンパイルする',()=>{
 const {descriptor}=parse(readFileSync(new URL('../src/ブラウザ/ガラス縁.vue',import.meta.url),'utf8'));
 const script=compileScript(descriptor,{id:'glass-rim',genDefaultAs:'component'});
 const template=compileTemplate({source:descriptor.template.content,filename:'Glass.vue',id:'glass-rim',compilerOptions:{bindingMetadata:script.bindings}});
 assert.deepEqual(template.errors,[]);
 const css=compileStyle({source:descriptor.styles[0].content,id:'data-v-glass-rim',scoped:true});assert.deepEqual(css.errors,[]);
 assert.equal((descriptor.template.content.match(/<feDisplacementMap /g)||[]).length,2);
 assert.match(descriptor.template.content,/:href="frame\.src"/);
 assert.match(descriptor.template.content,/<rect :x="12\*frame\.zoom" :y="12\*frame\.zoom"[^>]+fill="black"/);
 assert.doesNotMatch(descriptor.template.content,/\br[xy]=/);
 assert.match(descriptor.template.content,/maskUnits="userSpaceOnUse" x="0" y="0"/);
 assert.match(descriptor.template.content,/aria-hidden="true" focusable="false"/);
 assert.match(css.code,/pointer-events:none/);
 assert.doesNotMatch(descriptor.template.content,/feTurbulence|feGaussianBlur|<foreignObject/);
});

test('Browser板ガラス: preloadは専用pushの購読だけを提供し解除できる',()=>{
 const ipc=new EventEmitter();let api;const invoked=[];
 ipc.invoke=(...args)=>{invoked.push(args);};
 vm.runInNewContext(readFileSync(new URL('../デスクトップ/preload.cjs',import.meta.url),'utf8'),{require:()=>({contextBridge:{exposeInMainWorld(_name,value){api=value;}},ipcRenderer:ipc})});
 const frames=[],stop=api.onBrowserHeaderGlass(value=>frames.push(value));
 ipc.emit('development:browser-header-glass',{},null);assert.deepEqual(frames,[null]);assert.equal(invoked.length,0);
 stop();ipc.emit('development:browser-header-glass',{},{});assert.equal(frames.length,1);
 assert.equal(typeof api.onBrowserHeaderGlass(null),'function');
});

for(const headerOnly of [false,true])test(`Browser板ガラス: 実Vueの${headerOnly?'専用ヘッダー':'通常表示'}は購読範囲と破棄後の標本を管理する`,async()=>{
 const mounted=[],unmounted=[];let receive,subscribed=0,stopped=0;
 const {descriptor}=parse(readFileSync(new URL('../src/ブラウザ/ブラウザパネル.vue',import.meta.url),'utf8'));
 const script=compileScript(descriptor,{id:'browser-glass-lifetime',genDefaultAs:'component'}),module={exports:{}};
 vm.runInNewContext(transformSync(script.content+'\nmodule.exports=component;',{format:'cjs'}).code,{
  module,console,requestAnimationFrame:()=>1,cancelAnimationFrame(){},ResizeObserver:class{observe(){}disconnect(){}},document:{documentElement:{classList:{add(){},remove(){}}}},
  window:{aidiyWindow:{onBrowserChanged:()=>()=>{},browserAction:async()=>({ok:true,url:'about:blank',fullscreen:headerOnly,available:true}),onBrowserHeaderGlass(fn){subscribed++;receive=fn;return()=>{stopped++;};}}},
  require:id=>id==='./URL表示.js'?addressTools:id==='vue'?{...vue,onMounted:fn=>mounted.push(fn),onBeforeUnmount:fn=>unmounted.push(fn)}:{},
 });
 const state=module.exports.setup({headerOnly},{expose(){}});mounted.forEach(fn=>fn());
 assert.equal(subscribed,headerOnly?1:0);
 if(headerOnly){receive({src:'data:image/png;base64,aGVsbG8='});assert.ok(state.headerGlass.value);receive(null);assert.equal(state.headerGlass.value,null);}
 unmounted.forEach(fn=>fn());assert.equal(stopped,headerOnly?1:0);
 receive?.({src:'data:image/png;base64,bGF0ZQ=='});assert.equal(state.headerGlass.value,null,'破棄後の画素を保持しない');
 await Promise.resolve();
});


test('Browser板ガラス: 表示倍率が変わっても12pxの厚縁と強い屈折だけ描き中央は透明',async()=>{
 const {descriptor}=parse(readFileSync(new URL('../src/ブラウザ/ガラス縁.vue',import.meta.url),'utf8'));
 const script=compileScript(descriptor,{id:'glass-square-render',genDefaultAs:'component'});
 const template=compileTemplate({source:descriptor.template.content,filename:'Glass.vue',id:'glass-square-render',compilerOptions:{bindingMetadata:script.bindings}});
 assert.deepEqual(template.errors,[]);
 const module={exports:{}};
 vm.runInNewContext(transformSync(script.content+'\n'+template.code+'\ncomponent.render=render;module.exports=component;',{format:'cjs'}).code,{module,require:id=>id==='vue'?vue:{browserGlassFrame,browserGlassMap}});
 for(const zoom of [.75,1,1.5,2]){
  const frame={src:'data:image/png;base64,aGVsbG8=',width:1200,height:140,x:0,y:0,captureWidth:1200,captureHeight:140,zoom};
  const html=await renderToString(vue.createSSRApp(module.exports,{frame}));
  assert.match(html,new RegExp(`<rect x="${12*zoom}" y="${12*zoom}" width="${1200-24*zoom}" height="${140-24*zoom}" fill="black"`),'中央の標本画像を矩形で完全に除外する');
  assert.equal((html.match(new RegExp(`scale="${20*zoom}"`,'g'))||[]).length,2,'屈折を二軸とも倍率へ追従させる');
  assert.doesNotMatch(html,/\br[xy]="/,'SVG外周も内周も角丸なし');
  assert.match(html,/href="data:image\/png;base64,/,'屈折は実取得ピクセルを入力にする');
 }
 const empty=await renderToString(vue.createSSRApp(module.exports,{frame:null}));
 assert.doesNotMatch(empty,/<svg/,'取得できない場合に架空の屈折画像を作らない');
});
