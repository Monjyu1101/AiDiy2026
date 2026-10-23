const test=require('node:test');
const assert=require('node:assert/strict');
const {render,source}=require('./ui-components.cjs');

test('設定モデルのテストと結果は折り返さない横一列で表示する',async()=>{
 const css=source('設定モデル/設定モデル.css');
 const rule=css.match(/\.trial-test\{([^}]+)\}/)[1];
 for(const declaration of ['display:flex','flex-direction:row','flex-wrap:nowrap','white-space:nowrap','flex-shrink:0'])assert.ok(rule.includes(declaration),declaration);
 assert.doesNotMatch(css,/\.trial-test\{[^}]*flex-direction:column/);
 for(const state of ['未実施','実行中','OK','NG']){
  const html=await render('設定モデル/設定モデルパネル.vue',{data:{項目:[{id:'CHAT',区分:'CHAT',モデル:'long-model-name'}]},results:{CHAT:{状態:state}},selected:'CHAT',online:true,running:state==='実行中'});
  assert.match(html,new RegExp('class="trial-test"[^]*?<button[^]*?テスト</button>[^]*?class="badge"[^]*?data-state="'+state+'"'));
 }
});
