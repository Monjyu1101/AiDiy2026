<script setup>
import {watch,ref,nextTick} from 'vue';
import './アプリ起動.css';
import {アプリアイコン} from './アプリアイコン.mjs';
const props=defineProps({state:Object,online:Boolean,visible:Boolean});
defineEmits(['mini']);
const folderInput=ref();
watch(()=>!!props.state.一覧.value,async value=>{if(value){await nextTick();folderInput.value?.focus();}});
watch(()=>props.online&&props.visible,value=>{if(value)void props.state.読込();},{immediate:true});
const descriptions={avatar:'AIコアのアバター画面を開きます。',ide:'プロジェクトの開発スペースを開きます。',term:'プロジェクトでターミナルを開きます。',code:'プロジェクトのコード支援画面を開きます。',live:'プロジェクトのライブ会話画面を開きます。',discord:'プロジェクトのDiscord接続パネルを開きます。'};
</script>
<template>
<section class="panel app-launch-panel" v-show="visible" aria-label="アプリ起動">
 <div class="panel-heading"><h2>アプリ起動</h2><button :disabled="!online" @click="$emit('mini')">ミニ表示</button></div>
 <div class="app-project" :class="{required:!state.フォルダ.value}"><label for="app-project-folder">プロジェクトフォルダ</label><div class="app-project-row"><input id="app-project-folder" :value="state.フォルダ.value" readonly placeholder="プロジェクト選択してね"><button class="app-project-select" :disabled="!online||!!state.処理中.value||state.選択中.value" @click="state.選択()">フォルダ選択</button><button v-if="state.フォルダ.value" :disabled="!!state.処理中.value||state.選択中.value" @click="state.解除()">解除</button></div><p>Avatar 以外は、このフォルダを作業パスにして開きます。起動したアプリは Diag を閉じても動作を続けます。</p></div>
 <p v-if="state.通知.value" class="app-launch-message" role="status">{{state.通知.value}}</p>
 <div class="app-launch-list">
  <article v-for="item in state.項目.value" :key="item.id" class="app-launch-card" :data-app="item.id">
   <div class="app-launch-card-heading"><img class="app-launch-icon" :src="アプリアイコン[item.id]" alt="" width="32" height="32"><h3>{{item.名前}}</h3><span v-if="item.単一起動" class="app-single">単一起動</span></div>
   <p>{{descriptions[item.id]}}</p>
   <button class="app-launch-button" :disabled="!online||!state.フォルダ.value||!!state.処理中.value||state.選択中.value" @click="state.起動(item.id)">{{state.処理中.value===item.id?'起動確認中…':`${item.名前} を起動`}}</button>
   <p class="app-launch-result" role="status" :data-tone="state.結果.value[item.id]?.種別">{{state.結果.value[item.id]?.通知||'\u00a0'}}</p>
   <details v-if="state.結果.value[item.id]?.ログ"><summary>起動ログの保存先</summary><code>{{state.結果.value[item.id].ログ}}</code></details>
  </article>
 </div>
 <p class="app-launch-note">Avatar・Live・Discord は、起動ボタンを押した時だけ実行中のタスクを確認します。</p>
 <div v-if="state.一覧.value" class="app-folder-overlay" @keydown.esc="state.取消()">
  <section class="app-folder-dialog" role="dialog" aria-modal="true" aria-labelledby="app-folder-title">
   <h3 id="app-folder-title">プロジェクトフォルダを選択</h3>
   <form @submit.prevent="state.参照(state.パス入力.value)"><input ref="folderInput" aria-label="フォルダのパス" v-model="state.パス入力.value" :disabled="state.参照中.value"><button :disabled="state.参照中.value">移動</button></form>
   <p v-if="state.参照エラー.value" role="alert">{{state.参照エラー.value}}</p>
   <div class="app-folder-list" :aria-busy="state.参照中.value"><button :disabled="state.参照中.value||state.一覧.value.親===state.一覧.value.フォルダ" @click="state.参照(state.一覧.value.親)">↑ 親フォルダ</button><button v-for="folder in state.一覧.value.子フォルダ" :key="folder.パス" :disabled="state.参照中.value" @click="state.参照(folder.パス)">▸ {{folder.名前}}</button><p v-if="!state.一覧.value.子フォルダ.length">子フォルダはありません。</p></div>
   <div class="app-folder-actions"><button @click="state.取消()">キャンセル</button><button :disabled="state.参照中.value" @click="state.決定()">このフォルダを選択</button></div>
  </section>
 </div>
</section>
</template>
