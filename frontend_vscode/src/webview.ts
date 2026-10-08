import MarkdownIt from 'markdown-it';
import { streamControlOf, visibleStreamContent } from './stream-control';
import { 最下部追従 } from './scroll-follow';

declare function acquireVsCodeApi(): { postMessage(message: unknown): void; getState(): { 下書き?: string } | undefined; setState(state: unknown): void };
const vscode = acquireVsCodeApi();
const element = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const prompt = element<HTMLTextAreaElement>('prompt');
const 検証ループ = element<HTMLSelectElement>('self-check-loop');
検証ループ.value = '1';
let オフライン = false;
let 検証なし = false;
let オンライン検証回数 = '1';
const 初期起動画面 = element('welcome').cloneNode(true);
const modelButton = element<HTMLButtonElement>('choose-model');
const projectFolder = element<HTMLElement>('project-folder');
const historyList = element<HTMLElement>('history-list');
const newChat = element<HTMLButtonElement>('new-chat');
const historyToggle = element<HTMLButtonElement>('history-toggle');
const deleteHistoryDialog = element<HTMLDialogElement>('delete-history-dialog');
const deleteHistoryName = element<HTMLElement>('delete-history-name');
const modelPicker = element<HTMLDialogElement>('model-picker');
const providerSelect = element<HTMLSelectElement>('provider-select');
const modelSelect = element<HTMLSelectElement>('model-select');
const customModel = element<HTMLInputElement>('custom-model');
const customModelLabel = element<HTMLLabelElement>('custom-model-label');
const modelPickerStatus = element<HTMLParagraphElement>('model-picker-status');
const applyModel = element<HTMLButtonElement>('apply-model');
let 初期表示開始済み = false;
const 初期表示開始 = () => {
  if (初期表示開始済み) return;
  初期表示開始済み = true;
  clearTimeout(初期表示待ち);
  // 状態反映後にレイアウトが確定するのを待ち、初回だけ黒から表示する。
  requestAnimationFrame(() => requestAnimationFrame(() => document.body.classList.add('ui-ready')));
};
// 初回通知が届かなくても、接続状況を確認できる画面は表示する。
const 初期表示待ち = window.setTimeout(初期表示開始, 2500);
let provider = '', model = '';
let catalogProvider = '';
const markdown = new MarkdownIt({ html: false, linkify: false, breaks: true });
// 外部画像の読み込みやコマンド URI の実行を回答から発生させない。
markdown.renderer.rules.image = (tokens, index) => markdown.utils.escapeHtml(tokens[index].content);
let 実行中 = false, 送信待ち = false, 入力許可 = false, 接続済み = false;
let メッセージJSON = '';
let 履歴JSON = '';
let 会話ID = '';
let 一覧表示中 = false;
let 削除対象ID = '';
const 演出済み回答 = new Set<string>();
let 演出タイマー: number | undefined;
prompt.value = vscode.getState()?.下書き ?? '';
const 初期文字演出停止 = () => {
  if (prompt.value.length > 0) element('welcome').classList.add('welcome-input-started');
};
初期文字演出停止();
const post = (type: string, data = {}) => vscode.postMessage({ type, ...data });
const 実行表示更新 = (running: boolean) => {
  element('chat-header').classList.toggle('running', running);
  element('activity').classList.toggle('running', running && 接続済み);
};
const 末尾省略 = (value: string, maximum = 28) => value.length > maximum ? `...${value.slice(-(maximum - 3))}` : value;
const 最下部表示 = 最下部追従([element('conversation'), element('progress')]);
const コンソール演出 = (content: HTMLDivElement, text: string, key: string) => {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    content.innerHTML = markdown.render(text); 演出済み回答.add(key); 最下部表示(); return;
  }
  content.classList.add('console-effect');
  const terminalText = document.createElement('span');
  const cursor = document.createElement('span'); cursor.className = 'terminal-cursor';
  content.replaceChildren(terminalText, cursor);
  const batch = Math.max(1, Math.floor(text.length / 50) + 1);
  let index = 0;
  const tick = () => {
    const end = Math.min(index + batch, text.length);
    terminalText.textContent += text.slice(index, end); index = end;
    最下部表示();
    if (index < text.length) { 演出タイマー = window.setTimeout(tick, 10); return; }
    cursor.remove(); content.classList.remove('console-effect');
    content.innerHTML = markdown.render(text); 演出済み回答.add(key); 最下部表示();
  };
  演出タイマー = window.setTimeout(tick, 500);
};
const ボタン更新 = () => {
  const send = element<HTMLButtonElement>('send');
  send.disabled = !入力許可 || 実行中 || 送信待ち || !prompt.value.trim();
  send.classList.toggle('ws-disabled', !入力許可);
};
const 一覧切替 = (show: boolean) => {
  一覧表示中 = show;
  historyList.hidden = !show;
  element('conversation').hidden = show;
  element('progress-section').hidden = show || !element('progress').textContent;
  element('chat-footer').hidden = show;
  historyToggle.textContent = show ? '戻る' : '一覧';
  historyToggle.setAttribute('aria-expanded', String(show));
  if (!show) 最下部表示();
};
const 日時表示 = (value: number) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  const pad = (part: number) => String(part).padStart(2, '0');
  return `${date.getFullYear()}/${pad(date.getMonth() + 1)}/${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
};
const 履歴表示 = (entries: { id: string; 題名: string; 更新日時: number }[]) => {
  if (!entries.length) {
    const empty = document.createElement('p'); empty.className = 'history-empty'; empty.textContent = 'このフォルダに会話履歴はありません';
    historyList.replaceChildren(empty); return;
  }
  historyList.replaceChildren(...[...entries].sort((a, b) => b.更新日時 - a.更新日時).map(entry => {
    const row = document.createElement('div'); row.className = `history-row${entry.id === 会話ID ? ' active' : ''}`; row.setAttribute('role', 'listitem');
    const open = document.createElement('button'); open.type = 'button'; open.className = 'history-open'; open.disabled = 実行中;
    open.title = entry.題名; open.setAttribute('aria-label', `会話を開く: ${entry.題名}`);
    const title = document.createElement('span'); title.className = 'history-title'; title.textContent = entry.題名;
    const date = document.createElement('span'); date.className = 'history-date'; date.textContent = 日時表示(entry.更新日時);
    open.append(date, title); open.addEventListener('click', () => { post('selectHistory', { id: entry.id }); 一覧切替(false); });
    const remove = document.createElement('button'); remove.type = 'button'; remove.className = 'history-delete'; remove.textContent = '削除';
    remove.title = '会話を削除'; remove.setAttribute('aria-label', `会話を削除: ${entry.題名}`); remove.disabled = 実行中;
    remove.addEventListener('click', () => {
      if (実行中 || deleteHistoryDialog.open) return;
      削除対象ID = entry.id;
      deleteHistoryName.textContent = entry.題名;
      deleteHistoryDialog.showModal();
    });
    row.append(open, remove); return row;
  }));
};
const 選択状態更新 = () => {
  const custom = modelSelect.value === '__manual__';
  customModel.hidden = customModelLabel.hidden = !custom;
  applyModel.disabled = (!オフライン && providerSelect.disabled) || modelSelect.disabled || (custom && !customModel.value.trim());
};
const 候補取得 = (targetProvider: string) => {
  catalogProvider = targetProvider;
  providerSelect.disabled = true; modelSelect.disabled = true; applyModel.disabled = true;
  modelPickerStatus.classList.remove('error');
  modelPickerStatus.textContent = targetProvider ? 'モデルを取得中…' : 'プロバイダを取得中…';
  post('chooseModel', { provider: targetProvider });
};
const 自動選択表示 = () => {
  modelSelect.replaceChildren(new Option('AIコアの設定を使用', ''));
  modelSelect.disabled = true;
  modelPickerStatus.textContent = 'コードAIとモデルは AIコアの設定を使います。';
  applyModel.disabled = false;
  customModel.hidden = customModelLabel.hidden = true;
};
const モデル選択を開く = () => {
  if (modelButton.disabled || modelPicker.open) return;
  providerSelect.replaceChildren(new Option('取得中…', ''));
  modelSelect.replaceChildren(new Option('取得中…', ''));
  customModel.value = model;
  modelPicker.showModal();
  候補取得('');
};
prompt.addEventListener('input', () => { 初期文字演出停止(); vscode.setState({ 下書き: prompt.value }); ボタン更新(); 最下部表示(); });
element('composer').addEventListener('submit', event => {
  event.preventDefault();
  if (!入力許可 || 実行中 || 送信待ち || !prompt.value.trim()) return;
  送信待ち = true; ボタン更新(); 最下部表示();
  vscode.postMessage({ セッションID: 会話ID, チャンネル: 'code1', メッセージ識別: 'input_text', メッセージ内容: prompt.value, self_check_loop: オフライン ? 0 : Number(検証ループ.value) });
});
prompt.addEventListener('keydown', event => {
  if (event.key !== 'Tab' || event.shiftKey || event.altKey || event.ctrlKey || event.metaKey
      || event.isComposing || event.keyCode === 229) return;
  const send = element<HTMLButtonElement>('send');
  if (send.disabled || send.hidden) return;
  event.preventDefault();
  send.focus();
});
element('stop').addEventListener('click', () => vscode.postMessage({ セッションID: 会話ID, チャンネル: 'code1', メッセージ識別: 'cancel_run', メッセージ内容: '強制停止！' }));
modelButton.addEventListener('click', モデル選択を開く);
historyToggle.addEventListener('click', () => 一覧切替(!一覧表示中));
newChat.addEventListener('click', () => {
  if (newChat.disabled) return;
  post('new');
  一覧切替(false);
});
deleteHistoryDialog.addEventListener('close', () => { 削除対象ID = ''; });
element<HTMLButtonElement>('confirm-delete-history').addEventListener('click', () => {
  if (!削除対象ID || 実行中) return;
  post('deleteHistory', { id: 削除対象ID });
  deleteHistoryDialog.close();
});
element<HTMLDetailsElement>('progress-details').addEventListener('toggle', () => {
  最下部表示();
});
element('remove-attachment').addEventListener('click', () => post('removeAttachment'));
providerSelect.addEventListener('change', () => providerSelect.value ? 候補取得(providerSelect.value) : 自動選択表示());
modelSelect.addEventListener('change', 選択状態更新);
customModel.addEventListener('input', 選択状態更新);
applyModel.addEventListener('click', () => {
  const selectedModel = modelSelect.value === '__manual__' ? customModel.value.trim() : modelSelect.value;
  if (modelSelect.value === '__manual__' && !selectedModel) { customModel.focus(); return; }
  post('setModel', { provider: providerSelect.value, model: selectedModel });
  modelPicker.close();
});
document.addEventListener('click', event => {
  const link = (event.target as HTMLElement).closest('a');
  if (!link) return;
  event.preventDefault();
  const url = link.getAttribute('href');
  if (url && /^https?:\/\//i.test(url)) post('link', { url });
});
window.addEventListener('message', event => {
  const state = event.data;
  if (state.type === 'showConversation') { 一覧切替(false); return; }
  if (state.type === 'modelCatalog') {
    if (!modelPicker.open || state.provider !== catalogProvider) return;
    const rows: { id: string; label: string }[] = Array.isArray(state.items) ? state.items.filter((item: unknown): item is { id: string; label: string } => {
      if (!item || typeof item !== 'object') return false;
      const row = item as Record<string, unknown>;
      return typeof row.id === 'string' && typeof row.label === 'string';
    }) : [];
    if (!state.provider) {
      providerSelect.replaceChildren(...(オフライン ? [] : [new Option('自動（AIコアの設定）', '')]), ...rows.map(item => new Option(item.label, item.id)));
      providerSelect.value = provider;
      if (providerSelect.selectedIndex < 0) providerSelect.selectedIndex = 0;
      providerSelect.disabled = オフライン;
      if (providerSelect.value) 候補取得(providerSelect.value); else 自動選択表示();
      return;
    }
    modelSelect.replaceChildren(...(オフライン ? [] : [new Option('既定モデル（プロバイダの設定）', '')]), ...rows.map(item => new Option(item.label, item.id)));
    if (!オフライン) {
      if (state.provider === provider && model && !rows.some(item => item.id === model)) modelSelect.add(new Option(`${model}（現在のモデル）`, model));
      modelSelect.add(new Option('一覧にないモデル ID を入力…', '__manual__'));
    }
    modelSelect.value = state.provider === provider ? model : オフライン ? 'auto' : '';
    customModel.value = state.provider === provider ? model : '';
    if (modelSelect.selectedIndex < 0) modelSelect.selectedIndex = 0;
    providerSelect.disabled = オフライン; modelSelect.disabled = false;
    modelPickerStatus.textContent = '';
    選択状態更新();
    return;
  }
  if (state.type === 'modelCatalogError') {
    if (!modelPicker.open || state.provider !== catalogProvider) return;
    providerSelect.disabled = オフライン; modelSelect.disabled = true; applyModel.disabled = true;
    modelPickerStatus.classList.add('error');
    modelPickerStatus.textContent = String(state.message ?? '候補を取得できません。');
    return;
  }
  if (state.メッセージ識別 === 'output_stream') {
    const progressSection = element('progress-section');
    progressSection.hidden = false;
    const content = String(state.メッセージ内容 ?? '');
    const control = streamControlOf(content);
    if (control === 'start') {
      実行表示更新(true);
      progressSection.classList.add('running');
      element('progress-title').textContent = '';
      element<HTMLDetailsElement>('progress-details').open = true;
    } else if (control === 'end' || control === 'cancel') {
      実行表示更新(false);
      progressSection.classList.remove('running');
      element('progress-title').textContent = '';
      element<HTMLDetailsElement>('progress-details').open = false;
    } else {
      element('progress-title').textContent = visibleStreamContent(content).slice(0, 160);
    }
    最下部表示();
    return;
  }
  if (state.type === 'accepted') { prompt.value = ''; vscode.setState({ 下書き: '' }); 送信待ち = false; ボタン更新(); 最下部表示(); return; }
  if (state.type !== 'state') return;
  const 初回状態 = !会話ID;
  if (会話ID !== state.会話ID) {
    メッセージJSON = '';
    演出済み回答.clear();
    state.メッセージ.forEach((item: { 種別: string; 本文: string }, index: number) => {
      if (item.種別 === 'assistant') 演出済み回答.add(`${index}:${item.本文}`);
    });
    if (演出タイマー !== undefined) { clearTimeout(演出タイマー); 演出タイマー = undefined; }
    if (!初回状態) { prompt.value = ''; vscode.setState({ 下書き: '' }); }
    if (!state.メッセージ.length) {
      // 新規会話では入力で停止した状態を戻し、CSS のターミナル演出を最初から再開する。
      element('welcome').replaceWith(初期起動画面.cloneNode(true));
      初期文字演出停止();
      element('conversation').scrollTop = 0;
    }
  }
  会話ID = state.会話ID;
  const nextOffline = state.実行モード === 'offline' || (state.オフライン対応 === true && state.接続済み !== true);
  if (nextOffline !== オフライン) {
    if (modelPicker.open) modelPicker.close();
  }
  オフライン = nextOffline;
  const nextNoVerification = オフライン || (state.オフライン対応 && state.接続済み !== true);
  if (nextNoVerification && !検証なし) オンライン検証回数 = 検証ループ.value;
  if (!nextNoVerification && 検証なし) 検証ループ.value = オンライン検証回数;
  検証なし = Boolean(nextNoVerification);
  検証ループ.disabled = 検証なし;
  if (検証なし) 検証ループ.value = '0';
  element('model-picker-description').textContent = オフライン ? 'aidiy_hermes を直接実行します。オンラインとは別のモデルを保存します。' : 'AIコアのコードAIを選択します。';
  送信待ち = false; 実行中 = state.実行中;
  接続済み = state.接続済み === true;
  入力許可 = state.信頼済み && (オフライン || 接続済み) && !state.モデル変更中 && Boolean(state.作業フォルダ);
  element('welcome').hidden = state.メッセージ.length > 0;
  実行表示更新(実行中 && (オフライン || state.接続済み !== false));
  element('activity').classList.toggle('unavailable', !入力許可);
  element('activity').classList.toggle('connected', 接続済み);
  element('chat-header').classList.toggle('connected', 接続済み);
  element('activity-label').textContent = 接続済み ? '接続済み' : state.接続中 ? '接続中' : '未接続';
  newChat.disabled = 実行中 || state.モデル変更中 || !state.信頼済み || (!オフライン && state.接続済み === false) || (!state.作業フォルダ && !state.新規可能);
  const projectName = String(state.作業フォルダ?.名前 ?? '');
  projectFolder.textContent = 末尾省略(projectName);
  projectFolder.title = projectName;
  const history = Array.isArray(state.履歴) ? state.履歴 : [];
  if (deleteHistoryDialog.open && (実行中 || !history.some((entry: { id: string }) => entry.id === 削除対象ID))) deleteHistoryDialog.close();
  const historyJSON = JSON.stringify([history, 会話ID, 実行中]);
  if (historyJSON !== 履歴JSON) { 履歴表示(history); 履歴JSON = historyJSON; }
  provider = state.provider; model = state.model;
  const label = `${provider || '自動'} - ${model || (provider ? '既定モデル' : 'AIコアの設定')}`;
  const modelLabel = element('model-label');
  modelLabel.textContent = label;
  modelLabel.title = label;
  modelButton.title = 'コードAIとモデルを選択';
  modelButton.disabled = 実行中 || state.モデル変更中 || !state.信頼済み || (!オフライン && !state.作業フォルダ);
  element<HTMLButtonElement>('remove-attachment').disabled = 実行中;
  element('stop').hidden = !実行中;
  element<HTMLButtonElement>('stop').disabled = !オフライン && !接続済み;
  element('send').hidden = 実行中;
  const status = element('status');
  status.textContent = !state.信頼済み ? 'VS Code でワークスペースを信頼してください' : !state.作業フォルダ ? (state.作業URI ? '新規の会話を開始してください' : '作業フォルダを開いてください') : '';
  status.hidden = !status.textContent;
  const errorBox = element('error');
  errorBox.textContent = String(state.接続エラー || '');
  errorBox.hidden = !errorBox.textContent;
  element('attachment').hidden = !state.添付;
  element('attachment-name').textContent = state.添付 ?? '';
  const json = JSON.stringify(state.メッセージ);
  if (json !== メッセージJSON) {
    if (演出タイマー !== undefined) { clearTimeout(演出タイマー); 演出タイマー = undefined; }
    const 演出候補: { content: HTMLDivElement; text: string; key: string }[] = [];
    const 最新応答index = state.メッセージ.reduce((latest: number, item: { 種別: string }, index: number) => item.種別 === 'assistant' ? index : latest, -1);
    element('messages').replaceChildren(...state.メッセージ.map((item: { 種別: string; 本文: string }, index: number) => {
      const article = document.createElement('article'); article.className = `message ${item.種別}`;
      const content = document.createElement('div'); content.className = 'content';
      const key = `${index}:${item.本文}`;
      if (item.種別 === 'assistant' && index === 最新応答index && !演出済み回答.has(key)) 演出候補.push({ content, text: item.本文, key });
      else if (item.種別 === 'assistant') content.innerHTML = markdown.render(item.本文);
      else content.textContent = item.本文;
      if (item.種別 === 'user') {
        content.title = 'クリックして入力欄へ戻す';
        content.addEventListener('click', () => {
          prompt.value = item.本文; vscode.setState({ 下書き: prompt.value });
          prompt.focus(); prompt.setSelectionRange(prompt.value.length, prompt.value.length); ボタン更新(); 最下部表示();
        });
      }
      article.append(content); return article;
    }));
    最下部表示();
    メッセージJSON = json;
    const 最新応答 = 演出候補.at(-1);
    if (最新応答) {
      最下部表示();
      コンソール演出(最新応答.content, 最新応答.text, 最新応答.key);
    }
  }
  // 拡張ホスト側で除外済みでも、古い状態や単独試用からの制御文字を防御的に表示しない。
  const visibleProgress = state.進捗.map((line: string) => visibleStreamContent(String(line))).filter(Boolean);
  const progressSection = element('progress-section');
  progressSection.hidden = 一覧表示中 || !visibleProgress.length;
  progressSection.classList.toggle('running', 実行中);
  element('progress-title').textContent = 実行中 ? (visibleProgress.at(-1) ?? '実行中…').slice(0, 160) : '直前の実行状況';
  const progress = element('progress');
  const progressText = visibleProgress.join('\n');
  if (progress.textContent !== progressText) {
    progress.textContent = progressText;
    最下部表示();
  }
  ボタン更新();
  初期表示開始();
});
ボタン更新();
post('ready');
