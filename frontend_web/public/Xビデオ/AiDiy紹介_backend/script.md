# AiDiy backend_server 紹介 — ナレーション台本

## scene_000 INTRODUCTION
AiDiy の backend_server を紹介します。API サーバーの構成と実装ルールを見ていきます。

## scene_001 DUAL SERVER
サーバーは 2 台構成です。core_main がポート 8091、apps_main がポート 8092 で動きます。両サーバーは同じデータベースを共有します。

## scene_002 JAPANESE FIRST
テーブル名も API パスも日本語で書きます。接頭辞 C は共通、M はマスタ、T はトランザクション、V はビューを表します。

## scene_003 4-LAYER
新機能を作るときは Model、Schema、CRUD、Router の 4 ファイルを順に作ります。最後に apps_main.py への登録が必要です。

## scene_004 NUMBERING & AUDIT
ID は C採番テーブルで管理します。全テーブルに登録者・更新者などの情報を記録する 8 つのフィールドが必要です。

## scene_005 V-SERIES VIEW
V 系は複数テーブルを結合して一覧を返す API です。データベースの VIEW は作らず、Router ファイルに SQL を直書きします。

## scene_006 BUSINESS SAMPLES
業務サンプルとして M 系 9 テーブル、T 系 5 テーブルが実装済みです。これを参考に機能を追加できます。

## scene_999 CLOSING
2 サーバー、4 層、日本語設計、採番、監査フィールド、V 系 SQL。サンプルを参考に追加してみてください。
