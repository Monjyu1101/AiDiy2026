import {DEFAULT_NAVIGATION_GOAL} from '../src/components/開発スペース/Navigation既定値.js';
// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,writeFile,readFile,rm,mkdir,readdir} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createNavigation,validateNavigation,navigationModels,navigationCatalog,navigationDefaultModel} from '../ファイル機能/navigation.mjs';
const valid=(id='one',goal='検索画面を整える')=>({requestId:id,goal,items:[{id:'1',name:'入力を整える',progress:25,reason:'入力欄が存在、検証は未確認'}],nextPrompt:'入力の空状態を確認してください。'});
test('結果: 根拠/0と100/空リストを保持し未知の属性を除外',()=>{
 const data=valid();data.items.push({...data.items[0],id:'2',progress:100});data.items[0].progress=0;data.secret='ignore';
 const {secret,...expected}=data;assert.deepEqual(validateNavigation(data,{id:'one',goal:data.goal}),{...expected,inferred:false});
 assert.equal(validateNavigation({...data,items:[]},{id:'one',goal:data.goal}).items.length,0);
});
for(const [name,change]of [
 ['別要求',d=>d.requestId='other'],['別目標',d=>d.goal='other'],['負値',d=>d.items[0].progress=-1],['上限超過',d=>d.items[0].progress=101],['文字列',d=>d.items[0].progress='50'],['NaN',d=>d.items[0].progress=NaN],['小数',d=>d.items[0].progress=2.5],['根拠なし',d=>d.items[0].reason=''],['ID重複',d=>d.items.push({...d.items[0]})],['巨大リスト',d=>d.items=Array(51).fill(d.items[0])],['プロンプトなし',d=>d.nextPrompt=''],
])test(`不正な結果を拒否: ${name}`,()=>{const d=valid(),job={id:d.requestId,goal:d.goal};change(d);assert.throws(()=>validateNavigation(d,job));});
async function fixture(t,run,options={}){
 const temporary=await mkdtemp(join(tmpdir(),'aidiy-navigation-')),root=join(temporary,'project'),stateRoot=join(temporary,'state');await mkdir(root);const state={active:true,mode:'online',startedAt:1};
 const service=createNavigation(root,{state:()=>state,stateRoot,defaultModel:async()=>({provider:'aidiy_hermes',model:'same'}),runAgent:args=>run(args,root),...options});
 t.after(async()=>{service.close();await rm(temporary,{recursive:true,force:true});});return{service,root,state,stateRoot};
}
async function respond(prompt,root,mutate=d=>d){const shape=JSON.parse(prompt.slice(prompt.lastIndexOf('\n')+1));return {content:JSON.stringify(mutate(valid(shape.requestId,shape.goal)))};}
async function finish(service){for(let n=0;n<100;n++){const v=await service.get();if(v.job?.status!=='running')return v;await new Promise(r=>setTimeout(r,5));}throw Error('test timeout');}
test('通常経路1回→JSON保存→再起動読戻し、失敗時に前回成功を保持',async t=>{
 let calls=0;const {service,root,state,stateRoot}=await fixture(t,async({prompt},root)=>{calls++;return respond(prompt,root,d=>calls===1?d:{...d,items:[{...d.items[0],progress:999}]});});
 await service.start('検索画面を整える');assert.equal((await finish(service)).job.status,'complete');
 await service.start('次の目標');const failed=await finish(service);assert.equal(failed.job.status,'failed');assert.equal(failed.result.goal,'検索画面を整える');assert.equal(calls,2);
 const second=createNavigation(root,{state:()=>state,stateRoot});assert.equal((await second.get()).result.items[0].progress,25);second.close();assert.deepEqual(await readdir(root),[]);
});
test('空入力・オフラインを送信前に拒否',async t=>{let calls=0;const {service,state}=await fixture(t,()=>calls++);await assert.rejects(service.start('x'.repeat(4001)));state.mode='offline';await assert.rejects(service.start('test'));assert.equal(calls,0);});
test('連打でも1回、セッション変更後の結果を保存しない',async t=>{
 let release,calls=0;const {service,root,state}=await fixture(t,async({prompt},root)=>{calls++;await new Promise(r=>release=r);return respond(prompt,root);});
 const first=service.start('test');await assert.rejects(service.start('duplicate'));await first;await assert.rejects(service.start('duplicate'));state.startedAt=2;release();await new Promise(r=>setTimeout(r,30));assert.equal((await service.get()).result,null);assert.equal(calls,1);
});
test('期限でabortし失敗表示、完了済みにはしない',async t=>{let signal;const {service}=await fixture(t,args=>{signal=args.signal;return new Promise(()=>{});},{waitMs:15});await service.start('test');const result=await finish(service);assert.equal(result.job.status,'failed');assert.equal(signal.aborted,true);assert.equal(result.result,null);});
test('終了で処理をabort、追加開始不可',async t=>{let signal;const {service}=await fixture(t,args=>{signal=args.signal;return new Promise(()=>{});},{waitMs:20});await service.start('test');service.close();assert.equal(signal.aborted,true);await assert.rejects(service.start('test'));});

