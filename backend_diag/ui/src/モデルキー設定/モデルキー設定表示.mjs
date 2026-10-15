import { computed } from 'vue';
import { 外部連携か, 設定表示 } from '../キー設定共通/キー設定表示.mjs';
import { モデルキー設定状態を作成 } from './モデルキー設定状態.mjs';

export function モデルキー設定表示を作成(props) {
 const { selected } = モデルキー設定状態を作成();
 const items = computed(() => (props.data?.項目 || []).filter(item => !外部連携か(item)));
 const row = computed(() => items.value.find(item => item.id === selected.value));
 const result = computed(() => props.results?.[selected.value]);
 return { selected, items, row, result, config: 設定表示 };
}
