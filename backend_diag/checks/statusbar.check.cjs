const test=require('node:test');const assert=require('node:assert/strict');const {render,source}=require('./ui-components.cjs');
test('Term-like status bar distinguishes Tools and diagnostic connection without browser window controls',async()=>{
 for(const [props,text,bar] of [[{connected:true,enabled:true,online:true},'tools 接続済み','online'],[{connected:true,enabled:true},'tools 未接続',''],[{connected:true,enabled:false},'tools 確認OFF','offline'],[{connected:false,enabled:true,online:true},'診断 未接続','']]){
  const html=await render('ウィンドウ/ステータスバー.vue',props);assert.ok(html.includes('AiDiy Diag'));assert.ok(html.includes(text));assert.ok(html.includes(`connection-bar ${bar}`)||html.includes('connection-bar"'));assert.ok(!html.includes('aria-label="終了"'));
 }
 const css=source('style.css');assert.match(css,/-webkit-app-region:drag/);assert.match(css,/-webkit-app-region:no-drag/);assert.match(css,/prefers-reduced-motion/);
});
