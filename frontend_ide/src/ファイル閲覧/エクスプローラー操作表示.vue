<!-- COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
Licensed under "AiDiy 公開利用ライセンス v1.1".
Commercial use requires prior written consent from all copyright holders.
See LICENSE for full terms. Thank you for keeping the rules.
https://github.com/monjyu1101/AiDiy2026 -->
<script setup>
import { computed } from 'vue';
import { containsPath } from './エクスプローラー操作.js';
const props = defineProps({ actions: Object });
const state = props.actions.state;
const menuItems = computed(() => {
  const menu = state.menu, item = !!menu?.target.path;
  const paste = !!state.clipboard && !(state.clipboard.type === 'dir' && containsPath(state.clipboard.path, menu?.directory || ''));
  return [
    ['copy-path','パスのコピー','Ctrl+Shift+C',true],['copy-relative','相対パスのコピー','',true],
    ['copy','コピー（IDE内）','Ctrl+C',item],['paste','ペースト','Ctrl+V',paste],['duplicate','複製','',item],
    ['rename','名前の変更','F2',item],['trash','削除（ゴミ箱へ）','Delete',item],
    ['create-file','新しいファイル…','',true],['create-folder','新しいフォルダ…','',true],['refresh','再読み込み','',true],
  ];
});
function menuKey(event) {
  const menu = event.currentTarget, buttons = [...menu.querySelectorAll('button:not(:disabled)')], index = buttons.indexOf(menu.ownerDocument.activeElement);
  if (['ArrowDown','ArrowUp','Home','End','Tab'].includes(event.key)) {
    event.preventDefault();
    const next = event.key === 'Home' ? 0 : event.key === 'End' ? buttons.length - 1 : (index + (event.key === 'ArrowUp' || (event.key === 'Tab' && event.shiftKey) ? -1 : 1) + buttons.length) % buttons.length;
    buttons[next]?.focus();
  }
}
function dialogKey(event) {
  if (event.key === 'Escape') { event.preventDefault(); props.actions.cancel(); }
  if (event.key === 'Tab') {
    const items = [...event.currentTarget.querySelectorAll('input:not(:disabled),button:not(:disabled),textarea')], index = items.indexOf(event.currentTarget.ownerDocument.activeElement);
    if ((event.shiftKey && index <= 0) || (!event.shiftKey && index === items.length - 1)) { event.preventDefault(); items[event.shiftKey ? items.length - 1 : 0]?.focus(); }
  }
}
</script>
<template>
  <div v-if="state.menu" class="explorer-context-menu selection-popup" role="menu" aria-label="ファイル操作" data-aidiy-no-window-move :style="{left:state.menu.x+'px',top:state.menu.y+'px'}" @contextmenu.prevent.stop @keydown.stop="menuKey" @click.stop>
    <p class="menu-target" :title="state.menu.target.path">{{ state.menu.target.name || 'ルートフォルダ' }}</p>
    <button v-for="[action,label,shortcut,enabled] in menuItems" :key="action" role="menuitem" :data-action="action" :disabled="!enabled||state.busy" @click="actions.action(action)"><span>{{ label }}</span><small>{{ shortcut }}</small></button>
    <p class="menu-help">貼り付け・新規作成先: {{ state.menu.directory || 'ルート' }}<br>同名コピーは別名で作成します。</p>
  </div>
  <div v-if="state.dialog" class="explorer-dialog-overlay" data-aidiy-no-window-move @contextmenu.stop @click.stop @keydown.stop="dialogKey">
    <form class="explorer-action-dialog" role="dialog" aria-modal="true" :aria-label="state.dialog.action==='trash'?'削除の確認':state.dialog.action==='manual-copy'?'パスの手動コピー':'名前の入力'" @submit.prevent="actions.submitName">
      <template v-if="state.dialog.action==='trash'">
        <strong>ゴミ箱へ移動しますか？</strong>
        <p class="dialog-path">{{ state.dialog.path }}</p>
        <p>{{ state.dialog.type==='dir'?'フォルダ内のファイルも含めて移動します。':'' }}復元はOSのゴミ箱から行えます。ゴミ箱が利用できない場合は削除しません。</p>
        <div class="dialog-buttons"><button type="button" data-initial-focus :disabled="state.busy" @click="actions.cancel">キャンセル</button><button type="button" class="danger" :disabled="state.busy" @click="actions.perform({action:'trash',path:state.dialog.path,confirmed:true})">{{ state.busy?'移動中…':'ゴミ箱へ移動' }}</button></div>
      </template>
      <template v-else-if="state.dialog.action==='manual-copy'">
        <strong>パスを手動でコピー</strong><p>クリップボードに書き込めませんでした。下のパスを選択してコピーしてください。</p>
        <textarea readonly :value="state.dialog.value" @focus="$event.target.select()"></textarea><div class="dialog-buttons"><button type="button" @click="actions.cancel">閉じる</button></div>
      </template>
      <template v-else>
        <strong>{{ state.dialog.action==='create-folder'?'新しいフォルダ':'新しいファイル' }}</strong><p class="dialog-path">作成先: {{ state.dialog.directory || 'ルート' }}</p>
        <label>名前<input v-model="state.dialog.value" data-initial-focus :disabled="state.busy" maxlength="255" autocomplete="off" spellcheck="false"></label>
        <div class="dialog-buttons"><button type="button" :disabled="state.busy" @click="actions.cancel">キャンセル</button><button type="submit" :disabled="state.busy">{{ state.busy?'作成中…':'作成' }}</button></div>
      </template>
      <p v-if="state.error" class="operation-error" role="alert">{{ state.error }}</p>
    </form>
  </div>
  <div v-if="!state.dialog&&(state.busy||state.error||state.notice)" class="explorer-operation-status" :class="{error:state.error}" role="status" @click.stop><span>{{ state.busy?'処理中…':state.error||state.notice }}</span><button v-if="!state.busy" aria-label="操作メッセージを閉じる" @click="state.error='';state.notice=''">×</button></div>
