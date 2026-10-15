import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,writeFile,rm} from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {probe,resolveProgram,scan,catalog,expandPath} from '../probes.mjs';

async function fixture(code,options={}) {
 const directory=await mkdtemp(path.join(os.tmpdir(),'diag-test-'));
 try {const script=path.join(directory,'fixture.cjs');await writeFile(script,code);return await probe({id:'fixture',version_args:[script]}, {resolve:async()=>process.execPath,timeout:250,...options});}
 finally {await rm(directory,{recursive:true,force:true});}
}
test('missing and unsupported are separate',async()=>{
 assert.equal((await probe({id:'absent',commands:['no-such-aidiy-tool'],version_args:['--version']})).状態,'未検出');
 assert.equal((await probe({id:'other',platforms:['imaginary']})).状態,'対象外');
});
test('GUI/no version and Windows wrappers only discover',async()=>{
 for(const entry of [{id:'gui',version_args:null},{id:'wrapper',version_args:['--version']}]) {
 const result=await probe(entry,{resolve:async()=>'/fake/tool.cmd'});assert.equal(result.状態,'存在確認'); }
});
test('safe actual Node version',async()=>{
 const result=await probe({id:'node',commands:['node'],version_args:['--version']});assert.equal(result.状態,'導入済み');assert.equal(result.バージョン,process.versions.node);
});
test('failure, timeout and output caps',async()=>{
 assert.equal((await fixture('process.exit(9)')).状態,'確認失敗');
 assert.match((await fixture('setInterval(()=>{},1000)')).説明,/タイムアウト/);
 assert.match((await fixture('process.stdout.write("x".repeat(1000000))')).説明,/上限/);
});
test('parent exit with inherited pipe holder is bounded',{skip:process.platform==='win32'},async()=>{
 const start=Date.now(); const result=await fixture('require("child_process").spawn(process.execPath,["-e","setInterval(()=>{},1000)"],{stdio:["ignore",process.stdout,process.stderr]});console.log("1.2.3");process.exit(0);',{timeout:1000});
 assert.ok(Date.now()-start<1500);assert.equal(result.状態,'導入済み');
});
test('raw output and sensitive inherited environment never returned',async()=>{
 process.env.AIDIY_TEST_SECRET='private-fixture';
 try {const result=await fixture('console.log(process.env.AIDIY_TEST_SECRET?"9.9.9":"1.2.3");console.log("private-output");');assert.equal(result.バージョン,'1.2.3');assert.ok(!JSON.stringify(result).includes('private'));}
 finally {delete process.env.AIDIY_TEST_SECRET;}
});
test('scan maximum concurrency is four and results keep catalog ordering',async()=>{
 let active=0,max=0;const result=await scan(Array.from({length:13},(_,id)=>({id})),async e=>{active++;max=Math.max(max,active);await new Promise(r=>setTimeout(r,2));active--;return e.id;});assert.equal(max,4);assert.deepEqual(result,Array.from({length:13},(_,i)=>i));
});
test('standard paths expand supported environment syntax',()=>{
 assert.equal(expandPath('~/$ROOT/%ROOT%/${ROOT}',{ROOT:'value'},'/home/user'),'/home/user/value/value/value');
 assert.equal(expandPath('${UNKNOWN}/bin',{}),null);
 assert.equal(expandPath('${PROGRAMFILES(X86)}/Chrome',{'PROGRAMFILES(X86)':'C:/Program Files (x86)'}),'C:/Program Files (x86)/Chrome');
});
test('catalog identifiers unique; fixed version args and source evidence required',async()=>{
 const entries=await catalog();assert.ok(entries.length>=20);assert.equal(entries[0].id,'node');assert.equal(entries[1].id,'python');assert.equal(new Set(entries.map(e=>e.id)).size,entries.length);
 for(const entry of entries) {assert.ok(entry.sources.length);assert.ok(entry.commands.length);assert.ok(entry.version_args===null || (Array.isArray(entry.version_args)&&entry.version_args.every(v=>typeof v==='string')));}
});
test('Windows disk converter is not ImageMagick',async()=>{
 const directory=await mkdtemp(path.join(os.tmpdir(),'diag-convert-'));const {mkdir}=await import('node:fs/promises');
 try {const system=path.join(directory,'Windows','System32');await mkdir(system,{recursive:true});await writeFile(path.join(system,'convert.exe'),'fixture');assert.equal(await resolveProgram({id:'convert',commands:['convert']},{platform:'win32',env:{PATH:system}}),null);}
 finally {await rm(directory,{recursive:true,force:true});}
});
test('coverage is pinned to complete selected-source manifest and exact catalog bytes',async()=>{
 const {readFile}=await import('node:fs/promises');const {createHash}=await import('node:crypto');
 const coverage=JSON.parse(await readFile(new URL('../coverage.json',import.meta.url),'utf8'));
 const manifestBytes=await readFile(new URL('../reference/source-manifest.json',import.meta.url));
 const catalogBytes=await readFile(new URL('../catalog.json',import.meta.url));
 assert.equal(coverage.complete,true);assert.equal(coverage.sourceTargetFiles,3333);assert.equal(coverage.scannedSourceFiles,3333);
 assert.equal(JSON.parse(manifestBytes).length,3333);assert.equal(createHash('sha256').update(manifestBytes).digest('hex'),coverage.sourceTargetManifestSha256);
 assert.equal(JSON.parse(catalogBytes).length,246);assert.equal(createHash('sha256').update(catalogBytes).digest('hex'),coverage.catalogSha256);
 for (const entry of JSON.parse(catalogBytes)) assert.ok(entry.evidence?.length && entry.evidence.every(e=>e.path && Number.isInteger(e.line) && e.line>0));
});
