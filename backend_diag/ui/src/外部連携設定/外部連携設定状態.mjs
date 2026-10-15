import { ref } from 'vue';

// v-show で画面を切り替えても、設定更新中も選択を維持する。
export function 外部連携設定状態を作成() { return { selected: ref('') }; }
