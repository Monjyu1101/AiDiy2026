const test = require('node:test');
const assert = require('node:assert/strict');
const { createRequire } = require('node:module');
const path = require('node:path');
const { reactive } = createRequire(path.join(__dirname, '../../../package.json'))('vue');
const { render } = require('../../../../checks/ui-components.cjs');
test('確認不要（Azure・GitHub Copilot）以外の登録キーを重複なく2画面へ分類し、各群の設定順を保持する', async () => {
 const { KEY_PROVIDERS } = await import('../../../../key_status.mjs');
 const { モデルキー設定表示を作成 } = await import('../モデルキー設定表示.mjs');
 const { 外部連携設定表示を作成 } = await import('../../外部連携設定/外部連携設定表示.mjs');
 const props = reactive({ data: { 項目: KEY_PROVIDERS }, results: {} });
 const model = モデルキー設定表示を作成(props), external = 外部連携設定表示を作成(props);
 assert.deepEqual(model.items.value.map(x=>x.id),['gemini','freeai','claude','openai','openai_oauth','grok','openrt','ollama','local']);
 assert.deepEqual(external.items.value.map(x=>x.id),['huggingface_read','huggingface_write','discord']);
 assert.equal(new Set([...model.items.value,...external.items.value].map(x=>x.id)).size,KEY_PROVIDERS.length-2);
 // 秘匿対象とサーバーの登録には残す。
 assert.ok(KEY_PROVIDERS.some(x=>x.id==='azure')&&KEY_PROVIDERS.some(x=>x.id==='copilot'));
 model.selected.value='openai';external.selected.value='discord';props.data=null;
 assert.equal(model.row.value,undefined); assert.equal(model.selected.value,'openai');
 props.data={項目:KEY_PROVIDERS};props.results={openai:{状態:'OK',モデル:['example']}};
 assert.equal(model.row.value.id,'openai');assert.equal(model.result.value.状態,'OK');assert.equal(external.row.value.id,'discord');
 const html=await render('モデルキー設定/モデルキー設定パネル.vue',{...props,connected:true});
 assert.match(html,/OpenAI/);assert.doesNotMatch(html,/Discord|Hugging Face|Azure|GitHub Copilot/);
});
