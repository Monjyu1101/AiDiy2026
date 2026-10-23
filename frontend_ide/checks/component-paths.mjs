// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
// 実Vue部品の論理名と機能別ソースの対応（テスト専用）。
export const componentPaths = {
  "RefreshButton": "共通表示/再読込ボタン.vue",
  "CodePanel": "コード/コードパネル.vue",
  "LivePanel": "ライブ/ライブパネル.vue",
  "TermPanel": "ターミナル/ターミナルパネル.vue",
  "TerminalProgress": "ターミナル/進捗表示.vue",
  "TerminalWelcome": "ターミナル/開始表示.vue",
  "SpaceView": "開発スペース/開発スペース.vue",
  "SpaceCanvas": "開発スペース/宇宙キャンバス.vue",
  "FileExplorer": "ファイル閲覧/ファイル一覧.vue",
  "ExplorerActionView": "ファイル閲覧/エクスプローラー操作表示.vue",
  "FileTypeIcon": "ファイル閲覧/ファイル種別アイコン.vue",
  "ViewerWindow": "ファイル閲覧/閲覧ウィンドウ.vue",
  "BrowserPanel": "ブラウザ/ブラウザパネル.vue",
  "FolderPages": "ファイル閲覧/フォルダページ.vue",
  "FileViewer": "ファイル閲覧/ファイルビューア.vue",
  "ViewerSession": "ファイル閲覧/閲覧セッション.vue",
  "AISearchPanel": "ファイル検索/AI検索パネル.vue",
  "FileAnalysisDialog": "ファイル検索/ファイル解析ダイアログ.vue",
  "FileHistoryDialog": "ファイル検索/ファイル履歴ダイアログ.vue",
  "DraftHandoffDialog": "下書き連携/下書き連携ダイアログ.vue",
  "StatusBar": "共通表示/状態バー.vue",
  "ModalDialog": "共通表示/共通ダイアログ.vue"
};
export function componentName(path) { return Object.keys(componentPaths).find(name => `../${componentPaths[name]}` === path); }
