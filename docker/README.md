# Docker環境ガイド

## 🚀 起動

```bash
cd docker
docker_1build.bat    # 初回のみ（5-10分）
docker_2start.bat    # 起動（約10秒）
```

## 🌐 アクセス

⚠️ **音声機能にはHTTPS必須**

```
https://localhost/
```

**初回アクセス時の証明書警告:**
- Chrome: 「詳細設定」→「localhostにアクセスする」
- Edge: 「詳細」→「Webページへ移動」

**ログイン:**
- ユーザー名: `admin`
- パスワード: （README.mdを確認）

## 📚 API

```
http://localhost:8091/docs  # Core API (C系, A系)
http://localhost:8092/docs  # Apps API (M系, T系, V系, S系)
```

## 🔧 基本操作

```bash
docker_2start.bat    # 起動
docker_3stop.bat     # 停止
docker_4delete.bat   # 完全削除
```

## 🗑️ 削除方法

### パターン1: コンテナ停止のみ（データ保持）

```bash
docker_3stop.bat
```

- コンテナを停止
- イメージ・データベース・SSL証明書は保持
- 次回は`docker_2start.bat`で再起動可能

### パターン2: コンテナとイメージ削除

```bash
docker_4delete.bat
```

- コンテナを停止・削除
- Dockerイメージを削除
- SSL証明書を削除
- データベース（`../_data`）は保持
- 次回は`docker_1build.bat`から再構築

### パターン3: 完全削除（データベースも削除）

```bash
# 1. コンテナとイメージを削除
docker_4delete.bat

# 2. データベースを削除
cd ..
rmdir /s /q _data

# 3. 一時ファイルを削除
rmdir /s /q temp
```

### パターン4: SSL証明書の信頼削除

証明書を信頼済みルートに追加した場合：

```cmd
certutil -delstore "Root" localhost
```

## 🔐 SSL証明書

### 証明書の信頼設定（警告を消す）

```cmd
cd docker
certutil -addstore "Root" ssl\cert.pem
```

### 証明書の再生成

```cmd
cd docker
rmdir /s /q ssl
docker_1build.bat
```

## 🚨 トラブルシューティング

### HTTPSでアクセスできない

```bash
docker ps                # コンテナ確認
docker logs aidiy2026    # ログ確認
docker_3stop.bat         # 停止
docker_2start.bat        # 再起動
```

### ポートが使用中

```cmd
# ポート確認
netstat -ano | findstr :8090
netstat -ano | findstr :443

# ローカル起動を停止してから再実行
docker_2start.bat
```

### イメージビルドエラー

```bash
# 完全クリーンアップ
docker_4delete.bat
docker system prune -a -f

# 再ビルド
docker_1build.bat
```

### データベースエラー

```bash
# 停止
docker_3stop.bat

# データベース削除
cd ..
move _data\AiDiy\database.db _data\AiDiy\database.db.backup

# 再起動（新規DB自動作成）
cd docker
docker_2start.bat
```

### マイクが使えない

1. HTTPSでアクセスしているか確認: `https://localhost/`
2. アドレスバーの錠前アイコン → マイク → 許可
3. F12開発者ツールでエラー確認

## 📝 技術情報

**ポート:**
- 8090: Frontend (Vue 3)
- 8091: Backend Core API
- 8092: Backend Apps API
- 80: HTTP（Nginxプロキシ、自動的にHTTPSへリダイレクト）
- 443: HTTPS（Nginxプロキシ）

**データ永続化:**
- `../temp`: ログ・作業ファイル
- `../_data`: SQLiteデータベース
- `./ssl`: SSL証明書

**コンテナ名:**
- `aidiy2026`: メインアプリケーション
- `aidiy2026-nginx`: Nginxリバースプロキシ