</template>
<style scoped>
.explorer-context-menu{position:absolute;z-index:110;box-sizing:border-box;width:min(250px,calc(100% - 12px));max-height:calc(100% - 12px);overflow:auto;background:#101827;border:1px solid #65748e;box-shadow:0 8px 24px #000b;padding:4px;color:#e5eaf4}
.explorer-context-menu button{display:flex;justify-content:space-between;align-items:center;gap:10px;width:100%;text-align:left;border:0;padding:7px 8px;background:transparent;font-size:12px;min-height:30px}
.explorer-context-menu button:hover:not(:disabled),.explorer-context-menu button:focus-visible{background:#28405b;outline:1px solid #8de6eb}.explorer-context-menu button:disabled{opacity:.4;cursor:not-allowed}.explorer-context-menu small{color:#96abc8;font-size:10px;white-space:nowrap}
.menu-target,.menu-help{margin:3px;padding:4px;font-size:11px;overflow-wrap:anywhere}.menu-target{border-bottom:1px solid #344258;font-weight:bold}.menu-help{border-top:1px solid #344258;color:#aebdd1;font-size:10px}
.explorer-dialog-overlay{position:absolute;inset:0;z-index:120;display:flex;align-items:center;justify-content:center;padding:10px;background:#030814c9;overflow:auto}.explorer-action-dialog{box-sizing:border-box;width:100%;max-width:380px;max-height:100%;overflow:auto;background:#101827;border:1px solid #65748e;padding:14px;font-size:12px;line-height:1.6;color:#e5eaf4}.explorer-action-dialog p{margin:8px 0}.dialog-path{overflow-wrap:anywhere;color:#b1d9f9}.explorer-action-dialog input,.explorer-action-dialog textarea{display:block;box-sizing:border-box;width:100%;margin:5px 0;background:#080e1b;color:#fff;border:1px solid #718ba9;padding:7px;font-size:13px}.explorer-action-dialog textarea{height:100px}.dialog-buttons{display:flex;justify-content:flex-end;gap:8px;margin-top:12px}.dialog-buttons .danger{border-color:#dd7e82;color:#ffbdc1}.operation-error{color:#ffb4b9;overflow-wrap:anywhere}.explorer-operation-status{display:flex;align-items:start;gap:6px;border-top:1px solid #344258;padding:7px;color:#b1d9f9;font-size:11px;line-height:1.5;flex-shrink:0;max-height:100px;overflow:auto}.explorer-operation-status span{flex:1;overflow-wrap:anywhere}.explorer-operation-status.error{color:#ffb4b9}
</style>