test('既定指示は最近の日時と内容から仮目標を提案、GETではAIを呼ばない',async t=>{
 let calls=0,prompt='';const {service}=await fixture(t,async args=>{calls++;prompt=args.prompt;const shape=JSON.parse(prompt.slice(prompt.lastIndexOf('\n')+1));return {content:JSON.stringify(valid(shape.requestId,'仮の目標'))};});
 await service.get();assert.equal(calls,0);await assert.rejects(service.start(''),/開発目標/);assert.equal(calls,0);await service.start(DEFAULT_NAVIGATION_GOAL);const result=await finish(service);assert.equal(result.result.inferred,true);assert.equal(result.result.goal,'仮の目標');assert.match(prompt,/日時だけで達成を断定せず/);assert.equal(calls,1);
});

test('評価は保存済み目標と項目を固定し採点のみ更新、削除・改名を拒否',async t=>{
 let calls=0;const {service}=await fixture(t,async({prompt})=>{calls++;const shape=JSON.parse(prompt.slice(prompt.lastIndexOf('\n')+1).replace(/^出力形式: /,''));const data=valid(shape.requestId,shape.goal);data.items[0].progress=75;if(calls===3)data.items[0].name='別の項目';return {content:JSON.stringify(data)};});
 await assert.rejects(service.start('', 'evaluate'));await service.start('目標');await finish(service);await service.start('無視する入力','evaluate');let value=await finish(service);assert.equal(value.job.status,'complete',value.job.message);assert.equal(value.result.goal,'目標');assert.equal(value.result.items[0].progress,75);await service.start('','evaluate');value=await finish(service);assert.equal(value.job.status,'failed');assert.equal(value.result.items[0].name,'入力を整える');
});
for(const action of ['remove','rename','reorder','goal'])test('評価の構造変更を拒否: '+action,()=>{
 const d=valid();d.items.push({...d.items[0],id:'2',name:'2番目'});const job={id:d.requestId,goal:d.goal,items:structuredClone(d.items),action:'evaluate'};
 if(action==='remove')d.items.pop();if(action==='rename')d.items[0].name='変更';if(action==='reorder')d.items.reverse();if(action==='goal')d.goal='変更';assert.throws(()=>validateNavigation(d,job));
});

