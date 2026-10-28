import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,writeFile,readFile,readdir,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join,resolve,sep} from 'node:path';
import {createExplorerFiles} from '../ファイル機能/explorer-files.mjs';
async function fixture(t){const root=await mkdtemp(join(tmpdir(),'aidiy-pdf-test-'));t.after(async()=>{assert.ok(resolve(root).startsWith(resolve(tmpdir())+sep));await rm(root,{recursive:true,force:true});});await mkdir(join(root,'資料'));await writeFile(join(root,'資料','日本語.MD'),'# 日本語\n\n本文');return root;}
const pdf=Buffer.from('%PDF-1.4\nfixture');
test('PDF化は同じフォルダ・同名で作成し、元Markdownを保持して既存PDFを上書きする',async t=>{
 const root=await fixture(t);let count=0,changed=0;
 const service=createExplorerFiles(root,{pdfRenderer:async input=>{count++;assert.equal(input.path,'資料/日本語.MD');return pdf;},onChange:()=>changed++});
 const result=await service.apply({action:'pdf',path:'資料/日本語.MD'});
 assert.equal(result.path,'資料/日本語.pdf');assert.equal(result.type,'file');assert.equal(changed,1);
 assert.deepEqual(await readFile(join(root,result.path)),pdf);assert.equal(await readFile(join(root,'資料/日本語.MD'),'utf8'),'# 日本語\n\n本文');
 await writeFile(join(root,result.path),'old PDF');
 await service.apply({action:'pdf',path:'資料/日本語.MD'});assert.equal(count,2);assert.equal(changed,2);assert.deepEqual(await readFile(join(root,result.path)),pdf);
});
test('PDF化は対象外・外部パス・生成失敗・途中変更・利用終了時に出力しない',async t=>{
 const root=await fixture(t);await writeFile(join(root,'a.txt'),'text');let active=true;
 const service=createExplorerFiles(root,{state:()=>({active}),pdfRenderer:async()=>{throw Object.assign(Error('failed'),{status:503});}});
 for(const path of ['a.txt','資料','../outside.md'])await assert.rejects(service.apply({action:'pdf',path}));
 await assert.rejects(service.apply({action:'pdf',path:'資料/日本語.MD'}),{status:503});
 const edited=createExplorerFiles(root,{pdfRenderer:async()=>{await writeFile(join(root,'資料/日本語.MD'),'updated content');return pdf;}});
 await assert.rejects(edited.apply({action:'pdf',path:'資料/日本語.MD'}),{status:409});
 active=false;await assert.rejects(service.apply({action:'pdf',path:'資料/日本語.MD'}),{status:503});
 assert.deepEqual(await readdir(join(root,'資料')),['日本語.MD']);
});
test('PDF化中に作られた同名PDFも上書きする',async t=>{
 const root=await fixture(t),service=createExplorerFiles(root,{pdfRenderer:async()=>{await writeFile(join(root,'資料/日本語.pdf'),'keep');return pdf;}});
 await service.apply({action:'pdf',path:'資料/日本語.MD'});assert.deepEqual(await readFile(join(root,'資料/日本語.pdf')),pdf);
});
test('実Electronでプレビューの見出し・日本語・表・相対画像をPDF化', {skip:process.env.AIDIY_TEST_PDF_RENDER!=='1'},async t=>{
 const root=await fixture(t);await writeFile(join(root,'資料','図.svg'),'<svg xmlns="http://www.w3.org/2000/svg" width="300" height="80"><rect width="300" height="80" fill="#38bdf8"/></svg>');
 await writeFile(join(root,'資料','日本語.MD'),'# PDF化の確認\n\n日本語の本文です。\n\n|項目|結果|\n|---|---|\n|日本語|成功|\n\n![相対画像](図.svg)\n\n```js\nconsole.log("hello");\n```');
 const service=createExplorerFiles(root);const result=await service.apply({action:'pdf',path:'資料/日本語.MD'});const bytes=await readFile(join(root,result.path));assert.equal(bytes.subarray(0,5).toString(),'%PDF-');assert.ok(bytes.length>1000);
});

test('生成失敗は既存PDFを保持し、同名フォルダは置換しない',async t=>{
 const root=await fixture(t),target=join(root,'資料/日本語.pdf');await writeFile(target,'original');
 const service=createExplorerFiles(root,{pdfRenderer:async()=>{throw Error('failed');}});
 await assert.rejects(service.apply({action:'pdf',path:'資料/日本語.MD'}));assert.equal(await readFile(target,'utf8'),'original');
 await rm(target);await mkdir(target);
 await assert.rejects(createExplorerFiles(root,{pdfRenderer:async()=>pdf}).apply({action:'pdf',path:'資料/日本語.MD'}),{code:'not_file'});
 assert.deepEqual((await readdir(join(root,'資料'))).sort(),['日本語.MD','日本語.pdf'].sort());
});
