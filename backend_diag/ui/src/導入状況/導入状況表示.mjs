import { ref, computed, watch } from 'vue';

// 一覧の選択・開閉と詳細表示はインストール画面内で保持します。
export function 導入状況表示を作成(props) {
  const 選択ID=ref(null),折り畳み=ref(new Set(['その他拡張']));
  const 分類=['ベース','CLI群','その他拡張'];
  const 状態=id=>props.結果.find(r=>r.id===id)?.状態 || '未確認';
  const 選択項目=computed(()=>props.項目.find(e=>e.id===選択ID.value));
  const 選択結果=computed(()=>props.結果.find(r=>r.id===選択ID.value));
  const 詳細項目=computed(()=>{const e=選択項目.value,r=選択結果.value;if(!e)return [];return [['利用区分',({base:'実行・依存管理のベース',cli:'選択した LLM CLI 連携',integration:'本体から利用する機能別の拡張'})[e.usageTier]],['機能カテゴリ',e.category],['必要性',e.diagnosticsRequired?'診断アプリの起動に必須':e.wholeSystemRequired?'Python バックエンド利用時の基盤':'該当機能を選択して使用する場合に確認'],['必要バージョン',e.minimumVersion?`${e.minimumVersion} 以降（ソースの要件）`:''],['検出パス',r?.パス || '—'],['バージョン',r?.バージョン || '—'],['確認結果',r?.説明 || 'まだ確認していません。'],['確認日時',r?.確認日時?new Date(r.確認日時).toLocaleString():'—'],['検出コマンド',e.commands.join(' / ')],['利用機能',(e.required_by || []).join('、')],['注意事項',e.notes]].filter(([,v])=>v);});
  const 参照箇所=computed(()=>選択項目.value?.evidence?.length?[...new Set(選択項目.value.evidence.map(e=>`${e.path}:${e.line}`))]:選択項目.value?.sources || []);
  // 確認の演出中は、結果が出た項目へ選択（右側の詳細）を順に切り替え、閉じた分類は開く。
  watch(()=>props.表示中,id=>{if(!id)return;選択ID.value=id;const group=props.項目.find(e=>e.id===id)?.menuGroup || 'その他拡張';if(折り畳み.value.has(group)){const next=new Set(折り畳み.value);next.delete(group);折り畳み.value=next;}});
  function 開閉(group,event){const next=new Set(折り畳み.value);event.target.open?next.delete(group):next.add(group);折り畳み.value=next;}
  return { 選択ID, 折り畳み, 分類, 状態, 選択項目, 選択結果, 詳細項目, 参照箇所, 開閉 };
}
