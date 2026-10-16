// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
import test from 'node:test';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {fileDateInfo,nextLocalMidnight} from '../src/ファイル閲覧/ファイル日時.js';
test('日時: 無効値は例外を出さず、元日時と時刻を保持する',()=>{
 for(const value of [null,undefined,NaN,Infinity,'invalid',1e20])assert.deepEqual(fileDateInfo(value),{text:'—',today:false,iso:undefined,title:'更新日時不明'});
 const now=new Date(2026,9,16,12).getTime(), result=fileDateInfo(now,now);
 assert.equal(result.today,true);assert.match(result.text,/^今日 /);assert.match(result.title,/2026/);assert.equal(result.iso,new Date(now).toISOString());
 const yesterday=fileDateInfo(now-86400000,now);assert.equal(yesterday.today,false);assert.equal(yesterday.text,yesterday.title);
 assert.equal(new Date(nextLocalMidnight(now)).getHours(),0);
});
for(const zone of ['UTC','Asia/Tokyo','America/New_York'])test(`日時: ${zone} の深夜・年跨ぎ・UTC境界`,()=>{
 const module=new URL('../src/ファイル閲覧/ファイル日時.js',import.meta.url).href;
 const code=`import {fileDateInfo,nextLocalMidnight} from ${JSON.stringify(module)};
 const now=new Date(2026,0,1,0,1).getTime(), previous=new Date(2025,11,31,23,59).getTime();
 const boundary=Date.parse('2026-10-15T15:05:00Z'), file=Date.parse('2026-10-15T14:55:00Z');
 console.log(JSON.stringify({today:fileDateInfo(now,now).today,previous:fileDateInfo(previous,now).today,boundary:fileDateInfo(file,boundary).today,next:new Date(nextLocalMidnight(now)).getDate(),hour:new Date(nextLocalMidnight(now)).getHours()}));`;
 const result=JSON.parse(execFileSync(process.execPath,['--input-type=module','-e',code],{env:{...process.env,TZ:zone},encoding:'utf8'}));
 assert.deepEqual(result,{today:true,previous:false,boundary:zone!=='Asia/Tokyo',next:2,hour:0});
});
