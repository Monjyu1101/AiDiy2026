import { nextTick } from 'vue';

// 右上ボタンの一括処理が終わったら、パネル内の一覧・詳細を先頭の表示へ戻す。
export async function 先頭へスクロール(panel) {
  await nextTick();
  for (const element of panel?.querySelectorAll(':scope > main > aside, :scope > main > article') || []) element.scrollTop = 0;
}

// 実行中フラグが true から false へ変わったとき（一括処理の完了時）だけ呼ぶ。
export const 完了時 = callback => (now, before) => { if (before && !now) callback(); };
