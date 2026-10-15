const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
class Element {
  constructor() { this.children = []; this.listeners = {}; this.value = ''; this.hidden = false; this.disabled = false; this.attributes = {}; this.classList = { toggle() {} }; }
  get textContent() { return (this._text || '') + this.children.map(c=>c.textContent || '').join(''); }
  set textContent(value) { this._text=value; this.children=[]; }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this._text=""; this.children = children; }
  addEventListener(type, handler) { this.listeners[type] = handler; }
  setAttribute(key, value) { this.attributes[key] = value; }
  async click() { if (!this.disabled) return this.listeners.click?.({}); }
}
const entries = [{id:'node',menuGroup:'ベース',usageTier:'base',name:'Node.js',category:'基盤',commands:['node'],description:'runtime',required_by:['IDE'],sources:['_setup.py'],evidence:[{path:'_setup.py',line:3}]},{id:'ffmpeg',menuGroup:'その他拡張',usageTier:'integration',name:'FFmpeg',category:'メディア',commands:['ffmpeg'],description:'media',sources:['tools.py']}];
function fixture(fetchImpl) {
  const elements = new Map(); const calls = [], history = [];
  const document = {getElementById(id) { if (!elements.has(id)) elements.set(id, new Element()); return elements.get(id); },createElement() { return new Element(); }};
  const location = {hash:'#token=test-token',pathname:'/proxy/8097/',search:'',href:'https://example.test/proxy/8097/'};
  const context = vm.createContext({document,location,history:{replaceState(...args){history.push(args);}},URLSearchParams,URL,Map,Set,Date,console,fetch:async(url,options)=>{calls.push({url:String(url),options});return fetchImpl?.(url,options) || {ok:true,status:200,json:async()=>options.method==='POST'?{結果:[{id:'node',状態:'OK',パス:'/bin/node',バージョン:'24.0.0'}]}:{項目:entries,結果:[],調査:{complete:true,sourceTargetFiles:3333,scannedSourceFiles:3333,commit:'8adbdb484cafe31e145c4fe362897d2af1077eb1'}}};}});
  vm.runInContext(fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8'),context);
  return {elements, calls, history, context, get:id=>document.getElementById(id)};
}
const tick = () => new Promise(resolve => setImmediate(resolve));
test('fragment removed, API is prefix-relative, probes require explicit click', async()=>{
 const f=fixture(); await tick(); assert.equal(f.history[0][2],'/proxy/8097/'); assert.equal(f.calls.length,1); assert.equal(f.calls[0].url,'https://example.test/proxy/8097/api/%E4%B8%80%E8%A6%A7'); assert.equal(f.calls[0].options.headers.Authorization,'Bearer test-token'); assert.equal(f.calls[0].options.credentials,'same-origin'); assert.equal(f.get('list').children.length,1); assert.equal(f.get('list').children[0].children[0].textContent,'インストール確認'); assert.equal(f.get('list').children[0].children.length,4); assert.equal(f.get('run').disabled,false); assert.match(f.get('coverage').textContent,/3,333/); assert.match(f.get('coverage').textContent,/除外/);
 await f.get('run').click(); assert.equal(f.calls[1].options.method,'POST'); assert.match(f.get('message').textContent,/インストール確認完了/); assert.equal(f.get('run').textContent,'再チェック');
});
test('search, state filter, selection detail use actual catalog and results',async()=>{
 const f=fixture();await tick(); f.get('search').value='ffmpeg';f.get('search').listeners.input();assert.equal(f.get('list').children.length,1);
 const group=f.get('list').children[0].children[1];await group.children[1].click();assert.equal(f.get('detail').children[1].textContent,'FFmpeg');
 f.get('search').value='no-match';f.get('search').listeners.input();assert.equal(f.get('empty').hidden,false);
 f.get('search').value=''; await f.get('run').click(); f.get('status').value='OK';f.get('status').listeners.change();assert.equal(f.get('list').children.length,1);assert.equal(f.get('list').children[0].children[1].children[1].children[0].textContent,'Node.js');
});
test('unauthorized API shows login and disables probing',async()=>{
 const f=fixture(()=>({ok:false,status:401,json:async()=>({エラー:'認証が必要です。'})}));await tick();assert.equal(f.get('login').hidden,false);assert.equal(f.get('run').disabled,true);assert.match(f.get('message').textContent,/認証/);
});

test('real inventory hierarchy, collapse, excluded helpers and state filter',async()=>{
 const catalog=JSON.parse(fs.readFileSync(path.join(__dirname,'../catalog.json'),'utf8'));
 const f=fixture((_url,options)=>({ok:true,status:200,json:async()=>options.method==='POST'?{結果:catalog.map(e=>({id:e.id,状態:e.usageTier==='optional'||e.usageTier==='reference'?'未検出':'OK'}))}:{項目:catalog,結果:[]}}));
 await tick();
 let section=f.get('list').children[0];
 assert.equal(section.children[0].textContent,'インストール確認');
 assert.deepEqual(section.children.slice(1).map(g=>g.children[0].textContent.split(' · ')[0]),['ベース','CLI群','その他拡張']);
 assert.deepEqual(section.children[1].children.slice(1).map(b=>b.children[0].textContent),['Python','uv','Node.js','npm','npx','Electron']);
 assert.equal(section.children[3].open,false);
 section.children[1].open=false;section.children[1].listeners.toggle();
 f.get('search').value='node';f.get('search').listeners.input();assert.equal(f.get('list').children[0].children[1].open,true);
 f.get('search').value='';f.get('search').listeners.input();assert.equal(f.get('list').children[0].children[1].open,false);
 f.get('search').value='';await f.get('run').click();
 assert.match(f.get('message').textContent,/OK 19/);
 assert.doesNotMatch(f.get('message').textContent,/任意・参照/);
 f.get('status').value='未検出';f.get('status').listeners.change();assert.equal(f.get('empty').hidden,false);
 assert.ok(catalog.every(e=>!['optional','reference'].includes(e.usageTier)));
 assert.ok(catalog.every(e=>!['git','pip','edge','brave','afplay','gst-launch'].includes(e.id)));

});

test('five indicator labels match list, detail, summary, filters and legend',async()=>{
 const states=['未確認','未検出','OK','NG','ERR'];
 const items=states.map((state,i)=>({id:String(i),name:`tool${i}`,commands:[],description:'',menuGroup:'ベース'}));
 const results=states.map((状態,i)=>({id:String(i),状態}));
 const f=fixture((_url,options)=>({ok:true,status:200,json:async()=>options.method==='POST'?{結果:results}:{項目:items,結果:results}}));await tick();
 for(let i=0;i<states.length;i++) {
  f.get('status').value=states[i];f.get('status').listeners.change();
  const button=f.get('list').children[0].children[1].children[1];
  assert.equal(button.children[1].attributes['data-state'],states[i]);await button.click();
  assert.equal(f.get('detail').children[2].attributes['data-state'],states[i]);assert.equal(f.get('detail').children[2].textContent,states[i]);
 }
 await f.get('run').click();assert.deepEqual(f.get('message').children.filter(e=>e.attributes['data-state']).map(e=>e.attributes['data-state']),states);
 const html=fs.readFileSync(path.join(__dirname,'../static/index.html'),'utf8');
 for(const state of states){assert.ok(html.includes(`<option>${state}</option>`));assert.ok(html.includes(`data-state="${state}"`));}
});
