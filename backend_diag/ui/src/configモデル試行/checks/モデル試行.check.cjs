const test=require('node:test');
const assert=require('node:assert/strict');
const {render,source}=require('../../../../checks/ui-components.cjs');
const ids=['CHAT','LIVE',...Array.from({length:6},(_,i)=>`CODE${i+1}`),'TASK_plan','TASK_do','TASK_check','TEAM_plan','TEAM_do','TEAM_check'];
const snapshot={版:'v1',項目:ids.map(id=>({id,区分:id,役割:'',プロバイダ:'synthetic',モデル:'model-a',状態:'未実行'}))};
const tick=()=>new Promise(resolve=>setImmediate(resolve));
const deferred=()=>{let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b});return {promise,resolve,reject};};
async function setup(api){const {モデル試行状態を作成}=await import('../モデル試行状態.mjs');let online=true;return {state:モデル試行状態を作成({api,接続可能:()=>online}),offline:()=>{online=false;}};}

test('14行と共有元・経路・応答を描画し、未設定は成功にしない',async()=>{
 const data=structuredClone(snapshot);data.項目[0].状態='未設定';
 const html=await render('configモデル試行/モデル試行パネル.vue',{data,results:{LIVE:{状態:'OK',共有元:'CHAT',応答:'<script>bad</script>'}},selected:'LIVE',online:true});
 assert.equal((html.match(/class="trial-row(?: selected)?"/g)||[]).length,14);
 for(const id of ids)assert.ok(html.includes(id));
 assert.match(html,/未設定/);assert.match(html,/共有元/);assert.match(html,/Tools 内部 HTTP/);assert.match(html,/&lt;script&gt;/);assert.doesNotMatch(html,/<script>bad/);
 const empty=await render('configモデル試行/モデル試行パネル.vue',{data:{項目:[]},online:false});
 assert.match(empty,/設定項目がありません/);assert.match(empty,/id="model-trial-start" disabled/);assert.match(empty,/Tools 接続時/);
});

test('読込はGETのみ・手動開始後は厳密な順番で14行、共有はサーバー結果だけを使用',async()=>{
 const calls=[];let active=0;
 const {state}=await setup(async(path,method)=>{calls.push([path,method]);if(method==='GET')return snapshot;if(path.endsWith('/開始'))return {...snapshot,実行ID:'r1'};if(method==='DELETE')return {};assert.equal(++active,1);await tick();active--;const id=path.split('/').pop();return {id,状態:id==='CHAT'?'NG':'OK',共有元:id==='CODE2'?'CODE1':''};});
 assert.deepEqual(calls,[]);await state.読込();assert.deepEqual(calls,[['api/モデル試行','GET']]);
 const first=state.開始();await state.開始();await first;
 assert.deepEqual(calls.filter(x=>x[1]==='POST').map(x=>x[0].split('/').pop()),['開始',...ids]);
 assert.equal(state.結果.value.CHAT.状態,'NG');assert.equal(state.結果.value.CODE2.共有元,'CODE1');assert.equal(state.実行中.value,false);
});

test('中止は実行を止め、遅い応答を捨てて再開始を汚染しない',async()=>{
 const pending=deferred(),calls=[];let count=0;
 const {state}=await setup(async(path,method)=>{calls.push([path,method]);if(method==='GET')return snapshot;if(path.endsWith('/開始'))return {...snapshot,実行ID:`r${++count}`};if(method==='DELETE')return {};if(path.includes('/r1/'))return pending.promise;return {状態:'OK'};});
 await state.読込();const run=state.開始();await tick();state.中止();assert.equal(state.結果.value.CHAT.状態,'中止');
 await state.開始();pending.resolve({状態:'NG'});await run;
 assert.equal(state.結果.value.CHAT.状態,'OK');assert.ok(calls.some(x=>x[0]==='api/モデル試行/r1'&&x[1]==='DELETE'));assert.equal(calls.filter(x=>x[0].includes('/r1/')).length,1);
});

test('切断中の開始応答と再読込前の古い設定応答を無視する',async()=>{
 const start=deferred(),old=deferred(),calls=[];let reads=0;
 const {state,offline}=await setup(async(path,method)=>{calls.push([path,method]);if(method==='GET')return ++reads===1?snapshot:old.promise;if(path.endsWith('/開始'))return start.promise;return {};});
 await state.読込();const run=state.開始();offline();state.切断();start.resolve({...snapshot,実行ID:'late'});await run;
 assert.equal(state.設定.value,null);assert.deepEqual(state.結果.value,{});assert.ok(calls.some(x=>x[0].endsWith('/late')&&x[1]==='DELETE'));
 await state.開始();assert.equal(calls.filter(x=>x[0].endsWith('/開始')).length,1);
 const second=await setup(()=>old.promise);const read=second.state.読込();second.state.終了();old.resolve(snapshot);await read;assert.equal(second.state.設定.value,null);
});

test('設定変更エラーで残りを送らず、更新で前の結果を破棄する',async()=>{
 const calls=[];const {state}=await setup(async(path,method)=>{calls.push(path);if(method==='GET')return snapshot;if(path.endsWith('/開始'))return {...snapshot,実行ID:'r'};if(method==='DELETE')return {};throw new Error('設定が変更されました。再読込してください。');});
 await state.読込();await state.開始();assert.equal(state.結果.value.CHAT.状態,'ERR');assert.ok(!calls.some(x=>x.endsWith('/LIVE')));assert.match(state.通知.value,/設定が変更/);await state.読込();assert.deepEqual(state.結果.value,{});
});

test('Appは接続でタブを制御し、全診断へ試行を含めない',()=>{
 const app=source('App.vue');assert.match(app,/:disabled="!connected \|\| !toolsOnline"/);assert.match(app,/if\(!value\)試行.切断\(\)/);assert.doesNotMatch(app.match(/async function 全診断\(\).*\n/)[0],/試行/);
});

test('Tools再確認中は接続を保持し、失敗確定時だけオフライン',async()=>{
 const {Tools接続を作成}=await import('../../ウィンドウ/Tools接続.mjs');const states=[],pending=deferred();let n=0;
 const tools=Tools接続を作成({api:()=>++n===1?Promise.resolve({online:true}):pending.promise,反映:s=>states.push(s),setTimer:()=>0,clearTimer(){}});
 tools.接続(true);await tick();const check=tools.refresh();assert.deepEqual(states.at(-1),{online:true,checking:true});pending.reject(new Error('offline'));await check;assert.deepEqual(states.at(-1),{online:false,checking:false});tools.終了();
});
