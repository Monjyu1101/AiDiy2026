/*!
 * -*- coding: utf-8 -*-
 *
 * -------------------------------------------------------------------------
 * COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
 * Licensed under "AiDiy 公開利用ライセンス v1.1".
 * Commercial use requires prior written consent from all copyright holders.
 * See LICENSE for full terms. Thank you for keeping the rules.
 * https://github.com/monjyu1101/AiDiy2026
 * -------------------------------------------------------------------------
 */

import MarkdownIt from 'markdown-it';
import { streamControlOf, visibleStreamContent } from './stream-control';
import { 最下部追従 } from './scroll-follow';
import { 演出初期化, 到着表示, 枠飛行, 入力枠作成, 受信通知作成, type ターミナル演出 } from './arrival-effect';

declare function acquireVsCodeApi(): { postMessage(message: unknown): void; getState(): { 下書き?: string } | undefined; setState(state: unknown): void };
const vscode = acquireVsCodeApi();
const element = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const prompt = element<HTMLTextAreaElement>('prompt');
const 検証ループ = element<HTMLSelectElement>('self-check-loop');
// 検証回数は未保存ならオンライン・オフラインとも0回から始める。オフラインの間は0回に固定し、オンラインへ戻ると直前のオンラインの回数に戻す。
// オンラインで選んだ回数は拡張・単独起動版が保存し、次回の最初の状態通知（検証回数）で復元する。
検証ループ.value = '0';
let オフライン = false;
let 検証なし = false;
let オンライン検証回数 = '0';
let 検証回数復元済み = false;
const 初期起動画面 = element('welcome').cloneNode(true);
const modelButton = element<HTMLButtonElement>('choose-model');
const projectFolder = element<HTMLElement>('project-folder');
const 自動接続スイッチ = element<HTMLButtonElement>('auto-connect');
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
let 自動接続 = true;
let 停止待ち = false, 接続変更待ち = false;
let 操作許可 = false, モデル変更中 = false;
let メッセージJSON = '';
let 履歴JSON = '';
let 会話ID = '';
let 一覧表示中 = false;
let 削除対象ID = '';
const 演出済み回答 = new Set<string>();
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
let 飛行予約: { 起点: DOMRect; 本文: string; 件数: number; 期限: number } | undefined;
let 入力演出: { index: number; 先?: HTMLElement; 枠: HTMLElement } | undefined;
let 応答演出: { key: string; 段階: 'popup' | 'flight'; 先?: HTMLElement; 枠: HTMLElement; タイマー?: number; 文字?: ターミナル演出 } | undefined;
let 表示件数 = 0;
const 発言演出解除 = () => {
  飛行予約 = undefined;
  入力演出?.枠.remove(); 入力演出 = undefined;
  if (応答演出) { clearTimeout(応答演出.タイマー); 応答演出.文字?.停止(); 応答演出.枠.remove(); 応答演出 = undefined; }
};
// 発言の登場演出（共通処理は src/arrival-effect.ts）。Code は状態通知ごとに一覧を描き直すため、
// 演出中の発言は 入力演出 / 応答演出 で段階を引き継ぎ、飛行先はその発言の .content にする。
const 入力飛行開始 = (index: number, 起点: DOMRect, 本文: string) => {
  入力演出?.枠.remove();
  const frame = 入力枠作成(本文);
  const 演出: NonNullable<typeof 入力演出> = 入力演出 = { index, 枠: frame };
  return () => 枠飛行(frame, 起点, () => 演出.先?.querySelector<HTMLElement>('.content'), () => {
    if (入力演出 !== 演出) return;
    入力演出 = undefined; 到着表示(演出.先);
  });
};
// AI回答は画面中央に受信通知として出し、ターミナル演出で表示してから履歴へ飛ばす。
const 応答ポップアップ開始 = (key: string, text: string) => {
  if (応答演出) { clearTimeout(応答演出.タイマー); 応答演出.文字?.停止(); 応答演出.枠.remove(); 到着表示(応答演出.先); }
  const { popup, body } = 受信通知作成();
  const 演出: NonNullable<typeof 応答演出> = 応答演出 = { key, 段階: 'popup', 枠: popup };
  const 着地 = () => {
    if (応答演出 !== 演出) return;
    演出.段階 = 'flight';
    演出.先?.classList.remove('arrival-waiting'); 演出.先?.classList.add('arrival-pending');
    最下部表示();
    枠飛行(popup, popup.getBoundingClientRect(), () => 演出.先?.querySelector<HTMLElement>('.content'), () => {
      if (応答演出 !== 演出) return;
      応答演出 = undefined; 到着表示(演出.先);
    });
  };
  // 文字送りで全文を表示し終えたら、3秒中央に止めてから、確保した表示位置へ飛ばす。
  演出.文字 = 演出初期化(body, {
    カーソル色: '#00ff00', isStream: false,
    表示更新: () => { body.scrollTop = body.scrollHeight; },
    完了: () => { if (応答演出 === 演出) 演出.タイマー = window.setTimeout(着地, 3000); },
  });
  演出.文字.追加(text, true);
};
// ストリーム受信枠も AIコード.vue の output_stream 処理と同じく、受信した1行ごとに `行\n` をキューへ積んで
// ストリーム速度・シアンのカーソルで流す（行単位で積むため、短い行は1回8文字ずつ流れる）。
// 開始の制御コードで演出を作り、終了・中断の制御コードでだけ流し切ってカーソルを外す（実行中フラグでは終えない）。
// 拡張は次の送信まで進捗を貯めるため、検証などで再び開始されても枠を消さずに続きから流す。
let 進捗目標 = '';
let 進捗演出: ターミナル演出 | undefined;
let 進捗演出中 = false;
const 進捗演出終了 = () => {
  if (!進捗演出) return;
  const effect = 進捗演出; 進捗演出 = undefined;
  effect.追加('', true);
};
const 進捗演出開始 = (初期文字列 = '') => {
  進捗演出?.停止();
  進捗演出中 = true;
  const effect: ターミナル演出 = 演出初期化(element('progress'), {
    カーソル色: '#00ffff', isStream: true, 初期文字列, 表示更新: 最下部表示,
    完了: () => { if (!進捗演出 || 進捗演出 === effect) 進捗演出中 = false; },
  });
  進捗演出 = effect;
};
const 進捗行受信 = (line: string) => {
  // 途中から開いた画面などで開始を受けていなければ、表示中の内容の続きとして始める。
  if (!進捗演出) 進捗演出開始(進捗目標 ? `${進捗目標}\n` : '');
  進捗演出!.追加(`${line}\n`);
  進捗目標 = 進捗目標 ? `${進捗目標}\n${line}` : line;
};
// 状態通知の進捗全文は、初回表示・会話の切替と、演出していない間の表示合わせ（送信時の消去など）にだけ使う。
const 進捗表示更新 = (text: string, 直接: boolean) => {
  if (直接) { 進捗演出?.停止(); 進捗演出 = undefined; 進捗演出中 = false; }
  if (進捗演出中 || text === 進捗目標) return;
  element('progress').textContent = text; 進捗目標 = text; 最下部表示();
};
const ボタン更新 = () => {
  const send = element<HTMLButtonElement>('send');
  send.disabled = !入力許可 || 実行中 || 送信待ち || !prompt.value.trim();
  send.classList.toggle('ws-disabled', !入力許可);
  自動接続スイッチ.disabled = 実行中 || 送信待ち || 接続変更待ち || モデル変更中 || !操作許可;
  element<HTMLButtonElement>('stop').disabled = !操作許可 || 停止待ち || !実行中 || (!オフライン && !接続済み);
  if (送信待ち || 接続変更待ち) { newChat.disabled = true; modelButton.disabled = true; }
};
const 一覧切替 = (show: boolean) => {
  一覧表示中 = show;
  historyList.hidden = !show;
  element('conversation').hidden = show;
  element('progress-section').hidden = show || !進捗目標;
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
  飛行予約 = { 起点: prompt.getBoundingClientRect(), 本文: prompt.value, 件数: 表示件数, 期限: Date.now() + 15_000 };
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
element('stop').addEventListener('click', () => {
  if (element<HTMLButtonElement>('stop').disabled) return;
  停止待ち = true; ボタン更新();
  vscode.postMessage({ セッションID: 会話ID, チャンネル: 'code1', メッセージ識別: 'cancel_run', メッセージ内容: '強制停止！' });
});
modelButton.addEventListener('click', モデル選択を開く);
// オンラインで選び直した検証回数を保存し、次回も使う（オフラインの0回固定は選択できないため保存しない）。
検証ループ.addEventListener('change', () => {
  if (検証ループ.disabled) return;
  オンライン検証回数 = 検証ループ.value; 検証回数復元済み = true;
  post('setSelfCheckLoop', { count: Number(検証ループ.value) });
});
historyToggle.addEventListener('click', () => 一覧切替(!一覧表示中));
自動接続スイッチ.addEventListener('click', () => {
  if (自動接続スイッチ.disabled) return;
  接続変更待ち = true; ボタン更新();
  post('autoConnect', { enabled: !自動接続 });
});
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
      進捗演出開始(進捗目標 ? `${進捗目標}\n` : '');
    } else if (control === 'end' || control === 'cancel') {
      実行表示更新(false);
      progressSection.classList.remove('running');
      element('progress-title').textContent = '';
      element<HTMLDetailsElement>('progress-details').open = false;
      進捗演出終了();
    } else {
      const line = visibleStreamContent(content);
      element('progress-title').textContent = line.slice(0, 160);
      if (line) 進捗行受信(line);
    }
    最下部表示();
    return;
  }
  if (state.type === 'accepted') { prompt.value = ''; vscode.setState({ 下書き: '' }); 送信待ち = false; ボタン更新(); 最下部表示(); return; }
  if (state.type !== 'state') return;
  const 初回状態 = !会話ID;
  const 会話切替 = 会話ID !== state.会話ID;
  if (会話切替) {
    メッセージJSON = '';
    演出済み回答.clear();
    state.メッセージ.forEach((item: { 種別: string; 本文: string }, index: number) => {
      if (item.種別 === 'assistant') 演出済み回答.add(`${index}:${item.本文}`);
    });
    発言演出解除(); 表示件数 = 0;
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
  if (!検証回数復元済み && typeof state.検証回数 === 'number' && [0, 1, 2, 3].includes(state.検証回数)) {
    検証回数復元済み = true;
    オンライン検証回数 = String(state.検証回数);
    if (!nextNoVerification) 検証ループ.value = オンライン検証回数;
  }
  if (!nextNoVerification && 検証なし) 検証ループ.value = オンライン検証回数;
  検証なし = Boolean(nextNoVerification);
  検証ループ.disabled = 検証なし;
  if (検証なし) 検証ループ.value = '0';
  element('model-picker-description').textContent = オフライン ? 'aidiy_hermes を直接実行します。オンラインとは別のモデルを保存します。' : 'AIコアのコードAIを選択します。';
  送信待ち = false; 接続変更待ち = false; 実行中 = state.実行中;
  停止待ち = state.停止中 === true;
  操作許可 = state.信頼済み === true && state.画面接続済み !== false; モデル変更中 = state.モデル変更中 === true;
  接続済み = state.接続済み === true;
  自動接続 = state.自動接続 !== false;
  自動接続スイッチ.setAttribute('aria-checked', String(自動接続));
  自動接続スイッチ.title = `自動接続 ${自動接続 ? 'ON' : 'OFF'}`;
  自動接続スイッチ.disabled = 実行中 || 送信待ち || state.モデル変更中 || !state.信頼済み;
  element('chat-header').classList.toggle('auto-connect-off', !自動接続);
  入力許可 = 操作許可 && (オフライン || 接続済み) && !state.モデル変更中 && Boolean(state.作業フォルダ);
  element('welcome').hidden = state.メッセージ.length > 0;
  実行表示更新(実行中 && (オフライン || state.接続済み !== false));
  element('activity').classList.toggle('unavailable', !入力許可);
  element('activity').classList.toggle('connected', 接続済み);
  element('chat-header').classList.toggle('connected', 接続済み);
  element('activity-label').textContent = 接続済み ? '接続済み' : state.接続中 ? '接続中' : '未接続';
  newChat.disabled = 実行中 || state.モデル変更中 || !操作許可 || (!オフライン && state.接続済み === false) || (!state.作業フォルダ && !state.新規可能);
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
  modelButton.disabled = 実行中 || state.モデル変更中 || !操作許可 || (!オフライン && !state.作業フォルダ);
  element<HTMLButtonElement>('remove-attachment').disabled = 実行中;
  element('stop').hidden = !実行中;
  // STOP を表示している処理中は、入力欄の枠に光を流して処理中であることを示す。
  element('composer').classList.toggle('running', 実行中);
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
    const 最新応答index = state.メッセージ.reduce((latest: number, item: { 種別: string }, index: number) => item.種別 === 'assistant' ? index : latest, -1);
    // 送信後に追加されたユーザー発言を飛行先にする。届かないまま期限を過ぎた予約は破棄する。
    let 入力飛行実行: (() => void) | undefined;
    if (飛行予約 && Date.now() > 飛行予約.期限) 飛行予約 = undefined;
    if (飛行予約 && state.メッセージ.length > 飛行予約.件数) {
      const index = state.メッセージ.findLastIndex((item: { 種別: string }) => item.種別 === 'user');
      if (index >= 飛行予約.件数) 入力飛行実行 = 入力飛行開始(index, 飛行予約.起点, 飛行予約.本文);
      飛行予約 = undefined;
    }
    let 新規応答: { key: string; text: string; article: HTMLElement } | undefined;
    // 演出中の発言は描画し直しても同じ状態（ポップアップ中は非表示、飛行中は透明で場所を確保）を引き継ぐ。
    if (入力演出) 入力演出.先 = undefined;
    if (応答演出) 応答演出.先 = undefined;
    表示件数 = state.メッセージ.length;
    element('messages').replaceChildren(...state.メッセージ.map((item: { 種別: string; 本文: string }, index: number) => {
      const article = document.createElement('article'); article.className = `message ${item.種別}`;
      if (入力演出 && index === 入力演出.index) { article.classList.add('arrival-pending'); 入力演出.先 = article; }
      const content = document.createElement('div'); content.className = 'content';
      const key = `${index}:${item.本文}`;
      if (item.種別 === 'assistant') {
        content.innerHTML = markdown.render(item.本文);
        if (応答演出?.key === key) {
          article.classList.add(応答演出.段階 === 'popup' ? 'arrival-waiting' : 'arrival-pending'); 応答演出.先 = article;
        } else if (index === 最新応答index && !演出済み回答.has(key)) {
          演出済み回答.add(key);
          if (!document.hidden) { article.classList.add('arrival-waiting'); 新規応答 = { key, text: item.本文, article }; }
        }
      }
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
    入力飛行実行?.();
    if (新規応答) {
      応答ポップアップ開始(新規応答.key, 新規応答.text);
      if (応答演出) 応答演出.先 = 新規応答.article;
    }
  }
  // 拡張ホスト側で除外済みでも、古い状態や単独試用からの制御文字を防御的に表示しない。
  const visibleProgress = state.進捗.map((line: string) => visibleStreamContent(String(line))).filter(Boolean);
  const progressSection = element('progress-section');
  progressSection.hidden = 一覧表示中 || !visibleProgress.length;
  progressSection.classList.toggle('running', 実行中);
  element('progress-title').textContent = 実行中 ? (visibleProgress.at(-1) ?? '実行中…').slice(0, 160) : '直前の実行状況';
  // 会話の切替・初回表示では、保存済みの実行状況を演出せずにそのまま表示する。
  進捗表示更新(visibleProgress.join('\n'), 初回状態 || 会話切替);
  ボタン更新();
  初期表示開始();
});
ボタン更新();
post('ready');
