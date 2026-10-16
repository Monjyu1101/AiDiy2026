import { computed, watch } from 'vue';
import { 外部連携か, 確認不要か, 設定表示 } from '../キー設定共通/キー設定表示.mjs';
import { モデル一覧状態を作成 } from './モデル一覧状態.mjs';

export function モデル一覧表示を作成(props) {
 const { selected } = モデル一覧状態を作成();
 const items = computed(() => (props.data?.項目 || []).filter(item => !外部連携か(item) && !確認不要か(item)));
 const row = computed(() => items.value.find(item => item.id === selected.value));
 const result = computed(() => props.results?.[selected.value]);
 // 公開モデル一覧の取得状態。ネットワーク取得は OK、同梱キャッシュはキャッシュ利用。
 const 公開状態 = computed(() => props.publicModels?.状態 === '取得済' ? (props.publicModels.取得元 === 'キャッシュ' ? 'キャッシュ利用' : 'OK') : props.publicModels?.状態 || '未取得');
 // 一覧再取得中は、取得している行へ選択（右側のモデル一覧）を順に切り替える。
 watch(() => props.testing, id => { if (id && items.value.some(item => item.id === id)) selected.value = id; });
 return { selected, items, row, result, config: 設定表示, 公開状態 };
}
