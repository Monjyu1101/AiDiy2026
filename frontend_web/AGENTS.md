# frontend_web 実装概要

## 本書の目的

このファイルは `frontend_web` の構成、設計方針、実装入口を示す概要ドキュメントです。
画面追加、qTubler、明細型編集、UI 統一ルール、開発コマンド、デバッグは `.aidiy/knowledge` に移動しています。
AI エージェントは、本書に個別手順や一時的な作業メモを追記しないでください。
業務システム機能追加は `../docs/` の開発ガイドを優先し、コアシステム機能調整は `../.aidiy/knowledge/_index.md` を入口にします。

## HowTo 参照先

| 目的 | 参照先 |
|------|--------|
| frontend_web の実装パターン、UI ルール、qTubler、明細型編集 | [`../.aidiy/knowledge/frontend_web,実装パターン.md`](../.aidiy/knowledge/frontend_web,実装パターン.md) |
| 業務画面追加 | [`../.aidiy/knowledge/frontend_web,画面追加手順.md`](../.aidiy/knowledge/frontend_web,画面追加手順.md) |
| X系静的画面 / ゲーム / デモ追加 | [`../.aidiy/knowledge/frontend_web,X系静的画面追加.md`](../.aidiy/knowledge/frontend_web,X系静的画面追加.md) |
| Vite proxy / CORS / ポート | [`../.aidiy/knowledge/frontend_web,frontend_avatar,backend_server,Viteプロキシ設定.md`](../.aidiy/knowledge/frontend_web,frontend_avatar,backend_server,Viteプロキシ設定.md) |
| JWT 認証 | [`../.aidiy/knowledge/backend_server,frontend_web,frontend_avatar,JWT認証フロー.md`](../.aidiy/knowledge/backend_server,frontend_web,frontend_avatar,JWT認証フロー.md) |
| 認証延長 | [`../.aidiy/knowledge/backend_server,frontend_web,frontend_avatar,認証延長ルール.md`](../.aidiy/knowledge/backend_server,frontend_web,frontend_avatar,認証延長ルール.md) |
| AI コア WebSocket | [`../.aidiy/knowledge/backend_server,frontend_avatar,frontend_web,AIコアWebSocket仕様.md`](../.aidiy/knowledge/backend_server,frontend_avatar,frontend_web,AIコアWebSocket仕様.md) |
| AI モデル設定 | [`../.aidiy/knowledge/backend_server,frontend_avatar,frontend_web,AIモデル設定変更手順.md`](../.aidiy/knowledge/backend_server,frontend_avatar,frontend_web,AIモデル設定変更手順.md) |
| Pinia Store パターン | [`../.aidiy/knowledge/frontend_web,Pinia Storeパターン.md`](../.aidiy/knowledge/frontend_web,Pinia Storeパターン.md) |
| Vue Router パターン | [`../.aidiy/knowledge/frontend_web,Vue Routerパターン.md`](../.aidiy/knowledge/frontend_web,Vue Routerパターン.md) |
| 開発環境起動、type-check、よくある問題 | [`../.aidiy/knowledge/共通,開発環境運用手順.md`](../.aidiy/knowledge/共通,開発環境運用手順.md) |

## 概要

`frontend_web` は AiDiy の通常 Web UI です。
管理画面、マスタ、トランザクション、ビュー、スケジューラ、AIコア、AIタスク、X系デモを提供します。

## 技術スタック

- Vue 3。
- Vite。
- TypeScript。
- Vue Router。
- Pinia。
- Axios。
- dayjs。
- Monaco Editor。
- qTubler 独自テーブル。

## 基本方針

- 日本語ファイル名、日本語 route、日本語 JSON key を使う。
- template の component tag は ASCII にする。
- 日本語 component は import して `<component :is="...">` で扱う。
- UI framework / CSS framework は使わず、既存 CSS と共有コンポーネントへ合わせる。
- API は `/core/*`、`/apps/*`、`/task/*`、`/team/*` を Vite proxy 経由で呼ぶ（`/task/*` は backend_task 8093、`/team/*` は backend_team 8094）。
- ビルドや type-check の実行判断は `開発環境運用手順.md` を確認する。
- TypeScript は strict mode 無効の設定で運用しているが、既存型定義を使い、不要な `any` の拡大は避ける。

## ファイル構成

| パス | 役割 |
|------|------|
| `src/main.ts` | Vue app 初期化 |
| `src/App.vue` | root component |
| `src/router/` | Vue Router |
| `src/stores/` | Pinia store |
| `src/api/client.ts` | Axios client |
| `src/components/` | 画面・共通コンポーネント |
| `src/components/_share/` | qTubler、共通 UI、ダイアログ |
| `src/types/` | TypeScript 型 |
| `src/utils/` | qAlert など |
| `src/assets/` | CSS / static assets |

## Router 概要

3 ファイル分割構成です。

