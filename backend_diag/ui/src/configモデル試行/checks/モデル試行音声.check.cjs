const test=require('node:test');const assert=require('node:assert/strict');
const {render,source}=require('../../../../checks/ui-components.cjs');
const id='a'.repeat(32),result={状態:'OK',音声ファイル:{id,MIME:'audio/wav',長さms:1200,サイズ:100}};
const deferred=()=>{let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b});return {promise,resolve,reject};};

test('Liveの1秒以上の音声だけ手動ロード・ネイティブ再生を表示し、自動再生しない',async()=>{
 const props={data:{項目:[{id:'LIVE',区分:'LIVE'}]},results:{LIVE:result},selected:'LIVE',online:true,visible:true};
 let html=await render('configモデル試行/モデル試行パネル.vue',props);assert.match(html,/1\.20 秒/);assert.match(html,/音声を読み込む/);assert.doesNotMatch(html,/<audio/);
 html=await render('configモデル試行/モデル試行パネル.vue',{...props,audioStates:{[id]:{url:'blob:synthetic'}}});assert.match(html,/<audio[^>]*controls[^>]*preload="none"/);assert.doesNotMatch(html,/autoplay|Bearer|token=/);
 html=await render('configモデル試行/モデル試行パネル.vue',{...props,visible:false,audioStates:{[id]:{url:'blob:synthetic'}}});assert.doesNotMatch(html,/<audio/);
 for(const row of ['CHAT','LIVE']){html=await render('configモデル試行/モデル試行パネル.vue',{...props,data:{項目:[{id:row}]},selected:row,results:{[row]:{音声ファイル:{...result.音声ファイル,長さms:999}}}});assert.doesNotMatch(html,/音声を読み込む/);}
});

test('音声は認証APIで一度取得して共有し、破棄時にURLを解放',async()=>{
 const {モデル試行音声を作成}=await import('../モデル試行音声.mjs');const calls=[],revoked=[];
 const state=モデル試行音声を作成({api:async(...args)=>{calls.push(args);return new Blob([new Uint8Array(100)],{type:'audio/wav'});},接続可能:()=>true,createURL:()=> 'blob:test',revokeURL:url=>revoked.push(url)});
 await state.読込(result);await state.読込({...result,共有元:'LIVE'});assert.equal(calls.length,1);assert.equal(calls[0][0],`api/モデル試行/音声/${id}`);assert.equal(calls[0][3],'blob');assert.equal(state.音声状態.value[id].url,'blob:test');state.破棄();assert.deepEqual(revoked,['blob:test']);assert.deepEqual(state.音声状態.value,{});
});

test('切断・破棄・古い応答は音声URLを作らず、未設定や短い音声も取得しない',async()=>{
 const {モデル試行音声を作成}=await import('../モデル試行音声.mjs');const pending=deferred();let online=true,created=0,calls=0,signal;
 const state=モデル試行音声を作成({api:(_p,_m,s)=>{calls++;signal=s;return pending.promise;},接続可能:()=>online,createURL:()=>{created++;return 'blob:bad';},revokeURL:()=>{}});
 await state.読込({});await state.読込({音声ファイル:{...result.音声ファイル,長さms:999}});assert.equal(calls,0);const load=state.読込(result);await state.読込(result);assert.equal(calls,1);online=false;state.破棄();assert.equal(signal.aborted,true);pending.resolve(new Blob([new Uint8Array(100)],{type:'audio/wav'}));await load;assert.equal(created,0);assert.deepEqual(state.音声状態.value,{});await state.読込(result);assert.equal(calls,1);
});

test('期限切れ・認証エラー・不正音声は秘密や生エラーを表示せず再試行できる',async()=>{
 const {モデル試行音声を作成}=await import('../モデル試行音声.mjs');let attempts=0;const revoked=[];
 const state=モデル試行音声を作成({api:async()=>{if(++attempts===1)throw new Error('401 secret-token');if(attempts===2)return new Blob(['bad'],{type:'text/html'});return new Blob([new Uint8Array(100)],{type:'audio/wav'});},接続可能:()=>true,createURL:()=> 'blob:test',revokeURL:url=>revoked.push(url)});
 await state.読込(result);assert.match(state.音声状態.value[id].エラー,/取得できません/);assert.doesNotMatch(JSON.stringify(state.音声状態.value),/secret-token|401/);await state.読込(result);assert.ok(!state.音声状態.value[id].url);await state.読込(result);state.再生失敗(id);assert.deepEqual(revoked,['blob:test']);assert.match(state.音声状態.value[id].エラー,/再生できません/);
});

test('共通APIは音声にもBearerヘッダーを使い、キャンセルと終了で解放する',()=>{
 assert.match(source('App.vue'),/response.ok && format==='blob'/);assert.match(source('App.vue'),/headers:\{Authorization:`Bearer/);const state=source('configモデル試行/モデル試行状態.mjs');assert.match(state,/音声.破棄\(\);\+\+世代/);assert.match(state,/function 終了\(\)\{中止\(\)/);
});
