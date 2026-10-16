import { ref } from 'vue';

export const 分類順 = ['ベース', 'CLI群', 'その他拡張'];
const 待機 = ms => new Promise(resolve => setTimeout(resolve, ms));

// 認証付き API と通知欄は App と共有し、キー試験には触れません。
export function 導入状況状態を作成({ api, 接続済み, 通知, 間隔 = 80 }) {
  const 確認中 = ref(false), 確認済み = ref(false), 書込中 = ref(false), 書込済み = ref(false), 表示中 = ref(null);
  const 項目 = ref([]), 結果 = ref([]), 調査 = ref({});
  function 一覧を反映(data) {
    項目.value = data.項目;
    結果.value = data.結果;
    調査.value = data.調査 || {};
    確認済み.value = false; 書込済み.value = false;
  }
  // 画面の上から順（分類順・一覧順）。
  const 表示順 = () => 分類順.flatMap(group => 項目.value.filter(entry => (entry.menuGroup || 'その他拡張') === group));
  // 全項目を「確認中」で回し、応答後に上から順に結果へ切り替える。
  async function 状況確認() {
    if (確認中.value || 書込中.value || !接続済み.value) return false;
    確認中.value = true; 確認済み.value = false; 書込済み.value = false; 通知.value = '';
    const 前回 = 結果.value;
    結果.value = 項目.value.map(entry => ({ id: entry.id, 状態: '確認中' }));
    try {
      const data = await api('api/診断', 'POST'), 応答 = new Map(data.結果.map(result => [result.id, result]));
      for (const entry of 表示順()) {
        if (!応答.has(entry.id)) continue;
        結果.value = 結果.value.map(result => result.id === entry.id ? 応答.get(entry.id) : result);
        表示中.value = entry.id;
        if (間隔) await 待機(間隔);
      }
      結果.value = data.結果;
      確認済み.value = true;
      return true;
    } catch (error) { 結果.value = 前回; 通知.value = error.message; return false; }
    finally { 確認中.value = false; }
  }
  // 保存内容はサーバーが直前に確認した結果。画面の値は送らない。
  async function 書込() {
    if (!確認済み.value || 確認中.value || 書込中.value || !接続済み.value) return false;
    書込中.value = true; 通知.value = '';
    try { await api('api/書込', 'POST'); 書込済み.value = true; return true; }
    catch (error) { 通知.value = error.message; return false; }
    finally { 書込中.value = false; }
  }
  // 全テスト: 確認してから書き込む。
  async function 全テスト() { return await 状況確認() && await 書込(); }
  return { 確認中, 確認済み, 書込中, 書込済み, 表示中, 項目, 結果, 調査, 一覧を反映, 状況確認, 書込, 全テスト };
}
