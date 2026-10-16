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
import {startServer} from '../server.mjs';
import {request} from 'node:http';

const getWithHeaders=(url,headers)=>new Promise((done,reject)=>{
  const req=request(url,{headers},res=>{const chunks=[];res.on('data',part=>chunks.push(part));res.on('end',()=>done(new Response(Buffer.concat(chunks),{status:res.statusCode,headers:res.headers})));});
  req.on('error',reject);req.end();
});

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
    for(const url of [html,svg]){
      const response=await fetch(url);
      assert.match(response.headers.get('content-security-policy'),/allow-same-origin/);
      assert.equal(response.headers.get('referrer-policy'),'same-origin','外部資産へtokenとパスを漏らさない');
    }
    assert.equal(await (await fetch(new URL('/assets/picture.png',html),{headers:{referer:html}})).text(),'image','同一公開元のルート相対参照を維持');
    assert.equal((await fetch(new URL('/assets/picture.png',html),{headers:{referer:html.replace(new URL(html).origin,'https://evil.example')}})).status,404,'別サイトのRefererでは資産を配らない');
    assert.equal((await fetch(new URL('assets/picture.png',html))).headers.get('referrer-policy'),'same-origin');
    assert.equal((await fetch(svg)).headers.get('content-type'),'image/svg+xml');
    for(const url of [html,svg]){
      const response=await fetch(url,{headers:{'sec-fetch-dest':'iframe'}}),body=await response.text();
      assert.match(body,/aidiy-ide-viewer-activity/,'iframe内の操作を通知する');
      assert.equal(Number(response.headers.get('content-length')),Buffer.byteLength(body));
      assert.match(body,/assets\/picture.png|\.\.\/shared\/picture.png/,'相対参照を維持');
      if(url===svg)assert.match(body,/<script><!\[CDATA\[.*\]\]><\/script><\/svg>$/s);
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

test('Codespaces: HTML/SVG/Markdownは別の転送公開元、ローカル閲覧はループバックを使う',async()=>{
  const root=await mkdtemp(join(tmpdir(),'aidiy-preview-forwarded-'));
  const env={CODESPACES:'true',CODESPACE_NAME:'preview-space',GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN:'app.github.dev'};
  const app=await startServer(root,0,{env});
  try{
    await mkdir(join(root,'public/assets'),{recursive:true});
    await mkdir(join(root,'_config'));
    for(const [name,body] of Object.entries({'public/page.html':'<img src="/assets/picture.png">','public/drawing.svg':'<svg/>','public/readme.md':'# 日本語','public/assets/picture.png':'local image','_config/secret.json':'private'}))await writeFile(join(root,name),body);
    await fetch(new URL('/api/connection/offline',app.url),{method:'POST'});
    const ideOrigin=new URL(app.publicUrl).origin,ideHost=new URL(app.publicUrl).host;
    for(const path of ['public/page.html','public/drawing.svg','public/readme.md']){
      const api=new URL('/api/preview?'+new URLSearchParams({path}),app.url);
      const local=await (await fetch(api)).json();
      assert.equal(new URL(local.url).hostname,'127.0.0.1');
      const previewPort=new URL(local.url).port;
      for(const headers of [{host:ideHost},{origin:ideOrigin},{referer:app.publicUrl}]){
        const remote=await (await getWithHeaders(api,headers)).json();
        assert.equal(new URL(remote.url).origin,`https://preview-space-${previewPort}.app.github.dev`);
        assert.notEqual(new URL(remote.url).origin,ideOrigin,'IDE APIとは別公開元を維持');
        assert.equal(new URL(remote.url).pathname,new URL(local.url).pathname,'tokenと相対パスを維持');
        const response=await getWithHeaders(local.url,{host:new URL(remote.url).host});
        assert.equal(response.status,200);
        assert.equal(response.headers.get('referrer-policy'),'same-origin');
        assert.match(response.headers.get('content-security-policy'),/sandbox/);
        assert.equal(await (await getWithHeaders(new URL('/assets/picture.png',local.url),{host:new URL(remote.url).host,referer:remote.url})).text(),'local image');
      }
      assert.equal((await getWithHeaders(local.url,{host:`other-space-${previewPort}.app.github.dev`})).status,403);
      assert.equal((await fetch(local.url.replace(/\/p\/[^/]+\//,'/p/wrong-token/'))).status,404);
      assert.equal((await fetch(new URL('/api/file?path=public/page.html',local.url))).status,404);
      const prefix=new URL(local.url).pathname.split('/').slice(0,3).join('/')+'/';
      assert.equal((await fetch(new URL(prefix+'_config/secret.json',local.url))).status,404);
      assert.equal((await fetch(new URL(prefix+'..%2f..%2fprivate.txt',local.url))).status,404);
    }
  }finally{
    await app.close();await rm(root,{recursive:true,force:true});
  }
});
