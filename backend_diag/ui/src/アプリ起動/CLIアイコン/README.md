# CLI ランチャーの画像素材

CLI ID と同じ名前の SVG / PNG をここに保存します。ライセンス・引用元・権利上の注意は [LICENSE_ICONS.md](./LICENSE_ICONS.md) に集約しています。

## 原本と生成物

- `copilot.svg` / `.png`: 保存済み Octicons 素材。取得時の無改変原本は `upstream/copilot-24.svg` です。
- `agy.svg` / `.png`: AiDiy 向けの独自ロケット図案。既存 SVG を生成元に使います。
- `aidiy_hermes.png`: 既存の `frontend_web/public/icons/AiDiy.png` を無改変でコピーした 512×512px の画像。固定原本は `upstream/AiDiy.png` です。
- `aidiy_hermes.svg`: 同じ AiDiy PNG を内包する自己完結型 SVG ラッパー。描画寸法は 96×96px ですが、内部画像は 512×512px のラスターであり、ベクター化・描き直しはしていません。
- `claude.svg` / `.png`、`codex.svg` / `.png`: LobeHub の製品専用カラーバリアント。SVG は第三者配布元の全バイトを維持します。ベンダーから直接配布された公式ファイルとは称しません。
- `grok.svg` / `.png`: 公式ブランド配布物の白い logomark。1024 単位の viewBox と色を維持します。
- `opencode.svg` / `.png`: 公式リポジトリの暗色 UI 用 square 版。300 単位の viewBox と色を維持します。

外部 4 件の原本は `upstream/claude-code-color-lobe.svg`、`upstream/codex-color-lobe.svg`、`upstream/Grok_Logomark_Light.svg`、`upstream/opencode-logo-dark-square.svg` です。出典・固定コミット・ハッシュ・権利上の留意点は `LICENSE_ICONS.md` を参照してください。

SVG / PNG の外部ネットワーク参照はありません。AiDiy PNG と外部 4 件の原本 SHA-256 は生成スクリプトに固定しています。既存 `frontend_web/public/icons/AiDiy.png` と同じ画像を保持し、他アプリ用の文字や装飾を追加しません。

## 再生成

リポジトリのルートで、既存の Python 3 を使います。ネットワーク取得や追加パッケージの自動インストールは行いません。アプリ起動時に変換処理は不要です。

```sh
# AiDiy の固定原本から Hermes だけを再現。Inkscape は不要。
python 'backend_diag/ui/src/アプリ起動/CLIアイコン/PNG生成.py' aidiy_hermes

# 保存済み全 7 件を再生成。既存の Inkscape が PATH に必要。
python 'backend_diag/ui/src/アプリ起動/CLIアイコン/PNG生成.py'
```

ID を複数指定すると、その対象だけを更新します。AiDiy は原本とバイト単位で同一の PNG と埋込 SVG を作り、それ以外は各 SVG を 96×96px の透過 PNG に変換します。PNG の寸法と RGBA 形式を検査します。外部 4 件は保存原本の SHA-256 を検査し、その無改変コピーを各 ID の SVG に復元してから PNG を作ります。SVG の物理寸法が `1em` や 1024px でも、viewBox と縦横比を保って 96×96px に出力します。Inkscape が `1em` を空の viewport として扱う場合を避けるため、Lobe SVG は一時コピーの width / height のみ 96px と明示して描画し、保存原本・配布 SVG のバイトは変更しません。Copilot / agy の生成元 SVG を変更した場合は対応 PNG も再生成してください。

変換時の一時設定はこのフォルダ内で作成して終了時に削除します。生成処理は原本・ライセンスファイルを書き換えません。配布 UI のビルド・静的ファイル同期は別の手順です。

配布時は `LICENSE_ICONS.md`、`LICENSE-Octicons.txt`、`LICENSE-LobeHub.txt`、`LICENSE-OpenCode.txt` を同名のまま `static/` へ同梱し、相互の参照先を維持します。旧名 `CLI_LICENSES.txt` は使いません。

Windows の checkout で原本 SVG が CRLF になった場合は、ハッシュ検査前に LF へ正規化し、各 ID の SVG を取得時の LF で復元します。変更は改行形式だけで、形状・色は維持します。AiDiy PNG は改行処理せず常にバイト単位で照合します。
