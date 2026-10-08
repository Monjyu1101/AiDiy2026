const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { join } = require('node:path');
const { screen } = require('./code-screen.cjs');

test('Code: 履歴を上へスクロール中でも、入力メッセージ追加と送信受理後は末尾へ移動する', () => {
  const ui = screen(), history = ui.element('conversation');
  ui.state({ メッセージ: [{ 種別: 'user', 本文: '以前の入力' }] }); ui.render();
  history.scrollTop = 0;
  ui.state({ メッセージ: [{ 種別: 'user', 本文: '以前の入力' }, { 種別: 'user', 本文: '今回の入力' }] });
  assert.equal(history.scrollTop, history.scrollHeight);
  ui.input('複数行\nの入力'); history.scrollTop = 0;
  ui.notify({ type: 'accepted' });
  assert.equal(ui.element('prompt').value, '');
  history.scrollHeight = 1200; ui.render();
  assert.equal(history.scrollTop, 1200);
});

test('Code: ストリーム枠の開閉・更新・伸縮で、進捗と履歴の両方が末尾へ追従する', () => {
  const ui = screen(), history = ui.element('conversation'), progress = ui.element('progress');
  ui.state({ メッセージ: [{ 種別: 'user', 本文: '入力' }] }); ui.render();
  for (const content of ['\x02', '実行中の進捗', '\x03', '\x18']) {
    history.scrollTop = progress.scrollTop = 0;
    ui.notify({ メッセージ識別: 'output_stream', メッセージ内容: content });
    history.scrollHeight += 100; progress.scrollHeight += 100; ui.render();
    assert.equal(history.scrollTop, history.scrollHeight);
    assert.equal(progress.scrollTop, progress.scrollHeight);
  }
  history.scrollTop = 0;
  ui.element('progress-details').listeners.get('toggle')(); ui.render();
  assert.equal(history.scrollTop, history.scrollHeight);
  history.scrollTop = progress.scrollTop = 0;
  ui.resize(history); ui.render();
  assert.equal(history.scrollTop, history.scrollHeight);
  assert.equal(progress.scrollTop, progress.scrollHeight);
});

test('Code: 入力欄の伸縮と一覧からの復帰後も、描画後の履歴末尾へ揃える', () => {
  const ui = screen(), history = ui.element('conversation');
  ui.input('長い\n入力'); history.scrollHeight = 1400; ui.render();
  assert.equal(history.scrollTop, 1400);
  ui.element('history-toggle').listeners.get('click')();
  history.scrollTop = 0; ui.resize(history); ui.render();
  assert.equal(history.scrollTop, 0); // 非表示中の会話欄は動かさない。
  ui.notify({ type: 'showConversation' }); ui.render();
  assert.equal(history.scrollTop, 1400);
});

test('Code: 検証ループは初期値1回、選択した0〜3回を送信する', () => {
  const ui = screen(); ui.state({});
  assert.equal(ui.element('self-check-loop').value, '1');
  for (const count of [1, 0, 2, 3]) {
    ui.element('self-check-loop').value = String(count);
    ui.input('検証回数の確認');
    ui.element('composer').listeners.get('submit')({ preventDefault() {} });
    assert.equal(ui.posts.at(-1).self_check_loop, count);
    assert.equal(ui.posts.at(-1).メッセージ識別, 'input_text');
    ui.notify({ type: 'accepted' });
    assert.equal(ui.element('self-check-loop').value, String(count));
  }
});

test('Code offline: 未接続でも送信でき、検証0を固定し、オンラインの回数へ復帰する', () => {
  const ui = screen(); ui.state({オフライン対応:true,実行モード:'online'});
  ui.element('self-check-loop').value='3';
  ui.state({接続済み:false});
  ui.input(' ');
  assert.equal(ui.element('send').disabled,true);
  ui.input('未接続でも依頼');
  assert.equal(ui.element('send').disabled,false);
  ui.element('composer').listeners.get('submit')({preventDefault(){}});
  assert.equal(ui.posts.at(-1).self_check_loop,0);
  assert.equal(ui.element('send').disabled,true);
  ui.notify({type:'accepted'});
  assert.equal(ui.element('chat-header').classList.contains('connected'),false);
  assert.equal(ui.element('self-check-loop').value,'0');
  assert.equal(ui.element('self-check-loop').disabled,true);
  ui.state({接続済み:false});
  assert.equal(ui.element('self-check-loop').value,'0');
  ui.state({接続済み:true});
  assert.equal(ui.element('self-check-loop').value,'3');
  assert.equal(ui.element('self-check-loop').disabled,false);
  assert.equal(ui.element('chat-header').classList.contains('connected'),true);
  ui.state({接続済み:false});
  ui.state({実行モード:'offline',接続済み:false,provider:'aidiy_hermes',model:'auto'});
  ui.input('単独実行');
  assert.equal(ui.element('activity-label').textContent,'未接続');
  assert.equal(ui.element('activity').hidden,false);
  assert.equal(ui.element('self-check-loop').value,'0');
  assert.equal(ui.element('self-check-loop').disabled,true);
  assert.equal(ui.element('send').disabled,false);
  assert.equal(ui.element('new-chat').disabled,false);
  ui.element('composer').listeners.get('submit')({preventDefault(){}});
  assert.equal(ui.posts.at(-1).self_check_loop,0);
  ui.state({実行中:true});
  assert.equal(ui.element('stop').disabled,false);
  ui.state({実行中:false,実行モード:'online',接続済み:true});
  assert.equal(ui.element('self-check-loop').value,'3'); assert.equal(ui.element('self-check-loop').disabled,false);
  assert.equal(ui.element('activity').hidden,false);
});

