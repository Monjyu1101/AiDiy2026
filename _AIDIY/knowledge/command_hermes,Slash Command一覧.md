# Slash Command 一覧

> 文書: `command_hermes,Slash Command一覧.md` | 実装: `command_hermes/hermes_cli/commands.py`, `command_hermes/cli_main.py`

## このメモを使う場面

- 特定の slash command の存在やエイリアスを確認するとき
- 新しい slash command を追加するとき
- 既存 command のカテゴリや引数を変更するとき
- TUI 調整手順の補完として command 一覧を確認するとき

## アーキテクチャ

```text
cli_main.py の process_command()
  → hermes_cli/commands.py の resolve_command(name)
    → COMMAND_REGISTRY から CommandDef を検索（正規名 + alias）
  → 正規名で分岐処理
```

`COMMAND_REGISTRY` は `CommandDef` dataclass のリストです。

```python
@dataclass
class CommandDef:
    name: str              # 正規名（"/" 不含）
    description: str       # 説明文
    category: str          # カテゴリ
    aliases: tuple[str]    # エイリアス
    args_hint: str         # 引数ヒント
    subcommands: tuple[str] # タブ補完用サブコマンド
    cli_only: bool         # CLI 限定
    gateway_only: bool     # Gateway 限定
```

## 全コマンド一覧

### Session（23 コマンド）

| コマンド | エイリアス | 説明 |
|---------|-----------|------|
| `/new` | `reset` | 新規セッション開始 |
| `/clear` | | 画面クリア |
| `/redraw` | | 再描画 |
| `/history` | | 履歴表示 |
| `/save` | | セッション保存 |
| `/retry` | | 最後の応答を再試行 |
| `/undo` | | 最後のターンを取り消し |
| `/title` | | セッションタイトル変更 |
| `/branch` | `fork` | 分岐 |
| `/compress` | | コンテキスト圧縮 |
| `/rollback` | | ロールバック |
| `/snapshot` | `snap` | スナップショット |
| `/stop` | | 実行停止 |
| `/approve` | | 承認（Gateway） |
| `/deny` | | 拒否（Gateway） |
| `/background` | `bg`, `btw` | バックグラウンド実行 |
| `/agents` | `tasks` | エージェント/タスク管理 |
| `/queue` | `q` | キュー表示 |
| `/steer` | | 誘導 |
| `/goal` | | 目標設定 |
| `/status` | | ステータス表示 |
| `/resume` | | 再開 |
| `/sethome` | `set-home` | ホーム設定（Gateway） |

### Configuration（13 コマンド）

| コマンド | エイリアス | 説明 |
|---------|-----------|------|
| `/config` | | 設定変更 |
| `/model` | `provider` | モデル/プロバイダー切替 |
| `/personality` | | 人格設定 |
| `/statusbar` | `sb` | ステータスバー切替 |
| `/verbose` | | 冗長出力切替 |
| `/footer` | | フッター切替 |
| `/yolo` | | YOLO モード |
| `/reasoning` | | 推論表示切替 |
| `/fast` | | 高速モード |
| `/skin` | | スキン変更 |
| `/indicator` | | インジケータ切替 |
| `/voice` | | 音声設定 |
| `/busy` | | ビジー状態 |

### Tools & Skills（11 コマンド）

| コマンド | エイリアス | 説明 |
|---------|-----------|------|
| `/tools` | | ツール一覧 |
| `/toolsets` | | ツールセット管理 |
| `/skills` | | スキル一覧 |
| `/cron` | | Cron 管理 |
| `/curator` | | キュレーター |
| `/kanban` | | カンバン |
| `/reload` | | リロード |
| `/reload-mcp` | `reload_mcp` | MCP リロード |
| `/reload-skills` | `reload_skills` | スキルリロード |
| `/browser` | | ブラウザ操作 |
| `/plugins` | | プラグイン管理 |

### Info（12 コマンド）

| コマンド | エイリアス | 説明 |
|---------|-----------|------|
| `/commands` | | コマンド一覧表示 |
| `/help` | | ヘルプ |
| `/usage` | | 使用量表示 |
| `/insights` | | インサイト |
| `/platforms` | `gateway` | プラットフォーム一覧 |
| `/copy` | | コピー |
| `/paste` | | ペースト |
| `/image` | | 画像表示 |
| `/update` | | アップデート確認 |
| `/debug` | | デバッグ情報 |
| `/profile` | | プロファイル |
| `/gquota` | | クォータ表示 |

### Exit（1 コマンド）

| コマンド | エイリアス | 説明 |
|---------|-----------|------|
| `/quit` | `exit` | 終了 |

## コマンド追加手順

1. `hermes_cli/commands.py` の `COMMAND_REGISTRY` に `CommandDef` を追加
2. `cli_main.py` の `process_command()` に分岐処理を追加
3. 必要に応じて `_COMMAND_LOOKUP` は import 時に自動構築されるため再起動のみで反映

## 注意点

- **CLI only / Gateway only**: `cli_only` と `gateway_only` フラグで利用可能な表面を制御。両方 false なら両方で使える
- **エイリアス衝突**: `_build_command_lookup()` で全エイリアスがユニークであることを確認すること。衝突時は後の定義で上書きされる
- **サブコマンド**: `subcommands` はタブ補完用のヒント。実際の処理は `process_command()` で引数パースして分岐
