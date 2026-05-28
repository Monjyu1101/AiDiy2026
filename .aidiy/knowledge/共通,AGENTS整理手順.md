# AGENTS.md 整理手順

> 文書: `共通,AGENTS整理手順.md` | 実装: `AGENTS.md`, `CLAUDE.md`, `backend_server/AGENTS.md`, `frontend_web/AGENTS.md`

## このメモを使う場面

- ルートまたはサブシステムの `AGENTS.md` を整理する。
- `_AIDIY.md` / `CLAUDE.md` / `AGENTS.md` / 下位 `AGENTS.md` / `docs/` / `.aidiy/knowledge` の役割分担を確認する。
- AI エージェントが AGENTS に手順や作業ログを追記しそうなときに方針を揃える。

## 基本方針

- `_AIDIY.md` と `CLAUDE.md` は同一内容の最小入口にする。
- `AGENTS.md` はシステム概要、各サブシステム概要、文書インデックス、人間向け紹介資料の案内にする。
- 下位 `AGENTS.md` はサブシステム概要、構成、実装入口、参照先に絞る。
- HowTo、起動手順、追加手順、検証手順、トラブル対応、チェックリストは `.aidiy/knowledge` へ置く。
- 業務システム機能追加の説明は `docs/` を優先する。
- コアシステム機能調整の説明は `.aidiy/knowledge/_index.md` を入口にする。

## 整理前の確認

1. 対象 `AGENTS.md` の見出しを確認する。
2. 手順、コマンド、チェックリスト、トラブル対応、作業ログが混ざっていないか見る。
3. 既存ナレッジに転記先があるか `.aidiy/knowledge/_index.md` で探す。
4. 転記先がなければ、再利用できるテーマ名で新規ナレッジを作る。

## 転記ルール

- 内容は消す前に、該当する下位 `AGENTS.md` または `.aidiy/knowledge` へ移す。
- 古い・誤った記述は現行方針に合わせて補正して転記する。
- 単発履歴、今回だけの作業結果、issue 番号の実績記録は残さない。
- API キー、token、credential 実値は残さない。
- 転記後、AGENTS 側には「どこを参照するか」だけを残す。

## 文書別の役割

| 文書 | 役割 |
|------|------|
| `_AIDIY.md` | AI エージェント向け最小入口。詳細は `AGENTS.md` へ誘導するだけにする。 |
| `CLAUDE.md` | `_AIDIY.md` と同一内容にする。 |
| `AGENTS.md` | 全体概要、サブシステム概要、文書インデックス、人間向け紹介資料の案内。 |
| `backend_server/AGENTS.md` | backend_server の概要、構成、実装入口。 |
| `backend_hermes/AGENTS.md` | backend_hermes の概要、構成、実装入口。 |
| `backend_tools/AGENTS.md` | backend_tools の概要、構成、実装入口。 |
| `frontend_web/AGENTS.md` | frontend_web の概要、構成、実装入口。 |
| `frontend_avatar/AGENTS.md` | frontend_avatar の概要、構成、実装入口。 |
| `docs/` | 業務システム機能追加の手順。 |
| `.aidiy/knowledge/_index.md` | コアシステム機能調整や再利用 HowTo の入口。 |

## 確認順序

実装内容や方針を確認するときは、下記の順で読み進めます。

1. `_AIDIY.md` / `CLAUDE.md` — 最小限の入口（両ファイルは同一内容）
2. `AGENTS.md` — 全体概要、サブシステム概要、文書インデックス
3. `backend_server/AGENTS.md` — Backend 実装詳細
4. `backend_hermes/AGENTS.md` — Hermes CLI 実装詳細
5. `backend_tools/AGENTS.md` — MCP 実装詳細
6. `frontend_web/AGENTS.md` — Web UI 実装詳細
7. `frontend_avatar/AGENTS.md` — Avatar UI 実装詳細
8. `.aidiy/knowledge/_index.md` — コアシステム機能調整の HowTo 入口
9. `docs/` — 業務システム機能追加の手順（HTML）

各 AGENTS.md の記述より、実際のコードを最優先の同期元とします。
docs と実装が食い違う場合は、現行実装を確認したうえで「現行実装では」と明記します。

## AGENTS.md に残す内容

- 本書の役割。
- AI エージェント向けの「余計なことを追記しない」注意。
- システム概要またはサブシステム概要。
- 各文書へのインデックス。
- サブシステムの少し詳しい説明。
- 人間向け紹介資料 `frontend_web/public/X自己紹介/index.html` の案内はルート `AGENTS.md` に残す。

## AGENTS.md に残さない内容

- 起動コマンド。
- セットアップ手順。
- 依存関係同期手順。
- DB リセット手順。
- API / Swagger 確認手順。
- GitHub issue close 手順。
- 追加実装の詳細手順。
- Debugging 手順。
- Common Issues 表。
- 作業ログ、完了報告、直近変更メモ。

## 整理後の確認

```powershell
# AGENTS 系の大きな手順見出しが残っていないか
rg -n "^(## Development Commands|## 開発コマンド|## 起動方法|## 追加・変更の手順|## Debugging|## デバッグポイント|## よくある問題|## Common Issues|## Testing|## GitHub Issues)" -g AGENTS.md

# _AIDIY.md と CLAUDE.md が同一か
Compare-Object (Get-Content -Encoding UTF8 _AIDIY.md) (Get-Content -Encoding UTF8 CLAUDE.md)

# リンク切れ確認
$files = @("_AIDIY.md", "CLAUDE.md") + (rg --files -g AGENTS.md) + (rg --files .aidiy/knowledge -g "*.md")
$missingLinks = foreach ($file in $files) {
  $dir = Split-Path $file
  if (-not $dir) { $dir = "." }
  Select-String -Path $file -Pattern '\]\(([^)]+)\)' -AllMatches | ForEach-Object {
    foreach ($match in $_.Matches) {
      $link = $match.Groups[1].Value -replace '#.*$', ''
      if ($link -and $link -notmatch '^(https?://|#)') {
        $target = Join-Path $dir $link
        if (-not (Test-Path $target)) { "${file}:$($_.LineNumber) -> $link" }
      }
    }
  }
}
$missingLinks
```

## 注意点

- AGENTS を短くするときも、情報を単純削除せず、再利用価値がある内容は先に転記する。
- `_AIDIY.md` と `CLAUDE.md` に HowTo を戻さない。
- 下位 `AGENTS.md` にも手順を戻さず、参照リンクだけを置く。
