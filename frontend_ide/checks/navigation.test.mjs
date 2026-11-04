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
import {createNavigation,validateNavigation,validateNavigationResponse,navigationModels,navigationCatalog,navigationDefaultModel} from '../ファイル機能/navigation.mjs';
const valid=(id='one',goal='検索画面を整える')=>({schemaVersion:2,requestId:id,goal,items:[{id:'1',name:'入力を整える',progress:25,reason:'入力欄が存在、検証は未確認',weight:100,weightReason:'目標を達成するための主要作業'}],overall:{progress:25,reason:'主要作業の確認結果から評価'},nextPrompt:'入力の空状態を確認してください。'});
test('結果: 根拠/0と100/空リストを保持し未知の属性を除外',()=>{
 const data=valid();data.items.push({...data.items[0],id:'2',progress:100});data.items[0].progress=0;data.items.forEach(item=>item.weight=50);data.overall.progress=50;data.secret='ignore';
 const {secret,...expected}=data;assert.deepEqual(validateNavigation(data,{id:'one',goal:data.goal}),{...expected,inferred:false});
 assert.equal(validateNavigation({...data,items:[],overall:{progress:0,reason:'項目がないため0%'}},{id:'one',goal:data.goal}).items.length,0);
});
for(const [name,change]of [
 ['版なし',d=>delete d.schemaVersion],['旧版',d=>d.schemaVersion=1],['未来版',d=>d.schemaVersion=3],['版文字列',d=>d.schemaVersion='2'],['版null',d=>d.schemaVersion=null],
 ['重みなし',d=>delete d.items[0].weight],['重みゼロ',d=>d.items[0].weight=0],['重み負値',d=>d.items[0].weight=-1],['重み上限超過',d=>d.items[0].weight=101],['重み小数',d=>d.items[0].weight=99.5],['重み文字列',d=>d.items[0].weight='100'],['重みNaN',d=>d.items[0].weight=NaN],['重みInfinity',d=>d.items[0].weight=Infinity],['重み合計不足',d=>d.items[0].weight=99],['重み合計超過',d=>d.items.push({...d.items[0],id:'2'})],
 ['重み根拠なし',d=>delete d.items[0].weightReason],['重み根拠空白',d=>d.items[0].weightReason='  '],['重み根拠長過ぎ',d=>d.items[0].weightReason='x'.repeat(2001)],
 ['総合なし',d=>delete d.overall],['総合進捗なし',d=>delete d.overall.progress],['総合不一致',d=>d.overall.progress=26],['総合未評価不一致',d=>d.overall.progress=null],['総合小数',d=>d.overall.progress=25.5],['総合文字列',d=>d.overall.progress='25'],['総合NaN',d=>d.overall.progress=NaN],['総合Infinity',d=>d.overall.progress=Infinity],['総合負値',d=>d.overall.progress=-1],['総合上限超過',d=>d.overall.progress=101],['総合根拠なし',d=>delete d.overall.reason],['総合根拠空白',d=>d.overall.reason='  '],['総合根拠長過ぎ',d=>d.overall.reason='x'.repeat(4001)],['達成度null',d=>d.items[0].progress=null],['達成度なし',d=>delete d.items[0].progress],['空項目と数値総合',d=>d.items=[]],
 ['別要求',d=>d.requestId='other'],['別目標',d=>d.goal='other'],['負値',d=>d.items[0].progress=-1],['上限超過',d=>d.items[0].progress=101],['文字列',d=>d.items[0].progress='50'],['NaN',d=>d.items[0].progress=NaN],['小数',d=>d.items[0].progress=2.5],['根拠なし',d=>d.items[0].reason=''],['ID重複',d=>d.items.push({...d.items[0]})],['巨大リスト',d=>d.items=Array(51).fill(d.items[0])],['プロンプトなし',d=>d.nextPrompt=''],
])test(`不正な結果を拒否: ${name}`,()=>{const d=valid(),job={id:d.requestId,goal:d.goal};change(d);assert.throws(()=>validateNavigation(d,job));});
async function fixture(t,run,options={}){
 const temporary=await mkdtemp(join(tmpdir(),'aidiy-navigation-')),root=join(temporary,'project'),stateRoot=join(temporary,'state');await mkdir(root);const state={active:true,mode:'online',startedAt:1};
 const service=createNavigation(root,{state:()=>state,stateRoot,defaultModel:async()=>({provider:'aidiy_hermes',model:'same'}),runAgent:args=>run(args,root),...options});
 t.after(async()=>{service.close();await rm(temporary,{recursive:true,force:true});});return{service,root,state,stateRoot};
}
async function respond(prompt,root,mutate=d=>d){const shape=JSON.parse(prompt.slice(prompt.lastIndexOf('\n')+1).replace(/^出力形式: /,''));return {content:JSON.stringify(mutate(valid(shape.requestId,shape.goal)))};}
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
 let calls=0;const {service}=await fixture(t,async({prompt})=>{calls++;const shape=JSON.parse(prompt.slice(prompt.lastIndexOf('\n')+1).replace(/^出力形式: /,''));const data=valid(shape.requestId,shape.goal);data.items[0].progress=75;data.overall.progress=75;if(calls===3)data.items[0].name='別の項目';return {content:JSON.stringify(data)};});
 await assert.rejects(service.start('', 'evaluate'));await service.start('目標');await finish(service);await service.start('無視する入力','evaluate');let value=await finish(service);assert.equal(value.job.status,'complete',value.job.message);assert.equal(value.result.goal,'目標');assert.equal(value.result.items[0].progress,75);await service.start('','evaluate');value=await finish(service);assert.equal(value.job.status,'failed');assert.equal(value.result.items[0].name,'入力を整える');
});
for(const action of ['add','remove','rename','id','reorder','goal'])test('評価の構造変更を拒否: '+action,()=>{
 const d=valid();d.items.push({...d.items[0],id:'2',name:'2番目'});d.items.forEach(item=>item.weight=50);const job={id:d.requestId,goal:d.goal,items:structuredClone(d.items),action:'evaluate'};
 if(action==='add')d.items.push({...d.items[0],id:'3'});if(action==='id')d.items[0].id='changed';if(action==='remove')d.items.pop();if(action==='rename')d.items[0].name='変更';if(action==='reorder')d.items.reverse();if(action==='goal')d.goal='変更';assert.throws(()=>validateNavigation(d,job));
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

test('加重総合は整数に丸め、未実施・未評価の0%を分母に含める',()=>{
 const d=valid();d.items[0].weight=35;d.items[0].progress=100;
 d.items.push({...d.items[0],id:'2',name:'残りの作業',weight:65,progress:10});d.overall.progress=42;
 let result=validateNavigation(d,{id:d.requestId,goal:d.goal});assert.equal(result.overall.progress,42);assert.equal(result.items[0].weight,35);assert.equal(result.schemaVersion,2);
 d.items[1].progress=0;d.items[1].reason='根拠不足で未評価のため0%';d.overall={progress:35,reason:'未確認の作業は0%として含める'};
 result=validateNavigation(d,{id:d.requestId,goal:d.goal});assert.equal(result.items[1].progress,0);assert.equal(result.overall.progress,35);
 d.items[0].progress=0;d.overall.progress=0;assert.equal(validateNavigation(d,{id:d.requestId,goal:d.goal}).overall.progress,0);
});

test('評価で工数比率・両根拠・総合評価を変更し、保存・再起動・履歴選択で保持する',async t=>{
 let calls=0;const {service,root,state,stateRoot}=await fixture(t,async({prompt})=>{
  calls++;const shape=JSON.parse(prompt.split('\n').at(-1).replace(/^出力形式: /,''));const d=valid(shape.requestId,shape.goal);
  d.items[0].progress=100;d.items[0].weight=calls===1?50:80;d.items[0].weightReason=calls===1?'初回の作業量':'調査後の主要作業量';
  d.items.push({...d.items[0],id:'2',name:'追加確認',progress:0,weight:calls===1?50:20,weightReason:'残りの作業量'});
  d.overall={progress:calls===1?50:80,reason:calls===1?'初回評価':'追加調査に基づく工数比率の再評価'};
  return {content:JSON.stringify(d)};
 });
 await service.start('目標');const first=(await finish(service)).result;
 await service.start('','evaluate');const updated=await finish(service);assert.equal(updated.job.status,'complete',updated.job.message);
 assert.deepEqual(updated.result.items.map(({id,name})=>({id,name})),first.items.map(({id,name})=>({id,name})));
 assert.deepEqual(updated.result.items.map(item=>item.weight),[80,20]);assert.equal(updated.result.overall.progress,80);assert.equal(updated.result.navigationId,first.navigationId);
 const reopened=createNavigation(root,{state:()=>state,stateRoot});t.after(()=>reopened.close());assert.deepEqual((await reopened.get()).result,updated.result);
 await reopened.fresh();await reopened.select(first.navigationId);assert.deepEqual((await reopened.get()).result,updated.result);
 assert.equal((await service.list()).length,1);
});

for(const mutation of ['old-schema','wrong-overall','wrong-weights','null-progress'])test('保存済み不正結果を修復せず拒否: '+mutation,async t=>{
 const {service,root,state,stateRoot}=await fixture(t,async({prompt},root)=>respond(prompt,root));
 await service.start('目標');const saved=(await finish(service)).result;
 const projectDir=join(stateRoot,(await readdir(stateRoot))[0]);const latest=join(projectDir,'default','latest.json');const history=join(projectDir,'history',saved.navigationId+'.json');
 const invalid=JSON.parse(await readFile(latest,'utf8'));
 if(mutation==='old-schema'){delete invalid.schemaVersion;delete invalid.overall;for(const item of invalid.items){delete item.weight;delete item.weightReason;}}
 if(mutation==='wrong-overall')invalid.overall.progress=99;
 if(mutation==='wrong-weights')invalid.items[0].weight=99;
 if(mutation==='null-progress'){invalid.items[0].progress=null;invalid.overall.progress=null;}
 const contents=JSON.stringify(invalid);await writeFile(latest,contents);await writeFile(history,contents);
 const reopened=createNavigation(root,{state:()=>state,stateRoot});t.after(()=>reopened.close());
 await assert.rejects(reopened.get());await assert.rejects(reopened.select(saved.navigationId));assert.deepEqual(await reopened.list(),[]);
 assert.equal(await readFile(latest,'utf8'),contents);assert.equal(await readFile(history,'utf8'),contents);
});


test('旧形式は新規作成を案内する明確なエラーにして自動移行しない',()=>{
 const d=valid();delete d.schemaVersion;
 assert.throws(()=>validateNavigation(d,{id:d.requestId,goal:d.goal}),/新規.*再作成/);
 assert.equal(d.schemaVersion,undefined);
});

test('AI指示の出力例も加重評価schemaVersion 2の検証を通る',async t=>{
 const prompts=[];const {service}=await fixture(t,async({prompt})=>{
  prompts.push(prompt);const example=JSON.parse(prompt.split('\n').at(-1).replace(/^出力形式: /,''));
  validateNavigation(example,{id:example.requestId,goal:example.goal});return {content:JSON.stringify(example)};
 });
 await service.start('検証目標');assert.equal((await finish(service)).job.status,'complete');
 await service.start('','evaluate');assert.equal((await finish(service)).job.status,'complete');
 assert.equal(prompts.length,2);for(const prompt of prompts){assert.match(prompt,/weightReason/);assert.match(prompt,/overall/);assert.match(prompt,/schemaVersion/);assert.match(prompt,/未実施・未評価.*0%/);assert.match(prompt,/項目なしなら0/);assert.doesNotMatch(prompt,/場合はnull|ならnull/);}
});


for(const [progress,overall,expected] of [[null,null,0],[0,null,0],[25,null,25],[100,null,100],[null,0,0]])test(`今回のAI応答の未評価を数値化: ${progress}/${overall}`,()=>{
 const d=valid();d.items[0].progress=progress;d.overall.progress=overall;const before=structuredClone(d);
 const result=validateNavigationResponse(d,{id:d.requestId,goal:d.goal});
 assert.equal(result.items[0].progress,progress===null?0:progress);assert.equal(result.overall.progress,expected);assert.deepEqual(d,before);
});
test('今回のAI応答の空項目・混合未評価も全体工数の加重数値にする',()=>{
 const d=valid();d.items[0].weight=35;d.items[0].progress=100;d.items.push({...d.items[0],id:'2',weight:65,progress:null});d.overall.progress=null;
 const result=validateNavigationResponse(d,{id:d.requestId,goal:d.goal});assert.equal(result.overall.progress,35);assert.equal(result.items[1].progress,0);assert.match(result.overall.reason,/数値化/);
 d.items=[];assert.equal(validateNavigationResponse(d,{id:d.requestId,goal:d.goal}).overall.progress,0);
});
for(const [name,mutate] of [
 ['旧形式',d=>delete d.schemaVersion],['項目率欠損',d=>delete d.items[0].progress],['総合率欠損',d=>delete d.overall.progress],['総合欠損',d=>delete d.overall],['率文字列',d=>d.items[0].progress='未評価'],['率範囲外',d=>d.items[0].progress=101],['比率欠損',d=>delete d.items[0].weight],['比率不足',d=>d.items[0].weight=50],['項目根拠欠損',d=>delete d.items[0].reason],['総合根拠欠損',d=>delete d.overall.reason],['不整合な数値総合',d=>d.overall.progress=99]
])test('未評価0%処理でも壊れたAI応答を成功にしない: '+name,()=>{
 const d=valid();d.items[0].progress=null;d.overall.progress=null;mutate(d);assert.throws(()=>validateNavigationResponse(d,{id:d.requestId,goal:d.goal}));
});
test('長さ上限の根拠は切り捨てず保持して数値化する',()=>{
 const d=valid();d.items[0].progress=null;d.overall.progress=null;d.items[0].reason='x'.repeat(2000);d.overall.reason='y'.repeat(4000);
 const result=validateNavigationResponse(d,{id:d.requestId,goal:d.goal});assert.equal(result.items[0].reason,d.items[0].reason);assert.equal(result.overall.reason,d.overall.reason);assert.equal(result.overall.progress,0);
});
test('現行AIのnull回答を数値で保存・再評価・再起動・履歴復元し、失敗時は前回数値を保つ',async t=>{
 let calls=0;const {service,root,state,stateRoot}=await fixture(t,async({prompt},root)=>{
  calls++;if(calls===3)throw Error('AIとの通信失敗');
  return respond(prompt,root,d=>{d.items[0].weight=35;d.items[0].progress=100;d.items.push({...d.items[0],id:'2',weight:65,progress:calls===1?null:0});d.overall.progress=null;return d;});
 });
 await service.start('目標');let value=await finish(service);assert.equal(value.job.status,'complete',value.job.message);assert.equal(value.result.overall.progress,35);assert.equal(value.result.items[1].progress,0);
 await service.start('','evaluate');value=await finish(service);assert.equal(value.job.status,'complete',value.job.message);assert.equal(value.result.overall.progress,35);
 const saved=value.result;await service.start('','evaluate');value=await finish(service);assert.equal(value.job.status,'failed');assert.match(value.job.message,/通信失敗/);assert.deepEqual(value.result,saved);
 const reopened=createNavigation(root,{state:()=>state,stateRoot});t.after(()=>reopened.close());assert.deepEqual((await reopened.get()).result,saved);await reopened.fresh();await reopened.select(saved.navigationId);assert.deepEqual((await reopened.get()).result,saved);
});
test('初回AI通信失敗は0%の成功結果を捏造しない',async t=>{
 const {service}=await fixture(t,async()=>{throw Error('通信エラー');});await service.start('目標');const value=await finish(service);assert.equal(value.job.status,'failed');assert.equal(value.result,null);
});
