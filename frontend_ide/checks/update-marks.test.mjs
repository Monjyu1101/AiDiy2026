// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
import test from 'node:test';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {fileRecency,createUpdateMarks,updateFlash} from '../src/ファイル閲覧/更新の目印.js';
import {electronTargets,electronBuffer,createElectronOrbits,MAX_ELECTRON_FILES} from '../src/開発スペース/電子の周回.js';
const now=+new Date(2026,9,16,12), day=+new Date(2026,9,16);
const files=[{path:'older',mtime:day-86400001,size:1},{path:'yesterday',mtime:day-1,size:1},{path:'today',mtime:day+1,size:1},{path:'latest-a',mtime:now,size:1},{path:'latest-b',mtime:now,size:1}];
test('表示対象だけで今日/最新同率/前日を判定し、最新は4個へ置換する',()=>{
 const value=fileRecency(files,now);assert.deepEqual({...value.electrons},{yesterday:1,today:2,'latest-a':4,'latest-b':4});
 assert.deepEqual({...value.levels},{today:1,'latest-a':2,'latest-b':2});
 assert.deepEqual({...fileRecency(files.slice(0,3),now).electrons},{yesterday:1,today:4});
 assert.deepEqual({...fileRecency(files.slice(0,2),now).levels},{});
 assert.equal(fileRecency([{path:'bad',mtime:NaN},{path:'future',mtime:day+86400000}],now).latest,null);
});
test('初回/無差分/フォルダ・フィルター切替は発光せず、追加と実変更だけ短く発光する',()=>{
 const tracker=createUpdateMarks();assert.deepEqual(tracker.update(files,'root|on',now).flashes,{});
 assert.deepEqual(tracker.update(files,'root|on',now+1).flashes,{});
 const changed=files.map(file=>file.path==='today'?{...file,size:2}:file).concat({path:'added',mtime:now,size:2});
 let marks=tracker.update(changed,'root|on',now+2);assert.deepEqual(Object.keys(marks.flashes),['today','added']);
 const id=marks.flashes.today.id;assert.equal(tracker.update(changed,'root|on',now+3).flashes.today.id,id);
 assert.equal(updateFlash(marks.flashes.today,now+602),1);assert.equal(updateFlash(marks.flashes.today,now+1202),0);
 assert.deepEqual(Object.keys(tracker.update(changed.filter(file=>file.path!=='added'),'root|on',now+4).flashes),['today']);
 assert.deepEqual(tracker.snapshot(now+1202).flashes,{});
 assert.deepEqual(tracker.update(files,'root|off',now+1300).flashes,{});
 assert.deepEqual(tracker.update(changed,'root|off',now+1400,false).flashes,{});
 assert.deepEqual(tracker.update(files,'child|off',now+1500).flashes,{});
 tracker.clear();assert.deepEqual(tracker.snapshot(now).flashes,{});
});
for(const zone of ['UTC','Asia/Tokyo','America/New_York'])test(`ローカル日付 ${zone}: 日跨ぎ・夏時間・年跨ぎ`,()=>{
 const module=new URL('../src/ファイル閲覧/更新の目印.js',import.meta.url).href;
 const code=`import assert from 'node:assert/strict';import {fileRecency} from ${JSON.stringify(module)};
 for(const now of [new Date(2026,0,1,0,1),new Date(2026,2,9,0,1),new Date(2026,10,2,0,1)]){
 const prev=new Date(now);prev.setDate(prev.getDate()-1);prev.setHours(0,0,1,0);
 assert.equal(fileRecency([{path:'p',mtime:+prev}],+now).electrons.p,1);
 assert.equal(fileRecency([{path:'p',mtime:+prev}],+now).latest,null);}`;
 execFileSync(process.execPath,['--input-type=module','-e',code],{env:{...process.env,TZ:zone}});
});
test('大量電子: 安定した上限・同率4個・一括頂点・毎フレームの再転送なし・解放',()=>{
 const many=Array.from({length:5000},(_,i)=>({path:'file-'+i,x:i,y:0,z:0,R:10}));
 const counts=Object.fromEntries(many.map(file=>[file.path,4]));
 const chosen=electronTargets(many,counts);assert.equal(chosen.length,MAX_ELECTRON_FILES);
 assert.deepEqual(electronTargets([...many].reverse(),counts),chosen);
 assert.equal(electronBuffer(chosen).length,MAX_ELECTRON_FILES*4*7);
 const calls=[],canvas=new EventTarget();
 const gl=new Proxy({VERSION:1,getParameter:()=> 'WebGL 1.0',getShaderParameter:()=>true,getProgramParameter:()=>true,getAttribLocation:()=>0,getUniformLocation:(_,name)=>name,getExtension:()=>({loseContext(){calls.push(['lost']);}})}, {get:(o,k)=>k in o?o[k]:(...args)=>{calls.push([k,...args]);return {};}});
 canvas.getContext=()=>gl;
 const layer=createElectronOrbits({createElement:()=>canvas});layer.update(many,counts);const uploads=layer.stats.uploads;
 const ctx={save(){},restore(){},drawImage(){calls.push(['image']);}};
 const view={width:800,height:600,dpr:1,focal:600,rotation:[1,0,0,0,1,0,0,0,1],target:[0,0,0],offset:[0,0,1000],time:10,alpha:1,reduced:false};
 for(let i=0;i<60;i++)layer.render(ctx,view);
 assert.ok(calls.some(call=>call[0]==='blendFuncSeparate'),'透過Canvasのalphaを二重に乗算しない');
 assert.equal(layer.stats.uploads,uploads);assert.equal(layer.stats.draws,60);
 assert.equal(calls.filter(call=>call[0]==='drawArrays').length,60);
 layer.render(ctx,{...view,reduced:true});assert.deepEqual(calls.filter(call=>call[0]==='uniform1f'&&call[1]==='u_time').at(-1),['uniform1f','u_time',0]);
 canvas.dispatchEvent(new Event('webglcontextlost',{cancelable:true}));assert.equal(layer.stats.mode,'static');assert.equal(layer.stats.files,256);
 layer.render(ctx,view);assert.equal(layer.stats.draws,61);
 canvas.dispatchEvent(new Event('webglcontextrestored'));assert.equal(layer.stats.mode,'webgl');
 layer.dispose();layer.render(ctx,view);assert.equal(layer.stats.draws,61);assert.ok(calls.some(call=>call[0]==='deleteBuffer'));
});
