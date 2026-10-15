<script setup>
import StatusBadge from '../StatusBadge.vue';
import { 外部連携設定表示を作成 } from './外部連携設定表示.mjs';
import './外部連携設定.css';
const props=defineProps(['data','results','loading','testing','connected']);
defineEmits(['refresh']);
const { selected,items,row,config } = 外部連携設定表示を作成(props);
</script>
<template>
<section class="panel integration-panel" aria-label="外部連携設定">
 <div class="panel-heading"><h2>外部連携設定</h2><div class="panel-actions"><button :disabled="!connected || loading || Boolean(testing)" @click="$emit('refresh')">設定状況を更新</button></div></div>
 <main class="key-layout"><aside aria-label="外部連携の一覧">
  <p v-if="loading">設定状況を確認中…</p><p v-else-if="!data">接続すると設定状況を表示します。</p>
  <template v-else><p v-if="data.設定状態!=='読込済み'" role="status">設定ファイル: {{data.設定状態}}</p><p v-if="data.説明" role="status">{{data.説明}}</p>
   <div v-for="item in items" :key="item.id" class="integration-row" :class="{selected:selected===item.id}">
    <button class="key-select" :aria-pressed="selected===item.id" @click="selected=item.id"><span>{{item.名前}}</span><span class="config-state">{{config(item)}}</span></button>
    <div class="integration-test"><button disabled :title="item.理由 || '接続テストは未対応です。'">テスト</button><StatusBadge state="未実施"/><span class="integration-reason">{{item.理由 || '接続テストは未対応です。'}}</span></div>
   </div>
  </template>
 </aside>
 <article aria-live="polite"><template v-if="row"><span class="eyebrow">外部連携設定 / {{row.名前}}</span><h2>{{row.名前}}</h2><StatusBadge class="status" state="未実施"/>
  <dl><dt>キー名</dt><dd>{{row.キー名}}</dd><dt>設定状況</dt><dd>{{config(row)}}</dd><dt>確認内容</dt><dd>{{row.説明}}</dd><dt>テスト</dt><dd>{{row.理由 || '接続テストは未対応です。'}}</dd></dl>
 </template><div v-else class="welcome"><span class="eyebrow">EXTERNAL INTEGRATIONS</span><h2>外部連携の設定状況</h2><p>Hugging Face・Discord を選択すると設定の有無と確認範囲を表示します。</p></div></article></main>
 <details class="test-notes"><summary>確認範囲について</summary><p>キーの値は表示しません。Hugging Face 読取・書込、Discord は設定の有無のみ確認します。接続テストは未対応のため未実施と表示します。設定済は認証成功を意味しません。外部 API への接続・OAuth・メッセージ送信は行わず、「全テスト」の対象にも含みません。</p></details>
</section>
</template>
