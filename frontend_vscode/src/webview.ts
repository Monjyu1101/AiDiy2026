import MarkdownIt from 'markdown-it';
import { streamControlOf, visibleStreamContent } from './stream-control';

declare function acquireVsCodeApi(): { postMessage(message: unknown): void; getState(): { 下書き?: string } | undefined; setState(state: unknown): void };
const vscode = acquireVsCodeApi();
const element = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const prompt = element<HTMLTextAreaElement>('prompt');
const modelButton = element<HTMLButtonElement>('choose-model');
const projectFolder = element<HTMLElement>('project-folder');
const modelPicker = element<HTMLDialogElement>('model-picker');
const providerSelect = element<HTMLSelectElement>('provider-select');
const modelSelect = element<HTMLSelectElement>('model-select');
const customModel = element<HTMLInputElement>('custom-model');
const customModelLabel = element<HTMLLabelElement>('custom-model-label');
const modelPickerStatus = element<HTMLParagraphElement>('model-picker-status');
const applyModel = element<HTMLButtonElement>('apply-model');
let provider = '', model = '';
let catalogProvider = '';
const markdown = new MarkdownIt({ html: false, linkify: false, breaks: true });
// 外部画像の読み込みやコマンド URI の実行を回答から発生させない。
markdown.renderer.rules.image = (tokens, index) => markdown.utils.escapeHtml(tokens[index].content);
let 実行中 = false, 送信待ち = false, 入力許可 = false;
let メッセージJSON = '';
let 会話ID = '';
const 演出済み回答 = new Set<string>();
let 演出タイマー: number | undefined;
prompt.value = vscode.getState()?.下書き ?? '';
const post = (type: string, data = {}) => vscode.postMessage({ type, ...data });
const 末尾省略 = (value: string, maximum = 28) => value.length > maximum ? `...${value.slice(-(maximum - 3))}` : value;
const 最下部表示 = () => {
  const conversation = element('conversation');
  conversation.scrollTop = conversation.scrollHeight;
};
const コンソール演出 = (content: HTMLDivElement, text: string, key: string) => {
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
  element<HTMLButtonElement>('send').disabled = !入力許可 || 実行中 || 送信待ち || !prompt.value.trim();
};
const 選択状態更新 = () => {
  const custom = modelSelect.value === '__manual__';
  customModel.hidden = customModelLabel.hidden = !custom;
  applyModel.disabled = providerSelect.disabled || modelSelect.disabled || (custom && !customModel.value.trim());
};
const 候補取得 = (targetProvider: string) => {
  catalogProvider = targetProvider;
  providerSelect.disabled = true; modelSelect.disabled = true; applyModel.disabled = true;
  modelPickerStatus.classList.remove('error');
  modelPickerStatus.textContent = targetProvider ? 'モデルを取得中…' : 'プロバイダを取得中…';
  post('chooseModel', { provider: targetProvider });
};
const 自動選択表示 = () => {
  modelSelect.replaceChildren(new Option('CLI の設定を使用', ''));
  modelSelect.disabled = true;
  modelPickerStatus.textContent = 'プロバイダとモデルは CLI の設定に任せます。';
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
prompt.addEventListener('input', () => { vscode.setState({ 下書き: prompt.value }); ボタン更新(); });
element('composer').addEventListener('submit', event => {
  event.preventDefault();
  if (!入力許可 || 実行中 || 送信待ち || !prompt.value.trim()) return;
  送信待ち = true; ボタン更新();
  vscode.postMessage({ セッションID: 会話ID, チャンネル: 'code1', メッセージ識別: 'input_text', メッセージ内容: prompt.value });
});
prompt.addEventListener('keydown', event => {
  if (event.key === 'Enter' && !event.shiftKey && !event.isComposing && event.keyCode !== 229) {
    event.preventDefault(); element<HTMLFormElement>('composer').requestSubmit();
  }
});
element('stop').addEventListener('click', () => vscode.postMessage({ セッションID: 会話ID, チャンネル: 'code1', メッセージ識別: 'cancel_run', メッセージ内容: '強制停止！' }));
modelButton.addEventListener('click', モデル選択を開く);
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
  if (state.type === 'modelCatalog') {
    if (!modelPicker.open || state.provider !== catalogProvider) return;
    const rows: { id: string; label: string }[] = Array.isArray(state.items) ? state.items.filter((item: unknown): item is { id: string; label: string } => {
      if (!item || typeof item !== 'object') return false;
      const row = item as Record<string, unknown>;
      return typeof row.id === 'string' && typeof row.label === 'string';
    }) : [];
    if (!state.provider) {
      providerSelect.replaceChildren(new Option('自動（CLI の設定）', ''), ...rows.map(item => new Option(item.label, item.id)));
      providerSelect.value = provider;
      if (providerSelect.selectedIndex < 0) providerSelect.selectedIndex = 0;
      providerSelect.disabled = false;
      if (providerSelect.value) 候補取得(providerSelect.value); else 自動選択表示();
      return;
    }
    modelSelect.replaceChildren(new Option('既定モデル（プロバイダの設定）', ''), ...rows.map(item => new Option(item.label, item.id)));
    if (state.provider === provider && model && !rows.some(item => item.id === model)) modelSelect.add(new Option(`${model}（現在のモデル）`, model));
    modelSelect.add(new Option('一覧にないモデル ID を入力…', '__manual__'));
    modelSelect.value = state.provider === provider ? model : '';
    customModel.value = state.provider === provider ? model : '';
    if (modelSelect.selectedIndex < 0) modelSelect.selectedIndex = 0;
    providerSelect.disabled = false; modelSelect.disabled = false;
    modelPickerStatus.textContent = '';
    選択状態更新();
    return;
  }
  if (state.type === 'modelCatalogError') {
    if (!modelPicker.open || state.provider !== catalogProvider) return;
    providerSelect.disabled = false; modelSelect.disabled = true; applyModel.disabled = true;
    modelPickerStatus.classList.add('error');
    modelPickerStatus.textContent = String(state.message ?? '候補を取得できません。');
    return;
  }
  if (state.メッセージ識別 === 'output_stream') {
    element('progress-section').hidden = false;
    const content = String(state.メッセージ内容 ?? '');
    const control = streamControlOf(content);
    if (control === 'start') {
      element('progress-title').textContent = '';
      element<HTMLDetailsElement>('progress-details').open = true;
    } else if (control === 'end' || control === 'cancel') {
      element('progress-title').textContent = '';
      element<HTMLDetailsElement>('progress-details').open = false;
    } else {
      element('progress-title').textContent = visibleStreamContent(content).slice(0, 160);
    }
    return;
  }
  if (state.type === 'accepted') { prompt.value = ''; vscode.setState({ 下書き: '' }); 送信待ち = false; ボタン更新(); return; }
  if (state.type !== 'state') return;
  会話ID = state.会話ID;
  送信待ち = false; 実行中 = state.実行中;
  入力許可 = state.信頼済み && Boolean(state.作業フォルダ);
  const projectName = String(state.作業フォルダ?.名前 ?? '');
  projectFolder.textContent = 末尾省略(projectName);
  projectFolder.title = projectName;
  provider = state.provider; model = state.model;
  const label = `${provider || '自動'} / ${model || (provider ? '既定モデル' : 'CLI の設定')}`;
  element('model-label').textContent = label;
  modelButton.title = `${label}\nクリックしてプロバイダとモデルを選択`;
  modelButton.disabled = 実行中 || !入力許可;
  element<HTMLButtonElement>('remove-attachment').disabled = 実行中;
  element('stop').hidden = !実行中;
  element('send').hidden = 実行中;
  const status = element('status');
  status.textContent = !state.信頼済み ? 'VS Code でワークスペースを信頼してください' : !state.作業フォルダ ? (state.作業URI ? '新規の会話を開始してください' : 'VS Code でフォルダを開いてください') : '';
  status.hidden = !status.textContent;
  element('attachment').hidden = !state.添付;
  element('attachment-name').textContent = state.添付 ?? '';
  const json = JSON.stringify(state.メッセージ);
  if (json !== メッセージJSON) {
    if (演出タイマー !== undefined) { clearTimeout(演出タイマー); 演出タイマー = undefined; }
    const conversation = element('conversation');
    const 下端 = conversation.scrollHeight - conversation.scrollTop - conversation.clientHeight < 70;
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
          prompt.focus(); prompt.setSelectionRange(prompt.value.length, prompt.value.length); ボタン更新();
        });
      }
      article.append(content); return article;
    }));
    if (下端) conversation.scrollTop = conversation.scrollHeight;
    メッセージJSON = json;
    演出候補.at(-1) && コンソール演出(演出候補.at(-1)!.content, 演出候補.at(-1)!.text, 演出候補.at(-1)!.key);
  }
  element('progress-section').hidden = !state.進捗.length;
  element('progress-title').textContent = 実行中 ? (state.進捗.at(-1) ?? '実行中…').slice(0, 160) : '直前の実行状況';
  element('progress').textContent = state.進捗.join('\n');
  ボタン更新();
});
post('ready');
