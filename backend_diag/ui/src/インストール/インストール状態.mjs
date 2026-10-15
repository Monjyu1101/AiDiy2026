import { ref } from 'vue';

// 認証付き API と通知欄は App と共有し、キー試験には触れません。
export function インストール状態を作成({ api, 接続済み, 通知 }) {
  const 確認中 = ref(false), 項目 = ref([]), 結果 = ref([]), 調査 = ref({});
  function 一覧を反映(data) {
    項目.value = data.項目;
    結果.value = data.結果;
    調査.value = data.調査 || {};
  }
  async function インストール確認(){if(確認中.value || !接続済み.value)return;確認中.value=true;通知.value='インストール確認中です。プログラムごとに最大 5 秒、4 件ずつ確認しています…';try{結果.value=(await api('api/診断','POST')).結果;通知.value='';}catch(error){通知.value=error.message;}finally{確認中.value=false;}}
  return { 確認中, 項目, 結果, 調査, 一覧を反映, インストール確認 };
}