test('モデル初期値と保存/再読込、ナビと評価は同じ選択を固定して使用',async t=>{
 const selections=[];const {service,root,state,stateRoot}=await fixture(t,async args=>{selections.push(args.selection);const shape=JSON.parse(args.prompt.slice(args.prompt.lastIndexOf('\n')+1).replace(/^出力形式: /,''));return {content:JSON.stringify(valid(shape.requestId,shape.goal))};});
 assert.deepEqual((await service.get()).selection,{provider:'aidiy_hermes',model:'same'});
 await service.saveModel({provider:'codex_cli',model:'model-fixture'});
 const other=createNavigation(root,{state:()=>state,stateRoot});assert.deepEqual((await other.get()).selection,{provider:'codex_cli',model:'model-fixture'});other.close();
 await service.start('目標');await finish(service);await service.start('','evaluate');await finish(service);assert.deepEqual(selections,[{provider:'codex_cli',model:'model-fixture'},{provider:'codex_cli',model:'model-fixture'}]);
 await assert.rejects(service.saveModel({provider:'claude_cli',model:'same'}));assert.deepEqual((await service.get()).selection,{provider:'codex_cli',model:'model-fixture'});
});
test('実行中のモデル保存拒否、現在の処理へ途中反映しない',async t=>{
 let release;const {service}=await fixture(t,()=>new Promise(r=>release=r));await service.start('目標');await assert.rejects(service.saveModel({provider:'codex_cli',model:'same'}));release({content:'invalid'});await finish(service);
});

test('複数Naviの同時実行・モデル・結果・評価・終了が独立する',async t=>{
 const pending=[];const {service:a,root,state,stateRoot}=await fixture(t,args=>new Promise(resolve=>pending.push({args,resolve})),{instance:'navi-1'});
 const b=createNavigation(root,{state:()=>state,stateRoot,instance:'navi-2',runAgent:args=>new Promise(resolve=>pending.push({args,resolve}))});t.after(()=>b.close());
 await a.saveModel({provider:'codex_cli',model:'model-A'});await b.saveModel({provider:'aidiy_hermes',model:'model-B'});
 await a.start('目標A');await b.start('目標B');assert.equal(pending.length,2);
 assert.equal(pending[0].args.selection.model,'model-A');assert.equal(pending[1].args.selection.model,'model-B');
 for(const entry of pending){const shape=JSON.parse(entry.args.prompt.split('\n').at(-1));entry.resolve({content:JSON.stringify(valid(shape.requestId,shape.goal))});}
 await finish(a);await finish(b);assert.equal((await a.get()).result.goal,'目標A');assert.equal((await b.get()).result.goal,'目標B');
 await a.start('','evaluate');assert.equal((await b.get()).job.status,'complete');a.close();assert.equal(pending[2].args.signal.aborted,true);assert.equal((await b.get()).result.goal,'目標B');
 const reopened=createNavigation(root,{state:()=>state,stateRoot,instance:'navi-2'});t.after(()=>reopened.close());assert.equal((await reopened.get()).selection.model,'model-B');assert.equal((await reopened.get()).result.goal,'目標B');
});

test('Navigation履歴: 新規/一覧/選択/評価と別窓・別プロジェクトの分離',async t=>{
 let calls=0;const {service,root,state,stateRoot}=await fixture(t,async({prompt},root)=>{calls++;return respond(prompt,root);});
 await service.start('目標A');const first=(await finish(service)).result;
 await service.fresh();assert.equal((await service.get()).result,null);assert.equal((await service.list()).length,1);
 await service.start('目標B');await finish(service);assert.equal((await service.list()).length,2);
 await service.select(first.navigationId);assert.equal((await service.get()).result.goal,'目標A');
 await service.start('', 'evaluate');const evaluated=(await finish(service)).result;
 assert.equal(evaluated.navigationId,first.navigationId);assert.deepEqual(evaluated.items,first.items);assert.equal((await service.list()).length,2);
 const peer=createNavigation(root,{state:()=>state,stateRoot,instance:'navi-2'});t.after(()=>peer.close());
 assert.equal((await peer.list()).length,2);assert.equal((await peer.get()).result,null);await peer.select(first.navigationId);await peer.fresh();assert.equal((await service.get()).result.goal,'目標A');
 const otherRoot=join(root,'other');await mkdir(otherRoot);const other=createNavigation(otherRoot,{state:()=>state,stateRoot});t.after(()=>other.close());
 assert.deepEqual(await other.list(),[]);await assert.rejects(other.select(first.navigationId));await assert.rejects(service.select('../other'));
 assert.equal(calls,3);assert.deepEqual(await readdir(root),['other']);
});

