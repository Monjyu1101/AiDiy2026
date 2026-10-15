const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const source=name=>fs.readFileSync(path.join(__dirname,'../ui/src',name),'utf8');
test('Vue component source and precompiled runtime use no remote scripts or unsafe eval',()=>{
 const app=source('App.vue');assert.match(app,/InstallPanel/);assert.match(app,/KeyPanel/);
 const html=fs.readFileSync(path.join(__dirname,'../static/index.html'),'utf8');assert.match(html,/src="app.js"/);assert.doesNotMatch(html,/https?:|unpkg|cdn/);
 const js=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');assert.doesNotMatch(js,/new Function\(|eval\(/);
});
test('all-tests and install panel share only installation action, key tests require explicit row action',()=>{
 const app=source('App.vue');const install=app.match(/async function runInstall\(\)\{([\s\S]*?)\nasync function loadKeys/)[1];
 assert.match(install,/api\/診断/);assert.doesNotMatch(install,/キーテスト|testKey|loadKeys/);
 assert.match(app,/<button id="run"[^>]*@click="runInstall"/);
 assert.match(app,/@run="runInstall"/);assert.match(app,/@test="testKey"/);
 assert.match(app,/onMounted\(\(\)=>\{if\(key.value\)connect\(\);\}\)/);
 assert.match(source('KeyPanel.vue'),/まだモデルを取得していません/);
});
test('auth remains in memory with relative API and refresh discards stale key results',()=>{
 const app=source('App.vue');assert.match(app,/history.replaceState/);assert.match(app,/new URL\(path,location.href\)/);assert.match(app,/credentials:'same-origin'/);assert.doesNotMatch(app,/localStorage|sessionStorage/);
 assert.match(app,/keyData.value=null;keyResults.value=\{\};try\{const data=await api\('api\/キー設定'\)/);
 assert.match(app,/generation===keyGeneration/);
 assert.match(app,/response.status===401/);
});
test('states and safe text interpolation preserve hierarchy and model text rendering',()=>{
 const install=source('InstallPanel.vue');for(const label of ['未確認','未検出','OK','NG','ERR','ベース','CLI群','その他拡張'])assert.ok(install.includes(label));
 const keys=source('KeyPanel.vue');assert.match(keys,/\{\{model\}\}/);assert.match(keys,/未実施/);assert.match(keys,/設定済/);assert.match(keys,/未設定/);
 assert.doesNotMatch(source('App.vue')+install+keys,/v-html|innerHTML/);
 const catalog=JSON.parse(fs.readFileSync(path.join(__dirname,'../catalog.json'),'utf8'));assert.equal(catalog.length,19);assert.deepEqual(catalog.filter(e=>e.menuGroup==='ベース').map(e=>e.name),['Python','uv','Node.js','npm','npx','Electron']);
});
test('checked-in compiled assets match current Vue sources',async()=>{const {verify}=await import('../ui/verify.mjs');assert.equal(await verify(),true);});
test('source edits and altered bundle invalidate deployment manifest',async()=>{
 const os=require('node:os');const {pathToFileURL}=require('node:url');const folder=fs.mkdtempSync(path.join(os.tmpdir(),'diag-build-sync-'));
 try{const root=path.join(__dirname,'..');fs.cpSync(path.join(root,'ui'),path.join(folder,'ui'),{recursive:true,filter:file=>!file.split(path.sep).includes('node_modules')});fs.cpSync(path.join(root,'static'),path.join(folder,'static'),{recursive:true});
 const {verify}=await import(pathToFileURL(path.join(folder,'ui/verify.mjs')));assert.equal(await verify(),true);
 const app=path.join(folder,'ui/src/App.vue'),original=fs.readFileSync(app);fs.appendFileSync(app,'\n<!-- stale source -->\n');assert.equal(await verify(),false);fs.writeFileSync(app,original);
 fs.appendFileSync(path.join(folder,'static/app.js'),'\n// changed bundle\n');assert.equal(await verify(),false);
 }finally{fs.rmSync(folder,{recursive:true,force:true});}
});
test('config key order and public acquisition status are separate from tests with no router prerequisite',async()=>{
 const app=source('App.vue'),panel=source('KeyPanel.vue');const {KEY_PROVIDERS}=await import('../key_status.mjs');assert.deepEqual(KEY_PROVIDERS.slice(0,7).map(row=>row.id),['gemini','freeai','claude','openai','azure','copilot','openrt']);
 for(const label of ['公開モデル取得済','公開モデル取得中','公開モデル取得失敗','公開モデル未取得'])assert.ok(panel.includes(label));
 assert.doesNotMatch(app+panel,/prerequisite|先に実行してください|OpenRouter を選択/);assert.match(panel,/public-indicator/);assert.match(app,/api\/公開モデル/);assert.match(app,/Number\(data.世代\)>=Number\(publicModels.value.世代\)/);assert.match(app,/response.status===401\)\{resetPublic\(\)/);assert.match(app,/generation!==publicGeneration/);
});
