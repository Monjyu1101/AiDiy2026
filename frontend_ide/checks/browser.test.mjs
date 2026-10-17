// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
import test from 'node:test';
import assert from 'node:assert/strict';
import {EventEmitter} from 'node:events';
import {mkdtempSync,writeFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join,resolve,sep} from 'node:path';
import {pathToFileURL} from 'node:url';
import browser from '../デスクトップ/ブラウザ.cjs';
import layout from '../デスクトップ/window-layout.cjs';
import {openBrowser} from '../src/ブラウザ/起動.js';
const {HOME,browserURL,createBrowserViews}=browser;
test('Browser: Google既定、検索語・URL・開発サーバーの解決、実行スキーム拒否',()=>{
 assert.equal(browserURL(''),HOME);
 assert.equal(browserURL('宇宙 IDE'),HOME+'search?q='+encodeURIComponent('宇宙 IDE'));
 assert.equal(browserURL('example.com/a'),'https://example.com/a');
 assert.equal(browserURL('example.com:8080/a'),'https://example.com:8080/a');
 assert.equal(browserURL('localhost:8090/'),'http://localhost:8090/');
 assert.equal(browserURL('http://127.0.0.1:8090/'),'http://127.0.0.1:8090/');
 assert.equal(browserURL('file:///C:/project/index.html'),'file:///C:/project/index.html');
 for(const value of ['javascript:alert(1)','data:text/html,test','https://user:pass@example.com',null])assert.throws(()=>browserURL(value));
});

test('Browser: 選択ファイルは実絶対パスのfile URL、相対リソースはプロジェクト内だけ許可',t=>{
 const root=mkdtempSync(join(tmpdir(),'aidiy-browser-files-'));
 t.after(()=>{assert.ok(resolve(root).startsWith(resolve(tmpdir())+sep));rmSync(root,{recursive:true,force:true});});
 const name='宇宙 # 100%.html',file=join(root,name);writeFileSync(file,'<h1>test</h1>');writeFileSync(join(root,'style.css'),'body{}');
 const url=pathToFileURL(file).href;assert.equal(browser.browserFileURL(root,name),url);assert.equal(browserURL(file),url);assert.equal(browserURL(url),url);
 assert.throws(()=>browser.browserFileURL(root,'../outside.html'));assert.throws(()=>browser.browserFileURL(root,'missing.html'));
 let filter;const isolated={setPermissionRequestHandler(){},setPermissionCheckHandler(){},webRequest:{onBeforeRequest(fn){filter=fn;}}};
 const views=createBrowserViews({session:{fromPartition:()=>isolated},projectRoot:root});
 assert.equal(views.allowedURL(url),true);assert.equal(views.allowedURL(url+'#section'),true);assert.equal(views.allowedURL(pathToFileURL(join(root,'../outside.html')).href),false);
 filter({url:pathToFileURL(join(root,'style.css')).href},result=>assert.equal(result.cancel,false));
 filter({url:pathToFileURL(join(root,'../outside.css')).href},result=>assert.equal(result.cancel,true));
});
test('Browser: ページを権限なしで分離し、IDEへの要求と別画面IPCを拒否、終了で解放',async()=>{
 let view,filter;const sent=[];
 const isolated={setPermissionRequestHandler(fn){this.request=fn;},setPermissionCheckHandler(fn){this.check=fn;},webRequest:{onBeforeRequest(fn){filter=fn;}}};
 class View{
  constructor(options){view=this;this.options=options;this.webContents=new EventEmitter();Object.assign(this.webContents,{url:'',getURL(){return this.url;},getTitle:()=>'',isLoading:()=>false,isDestroyed:()=>false,navigationHistory:{canGoBack:()=>false,canGoForward:()=>false},loadURL:async function(url){this.url=url;},setWindowOpenHandler(fn){this.popup=fn;},close(options){this.closed=options;}});}
  setVisible(value){this.visible=value;}setBounds(value){this.bounds=value;}
 }
 const window=new EventEmitter();Object.assign(window,{isDestroyed:()=>false,contentView:{addChildView(){}},getContentBounds:()=>({width:1000,height:700}),webContents:{getZoomFactor:()=>1.25,send:(...args)=>sent.push(args)}});
 const record={kind:'browser',window,url:'http://127.0.0.1:1234/'},event={record};
 const control=createBrowserViews({WebContentsView:View,session:{fromPartition:name=>{assert.equal(name,'aidiy-browser');return isolated;}},trustedEvent:event=>event.record});
 control.attach(record);assert.equal(view.webContents.url,HOME);
 assert.equal(view.options.webPreferences.sandbox,true);assert.equal(view.options.webPreferences.nodeIntegration,false);assert.equal(view.options.webPreferences.preload,undefined);
 assert.equal(isolated.check(),false);isolated.request(null,'media',allowed=>assert.equal(allowed,false));
 filter({url:record.url+'api/connection'},result=>assert.equal(result.cancel,true));
 assert.equal((await control.action({record:{kind:'ide'}},'navigate',HOME)).ok,false);
 assert.equal((await control.action(event,'navigate',record.url)).ok,false);
 assert.equal((await control.action(event,'navigate','file:///tmp/a.html')).ok,false);
 await control.action(event,'bounds',{left:0,top:90,width:800,height:470});assert.equal(view.visible,true);assert.equal(view.bounds.y,113);assert.ok(view.bounds.height+view.bounds.y<=700);
 let prevented=false;view.webContents.emit('will-navigate',{preventDefault(){prevented=true;}},'javascript:alert(1)');assert.equal(prevented,true);
 assert.deepEqual(view.webContents.popup({url:'https://example.com/'}),{action:'deny'});assert.equal(view.webContents.url,'https://example.com/');
 window.emit('closed');assert.deepEqual(view.webContents.closed,{waitForBeforeUnload:false});assert.equal((await control.action(event,'state')).ok,false);
});
test('Browser: 負座標・縦画面と小画面でも選択画面内に配置する',()=>{
 for(const area of [{x:-1920,y:0,width:1920,height:1040},{x:0,y:-1080,width:1080,height:1880},{x:0,y:0,width:320,height:240}])for(let slot=0;slot<9;slot++){
  const b=layout.allWindowBounds('browser',area,slot);assert.ok(b.x>=area.x&&b.y>=area.y&&b.x+b.width<=area.x+area.width&&b.y+b.height<=area.y+area.height);
 }
});
test('Web: HTML予約タブのopenerを切り離し、プレビュー失敗時は空タブを閉じる',async()=>{
 const popup={opener:{},location:{replace(url){this.url=url;}},close(){this.closed=true;}};
 const win={open:()=>popup,fetch:async url=>({ok:true,json:async()=>url==='/api/connection'?{active:true,mode:'online',connected:true}:{url:'http://127.0.0.1:9000/test.html'}})};
 assert.equal((await openBrowser('test.html',undefined,win)).ok,true);assert.equal(popup.opener,null);assert.equal(popup.location.url,'http://127.0.0.1:9000/test.html');
 win.fetch=async()=>({ok:true,json:async()=>({active:true,mode:'offline',connected:false})});assert.equal((await openBrowser('missing.htm',undefined,win)).ok,false);assert.equal(popup.closed,true);
});