test('モデル候補はCode共通資料の公開ラベルだけ、非対応CLIを除外',async t=>{
 const root=await mkdtemp(join(tmpdir(),'navi-catalog-'));t.after(()=>rm(root,{recursive:true,force:true}));const file=join(root,'catalog.json');
 await writeFile(file,JSON.stringify({_meta:{schema:1,readOnly:true},secret:'must not return',aidiy_hermes:{models:{'openai_oauth/test':'OpenAI test','codex_cli/test':'unsupported'}}}));
 const items=await navigationModels('aidiy_hermes',file);assert.ok(items.some(item=>item.id==='openai_oauth/test'));assert.ok(!items.some(item=>item.id==='codex_cli/test'));assert.ok(!JSON.stringify(items).includes('must not return'));await assert.rejects(navigationModels('other',file));
});

test('依存停止でも履歴閲覧可能、実行は拒否し復帰後に再開できる',async t=>{
 let available=true,calls=0;const {service}=await fixture(t,async({prompt},root)=>{calls++;return respond(prompt,root);},{availability:async()=>({available,reason:available?'':'試験依存が停止しています'})});
 await service.start('test');const previous=(await finish(service)).result;
 available=false;const stopped=await service.get();assert.equal(stopped.availability.available,false);assert.deepEqual(stopped.result,previous);assert.equal((await service.list()).length,1);
 await assert.rejects(service.start('test'),/試験依存/);await assert.rejects(service.start('','evaluate'),/試験依存/);assert.equal(calls,1);
 available=true;assert.equal((await service.get()).availability.available,true);await service.start('test');assert.equal((await finish(service)).job.status,'complete');assert.equal(calls,2);
});

test('Code Hermes既定値と保存選択の優先順位',async t=>{
 const f=await fixture(t,respond,{defaultModel:async()=>({provider:'aidiy_hermes',model:'openai_oauth/test-default'})});
 assert.equal((await f.service.get()).selection.model,'openai_oauth/test-default');
 await f.service.saveModel({provider:'aidiy_hermes',model:'same'});
 assert.equal((await f.service.get()).selection.model,'same');
 const file=join(f.root,'config.json');
 await writeFile(file,JSON.stringify({CODE_AIDIY_HERMES_MODEL:'openai_oauth/config-model',secret:'not-returned'}));
 assert.deepEqual(await navigationDefaultModel(file),{provider:'aidiy_hermes',model:'openai_oauth/config-model'});
 await writeFile(file,JSON.stringify({CODE_AIDIY_HERMES_MODEL:'auto'}));
 assert.equal((await navigationDefaultModel(file)).model,'auto');
 assert.equal((await navigationDefaultModel(join(f.root,'missing.json'))).model,'auto');
 await writeFile(file,JSON.stringify({CODE_AIDIY_HERMES_MODEL:'bad\nmodel'}));
 assert.equal((await navigationDefaultModel(file)).model,'auto');
});

test('Navi専用一覧の欠損・旧形式・破損は安全な基本候補と案内、危険経路を表示しない',async t=>{
 const root=await mkdtemp(join(tmpdir(),'navi-info-'));t.after(()=>rm(root,{recursive:true,force:true}));const file=join(root,'navi_models_info.json');
 for(const contents of [null,'{broken',JSON.stringify({aidiy_hermes:{models:{unsafe:'old'}}})]){
  if(contents!==null)await writeFile(file,contents);
  const c=await navigationCatalog('aidiy_hermes',file);assert.deepEqual(c.items.map(x=>x.id),['same','auto']);assert.ok(c.notice);
 }
 await writeFile(file,JSON.stringify({_meta:{schema:1,readOnly:true},aidiy_hermes:{models:{'copilot-cli/same':'unsafe','openai_oauth/x':'safe'}},copilot_cli:{models:{'claude-sonnet':'Claude'}}}));
 const c=await navigationCatalog('aidiy_hermes',file);assert.equal(c.notice,'');assert.ok(c.items.some(x=>x.id==='openai_oauth/x'));assert.ok(!c.items.some(x=>x.id==='copilot-cli/same'));
 assert.ok((await navigationModels('copilot_cli',file)).some(x=>x.id==='claude-sonnet'));
});