| Router | 対象 |
|--------|------|
| `index.ts` | 基底 + router 生成。ログイン、ログアウト、X系全般 |
| `coreRouter.ts` | C系 / A系 / AIタスク（`/AIタスク`） |
| `appsRouter.ts` | M系 / T系 / V系 / S系 |

詳細なルート一覧と追加手順は `.aidiy/knowledge/frontend_web,Vue Routerパターン.md` を参照してください。

## 主要 UI

- `_Layout.vue`
- `_TopBar.vue`
- `_TopMenu.vue`
- `qTublerFrame.vue`
- `qAlert`
- `qConfirm`
- `qColorPicker`

qTubler は `_share/qTublerFrame.vue` を中心にした独自テーブルです。
ソート、ページング、行選択を持ち、外部 UI framework へ置き換えない方針です。

## 認証

JWT token と user は `frontend_web` では `localStorage` に保存します。
401 は Axios response interceptor でログアウト処理へ流します。
認証延長対象は `認証延長ルール.md` を参照してください。

## AI コア

`frontend_web` 版 AI コアは backend の `/core/AIコア` と WebSocket で接続します。
code1〜code6、ファイル、画像、チャット、設定ダイアログを扱います。

AI packet やモデル設定の詳細は `.aidiy/knowledge` の AI コア関連 HowTo を参照してください。

## 実装時の入口

- 業務 CRUD 画面は `components/C管理/`、`components/Mマスタ/`、`components/Tトラン/` を見る。
- V系一覧は `components/Vビュー/` を見る。
- S系は `components/Sスケジューラー/` を見る（route path は `/Sスケジュール/*`）。
- X系は `components/Xその他/` と `public/` を見る。
- AIタスク画面は `components/AIタスク/`（要求一覧 / フロー図 / 明細一覧 + 編集ダイアログ、API は backend_task の `/task/*`）を見る。
- AIチーム画面は `components/AIチーム/AIチーム.vue` を軽量な親とし、メンバー・立体表示・依頼状況・経験状況・会話状況・作業状況のコンポーネントへ責務を分ける。経験状況は掲示板のプロジェクトだけを「何を／誰が／完了日時」で表示し、行ダブルクリックで `dialog/AIチーム_応答内容.vue`（要求内容・応答内容・まとめ内容の共通ダイアログ）を開く。チーム空間のエージェント本体または名前ラベルをダブルクリックすると `dialog/AIチーム_会話要求.vue` を開き、掲示板のプロジェクトを初期値としてフォルダと `TASK_AI_*` を選び、`/team/エージェント/会話`へ単発会話を依頼する。AIは対象プロジェクトのソースを読んでから回答する調査モードで動くため、待機上限は6分（`最大待機秒`）で backend_team 側のHTTPタイムアウトと揃える。作業状況（`AIチーム_作業状況.vue`、`/team/作業/*`）は掲示板の目標の `作業ループ` がオンのときだけ画面下・中央に出し、作業ループ（`S`相談 → `P`計画 → `D`実行 → `C`評価 → `A`改善）の実行状況を「何を（PDCA区分）／誰が／開始日時」で表示する。会話状況（`AIチーム_会話状況.vue`、`/team/会話/*`）は掲示板の`チーム目標`が入力済み、`自動作業設定`がオン、`チーム作業`が空欄の協議中だけ出す。目標編集では、自動作業設定を利用者操作でオフからオンにしたときだけチーム作業欄を空にし、自動作業オンなら作業ループ設定に関係なく空欄保存を許可する。作業ループの右側には作業ループ回数（1〜99、99は無制限）を表示する。各パネルの定期API更新は`use表示連動ポーリング.ts`を共用し、非表示中は停止、タイトルバーの▶で折り畳み中は通常の2倍の間隔にする。草原の NPC（ネコ・イヌ・雲・蝶・飛行船）は `components/AIチーム/AIチーム_NPC制御.ts` が種別の登録と配置・更新の入口を持ち、個々の造形と動作は `AIチーム_NPC動作_ネコ.ts` / `_イヌ.ts` / `_雲.ts` / `_蝶.ts` / `_飛行船.ts` で調整する（ネコ・イヌ共通の四足処理は `AIチーム_NPC四足.ts`、共通型と擬似乱数は `AIチーム_NPC型.ts`）。NPC を増やすときは動作モジュールを追加し、`AIチーム_NPC制御.ts` の `NPC定義一覧` へ 1 行足す。チーム作業は NPC飛行船が 4 エリア上空を旋回しながら吊り下げる掲示板（常にカメラを向く）に最終更新値を表示し、クリックで `dialog/AIチーム_目標編集.vue`（`/team/目標/*`）を開く。掲示板の位置と向きは `AIチーム_NPC動作_飛行船.ts` の `吊り下げ物` として飛行船側が決める。
- API client や認証は `src/api/client.ts` と `src/stores/auth.ts` を見る。
- UI ルールや画面追加手順は必ず `.aidiy/knowledge/_index.md` から該当 HowTo を開く。
