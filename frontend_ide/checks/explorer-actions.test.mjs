// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
import test from 'node:test';
import assert from 'node:assert/strict';
import { createExplorerActions, explorerNameError, parentPath, containsPath, renamedPath } from '../src/ファイル閲覧/エクスプローラー操作.js';
const file={path:'docs/sample.txt',name:'sample.txt',type:'file'},folder={path:'docs',name:'docs',type:'dir'};
function fixture(){
  const requests=[],changes=[],copied=[];let response,resolve,pending=false,root='/project';
  const document={defaultView:{navigator:{clipboard:{writeText:async text=>copied.push(text)}}},querySelector:()=>null};
  const actions=createExplorerActions({root:()=>root,document:()=>document,changed:async result=>changes.push(result),request:async(url,options)=>{
    requests.push({url,options,payload:JSON.parse(options.body)});if(pending)await new Promise(done=>{resolve=done;});
    return response||new Response(JSON.stringify({action:JSON.parse(options.body).action,path:'docs/new.txt',previousPath:file.path,type:'file',name:'new.txt'}));
  }});
  return{actions,state:actions.state,requests,changes,copied,root:value=>{root=value;},response:value=>{response=value;},pending:value=>{pending=value;},resolve:()=>resolve()};
}
test('Explorer名前: Windows予約名・区切り・制御文字を拒否し、日本語名を維持',()=>{
  for(const name of ['', ' ','.','..','../bad','a/b','a\\b','a:b','foo.','foo ','a\0b','CON','nul.txt','LPT1.md','x'.repeat(256)])assert.ok(explorerNameError(name),name);
  for(const name of ['日本語 資料.txt','.gitignore','CONTEXT.md','report (2).txt'])assert.equal(explorerNameError(name),'');
  assert.equal(parentPath('hello.txt'),'');assert.equal(parentPath(file.path),'docs');assert.equal(containsPath('doc','docs/file'),false);assert.equal(containsPath('docs','docs/a'),true);
  assert.equal(renamedPath('docs/a','docs','new'),'new/a');assert.equal(renamedPath('docstring','docs','new'),'docstring');
});
test('Explorerコピー: IDE内clipboard、ルート背景貼付け・複製・パスコピー',async()=>{
  const f=fixture();await f.actions.action('paste',folder);assert.equal(f.requests.length,0);
  await f.actions.action('copy',file);assert.equal(f.requests.length,0);
  await f.actions.action('paste');assert.deepEqual(f.requests[0].payload,{action:'copy',path:file.path,directory:''});assert.equal(f.requests[0].options.headers['X-AiDiy-Explorer'],'1');
  await f.actions.action('duplicate',file);assert.equal(f.requests[1].payload.directory,'docs');
  await f.actions.action('copy-path',file);await f.actions.action('copy-relative',file);await f.actions.action('copy-path');await f.actions.action('copy-relative');assert.deepEqual(f.copied,['/project/docs/sample.txt','docs/sample.txt','/project','.']);
  f.root('/other');await f.actions.action('paste');assert.equal(f.requests.length,2);f.actions.dispose();
});
test('Explorer: 自分自身・子孫へ貼り付けない、rootのrename/trash/copy禁止',async()=>{
  const f=fixture();await f.actions.action('copy',folder);await f.actions.action('paste',folder);await f.actions.action('paste',{path:'docs/deep',type:'dir'});assert.equal(f.requests.length,0);assert.match(f.state.error,/配下/);
  for(const action of ['rename','trash','copy'])await f.actions.action(action);assert.equal(f.state.dialog,null);assert.equal(f.state.rename,null);assert.equal(f.requests.length,0);f.actions.dispose();
});
test('Explorer削除: ダイアログだけでは変更しない、キャンセル・確認・失敗',async()=>{
  const f=fixture();await f.actions.action('trash',folder);assert.equal(f.state.dialog.path,'docs');assert.equal(f.requests.length,0);f.actions.cancel();assert.equal(f.state.dialog,null);
  await f.actions.action('trash',file);f.response(new Response(JSON.stringify({error:'ゴミ箱を利用できません'}),{status:503}));await f.actions.perform({action:'trash',path:file.path,confirmed:true});assert.equal(f.changes.length,0);assert.equal(f.state.dialog.path,file.path);assert.match(f.state.error,/ゴミ箱/);
  f.response(new Response(JSON.stringify({action:'trash',path:file.path,name:file.name,type:'file'})));await f.actions.perform({action:'trash',path:file.path,confirmed:true});assert.equal(f.state.dialog,null);assert.equal(f.changes.length,1);assert.match(f.state.notice,/復元/);f.actions.dispose();
});
test('Explorer名前: 検証後1回だけ送信、同名/キャンセル/エラーは保持',async()=>{
  const f=fixture();await f.actions.beginRename(file);f.state.rename.value='../invalid';await f.actions.submitName();assert.equal(f.requests.length,0);f.state.rename.value=file.name;await f.actions.submitName();assert.equal(f.requests.length,0);assert.equal(f.state.rename,null);
  await f.actions.beginRename(file);f.state.rename.value='new.txt';f.response(new Response(JSON.stringify({message:'同名が存在します'}),{status:409}));await f.actions.submitName();assert.equal(f.state.rename.value,'new.txt');assert.match(f.state.error,/同名/);f.actions.cancel();assert.equal(f.state.rename,null);
  await f.actions.action('create-folder',file);assert.equal(f.state.dialog.directory,'docs');assert.equal(f.requests.length,1);f.state.dialog.value='new folder';f.response(null);await f.actions.submitName();assert.equal(f.requests[1].payload.action,'create-folder');f.actions.dispose();
});
test('Explorer処理: 連打は重複送信しない、セッション変更後の応答は無視',async()=>{
  const f=fixture();f.pending(true);const first=f.actions.action('duplicate',file);await f.actions.action('duplicate',file);assert.equal(f.requests.length,1);f.actions.cancel();assert.equal(f.state.busy,true);f.actions.reset();f.resolve();await first;assert.equal(f.changes.length,0);assert.equal(f.state.notice,'');assert.equal(f.state.busy,false);f.actions.dispose();
});
test('Explorerキーボード: 入力欄は通常clipboard、Shift+Deleteを削除しない',async()=>{
  const f=fixture(),event=(key,extra={})=>({key,target:{closest:()=>null},preventDefault(){this.prevented=true;},stopPropagation(){},...extra});
  assert.equal(f.actions.keyboard(event('Delete',{shiftKey:true}),file),false);assert.equal(f.actions.keyboard(event('c',{ctrlKey:true,target:{closest:()=>({})}}),file),false);
  const copy=event('c',{ctrlKey:true});assert.equal(f.actions.keyboard(copy,file),true);assert.ok(copy.prevented);assert.equal(f.state.clipboard.path,file.path);assert.equal(f.actions.keyboard(event('F10',{shiftKey:true}),file),'menu');
  f.actions.keyboard(event('Delete'),file);assert.equal(f.state.dialog.action,'trash');assert.equal(f.requests.length,0);f.actions.dispose();
});
test('Explorer非同期UI: rename準備・clipboard・refreshの遅い応答をreset後に表示しない',async()=>{
  let finishClipboard,finishRefresh;
  const actions=createExplorerActions({root:()=>'/project',document:()=>({querySelector:()=>null,defaultView:{navigator:{clipboard:{writeText:()=>new Promise((_resolve,reject)=>{finishClipboard=reject;})}}}}),refresh:()=>new Promise(done=>{finishRefresh=done;})});
  const rename=actions.beginRename(file);actions.reset();await rename;assert.equal(actions.state.rename,null);
  const copying=actions.action('copy-path',file);actions.reset();finishClipboard(Error('rejected'));await copying;assert.equal(actions.state.dialog,null);assert.equal(actions.state.notice,'');
  const refreshing=actions.action('refresh');actions.reset();finishRefresh();await refreshing;assert.equal(actions.state.notice,'');assert.equal(actions.state.busy,false);actions.dispose();
});
test('Explorerコピー元状態: 名前変更後のclipboardは追従、削除後は解除',async()=>{
  const f=fixture();await f.actions.action('copy',file);
  await f.actions.perform({action:'rename',path:file.path,name:'new.txt'});assert.equal(f.state.clipboard.path,'docs/new.txt');
  f.response(new Response(JSON.stringify({action:'trash',path:'docs',name:'docs',type:'directory'})));await f.actions.perform({action:'trash',path:'docs',confirmed:true});assert.equal(f.state.clipboard,null);f.actions.dispose();
});
test('Explorer: 途中コピー失敗は再試行せず一覧更新して残存先を案内',async()=>{
  let refreshes=0,requests=0;
  const actions=createExplorerActions({root:()=>'/project',document:()=>null,refresh:async()=>refreshes++,request:async()=>{requests++;return new Response(JSON.stringify({message:'途中のコピーが残っています: copy.txt',partialPath:'copy.txt'}),{status:408});}});
  await actions.action('duplicate',file);assert.equal(requests,1);assert.equal(refreshes,1);assert.match(actions.state.error,/copy.txt/);actions.dispose();
});

test('Explorer PDF化: .mdのみを要求し、成功後に作成先を一覧へ反映する',async()=>{
 const f=fixture();await f.actions.action('pdf',file);assert.equal(f.requests.length,0);
 f.response(new Response(JSON.stringify({action:'pdf',path:'docs/日本語.pdf',name:'日本語.pdf',type:'file'})));
 await f.actions.action('pdf',{type:'file',path:'docs/日本語.MD',name:'日本語.MD'});
 assert.deepEqual(f.requests[0].payload,{action:'pdf',path:'docs/日本語.MD'});assert.equal(f.changes.length,1);assert.match(f.state.notice,/日本語.pdf.*作成/);f.actions.dispose();
});