test('Code offline: モデル選択は取得した固定候補だけで、手入力・既定の空欄を追加しない', () => {
  const ui = screen(); ui.state({オフライン対応:true,実行モード:'offline',provider:'aidiy_hermes',model:'auto',接続済み:false});
  ui.element('choose-model').listeners.get('click')();
  ui.notify({type:'modelCatalog',provider:'',items:[{id:'aidiy_hermes',label:'aidiy_hermes'}]});
  ui.notify({type:'modelCatalog',provider:'aidiy_hermes',items:[{id:'auto',label:'auto'},{id:'openai_oauth/gpt-6.1-sol',label:'openai_oauth/gpt-6.1-sol'}]});
  assert.deepEqual(ui.element('provider-select').children.map(item=>item.value),['aidiy_hermes']);
  assert.equal(ui.element('provider-select').disabled,true);
  assert.equal(ui.element('apply-model').disabled,false);
  assert.deepEqual(ui.element('model-select').children.map(item=>item.value),['auto','openai_oauth/gpt-6.1-sol']);
  assert.equal(ui.element('custom-model').hidden,true);
  ui.element('model-select').value='openai_oauth/gpt-6.1-sol';
  ui.element('apply-model').listeners.get('click')();
  assert.equal(ui.posts.at(-1).model,'openai_oauth/gpt-6.1-sol');
});

test('Code: タイトルバーに接続状態を表示し、切断中は送信を無効化する', () => {
  const ui = screen(); ui.state({}); ui.input('依頼');
  assert.equal(ui.element('activity-label').textContent, '接続済み');
  assert.equal(ui.element('chat-header').classList.contains('connected'), true);
  assert.equal(ui.element('activity').classList.contains('connected'), true);
  assert.equal(ui.element('send').disabled, false);
  ui.state({接続済み:false});
  assert.equal(ui.element('activity-label').textContent, '未接続');
  assert.equal(ui.element('chat-header').classList.contains('connected'), false);
  assert.equal(ui.element('activity').classList.contains('connected'), false);
  assert.equal(ui.element('send').disabled, true);
  const count = ui.posts.length;
  ui.element('composer').listeners.get('submit')({preventDefault(){}});
  assert.equal(ui.posts.length,count);
  ui.state({接続中:true});
  assert.equal(ui.element('activity-label').textContent, '接続中');
  assert.equal(ui.element('chat-header').classList.contains('connected'),false);
  assert.equal(ui.element('send').disabled,true);
  ui.state({接続済み:true,接続中:false});
  assert.equal(ui.element('send').disabled,false);
  ui.state({実行中:true});
  assert.equal(ui.element('activity-label').textContent, '接続済み');
  assert.equal(ui.element('chat-header').classList.contains('connected'), true);
  assert.equal(ui.element('activity').classList.contains('running'), true);
  ui.state({実行中:false});
  assert.equal(ui.element('activity-label').textContent, '接続済み');
  assert.equal(ui.element('chat-header').classList.contains('connected'), true);
  assert.equal(ui.element('activity').classList.contains('running'), false);
  const html = readFileSync(join(__dirname,'../media/chat.html'),'utf8');
  assert.ok(!html.includes('id="connect-toggle"'));
  assert.ok(!html.includes('id="execution-mode'));
  assert.ok(html.indexOf('id="activity"') < html.indexOf('id="conversation-toolbar"'));
  assert.ok(!html.slice(html.indexOf('<footer')).includes('id="activity"'));
});
