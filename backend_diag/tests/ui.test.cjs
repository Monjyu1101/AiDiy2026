const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
class Element {
  constructor() { this.children = []; this.listeners = {}; this.value = ''; this.hidden = false; this.disabled = false; this.attributes = {}; this.classList = { toggle() {} }; }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = children; }
  addEventListener(type, handler) { this.listeners[type] = handler; }
  setAttribute(key, value) { this.attributes[key] = value; }
  async click() { if (!this.disabled) return this.listeners.click?.({}); }
}
const entries = [{id:'node',name:'Node.js',category:'基盤',commands:['node'],description:'runtime',required_by:['IDE'],sources:['_setup.py'],evidence:[{path:'_setup.py',line:3}]},{id:'ffmpeg',name:'FFmpeg',category:'メディア',commands:['ffmpeg'],description:'media',sources:['tools.py']}];
function fixture(fetchImpl) {
  const elements = new Map(); const calls = [], history = [];
  const document = {getElementById(id) { if (!elements.has(id)) elements.set(id, new Element()); return elements.get(id); },createElement() { return new Element(); }};
  const location = {hash:'#token=test-token',pathname:'/proxy/8097/',search:'',href:'https://example.test/proxy/8097/'};
  const context = vm.createContext({document,location,history:{replaceState(...args){history.push(args);}},URLSearchParams,URL,Map,Set,Date,console,fetch:async(url,options)=>{calls.push({url:String(url),options});return fetchImpl?.(url,options) || {ok:true,status:200,json:async()=>options.method==='POST'?{結果:[{id:'node',状態:'導入済み',パス:'/bin/node',バージョン:'24.0.0'}]}:{項目:entries,結果:[],調査:{complete:true,sourceTargetFiles:3333,scannedSourceFiles:3333,commit:'8adbdb484cafe31e145c4fe362897d2af1077eb1'}}};}});
  vm.runInContext(fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8'),context);
  return {elements, calls, history, context, get:id=>document.getElementById(id)};
}
const tick = () => new Promise(resolve => setImmediate(resolve));
test('fragment removed, API is prefix-relative, probes require explicit click', async()=>{
 const f=fixture(); await tick(); assert.equal(f.history[0][2],'/proxy/8097/'); assert.equal(f.calls.length,1); assert.equal(f.calls[0].url,'https://example.test/proxy/8097/api/%E4%B8%80%E8%A6%A7'); assert.equal(f.calls[0].options.headers.Authorization,'Bearer test-token'); assert.equal(f.calls[0].options.credentials,'same-origin'); assert.equal(f.get('list').children.length,2); assert.equal(f.get('run').disabled,false); assert.match(f.get('coverage').textContent,/3,333/); assert.match(f.get('coverage').textContent,/除外/);
 await f.get('run').click(); assert.equal(f.calls[1].options.method,'POST'); assert.match(f.get('message').textContent,/診断完了/); assert.equal(f.get('run').textContent,'再チェック');
});
test('search, state filter, selection detail use actual catalog and results',async()=>{
 const f=fixture();await tick(); f.get('search').value='ffmpeg';f.get('search').listeners.input();assert.equal(f.get('list').children.length,1);
 const group=f.get('list').children[0];await group.children[1].click();assert.equal(f.get('detail').children[1].textContent,'FFmpeg');
 f.get('search').value='no-match';f.get('search').listeners.input();assert.equal(f.get('empty').hidden,false);
 f.get('search').value=''; await f.get('run').click(); f.get('status').value='導入済み';f.get('status').listeners.change();assert.equal(f.get('list').children.length,1);assert.equal(f.get('list').children[0].children[1].children[0].textContent,'Node.js');
});
test('unauthorized API shows login and disables probing',async()=>{
 const f=fixture(()=>({ok:false,status:401,json:async()=>({エラー:'認証が必要です。'})}));await tick();assert.equal(f.get('login').hidden,false);assert.equal(f.get('run').disabled,true);assert.match(f.get('message').textContent,/認証/);
});
