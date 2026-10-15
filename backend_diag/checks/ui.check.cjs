const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const source=name=>fs.readFileSync(path.join(__dirname,'../ui/src',name),'utf8');
test('Vue component source and precompiled runtime use no remote scripts or unsafe eval',()=>{
 const app=source('App.vue');assert.match(app,/インストール\/インストールパネル\.vue/);assert.match(app,/モデルキー設定パネル/);
 const html=fs.readFileSync(path.join(__dirname,'../static/index.html'),'utf8');assert.match(html,/src="app.js"/);assert.doesNotMatch(html,/https?:|unpkg|cdn/);
 const js=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');assert.doesNotMatch(js,/new Function\(|eval\(/);
});
test('all-tests and install panel share only installation action, key tests require explicit row action',()=>{
 const app=source('App.vue');const install=source('インストール/インストール状態.mjs');
 assert.match(install,/api\/診断/);assert.doesNotMatch(install,/キーテスト|testKey|loadKeys/);
 assert.match(app,/<button id="run"[^>]*@click="全診断"/);assert.match(app,/async function 全診断\(\)\{if\(!await 全テスト\(\)\)return;await 最新モデル取得\(\);await モデル書込\(\);\}/);
 assert.match(app,/@確認="インストール確認"/);assert.match(app,/@書込="書込"/);assert.match(install,/全テスト\(\) \{ return await インストール確認\(\) && await 書込\(\); \}/);assert.match(app,/@test="testKey"/);
 assert.match(app,/onMounted\(\(\)=>\{if\(key.value\)connect\(\);\}\)/);
 assert.match(source('モデルキー設定/モデルキー設定パネル.vue'),/まだモデルを取得していません/);
});
test('auth remains in memory with relative API and refresh discards stale key results',()=>{
 const app=source('App.vue');assert.match(app,/history.replaceState/);assert.match(app,/new URL\(path,location.href\)/);assert.match(app,/credentials:'same-origin'/);assert.doesNotMatch(app,/localStorage|sessionStorage/);
 const state=source('キー設定共通/キー設定状態.mjs');assert.match(state,/keyData.value=null;keyResults.value=\{\};try\{const data=await api\('api\/キー設定'\)/);
 assert.match(state,/generation===keyGeneration/);
 assert.match(app,/response.status===401/);
});
test('states and safe text interpolation preserve hierarchy and model text rendering',()=>{
 const install=source('インストール/インストールパネル.vue')+source('インストール/インストール表示.mjs');for(const label of ['未確認','ベース','CLI群','その他拡張'])assert.ok(install.includes(label));
 const keys=source('モデルキー設定/モデルキー設定パネル.vue');assert.match(keys,/\{\{model\}\}/);assert.match(keys,/未実施/);assert.match(source('キー設定共通/キー設定表示.mjs'),/設定済/);assert.match(source('キー設定共通/キー設定表示.mjs'),/未設定/);
 assert.doesNotMatch(source('App.vue')+install+keys,/v-html|innerHTML/);
 const catalog=JSON.parse(fs.readFileSync(path.join(__dirname,'../診断/catalog.json'),'utf8'));assert.equal(catalog.length,19);assert.deepEqual(catalog.filter(e=>e.menuGroup==='ベース').map(e=>e.name),['Python','uv','Node.js','npm','npx','Electron']);
});
test('checked-in compiled assets match current Vue sources',async()=>{const {verify}=await import('../ui/verify.mjs');assert.equal(await verify(),true);});
test('source edits and altered bundle invalidate deployment manifest',async()=>{
 const os=require('node:os');const {pathToFileURL}=require('node:url');const folder=fs.mkdtempSync(path.join(os.tmpdir(),'diag-build-sync-'));
 try{const root=path.join(__dirname,'..');fs.cpSync(path.join(root,'ui'),path.join(folder,'ui'),{recursive:true,filter:file=>!file.split(path.sep).includes('node_modules')});fs.cpSync(path.join(root,'static'),path.join(folder,'static'),{recursive:true});fs.cpSync(path.join(root,'runtime'),path.join(folder,'runtime'),{recursive:true});
 const {verify}=await import(pathToFileURL(path.join(folder,'ui/verify.mjs')));assert.equal(await verify(),true);
 const app=path.join(folder,'ui/src/App.vue'),original=fs.readFileSync(app);fs.appendFileSync(app,'\n<!-- stale source -->\n');assert.equal(await verify(),false);fs.writeFileSync(app,original);
 fs.appendFileSync(path.join(folder,'static/app.js'),'\n// changed bundle\n');assert.equal(await verify(),false);
 }finally{fs.rmSync(folder,{recursive:true,force:true});}
});
test('config key order and public acquisition status are separate from tests with no router prerequisite',async()=>{
 const app=source('App.vue'),panel=source('モデルキー設定/モデルキー設定パネル.vue');const {KEY_PROVIDERS}=await import('../モデル情報/key_status.mjs');assert.deepEqual(KEY_PROVIDERS.slice(0,9).map(row=>row.id),['gemini','freeai','claude','openai','openai_oauth','grok','azure','copilot','openrt']);
 assert.match(panel,/公開モデル一覧取得: <component :is="状態バッジ" class="public-indicator" :state="公開状態"\/>/);const view=source('モデルキー設定/モデルキー設定表示.mjs');assert.match(view,/取得元 === 'キャッシュ' \? 'キャッシュ利用' : 'OK'/);
 assert.doesNotMatch(app+panel,/prerequisite|先に実行してください|OpenRouter を選択/);assert.match(panel,/public-indicator/);const state=source('キー設定共通/キー設定状態.mjs');assert.match(state,/api\/公開モデル/);assert.match(state,/Number\(data.世代\)>=Number\(publicModels.value.世代\)/);assert.match(app,/response.status===401\)\{設定を破棄\(\)/);assert.match(state,/generation!==publicGeneration/);
});
test('Vue templates never use non-ASCII component tags (rendered as raw text); use <component :is>',()=>{
 const walk=dir=>fs.readdirSync(dir,{withFileTypes:true}).flatMap(entry=>entry.isDirectory()?walk(path.join(dir,entry.name)):entry.name.endsWith('.vue')?[path.join(dir,entry.name)]:[]);
 for(const file of walk(path.join(__dirname,'../ui/src'))){
  const template=(fs.readFileSync(file,'utf8').match(/<template>([\s\S]*)<\/template>/)||['',''])[1];
  assert.doesNotMatch(template,/<\/?[^\x00-\x7F]/,path.relative(path.join(__dirname,'..'),file));
 }
});
test('all-tests button sits at the end of the tab bar without the scope caption',()=>{
 const app=source('App.vue');const tabs=app.match(/<nav class="tabs"[^]*?<\/nav>/)[0];
 assert.match(tabs,/<button id="run" class="run-all"[^>]*>[^<]*<\/button><\/nav>$/);
 assert.doesNotMatch(app,/全テストの対象/);
 // tools 接続確認の ON/OFF・再確認の行は持たない（接続状態はステータスバーに表示）。
 assert.doesNotMatch(app,/component-toolbar|tools-toggle|tools接続確認|再確認/);assert.match(app,/:enabled="true"/);
});
