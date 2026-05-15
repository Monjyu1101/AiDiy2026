# AiDiy backend_server 紹介 — ナレーション台本

## scene_000 (0〜12秒) INTRODUCTION
この動画では、AiDiy の backend_server を紹介します。2 サーバー構成と 4 層アーキテクチャ、日本語ファースト命名、採番と監査フィールド、V系ビューまで、実装に沿って見ていきます。

## scene_001 (12〜26秒) DUAL SERVER
backend_server は core_main と apps_main の 2 サーバー構成です。core_main はポート 8091 で C系、A系、認証、AIコアを担当。apps_main はポート 8092 で M系、T系、V系、S系を担当します。両サーバーは同じ SQLite DB ファイルを共有します。

## scene_002 (26〜40秒) JAPANESE FIRST
AiDiy は全レイヤーで日本語識別子を使う「日本語ファースト設計」です。テーブル名・カラム名・API パス・JSON キー・ファイル名・Vue コンポーネント名まで日本語で統一します。接頭辞 C が Core 共通、A が AI、M がマスタ、T がトランザクション、V がビュー、S がスケジューラ、X が実験的機能を表します。

## scene_003 (40〜54秒) 4-LAYER
新規機能の実装は Model、Schema、CRUD、Router の 4 層構造に従います。Model は SQLAlchemy テーブル定義、Schema は Pydantic のリクエスト・レスポンス定義、CRUD は DB アクセスロジック、Router は FastAPI のエンドポイントです。最後に apps_main.py への include_router 登録と __init__.py への import 追加が必要です。これを漏らすと create_all で対象外になります。

## scene_004 (54〜68秒) NUMBERING & AUDIT
AiDiy は AUTOINCREMENT を使わず、C採番テーブルで採番を一元管理します。新規レコード作成前に get_next_id() で ID を取得します。全テーブルに 8 フィールドの監査情報が必須です。登録時は create_audit_fields()、更新時は update_audit_fields() を使い、個別実装で監査日時を直接作らないのがルールです。

## scene_005 (68〜82秒) V-SERIES VIEW
V系ビューは DB の VIEW オブジェクトを作らず、V系 Router ファイルに生 SQL を直接書きます。Model 層と CRUD 層は作りません。一覧取得では items と total で同じ FROM・JOIN・WHERE を使い、SQL への値埋め込みには bind params を使います。SQLAlchemy の Row は dict(row._mapping) で辞書化します。

## scene_006 (82〜96秒) BUSINESS SAMPLES
apps_main には業務サンプルとして M系が 9 テーブル、T系が 5 テーブル実装されています。M配車区分・M車両・M商品・M商品分類・M取引先分類・M取引先・M生産区分・M生産工程・M商品構成。T配車・T生産・T商品入庫・T商品出庫・T商品棚卸。S系スケジューラは配車と生産の日表示・週表示が 4 エンドポイント。明細型テーブルは明細SEQ=0 をヘッダー行に予約し、親ID と明細SEQ の複合主キーで管理します。

## scene_999 (96〜112秒) CLOSING
ご視聴ありがとうございました。backend_server は core_main と apps_main の 2 サーバーが同じ SQLite DB を共有し、Model・Schema・CRUD・Router の 4 層で業務機能を実装します。日本語ファースト設計、C採番、8 監査フィールド、V系生 SQL。業務サンプルを参考に、あなたの業務テーブルを追加してみてください。
