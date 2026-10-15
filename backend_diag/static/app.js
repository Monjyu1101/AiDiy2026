const $ = id => document.getElementById(id);
let key = new URLSearchParams(location.hash.slice(1)).get('token') || '';
// 認証キーはメモリ内だけに保持。履歴・Storage・URL に残さない。
if (location.hash) history.replaceState(null, '', location.pathname + location.search);
let entries = [], results = new Map(), selected = null;
let connecting = false;
const collapsed = new Set();
const state = id => results.get(id)?.状態 || '未確認';
const statuses = ['未確認', '未検出', 'OK', 'NG', 'ERR'];
const indicator = (value, className = 'badge', label = value) => { const el = node('span', label, className); el.setAttribute('data-state', value); return el; };
const node = (tag, text, className) => { const el = document.createElement(tag); el.textContent = text; if (className) el.className = className; return el; };
async function api(path, method = 'GET') {
  const response = await fetch(new URL(path, location.href), { method, headers: { Authorization: `Bearer ${key}` }, cache: 'no-store', credentials: 'same-origin' });
  const data = await response.json();
  if (!response.ok) { if (response.status === 401) { key = ''; $('login').hidden = false; $('run').disabled = true; } throw new Error(data.エラー || '通信に失敗しました。'); }
  return data;
}
const menuGroups = ['ベース', 'CLI群', 'その他拡張'];
const groupOf = entry => entry.menuGroup || 'その他拡張';
const includedEntries = () => entries;
const usageLabels = { base: '実行・依存管理のベース', cli: '選択した LLM CLI 連携', integration: '本体から利用する機能別の拡張' };
function makeGroup(label, id, expanded) {
  const group = node('details', ''); group.open = expanded || !collapsed.has(id);
  group.append(node('summary', label));
  group.addEventListener('toggle', () => { if (!expanded) group.open ? collapsed.delete(id) : collapsed.add(id); });
  return group;
}
function render() {
  const query = $('search').value.trim().toLowerCase(), filter = $('status').value;
  const visible = includedEntries().filter(entry => `${entry.name} ${entry.description} ${entry.commands.join(' ')} ${entry.category}`.toLowerCase().includes(query) && (!filter || state(entry.id) === filter));
  $('list').replaceChildren(); $('empty').hidden = visible.length > 0;
  const section = makeGroup('インストール確認', 'installation', Boolean(query || filter));
  $('list').append(section);
  for (const category of menuGroups) {
    const members = visible.filter(entry => groupOf(entry) === category);
    if (!members.length && (query || filter)) continue;
    const group = makeGroup(`${category} · ${members.length}`, category, Boolean(query || filter));
    for (const entry of members) {
      const button = node('button', '', 'item'); button.classList.toggle('selected', selected === entry.id);
      button.setAttribute('aria-pressed', String(selected === entry.id));
      const badge=indicator(state(entry.id));
      button.append(node('span', entry.name), badge);
      button.addEventListener('click', () => { selected = entry.id; render(); renderDetail(); }); group.append(button);
    }
    section.append(group);
  }
}
function renderSummary() {
  const counts = entries.reduce((a, entry) => { const value = state(entry.id); a[value] = (a[value] || 0) + 1; return a; }, {});
  const message = $('message'); message.replaceChildren(node('span', 'インストール確認完了 · '));
  for (const value of statuses) if (counts[value]) message.append(indicator(value, 'badge', `${value} ${counts[value]}`));
  message.append(node('span', ' 未検出は全体の起動失敗を意味しません。'));
}
function renderDetail() {
  const entry = entries.find(e => e.id === selected); if (!entry) return;
  const result = results.get(entry.id), root = $('detail'); root.replaceChildren();
  root.append(node('span', `インストール確認 / ${groupOf(entry)}`, 'eyebrow'), node('h2', entry.name), indicator(state(entry.id), 'status'), node('p', entry.description));
  const fields = [ ['利用区分', usageLabels[entry.usageTier] || '機能別の拡張'], ['機能カテゴリ', entry.category], ['必要性', entry.diagnosticsRequired ? '診断アプリの起動に必須' : entry.wholeSystemRequired ? 'Python バックエンド利用時の基盤' : '該当機能を選択して使用する場合に確認'], ['必要バージョン', entry.minimumVersion ? `${entry.minimumVersion} 以降（ソースの要件）` : ''], ['検出パス', result?.パス || '—'], ['バージョン', result?.バージョン || '—'], ['確認結果', result?.説明 || 'まだ診断していません。'], ['確認日時', result?.確認日時 ? new Date(result.確認日時).toLocaleString() : '—'], ['検出コマンド', entry.commands.join(' / ')], ['利用機能', (entry.required_by || []).join('、')], ['注意事項', entry.notes || ''] ];
  const dl = node('dl', ''); for (const [label, value] of fields) if (value) dl.append(node('dt', label), node('dd', value)); root.append(dl);
  root.append(node('h3', 'ソースの参照箇所')); const ul = node('ul', ''); const references=entry.evidence?.length ? [...new Set(entry.evidence.map(e => `${e.path}:${e.line}`))] : entry.sources || []; for (const source of references) ul.append(node('li', source)); root.append(ul);
}
async function connect() {
  if (connecting) return;
  connecting = true; $('connect').disabled = true; $('token').disabled = true;
  try { const data = await api('api/一覧'); entries = data.項目; collapsed.add('その他拡張'); results = new Map(data.結果.map(r => [r.id, r])); $('login').hidden = true; $('run').disabled = false; const coverage=data.調査; if (coverage?.sourceTargetFiles) $('coverage').textContent = `調査${coverage.complete ? '完了' : '途中'}: 対象ソース・設定 ${Number(coverage.scannedSourceFiles || 0).toLocaleString()} / ${Number(coverage.sourceTargetFiles).toLocaleString()} 件 · ${entries.length} 項目 · ${String(coverage.commit || '').slice(0,8)}。通常の Markdown 本文・画像・音声・モデル等は除外。任意設定やリモート環境の導入状況は静的調査では保証しません。`; $('message').textContent = `インストール確認: ${entries.length} 件。診断開始で、このサーバーの実行環境を確認します。`; render(); }
  catch (error) { $('message').textContent = error.message; }
  finally { connecting = false; $('connect').disabled = false; $('token').disabled = false; }
}
$('connect').addEventListener('click', () => { if (connecting) return; key = $('token').value.trim(); $('token').value = ''; connect(); });
$('token').addEventListener('keydown', e => { if (e.key === 'Enter') $('connect').click(); });
$('search').addEventListener('input', render); $('status').addEventListener('change', render);
$('run').addEventListener('click', async () => {
  $('run').disabled = true; $('message').textContent = '診断中です。プログラムごとに最大 5 秒、4 件ずつ確認しています…';
  try { const data = await api('api/診断', 'POST'); results = new Map(data.結果.map(r => [r.id, r])); render(); renderDetail(); renderSummary(); $('run').textContent = '再チェック'; }
  catch (error) { $('message').textContent = error.message; }
  finally { $('run').disabled = !key; }
});
if (key) connect();
