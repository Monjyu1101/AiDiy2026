const test=require('node:test');const assert=require('node:assert/strict');const {render,source}=require('./ui-components.cjs');
test('Term-like status bar distinguishes Tools and diagnostic connection without browser window controls',async()=>{
 for(const [props,text,bar] of [[{connected:true,enabled:true,online:true},'Tools 接続中','online'],[{connected:true,enabled:true},'Tools 未接続',''],[{connected:true,enabled:false},'Tools 確認OFF','offline'],[{connected:false,enabled:true,online:true},'診断 未接続','']]){
  const html=await render('ウィンドウ/ステータスバー.vue',props);assert.ok(html.includes('AiDiy Diag'));assert.ok(html.includes(text));assert.ok(html.includes(`connection-bar ${bar}`)||html.includes('connection-bar"'));assert.ok(!html.includes('aria-label="終了"'));
 }
 const css=source('style.css');assert.match(css,/-webkit-app-region:drag/);assert.match(css,/-webkit-app-region:no-drag/);assert.doesNotMatch(css,/prefers-reduced-motion/);
});
test('mini restore lives in the titlebar in browser mode too',async()=>{
 const compact=await render('ウィンドウ/ステータスバー.vue',{compact:true,connected:true,enabled:true});
 assert.match(compact,/<header[^>]*>[\s\S]*aria-label="通常表示"[\s\S]*<\/header>/);
 assert.ok(!compact.includes('aria-label="終了"'));
 const normal=await render('ウィンドウ/ステータスバー.vue',{connected:true,enabled:true});
 assert.ok(!normal.includes('aria-label="通常表示"'));
});
