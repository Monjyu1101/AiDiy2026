// -*- coding: utf-8 -*-

// -------------------------------------------------------------------------
// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
// -------------------------------------------------------------------------

import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,writeFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join,relative,isAbsolute} from 'node:path';
import {createPreview} from '../preview.mjs';

test('HTML/SVG: フォルダ基準の相対参照・ディレクトリURL・配信境界',async()=>{
  const root=await mkdtemp(join(tmpdir(),'aidiy-preview-'));let active=true;
  const preview=createPreview(root,()=>active);
  try{
    for(const dir of ['pages/assets','shared','pages/sub','_config'])await mkdir(join(root,dir),{recursive:true});
    const files={'pages/日本語 ページ.html':'<img src="assets/picture.png">','pages/drawing.svg':'<svg xmlns="http://www.w3.org/2000/svg"><image href="../shared/picture.png"/></svg>','pages/assets/picture.png':'image','shared/picture.png':'shared image','pages/sub/index.html':'<img src="../assets/picture.png">','_config/secret.json':'private'};
    for(const [name,body] of Object.entries(files))await writeFile(join(root,name),body);
    const html=await preview.url('pages/日本語 ページ.html'),svg=await preview.url('pages/drawing.svg');
    assert.equal(await (await fetch(new URL('assets/picture.png',html))).text(),'image');
    assert.equal(await (await fetch(new URL('../shared/picture.png',svg))).text(),'shared image');
    for(const url of [html,svg])assert.match((await fetch(url)).headers.get('content-security-policy'),/allow-same-origin/);
    assert.equal((await fetch(svg)).headers.get('content-type'),'image/svg+xml');
    for(const url of [html,svg]){
      const response=await fetch(url,{headers:{'sec-fetch-dest':'iframe'}}),body=await response.text();
      assert.match(body,/aidiy-ide-viewer-activity/,'iframe内の操作を通知する');
      assert.equal(Number(response.headers.get('content-length')),Buffer.byteLength(body));
      assert.match(body,/assets\/picture.png|\.\.\/shared\/picture.png/,'相対参照を維持');
      if(url===svg)assert.match(body,/<script><!\[CDATA\[.*\]\]><\/script><\/svg>$/);
    }
    assert.equal(await (await fetch(svg)).text(),files['pages/drawing.svg'],'画像など通常取得は元のまま');
    const directory=await preview.url('pages/sub');
    const response=await fetch(directory+'?v=1');assert.ok(response.url.endsWith('/?v=1'));
    assert.equal(await (await fetch(new URL('../assets/picture.png',response.url))).text(),'image');
    assert.equal(await preview.url('_config/secret.json'),null);
    assert.equal((await fetch(new URL('../_config/secret.json',new URL('../',html)))).status,404);
    assert.equal((await fetch(new URL('/api/file',html))).status,404);
    active=false;assert.equal((await fetch(html)).status,503);
  }finally{
    await preview.close();const back=relative(tmpdir(),root);if(!back||back.startsWith('..')||isAbsolute(back))throw Error('一時パス不正');
    await rm(root,{recursive:true,force:true});
  }
});
