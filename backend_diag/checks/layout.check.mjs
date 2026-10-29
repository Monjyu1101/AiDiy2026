// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
import test from 'node:test';
import assert from 'node:assert/strict';
import {copyFile,mkdir,mkdtemp,readFile,rm,writeFile} from 'node:fs/promises';
import {fileURLToPath,pathToFileURL} from 'node:url';
import os from 'node:os';
import path from 'node:path';
import {CATALOG_PATH} from '../診断/probes.mjs';
import {BUNDLED_ZIP} from '../モデル情報/bundled_models.mjs';
import {STOP_FILE} from '../起動/lifecycle.mjs';
import {DESKTOP_LOG} from '../起動/desktop-log.mjs';
const root=fileURLToPath(new URL('../',import.meta.url));

test('feature folders retain package entry, catalog, bundled models and root control files',async()=>{
 const metadata=JSON.parse(await readFile(new URL('../package.json',import.meta.url),'utf8'));
 assert.equal(metadata.main,'起動/electron-main.cjs');
 assert.equal(CATALOG_PATH,path.join(root,'診断/catalog.json'));
 assert.equal(BUNDLED_ZIP,path.join(root,'モデル情報/openrouter_models/openrouter_models.zip'));
 assert.equal(fileURLToPath(STOP_FILE),path.join(root,'.stop-request'));
 assert.equal(fileURLToPath(DESKTOP_LOG),path.join(root,'.desktop-errors.log'));
 await readFile(path.join(root,metadata.main));
});

test('moved desktop module still finds Electron in the package root without a caller override',async()=>{
 const directory=await mkdtemp(path.join(os.tmpdir(),'diag-layout-'));
 try {
  const startup=path.join(directory,'起動'),electron=path.join(directory,'node_modules/electron');
  await mkdir(startup);await mkdir(path.join(electron,'dist'),{recursive:true});
  for(const name of ['desktop.mjs','desktop-log.mjs'])await copyFile(path.join(root,'起動',name),path.join(startup,name));
  const suffix=process.platform==='win32'?'electron.exe':process.platform==='darwin'?'Electron.app/Contents/MacOS/Electron':'electron';
  const executable=path.join(electron,'dist',suffix);await mkdir(path.dirname(executable),{recursive:true});
  await writeFile(path.join(electron,'package.json'),JSON.stringify({version:'1.2.3'}));
  await writeFile(path.join(electron,'dist/version'),'1.2.3');await writeFile(path.join(electron,'path.txt'),suffix);
  await writeFile(executable,'fixture only',{mode:0o755});
  const {desktopBinary}=await import(pathToFileURL(path.join(startup,'desktop.mjs')).href);
  assert.equal(await desktopBinary(),executable);
 }finally{await rm(directory,{recursive:true,force:true});}
});
