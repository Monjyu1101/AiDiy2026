const test=require('node:test');
const assert=require('node:assert/strict');
const {render,source}=require('./ui-components.cjs');
const value=value=>({value});

function startState({empty=false,loading=false,busy=false}={}){
 const item={id:'web',名前:'Web',フォルダ:'frontend_web',状態:'稼働中',設定:{起動対象:true,自動再起動:true,ブラウザ表示:true}};
 return {
  項目:value(empty?[]:[item]),選択:value(empty?'':'web'),選択対象:value(empty?null:item),
  停止警告対象:value(new Set()),ポート項目:value([{id:'web',開放:true}]),
  保存表示:value('設定を保存しました'),コンソール:value('fixture log'),読込中:value(loading),
  保存中:value(busy),処理中:value(busy),起動中:value(busy),通知:value(''),
  ブラウザ起動可能:value(true),ブラウザ起動中:value(false),ブラウザ通知:value(''),
 };
}
function appState({empty=false,folder='',busy=false}={}){
 return {
  一覧:value(null),フォルダ:value(folder),処理中:value(busy?'code':''),選択中:value(false),通知:value(''),
  項目:value(empty?[]:[{id:'code',名前:'Code',単一起動:false}]),結果:value({}),読込:async()=>{},
 };
}

test('通常のシステム起動は未接続・空・読込中・処理中でもページ内ミニボタンを持たない',async()=>{
 for(const online of [true,false])for(const options of [{},{empty:true},{loading:true},{busy:true}]){
  const html=await render('起動/起動パネル.vue',{state:startState(options),online,visible:true});
  assert.doesNotMatch(html,/ミニ表示|start-mini-switch/);
  assert.match(html,/システム起動/);assert.match(html,/class="start-save"[^>]*>設定を保存しました/);
  if(!options.empty&&!options.loading){
   for(const label of ['再起動','停止（Ctrl+C）','手動で開く'])assert.ok(html.includes(label),label);
   assert.match(html,/role="log"/);assert.equal((html.match(/type="checkbox"/g)||[]).length,3);
  }
 }
 assert.doesNotMatch(source('起動/起動パネル.vue'),/defineEmits|\$emit\(['"]mini['"]\)/);
});

test('通常のアプリ起動は未接続・未選択・処理中でもページ内ミニボタンを持たない',async()=>{
 for(const online of [true,false])for(const options of [{},{empty:true},{folder:'/fixture/project'},{folder:'/fixture/project',busy:true}]){
  const html=await render('アプリ起動/アプリ起動パネル.vue',{state:appState(options),online,visible:true});
  assert.doesNotMatch(html,/ミニ表示/);assert.match(html,/フォルダ選択/);
  if(options.folder)assert.match(html,/>解除<\/button>/);
  if(!options.empty){
   assert.match(html,/class="app-launch-button"/);
   assert.ok(html.includes(options.busy?'起動確認中…':'Code を起動'));
   const launch=html.match(/<button class="app-launch-button"[^>]*>/)[0];
   assert.equal(/ disabled(?:[ >])/.test(launch),!online||!options.folder||!!options.busy);
  }
 }
 assert.doesNotMatch(source('アプリ起動/アプリ起動パネル.vue'),/defineEmits|\$emit\(['"]mini['"]\)/);
});

test('ミニ切替の配線はタイトルバーだけに残し、通常ページの表示条件を維持する',async()=>{
 const app=source('App.vue');
 assert.equal((app.match(/@mini=/g)||[]).length,1);
 assert.match(app,/<component :is="ステータスバー"[^>]*@mini="ミニ\.変更\(true\)"[^>]*@restore="ミニ\.変更\(false\)"/);
 for(const [name,tab] of [['起動パネル','start'],['アプリ起動パネル','apps']]){
  const panel=app.match(new RegExp(`<component :is="${name}"[^>]*>`))[0];
  assert.ok(panel.includes(`:visible="tab==='${tab}'&&!ミニ表示"`));assert.doesNotMatch(panel,/@mini=/);
 }
 for(const connected of [true,false]){
  const html=await render('ウィンドウ/ステータスバー.vue',{connected,compact:false});
  assert.equal((html.match(/aria-label="ミニ表示"/g)||[]).length,1);
  const button=html.match(/<button class="title-mini-switch"[^>]*>/)[0];
  assert.equal(/ disabled(?:[ >])/.test(button),!connected);
 }
});
