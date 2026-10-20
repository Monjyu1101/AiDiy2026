// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
// タスク / チームの実SFCを合成APIで実行する。実AI・実サーバーへの通信や保存は行わない。
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { createRequire } = require('node:module');
const root = path.resolve(__dirname, '../..');
const projects = ['frontend_web', 'frontend_avatar'];
const providers = ['claude_sdk', 'claude_cli', 'claude_ollama', 'copilot_cli', 'codex_cli', 'codex_ollama', 'antigravity_cli', 'grok_cli', 'opencode_cli', 'aidiy_hermes'];
const dialogs = [
  {name: 'task detail', file: 'AIタスク/dialog/AIタスク_明細編集.vue', fields: {TASK: ['do']}, save: '登録', endpoint: '/task/タスク明細/更新登録', event: 'registered'},
  {name: 'task request', file: 'AIタスク/dialog/AIタスク_要求編集.vue', fields: {TASK: ['plan', 'do', 'check']}, save: '登録', endpoint: '/task/タスク要求/更新登録', event: 'registered'},
  {name: 'team request', file: 'AIチーム/dialog/AIチーム_依頼編集.vue', fields: {TEAM: ['plan', 'do', 'check'], TASK: ['plan', 'do', 'check']}, save: '登録', endpoint: '/team/依頼/変更', event: 'saved'},
  {name: 'team goal', file: 'AIチーム/dialog/AIチーム_目標編集.vue', fields: {TEAM: ['plan', 'do', 'check'], TASK: ['plan', 'do', 'check']}, save: '保存', endpoint: '/team/目標/保存', event: 'saved'},
  {name: 'team conversation', file: 'AIチーム/dialog/AIチーム_会話要求.vue', fields: {TASK: ['plan']}, save: '会話送信', endpoint: '/team/エージェント/会話'},
];
function fixture() {
  const code_models = Object.fromEntries(providers.map(p => [p, {auto: 'Auto', same: 'Same', ...Object.fromEntries(['plan','do','check'].map(phase => [`${p === 'opencode_cli' ? 'openai' : p === 'aidiy_hermes' ? 'openai_oauth' : p}/${phase}`, phase]))}]));
  const settings = {CODE_BASE_PATH: '/fixture/project', TEAM_AI_NAME: 'claude_cli', TASK_AI_NAME: 'opencode_cli'};
  for (const group of ['TEAM','TASK']) for (const phase of ['plan','do','check']) settings[`${group}_AI_MODEL_${phase}`] = `${group === 'TEAM' ? 'claude_cli' : 'openai'}/${phase}`;
  const saved = {...settings, タスクID: 'fixture-task', 明細SEQ: 1, 依頼ID: 'fixture-work', 要員ID: 'fixture-owner', 利用者ID: 'fixture-owner', タイトル: 'Fixture', プロジェクト: '/fixture/project', 要求内容: 'Fixture request', チーム目標: 'Fixture goal', チーム作業: 'Fixture work', 実行有効: false, 状態: '中止'};
  return {code_models, settings, saved};
}
function load(project, dialog, data = fixture(), propOverrides = {}) {
  const localRequire = createRequire(path.join(root, project, 'package.json'));
  const vue = localRequire('vue'), ts = localRequire('typescript'), compiler = localRequire('@vue/compiler-sfc');
  const filename = path.join(root, project, 'src/components', dialog.file);
  const {descriptor, errors} = compiler.parse(fs.readFileSync(filename,'utf8'), {filename});
  assert.deepEqual(errors, []);
  const compiled = compiler.compileScript(descriptor, {id: 'taskteam-test'});
  assert.deepEqual(compiler.compileTemplate({source: descriptor.template.content, filename, id: 'taskteam-test', compilerOptions: {bindingMetadata: compiled.bindings}}).errors, []);
  const source = descriptor.scriptSetup.content.replace(/^import .*$/gm, '');
  const parsed = ts.createSourceFile(filename, source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS);
  const bindings = parsed.statements.flatMap(s => ts.isVariableStatement(s) ? s.declarationList.declarations.map(d => d.name.text) : ts.isFunctionDeclaration(s) ? [s.name.text] : []).filter(Boolean);
  const js = ts.transpileModule(source, {compilerOptions: {target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.None}}).outputText;
  const calls = [], emits = [], messages = [], scope = vue.effectScope();
  const props = vue.reactive({isOpen: false, 編集明細: structuredClone(data.saved), 編集タスク: structuredClone(data.saved), 最終タスク: null, 編集依頼: structuredClone(data.saved), 最終依頼: null, エージェント: {id: 'fixture-agent'}, チーム目標: structuredClone(data.saved), 利用者ID: 'fixture-user', 利用者名: 'Fixture user', ...propOverrides});
  const client = clientName => ({post: async (url, body, options) => {
    calls.push({url, body: structuredClone(body), options, clientName});
    if (data.failModels && url.includes('TASK選択肢')) throw new Error('fixture model unavailable');
    let result;
    if (url === '/core/AIコア/モデル情報/TASK選択肢') result = {available_models: {code_models: structuredClone(data.code_models)}, モデル設定: structuredClone(data.settings)};
    else if (url === '/team/設定/取得') result = structuredClone(data.settings);
    else if (url === '/task/プロジェクト選択肢') result = {選択肢: {'/fixture/project': 'Fixture project'}};
    else if (url === '/task/タスク要求/新規既定値') result = structuredClone(data.newDefaults || data.saved);
    else if (url === '/team/目標/一覧') result = {items: data.goals || [structuredClone(data.saved)]};
    else if (url === '/team/要員/一覧') result = {items: [{要員ID:'fixture-agent'}]};
    else if (url === '/task/タスク明細/一覧') result = {items: []};
    else if (url === '/task/タスク実行条件/取得') result = {item: null};
    else if (url === '/team/エージェント/会話') result = {応答内容: 'Fixture response'};
    else if (['/task/タスク明細/更新登録','/task/タスク要求/更新登録','/task/タスク要求/AI登録','/team/依頼/変更','/team/依頼/登録','/team/目標/保存'].includes(url)) result = {item: {...body, 依頼ID:'fixture-work'}};
    else throw new Error(`Unexpected fixture API: ${url}`);
    return {data: {status:'OK', message:'Fixture OK', data:result}};
  }});
  const dependencies = {...vue, defineProps: () => props, defineEmits: () => (...args) => emits.push(args), onBeforeUnmount: () => {}, apiClient: client('core'), taskClient: client('task'), teamClient: client('team'), useAuthStore: () => ({user:{利用者ID:'fixture-user', 利用者名:'Fixture user'}}), qMessage: (...args) => messages.push(args), qConfirm: async () => true};
  const app = scope.run(() => new Function(...Object.keys(dependencies), `${js}\nreturn {${bindings.join(',')}};`)(...Object.values(dependencies)));
  const templateCode = compiler.compileTemplate({source: descriptor.template.content, filename, id: 'taskteam-test', compilerOptions: {bindingMetadata: compiled.bindings}}).code;
  const templateModule = {exports: {}};
  const templateJs = ts.transpileModule(templateCode, {compilerOptions: {target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.CommonJS}}).outputText;
  new Function('require', 'module', 'exports', templateJs)(id => {assert.equal(id, 'vue');return {...vue, withDirectives: node => node};}, templateModule, templateModule.exports);
  const walk = (node, predicate) => {
    if (predicate(node)) return node;
    const children = Array.isArray(node?.children) ? node.children : node?.children?.default?.() || [];
    for (const child of children) {const found = walk(child, predicate);if (found) return found;}
  };
  const render = () => templateModule.exports.render({}, [], props, vue.proxyRefs(app), {}, {});
  const control = field => walk(render(), node => node?.type === 'select' && String(node.props?.['onUpdate:modelValue']).includes(`入力${field})`));
  return {...app, control,
    async choose(field, value) {
      const node = control(field);assert.ok(node, `actual select for ${field}`);assert.ok(!node.props.disabled);
      const el = new EventTarget(), options = [];
      walk(node, child => {if (child?.type === 'option') options.push({_value: child.props.value, selected: false});return false;});
      Object.assign(el, {options, multiple: false});
      Object.defineProperty(el, 'selectedIndex', {get: () => options.findIndex(o => o.selected), set: index => options.forEach((o, i) => o.selected = i === index)});
      vue.vModelSelect.created(el, {value: '', modifiers: {}}, node);
      vue.vModelSelect.mounted(el, {value: ''});
      el.addEventListener('change', event => {for (const fn of [node.props.onChange].flat().filter(Boolean)) fn(event);});
      el.selectedIndex = options.findIndex(o => o._value === value);assert.notEqual(el.selectedIndex, -1, `${field}: ${value}`);
      el.dispatchEvent(new Event('change'));await this.flush();
      assert.equal(app[`入力${field}`].value, value, `${field}: native change updates selection`);
    }, props, calls, emits, messages, template: descriptor.template.content, nextTick: vue.nextTick, close: () => scope.stop(), async flush() {for(let i=0;i<12;i++) await vue.nextTick(); await new Promise(resolve => setImmediate(resolve)); await vue.nextTick();}, async open(){props.isOpen=true;await this.flush();}};
}
function values(app, dialog) {return Object.fromEntries(Object.entries(dialog.fields).flatMap(([g,phases]) => [[`${g}_AI_NAME`, app[`入力${g}_AI_NAME`].value], ...phases.map(p => [`${g}_AI_MODEL_${p}`,app[`入力${g}_AI_MODEL_${p}`].value])]));}
function options(app, group) {const options = app[`${group === 'TEAM' ? 'team' : 'task'}ModelOptions`] || app[`${group}モデル選択肢`];return options.value.map(o => o.value);}
async function saveAndAssert(app, dialog, expectedEndpoint = dialog.endpoint) {
  if(app.入力要求内容) app.入力要求内容.value = 'Fixture request';
  await app[dialog.save]();await app.flush();
  const call=app.calls.findLast(c=>c.url===expectedEndpoint);assert.ok(call,JSON.stringify(app.messages));
  for(const [key,value] of Object.entries(values(app,dialog))) assert.equal(call.body[key],value,`${dialog.name}: payload ${key}`);
  if(dialog.event) {
    const emitted=app.emits.findLast(e=>e[0]===dialog.event);assert.ok(emitted,`${dialog.name}: ${dialog.event}`);
    for(const [key,value] of Object.entries(values(app,dialog))) assert.equal(emitted[1][key],value,`${dialog.name}: emitted ${key}`);
  } else assert.equal(app.応答内容.value,'Fixture response');
  if(expectedEndpoint.startsWith('/team/') && app.calls.some(c=>c.clientName==='team')) assert.equal(call.clientName,'team');
  if(expectedEndpoint.startsWith('/task/') && app.calls.some(c=>c.clientName==='task')) assert.equal(call.clientName,'task');
  return call;
}
for(const project of projects) {
  test(`${project}: all five dialogs bind all 24 native provider/model selects`, () => {
    const actual = [];
    for (const category of ['AIタスク', 'AIチーム']) {
      const directory = path.join(root, project, 'src/components', category, 'dialog');
      for (const name of fs.readdirSync(directory).filter(name => name.endsWith('.vue'))) {
        if (/<select[^>]*v-model="入力(?:TEAM|TASK)_AI_/.test(fs.readFileSync(path.join(directory, name), 'utf8'))) actual.push(`${category}/dialog/${name}`);
      }
    }
    assert.deepEqual(actual.sort(), dialogs.map(dialog => dialog.file).sort());
    let count=0;
    for(const dialog of dialogs){const app=load(project,dialog);try{for(const field of Object.keys(values(app,dialog))){assert.match(app.template,new RegExp(`<select[^>]*v-model="入力${field}"`));count++;}}finally{app.close();}}
    assert.equal(count,24);
  });
  for(const dialog of dialogs) {
    test(`${project}: ${dialog.name} preserves saved values, changes every provider/phase and captures save/emit`,async()=>{
      const data=fixture(),app=load(project,dialog,data);
      try{
        await app.open();
        for(const [key,value] of Object.entries(values(app,dialog))) assert.equal(value,data.saved[key],`saved ${key}`);
        await saveAndAssert(app,dialog);
        for(const provider of providers){
          for(const [group,phases] of Object.entries(dialog.fields)){
            app[`入力${group}_AI_NAME`].value=provider;await app.flush();
            for(const phase of phases) assert.ok(options(app,group).includes(app[`入力${group}_AI_MODEL_${phase}`].value),`${provider}/${group}/${phase} cascade`);
            for(const model of Object.keys(data.code_models[provider])){
              for(const phase of phases)app[`入力${group}_AI_MODEL_${phase}`].value=model;
              await app.flush();
              for(const phase of phases) assert.equal(app[`入力${group}_AI_MODEL_${phase}`].value,model,`${provider}/${phase}`);
              await saveAndAssert(app,dialog);
            }
          }
        }
        assert.ok(app.calls.every(c=>!c.url.includes('再起動')));
      }finally{app.close();}
    });
    test(`${project}: ${dialog.name} failed model loading leaves selectable fallback and saves it`,async()=>{
      const data=fixture();data.failModels=true;const app=load(project,dialog,data);
      try{await app.open();for(const [group,phases] of Object.entries(dialog.fields))for(const phase of phases)assert.ok(options(app,group).includes(app[`入力${group}_AI_MODEL_${phase}`].value));await saveAndAssert(app,dialog);}finally{app.close();}
    });
  }
  test(`${project}: actual template select change handlers save all 24 provider/model fields`,async()=>{
    let count=0;
    for(const dialog of dialogs){
      const app=load(project,dialog);
      try{
        await app.open();
        for(const [group,phases] of Object.entries(dialog.fields)){
          await app.choose(`${group}_AI_NAME`,'aidiy_hermes');count++;
          for(const phase of phases){await app.choose(`${group}_AI_MODEL_${phase}`,'openai_oauth/check');count++;}
        }
        await saveAndAssert(app,dialog);
        if(dialog.name==='team request'){
          await app.choose('TEAM_AI_NAME','claude_cli');
          await app.choose('TASK_AI_NAME','opencode_cli');
          await app.choose('TASK_AI_MODEL_do','openai/do');
          await app.choose('TEAM_AI_MODEL_do','claude_cli/do');
          assert.equal(app.入力TASK_AI_MODEL_do.value,'openai/do');
          await saveAndAssert(app,dialog);
        }
      }finally{app.close();}
    }
    assert.equal(count,24);
  });
  test(`${project}: new task/team requests submit each saved phase without collapsing to one model`,async()=>{
    for(const name of ['task request','team request']){const dialog=dialogs.find(d=>d.name===name),data=fixture();const app=load(project,dialog,data,{編集タスク:null,編集依頼:null,最終タスク:data.saved,最終依頼:data.saved});try{await app.open();for(const [key,value]of Object.entries(values(app,dialog)))assert.equal(value,data.saved[key]);await saveAndAssert(app,dialog,name==='task request'?'/task/タスク要求/AI登録':'/team/依頼/登録');}finally{app.close();}}
  });
  test(`${project}: TEAM provider change copies provider/phases, but independent TASK provider and values survive phase-only changes`,async()=>{
    const dialog=dialogs.find(d=>d.name==='team request'),app=load(project,dialog);
    try{
      await app.open();
      app.入力TEAM_AI_NAME.value='aidiy_hermes';await app.flush();
      assert.equal(app.入力TASK_AI_NAME.value,'aidiy_hermes');
      for(const phase of ['plan','do','check']){
        app[`入力TEAM_AI_MODEL_${phase}`].value=`openai_oauth/${phase}`;await app.flush();
        assert.equal(app[`入力TASK_AI_MODEL_${phase}`].value,`openai_oauth/${phase}`);
      }
      app.入力TASK_AI_NAME.value='opencode_cli';await app.flush();
      for(const phase of ['plan','do','check'])app[`入力TASK_AI_MODEL_${phase}`].value=`openai/${phase}`;
      for(const phase of ['plan','do','check'])app[`入力TEAM_AI_MODEL_${phase}`].value='same';
      await app.flush();assert.equal(app.入力TASK_AI_NAME.value,'opencode_cli');
      for(const phase of ['plan','do','check'])assert.equal(app[`入力TASK_AI_MODEL_${phase}`].value,`openai/${phase}`);
      await saveAndAssert(app,dialog);
      app.入力TEAM_AI_NAME.value='grok_cli';await app.flush();
      assert.equal(app.入力TASK_AI_NAME.value,'grok_cli');
      for(const phase of ['plan','do','check'])assert.equal(app[`入力TASK_AI_MODEL_${phase}`].value,app[`入力TEAM_AI_MODEL_${phase}`].value);
      await saveAndAssert(app,dialog);
    }finally{app.close();}
  });
  test(`${project}: separated TASK provider never receives an unsupported TEAM model`,async()=>{
    const dialog=dialogs.find(d=>d.name==='team request'),app=load(project,dialog);
    try{await app.open();app.入力TASK_AI_NAME.value='codex_cli';await app.flush();app.入力TEAM_AI_MODEL_do.value='claude_cli/plan';await app.flush();assert.ok(options(app,'TASK').includes(app.入力TASK_AI_MODEL_do.value),`TASK ${app.入力TASK_AI_NAME.value} received invisible model ${app.入力TASK_AI_MODEL_do.value}`);await saveAndAssert(app,dialog);}finally{app.close();}
  });
}
