import { ref } from 'vue';

const 操作名 = new Set(['導入', '再導入', '削除']);
const 動作中 = run => Boolean(run && (run.実行中 === true || ['実行中', '確認中'].includes(run.状態)));

// コマンド・導入方式はサーバーだけが決める。画面の検出結果から操作権限を推測しない。
export function 導入操作状態を作成({ api, 接続済み, 操作中 = ref(false), 競合中 = () => false, 結果反映 = () => {}, 確認 = text => globalThis.confirm?.(text) === true, 間隔 = 750, setTimer = setTimeout, clearTimer = clearTimeout }) {
  const 項目 = ref([]), 実行 = ref(null), 読込中 = ref(false), 取消中 = ref(false), 取消要求済み = ref(false), エラー = ref(''), 受付 = ref(null);
  let enabled = false, disposed = false, version = 0, timer, controller, pending, merged = '', uncertain = false, startFailure, cancelFailure;
  const 能力 = id => 項目.value.find(item => item.id === id);
  const 可能操作 = id => (能力(id)?.操作 || []).filter(action => 操作名.has(action));
  const 有効 = revision => !disposed && enabled && 接続済み.value && revision === version;
  function 解除() { version++; clearTimer(timer); timer = undefined; controller?.abort(); controller = undefined; pending = undefined; }
  function 予約() { clearTimer(timer); if (enabled && !disposed && 接続済み.value && (操作中.value || uncertain)) timer = setTimer(() => { void 読込(); }, 間隔); }
  function 反映(data) {
    項目.value = Array.isArray(data.項目) ? data.項目 : [];
    const run = data.実行 || null;
    if (run?.実行ID !== 実行.value?.実行ID) 取消要求済み.value = false;
    実行.value = run; uncertain = false; 受付.value = null;
    操作中.value = 動作中(run);
    if (!操作中.value) {
      取消要求済み.value = false;
      // 同じ完了応答を繰り返し取得しても、後から行った個別確認を上書きしない。
      if ((run?.結果 || run?.結果一覧?.length) && run.実行ID !== merged) { 結果反映(run); merged = run.実行ID; }
    }
  }
  async function 読込() {
    if (!enabled || disposed || !接続済み.value) return false;
    if (pending) return pending;
    clearTimer(timer); timer = undefined;
    const revision = version, current = new AbortController(); controller = current; 読込中.value = true;
    pending = (async () => {
      try {
        const data = await api('api/導入管理', 'GET', current.signal); if (!有効(revision)) return false;
        反映(data); エラー.value = '';
        if (startFailure) {
          const run = data.実行;
          if (!run || run.実行ID === startFailure.previous || run.対象 !== startFailure.id || run.操作 !== startFailure.action) エラー.value = `${startFailure.message} 新しい実行の受付は確認できませんでした。`;
          startFailure = undefined;
        }
        if (cancelFailure) {
          // 中止要求の応答が失われた場合、最新状態を照合した後だけ手動の再試行を許す。
          if (動作中(data.実行)) { 取消要求済み.value = false; エラー.value = `${cancelFailure} 中止を確認できません。必要なら再度「中止」を押してください。`; }
          cancelFailure = undefined;
        }
        return true;
      }
      catch (error) { if (有効(revision)) { エラー.value = `${error.message} 状況を再取得しています。`; uncertain = true; 操作中.value = true; } return false; }
      finally { if (有効(revision)) { controller = undefined; pending = undefined; 読込中.value = false; 予約(); } }
    })();
    return pending;
  }
  function 確認文(id, action, name) {
    const capability = 能力(id);
    const change = action === '削除' ? '対象パッケージを削除します。このプログラムは利用できなくなります。' : action === '再導入' ? (capability?.再導入説明 || '対象パッケージを削除してから、再度インストールします。再導入に失敗すると、このプログラムが利用できなくなる場合があります。') : '診断サーバーの環境へパッケージを導入します。';
    return `${name || id} を${action}しますか？\n対象パッケージ: ${capability?.パッケージ || id}\n\n${change}\n認証情報・利用者設定・会話履歴は削除しません。\n${[capability?.説明, capability?.確認説明].filter(Boolean).join('\n')}\n${capability?.関連項目?.length > 1 ? `一式の対象: ${capability.関連項目.join(' / ')}\n` : ''}${capability?.規約URL ? `提供元の案内・規約: ${capability.規約URL}\n` : ''}${action === '削除' ? 'パッケージ管理コマンドを実行します。' : 'ネットワークからパッケージを取得し、インストール処理を実行します。'}\n終了後に対象の各項目で「確認」ボタンと同じ処理を自動実行します。`;
  }
  async function 開始(id, action, name) {
    if (!enabled || disposed || !接続済み.value || 操作中.value || 読込中.value || 競合中() || !可能操作(id).includes(action)) return false;
    操作中.value = true;
    const revision = version;
    let approved;
    try { approved = await 確認(確認文(id, action, name)); }
    catch (error) { if (有効(revision)) { エラー.value = error.message; 操作中.value = false; } return false; }
    if (!有効(revision)) return false;
    if (!approved) { 操作中.value = false; return false; }
    // 確認中に能力や別処理が変わった場合、古い同意で開始しない。
    if (競合中() || !可能操作(id).includes(action)) { 操作中.value = false; return false; }
    解除(); const requestVersion = version; controller = new AbortController();
    エラー.value = ''; 受付.value = { 対象: id, 操作: action }; 取消要求済み.value = false; startFailure = undefined; cancelFailure = undefined;
    const previous = 実行.value?.実行ID;
    try {
      const data = await api(`api/導入管理/${encodeURIComponent(id)}/${encodeURIComponent(action)}`, 'POST', controller.signal);
      if (!有効(requestVersion)) return false;
      反映(data); return true;
    } catch (error) {
      if (有効(requestVersion)) { エラー.value = `${error.message} 実行の有無を確認しています。`; startFailure = { id, action, previous, message: error.message }; uncertain = true; }
      // 受付結果が不明でも POST は再送せず、GET で既存実行を照合する。
      return false;
    } finally { if (有効(requestVersion)) { controller = undefined; 予約(); } }
  }
  async function 中止() {
    if (!enabled || disposed || !接続済み.value || !動作中(実行.value) || 取消中.value || 取消要求済み.value) return false;
    const id = 実行.value.実行ID;
    解除(); const revision = version; controller = new AbortController(); 取消中.value = true; 取消要求済み.value = true; エラー.value = '';
    try { const data = await api(`api/導入管理/${encodeURIComponent(id)}`, 'DELETE', controller.signal); if (!有効(revision)) return false; 反映(data); return true; }
    catch (error) { if (有効(revision)) { エラー.value = `${error.message} 中止結果を確認しています。`; cancelFailure = error.message; uncertain = true; } return false; }
    finally { if (有効(revision)) { controller = undefined; 取消中.value = false; 読込中.value = false; 予約(); } }
  }
  function 接続(value) {
    解除(); enabled = Boolean(value); 読込中.value = false; 取消中.value = false; 取消要求済み.value = false; 受付.value = null;
    項目.value = []; uncertain = enabled; 操作中.value = enabled; startFailure = undefined; cancelFailure = undefined;
    if (enabled && !disposed) return 読込();
    return Promise.resolve(false);
  }
  function 終了() { disposed = true; enabled = false; 解除(); 操作中.value = false; 読込中.value = false; 取消中.value = false; }
  return { 項目, 実行, 読込中, 取消中, 取消要求済み, 操作中, エラー, 受付, 能力, 可能操作, 接続, 読込, 開始, 中止, 終了 };
}
