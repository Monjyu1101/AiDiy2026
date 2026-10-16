const test = require('node:test');
const assert = require('node:assert/strict');
const { render, source } = require('../../../../checks/ui-components.cjs');
test('外部連携は未実施と理由を表示し、未対応のテストボタンを置かない', async () => {
 const data={設定状態:'読込済み',項目:[{id:'openai',名前:'OpenAI'},{id:'huggingface_read',名前:'Hugging Face 読取',設定済み:true,理由:'モデル一覧試験は未対応です。'},{id:'huggingface_write',名前:'Hugging Face 書込',設定済み:null},{id:'discord',名前:'Discord Bot',設定済み:false}]};
 const html=await render('外部連携/外部連携パネル.vue',{data,results:{discord:{状態:'OK'}},connected:true});
 assert.equal((html.match(/class="integration-row"/g)||[]).length,3);
 assert.equal((html.match(/data-state="未実施"/g)||[]).length,3);
 assert.equal((html.match(/>テスト<\/button>/g)||[]).length,0);
 assert.match(html,/>外部連携確認<\/h2>/);assert.match(html,/>設定状況を更新<\/button>/);
 assert.match(html,/モデル一覧試験は未対応/);assert.match(html,/確認不可/);assert.match(html,/未設定/);
 assert.doesNotMatch(html,/OpenAI|公開モデル|class="models"|data-state="OK"/);
 const panel=source('外部連携/外部連携パネル.vue');assert.doesNotMatch(panel,/\$emit\('test'|v-html|innerHTML/);
});
