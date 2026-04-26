# Docker 構成と起動手順

## このメモを使う場面
- HTTPS 付き Nginx プロキシ構成で本番デプロイしたい
- Docker で全サービスをまとめて起動したい

## 関連ファイル
- `docker/` — Docker 構成一式
- `docker/README.md` — 詳細手順
- `docker/docker_1build.bat` — 初回ビルド
- `docker/docker_2start.bat` — 起動
- `docker/docker_3stop.bat` — 停止

## 構成概要

```
Nginx (HTTPS :443 / HTTP :80)
  ↓ プロキシ
  frontend_web  (静的ファイル)
  backend core  (:8091)
  backend apps  (:8092)
※ backend_mcp (:8095) は含まない
```

`backend_mcp` は Docker に含めない設計。MCP 連携が必要な場合はローカルで別途起動する。

`docker-compose.yml` では backend core/apps の 8091/8092 も直接公開している。通常の画面アクセスは Nginx の `https://localhost/` を使い、API確認や Swagger は `http://localhost:8091/docs` / `http://localhost:8092/docs` を使う。

## 起動手順

```bash
cd docker
docker_1build.bat   # 初回のみ（frontend_web npm run build → Docker イメージビルド）
docker_2start.bat   # 起動 → https://localhost/ でアクセス
docker_3stop.bat    # 停止
```

`docker_1build.bat` は `frontend_web` の `npm run build` を先行実行して `dist/` を生成してからイメージをビルドする。再ビルドが必要な場合も同じバッチを実行する。

## マウント構成

| ホスト側 | コンテナ内 | 備考 |
|---------|----------|------|
| `../_data/` | `/app/backend_server/_data/` | SQLite DB（書き込み可） |
| `../_config/` | `/app/backend_server/_config/` | APIキー設定（read-only） |
| `../frontend_web/dist/` | `/app/frontend_web/dist/` | ビルド済み静的ファイル |

- ローカル開発時の DB（`backend_server/_data/database.db`）と Docker の DB はパスが別。Docker 側で作成されたデータはホストの `_data/` 以下に残る。
- `_config` は read-only のため、コンテナ内から API キーを書き換えることはできない。設定変更後は Docker 外で `_config/AiDiy_key.json` を編集してから `docker_2start.bat` で再起動する。

## ポート構成

| ポート | 内容 |
|-------|------|
| 443 (HTTPS) | Nginx プロキシ → frontend_web + backend core/apps |
| 80 (HTTP) | HTTPS へリダイレクト |
| 8091 | backend core（Swagger 確認用） |
| 8092 | backend apps（Swagger 確認用） |

コンテナ名は `aidiy2026`（`docker logs aidiy2026` で確認可）。

## 注意点

- `backend_mcp` は Docker 構成外のため、MCP が必要な検証ではローカル起動も合わせて行う。
- 画面の HTTPS は Nginx 経由で確認する。API確認用には compose で公開されている 8091 / 8092 を直接使える。
- Docker 側の詳細手順や証明書まわりの変更は `docker/README.md` を優先して確認する。
- 音声機能やマイク権限を確認する場合は HTTPS が必須。`http://localhost:8091/docs` は API 確認用であり、ブラウザ音声機能の検証先ではない。
- `backend_mcp` の 8095 は Docker README 上の技術情報には載るが、この compose では未提供。MCP の疎通確認を Docker だけで完結させようとしない。
- HTTPS は自己署名証明書のため、初回アクセス時にブラウザの「安全でない」警告が出る。開発・検証用として扱う。
- `frontend_web` の変更を Docker に反映するには `docker_1build.bat` の再実行（`npm run build` + イメージ再ビルド）が必要。`npm run dev` の変更だけでは Docker 側には反映されない。

## 確認方法

起動後 `https://localhost/` にアクセスして frontend_web のログイン画面が表示されることを確認。

API と永続化の確認:

```powershell
cd docker
docker logs aidiy2026
curl http://localhost:8091/docs
curl http://localhost:8092/docs
```
