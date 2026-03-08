# frontend_avatar

既存の `frontend_server` / `backend_server` には手を入れずに動かせる、独立した Python 製デスクトップアバターです。
`frontend_avatar` フォルダ内で `uv` のローカル環境（`.venv`）を持つ前提に切り替えています。

起動時に `localhost:8091` の core API `POST /core/auth/ログイン` を使ってログインし、認証成功後だけアバター本体を表示します。
ログイン後は、同じログインIDをそのまま `セッションID` として `ws://localhost:8091/core/ws/AIコア` へ接続し、`audio` `input` `0` の3ソケットを張ります。
現在の既定動作は `frontend_avatar/アバター制御/vrm` の VRM を `three-vrm` で描画し、透明な常駐ウィンドウとして画面右下へ表示する構成です。
アバター本体は `PySide6 + QWebEngineView + three-vrm` で表示し、吹き出し、右クリックメニュー、入力ダイアログは `tkinter` オーバーレイで扱います。
表示制御の実体は `frontend_avatar/アバター制御/` 配下へ寄せてあり、VRM 表示と従来の 2D 表示を切り替えられる構成です。
認証・WebSocket などの AI 連携処理は `frontend_avatar/通信制御/`、音声入出力は `frontend_avatar/音声制御/`、画像送信は `frontend_avatar/画像制御/` 配下へ寄せています。

## 現在の機能

- `frontend_avatar/アバター制御/vrm` の VRM を使った `three-vrm` 表示
- 透明ウィンドウの常駐アバター
- 起動時ログインダイアログ
- ログインIDをそのまま使う AIコア WebSocket 接続
- `audio` `input` `0` ソケットの自動再接続
- `input` ソケットの `init.ボタン` を使う 3 状態同期
- 右クリックメニューから `マイク` `スピーカー` `カメラ` をオンオフ
- マイクON時は `audio/input_audio` をリアルタイム送信
- `audio` ソケットの `output_audio` を連続ストリームとして受信し、スピーカーON時だけ再生
- `input_image` を使う画像ストリーム送信
- 右クリックで `カメラ` を ON にしたとき、`画像ファイル` `カメラキャプチャ` `デスクトップキャプチャ` から送信元を選択
- `デスクトップキャプチャ` を選んだ場合は `フォーム選択` または `スクリーン選択` を選べる
- 変化検知後の安定待ち送信と、一定間隔での強制再送
- `0` チャンネルの `welcome_text` / `output_text` / `recognition_output` の吹き出し反映
- 左ドラッグで位置移動
- ダブルクリックで AI入力ダイアログ表示
- 右クリックメニュー
- 一定間隔でセリフを自動更新
- 2D ポーズ表示へのフォールバック

## 起動方法

初回セットアップ:

```powershell
python _setup_avatar.py
```

通常起動:

```powershell
cd frontend_avatar
uv run python main.py
```

認証先 URL は `frontend_avatar/settings.json` の `auth_base_url` で変更できます。

`uv` を使わずに手元の Python で実行したい場合だけ、従来どおり `requirements.txt` でも入れられます。

```powershell
python -m pip install -r frontend_avatar/requirements.txt
```

## 動作確認

アセット解決だけ確認する場合:

```powershell
cd frontend_avatar
uv run python main.py --check-assets
```

数秒だけ起動して閉じる場合:

```powershell
cd frontend_avatar
uv run python main.py --skip-login --demo-seconds 3
```

AIコア接続なしで見た目だけ確認する場合:

```powershell
cd frontend_avatar
uv run python main.py --skip-login --skip-core-connect --demo-seconds 3
```

## 設定

`frontend_avatar/settings.json` を編集すると以下を変更できます。

- 表示名
- 認証先 URL
- 表示バックエンド
- 初期位置
- サイズ倍率
- 最前面表示の初期値
- 初期オフセット
- 吹き出し表示時間
- VRM パス

## 備考

- フォルダ名は `frontend_avatar` で統一しています。
- Python 環境は `frontend_avatar/.venv` に閉じる前提です。
- 既定では `frontend_avatar/アバター制御/vrm` の VRM を読み込みます。
- `display_backend` を `2d` にすると従来の `frontend_avatar/アバター制御/ポーズ集` を使う表示へ戻せます。
- 通常起動では認証成功が必須です。`--skip-login` はローカル確認用です。
- 通常起動では、アバター再起動後も同じログインIDのセッションへ戻る前提です。
- マイク入力は `frontend_server` と同じ方針で、`openai_live` のとき 24kHz、それ以外は 16kHz です。
- スピーカーOFF時も `audio` ソケットの受信自体は継続し、再生だけ止めます。
- スピーカー出力は `sounddevice` のストリームを開いたまま維持し、`cancel_audio` では再生バッファだけクリアします。
- カメラON時は `AIイメージ.vue` と同じ考え方で、内容変化の収束後に `input_image` を送信し、変化がなくても一定間隔で再送します。
- `--skip-core-connect` を付けると WebSocket 接続を抑止できます。
