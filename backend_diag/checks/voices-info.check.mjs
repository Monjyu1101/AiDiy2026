// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1". See LICENSE.
import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp, readFile, rm} from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {liveVoicesInfo, LIVE_VOICES_FILE} from '../voices_info.mjs';
import {writeModelsInfo} from '../models_info.mjs';

const providers=['gemini','freeai','openai'].map(id=>({id,名前:id,設定済み:true,テスト可能:true}));
const results=Object.fromEntries(providers.map(({id})=>[id,{状態:'OK',モデル詳細:[]}]));

test('fixed voices use live provider keys and preserve labels and order',()=>{
 const info=liveVoicesInfo(providers,results);
 assert.deepEqual(Object.keys(info),['freeai_live','gemini_live','openai_live']);
 assert.equal(Object.keys(info.gemini_live.voices).length,30);
 assert.equal(Object.keys(info.openai_live.voices).length,13);
 assert.equal(Object.keys(info.gemini_live.voices)[0],'Zephyr');
 assert.equal(info.gemini_live.voices.Zephyr,'(2.5) Zephyr Female');
 assert.equal(Object.keys(info.openai_live.voices)[0],'marin');
 assert.deepEqual(info.freeai_live,info.gemini_live);
 info.freeai_live.voices.Zephyr='changed';
 assert.equal(info.gemini_live.voices.Zephyr,'(2.5) Zephyr Female');
 assert.equal(liveVoicesInfo(providers,results).freeai_live.voices.Zephyr,'(2.5) Zephyr Female');
});

test('only configured, testable and successfully confirmed keys expose voices',()=>{
 for(const {id} of providers){
  for(const state of ['NG','未実施','ERR']){
   const info=liveVoicesInfo(providers,{...results,[id]:{状態:state}});
   assert.equal(Object.hasOwn(info,id+'_live'),false);
   assert.equal(Object.keys(info).length,2);
  }
  for(const flag of ['設定済み','テスト可能']){
   const info=liveVoicesInfo(providers.map(row=>row.id===id?{...row,[flag]:false}:row),results);
   assert.equal(Object.hasOwn(info,id+'_live'),false);
  }
 }
 assert.deepEqual(liveVoicesInfo(providers,{}),{});
});

test('partial writes preserve confirmed voices and remove disabled or failed keys, including no-test runs',async()=>{
 const directory=await mkdtemp(path.join(os.tmpdir(),'diag-live-voices-'));
 const options={directory,installedClis:{}};
 const load=async()=>JSON.parse(await readFile(path.join(directory,LIVE_VOICES_FILE),'utf8'));
 try{
  assert.ok((await writeModelsInfo(providers,results,options)).includes(LIVE_VOICES_FILE));
  assert.deepEqual(Object.keys(await load()),['freeai_live','gemini_live','openai_live']);
  await writeModelsInfo(providers,{gemini:{状態:'NG'}},options);
  assert.deepEqual(Object.keys(await load()),['freeai_live','openai_live']);
  await writeModelsInfo(providers.map(row=>row.id==='openai'?{...row,設定済み:false,テスト可能:false}:row),{freeai:{状態:'OK',モデル詳細:[]}},options);
  assert.deepEqual(Object.keys(await load()),['freeai_live']);
  await writeModelsInfo(providers.map(row=>({...row,設定済み:false,テスト可能:false})),{},options);
  assert.deepEqual(await load(),{});
 }finally{await rm(directory,{recursive:true,force:true});}
});
