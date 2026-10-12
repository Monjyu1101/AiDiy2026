// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,writeFile,rm,symlink} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join,dirname,resolve,sep} from 'node:path';
import {createFileHistory} from '../file-history.mjs';
import {startDevelopment} from '../server.mjs';
async function put(root,path,text){await mkdir(dirname(join(root,path)),{recursive:true});await writeFile(join(root,path),text);}
async function fixture(t){const root=await mkdtemp(join(tmpdir(),'aidiy-history-'));t.after(()=>{assert.ok(resolve(root).startsWith(resolve(tmpdir())+sep));return rm(root,{recursive:true,force:true});});await put(root,'src/main.js','const current = 3;');return root;}
test('更新履歴: ルートと祖先の差分・全件バックアップを日時順に選び、同名別ファイルを混ぜない',async t=>{
 const root=await fixture(t),service=createFileHistory(root);
 await put(root,'backup/20261010/100000.all/src/main.js','const original = 1;');
 await put(root,'src/backup/20261011/120000/main.js','const previous = 2;');
 await put(root,'backup/20261012/120000/other/main.js','wrong file');
 const list=await service.list('src/main.js');assert.equal(list.versions.length,2);assert.equal(list.versions[0].label,'2026/10/11 12:00:00');assert.equal(list.versions[1].fullBackup,true);
 const newer=await service.compare('src/main.js',list.versions[0].id);assert.equal(newer.original.text,'const previous = 2;');assert.equal(newer.modified.text,'const current = 3;');
 assert.equal((await service.compare('src/main.js',list.versions[1].id)).original.text,'const original = 1;');
 await put(root,'empty.js','nothing');assert.deepEqual((await service.list('empty.js')).versions,[]);
 await assert.rejects(()=>service.compare('empty.js',list.versions[0].id),{status:404});
 await rm(join(root,list.versions[0].backupPath));await assert.rejects(()=>service.compare('src/main.js',list.versions[0].id),{status:404});
});
test('更新履歴: プロジェクト外・不正ID・バックアップ外へのリンクを拒否する',async t=>{
 const root=await fixture(t),outside=await fixture(t),service=createFileHistory(root);
 for(const path of ['../src/main.js','/src/main.js','C:/file','src\\main.js','backup/20261010/100000/main.js','src/./main.js'])await assert.rejects(()=>service.list(path),{status:400});
 await symlink(outside,join(root,'linked'),process.platform==='win32'?'junction':'dir');await assert.rejects(()=>service.list('linked/src/main.js'),{status:404});
 await symlink(outside,join(root,'backup'),process.platform==='win32'?'junction':'dir');assert.deepEqual((await service.list('src/main.js')).versions,[]);
 await rm(join(root,'backup'));await put(root,'backup/20261010/100000.all/placeholder','x');
 await symlink(join(root,'src'),join(root,'backup/20261010/100000.all/src'),process.platform==='win32'?'junction':'dir');
 assert.deepEqual((await service.list('src/main.js')).versions,[]);
 await assert.rejects(()=>service.compare('src/main.js','../../src/main.js'),{status:404});
});
test('更新履歴: UTF-8・Shift_JIS、サイズ上限、バイナリを明確に扱う',async t=>{
 const root=await fixture(t),service=createFileHistory(root),old='backup/20261010/100000.all/src/main.js';
 await put(root,old,Buffer.from([0x82,0xa0]));let version=(await service.list('src/main.js')).versions[0];
 assert.equal((await service.compare('src/main.js',version.id)).original.text,'あ');
 await put(root,old,Buffer.alloc(1024*1024+1,65));await assert.rejects(()=>service.compare('src/main.js',version.id),{status:413});
 await put(root,old,Buffer.from([0,1]));await assert.rejects(()=>service.compare('src/main.js',version.id),{status:415});
});
test('更新履歴API: 利用状態・同一オリジン・GET限定と比較内容',async t=>{
 const root=await fixture(t);await put(root,'backup/20261010/100000.all/src/main.js','old');
 const app=await startDevelopment(root);t.after(()=>app.close());const url=app.url+'api/file-history?path=src/main.js';
 assert.equal((await fetch(url)).status,503);await fetch(app.url+'api/connection/offline',{method:'POST'});
 assert.equal((await fetch(url,{headers:{origin:'https://foreign.invalid'}})).status,403);
 assert.equal((await fetch(url,{method:'POST'})).status,405);
 const value=await fetch(url).then(r=>r.json());assert.equal(value.versions.length,1);
 assert.equal((await fetch(url+'&version='+value.versions[0].id).then(r=>r.json())).original.text,'old');
 assert.equal((await fetch(url+'&version=invalid')).status,404);
});
