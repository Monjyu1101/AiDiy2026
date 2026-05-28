# Docker 構成と起動手順

> 文書: `backend_server,frontend_web,Docker構成.md` | 実装: `docker/`, `docker/README.md`

## このメモを使う場面
- HTTPS 付き Nginx プロキシ構成で画面を確認する
- Docker で core/apps/backend と frontend_web をまとめて起動する
- Docker 環境とローカル起動環境の差を判断する

## 関連ファイル
- `docker/` — Docker 構成一式
- `docker/README.md` — 証明書や詳細手順の一次確認先
- `docker/docker_1build.bat` — 初回ビルド、再ビルド
- `docker/docker_2start.bat` — 起動
- `docker/docker_3stop.bat` — 停止
- `frontend_web/dist/` — Docker が配信するビルド済み静的ファイル

## 構成

```text
Nginx (HTTPS :443 / HTTP :80)
  -> frontend_web 静的ファイル
  -> backend core (:8091)
  -> backend apps (:8092)
```

- `backend_tools` (`:8095`) は Docker 構成に含めない。MCP 検証が必要な場合はローカルで別途起動する。
- `docker-compose.yml` は core/apps の `8091` / `8092` も直接公開する。
- 通常の画面確認は `https://localhost/`、Swagger 確認は `http://localhost:8091/docs` / `http://localhost:8092/docs` を使う。
- コンテナ名は `aidiy2026`。ログ確認は `docker logs aidiy2026`。

## 起動手順

```powershell
cd docker
.\docker_1build.bat   # 初回、または frontend_web 変更反映時
.\docker_2start.bat   # 起動
.\docker_3stop.bat    # 停止
```

`docker_1build.bat` は `frontend_web` の `npm run build` で `dist/` を作ってから Docker イメージをビルドする。`npm run dev` の変更は Docker 側へ反映されないため、Docker で画面確認する前に再ビルドする。

## マウント構成

| ホスト側 | コンテナ内 | 備考 |
|---------|------------|------|
| `../_data/` | `/app/backend_server/_data/` | SQLite DB（書き込み可） |
| `../_config/` | `/app/backend_server/_config/` | APIキー設定（read-only） |
| `../frontend_web/dist/` | `/app/frontend_web/dist/` | ビルド済み静的ファイル |

- ローカル開発時の DB（`backend_server/_data/database.db`）と Docker 側の DB（ルート `_data/`）は別。
- `_config` は read-only。設定変更は Docker 外で `_config/AiDiy_key.json` を編集し、コンテナを再起動して反映する。

## 判断基準

- 音声機能やマイク権限を確認する場合は HTTPS の `https://localhost/` を使う。
- API の単体確認や Swagger は `8091` / `8092` を直接使ってよい。
- MCP を含む疎通確認は Docker だけで完結しない。`backend_tools` をローカル起動する。
- HTTPS は自己署名証明書のため、ブラウザ警告は開発・検証用として扱う。
- Docker 仕様や証明書まわりで迷った場合は `docker/README.md` を優先する。

## 確認方法

```powershell
curl.exe -k https://localhost/
curl.exe http://localhost:8091/docs
curl.exe http://localhost:8092/docs
docker logs aidiy2026
```

画面確認では `https://localhost/` にログイン画面が表示されることを確認する。
