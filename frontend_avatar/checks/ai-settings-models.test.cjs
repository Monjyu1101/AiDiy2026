// Web / Avatar の実際の SFC スクリプトを Vue のリアクティビティで実行する。API は合成データのみ。
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { createRequire } = require('node:module');
const root = path.resolve(__dirname, '../..');
const providers = ['claude_sdk', 'claude_cli', 'claude_ollama', 'copilot_cli', 'codex_cli', 'codex_ollama', 'antigravity_cli', 'grok_cli', 'opencode_cli', 'aidiy_hermes'];

function fixture() {
  const settings = {CODE_BASE_PATH: '../', CODE_PERMISSIONS: 'auto', TASK_AI_NAME: 'codex_cli', TEAM_AI_NAME: 'aidiy_hermes'};
  const code_models = Object.fromEntries(providers.map(provider => {
    settings[`CODE_${provider.toUpperCase()}_MODEL`] = provider === 'grok_cli' ? 'same' : provider === 'opencode_cli' ? 'openai/custom' : 'auto';
    return [provider, {auto: 'auto', same: 'same', custom: 'Custom', 'openai/custom': 'OpenCode', 'openai_oauth/custom': 'Hermes'}];
  }));
  for (let index = 1; index <= 6; index++) {
    settings[`CODE_AI${index}_NAME`] = providers[index - 1];
    settings[`CODE_AI${index}_MODEL`] = index % 2 ? 'custom' : 'same';
  }
  for (const group of ['TASK', 'TEAM']) for (const phase of ['plan', 'do', 'check']) settings[`${group}_AI_MODEL_${phase}`] = phase === 'plan' ? 'custom' : 'same';
  return {settings, code_models};
}

function load(project, filename, data) {
  const requireLocal = createRequire(path.join(root, project, 'package.json'));
  const vue = requireLocal('vue'), ts = requireLocal('typescript'), compiler = requireLocal('@vue/compiler-sfc');
  const source = fs.readFileSync(path.join(root, filename), 'utf8');
  const {descriptor, errors} = compiler.parse(source);
  assert.deepEqual(errors, []);
  const compiled = compiler.compileScript(descriptor, {id: 'settings-test'});
  assert.deepEqual(compiler.compileTemplate({source: descriptor.template.content, filename, id: 'settings-test', compilerOptions: {bindingMetadata: compiled.bindings}}).errors, []);
  const script = descriptor.scriptSetup.content.replace(/^import .*$/gm, '');
  const js = ts.transpileModule(script, {compilerOptions: {target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.None}}).outputText;
  const calls = [], scope = vue.effectScope();
  const dependencies = {...vue, onMounted: () => {}, defineProps: () => ({isOpen: false, sessionId: 'fixture'}), defineEmits: () => () => {},
    apiClient: {post: async (url, body) => {calls.push({url, body});return {data: {status: 'OK', data: {available_models: {code_models: data.code_models}, モデル設定: structuredClone(data.settings)}}};}},
    qAlert: async () => {}, qMessage: async () => {}, qConfirm: async () => true};
  const api = scope.run(() => new Function(...Object.keys(dependencies), js + '\nreturn {selections, errorMessage, loadConfig, buildNextSettings, handleCodeAiChange, copyCode1Settings, copyCode4Settings, handleTaskAiChange, handleTeamAiChange, handleSaveOnly};')(...Object.values(dependencies)));
  return {...api, calls, nextTick: vue.nextTick, close: () => scope.stop(), template: descriptor.template.content};
}

for (const [project, filename] of [['frontend_web', 'frontend_web/src/components/AiDiy/dialog/AI設定再起動.vue'], ['frontend_avatar', 'frontend_avatar/src/dialog/AI設定再起動.vue']]) {
  test(`${project}: saved values survive loading and every Code slot uses the provider default on manual change`, async () => {
    const data = fixture(), app = load(project, filename, data);
    try {
      await app.loadConfig();await app.nextTick();assert.equal(app.errorMessage.value, '');
      for (let index = 1; index <= 6; index++) {
        assert.equal(app.selections[`codeModel${index}`], data.settings[`CODE_AI${index}_MODEL`]);
        assert.match(app.template, new RegExp(`id="config-code-ai${index}-select"[^>]*@change="handleCodeAiChange\\(${index}\\)"`));
      }
      for (const [key, value] of Object.entries(data.settings)) assert.equal(app.buildNextSettings()[key], value, key);
      for (const provider of providers) for (let index = 1; index <= 6; index++) {
        app.selections[`codeAi${index}`] = provider;
        app.handleCodeAiChange(index);await app.nextTick();
        assert.equal(app.selections[`codeModel${index}`], data.settings[`CODE_${provider.toUpperCase()}_MODEL`], `${provider}/${index}`);
      }
      assert.equal(app.calls.length, 1);
    } finally {app.close();}
  });

  test(`${project}: explicit model copies survive cascades and save payloads retain Grok same and prefixed models`, async () => {
    const app = load(project, filename, fixture());
    try {
      await app.loadConfig();
      app.selections.codeAi1 = 'grok_cli';app.handleCodeAiChange(1);await app.nextTick();
      for (let index = 1; index <= 6; index++) assert.equal(app.selections[`codeModel${index}`], 'same');
      app.selections.codeModel1 = 'custom';app.copyCode1Settings();await app.nextTick();
      for (let index = 1; index <= 6; index++) assert.equal(app.selections[`codeModel${index}`], 'custom');
      app.selections.codeAi4 = 'opencode_cli';app.handleCodeAiChange(4);await app.nextTick();
      for (const index of [4, 5, 6]) assert.equal(app.selections[`codeModel${index}`], 'openai/custom');
      assert.equal(app.selections.codeModel3, 'custom');
      app.selections.codeAi5 = 'grok_cli';app.handleCodeAiChange(5);
      app.selections.codeAi6 = 'aidiy_hermes';app.handleCodeAiChange(6);
      app.selections.codeModel6 = 'openai_oauth/custom';
      app.selections.taskAi = 'grok_cli';app.handleTaskAiChange();await app.nextTick();
      for (const key of ['taskModelPlan', 'taskModelDo', 'taskModelCheck', 'teamModelPlan', 'teamModelDo', 'teamModelCheck']) assert.equal(app.selections[key], 'same');
      app.selections.teamAi = 'opencode_cli';app.handleTeamAiChange();await app.nextTick();
      assert.equal(app.selections.teamModelPlan, 'openai/custom');
      await app.handleSaveOnly();
      const sent = app.calls.at(-1).body;
      assert.equal(sent.モデル設定.CODE_AI5_MODEL, 'same');
      assert.equal(sent.モデル設定.CODE_AI4_MODEL, 'openai/custom');
      assert.equal(sent.モデル設定.CODE_AI6_MODEL, 'openai_oauth/custom');
      assert.equal(sent.モデル設定.CODE_GROK_CLI_MODEL, 'same');
      assert.equal(sent.モデル設定.TASK_AI_MODEL_plan, 'same');
      assert.ok(Object.values(sent.再起動要求).every(value => value === false));
    } finally {app.close();}
  });
}
