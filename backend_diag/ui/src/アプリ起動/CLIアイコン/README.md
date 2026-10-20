# CLI ランチャーの画像素材

CLI ID と同じ名前の SVG / PNG をここに保存します。ライセンス・引用元・権利上の注意は [LICENSE_ICONS.md](./LICENSE_ICONS.md) を参照してください。

## 表示用の合成画像

7 件とも 120×120px の自己完結した SVG と、その PNG 派生物です。ミニ表示では 40×40px の画像として使います。画像内に白い名前帯があるため、HTML 側で同じキャプションを重ねて表示しません。

| CLI ID / ファイル名 | 画像内の名前 | ロゴ・人物の保存原本 |
|---|---|---|
| `claude.svg` / `claude.png` | Claude | `upstream/claude-code-color-lobe.svg` |
| `codex.svg` / `codex.png` | Codex | `upstream/codex-color-lobe.svg` |
| `copilot.svg` / `copilot.png` | Copilot | `upstream/copilot-24.svg` |
| `agy.svg` / `agy.png` | Agy | `upstream/agy-aidiy.svg` |
| `grok.svg` / `grok.png` | Grok | `upstream/Grok_Logomark_Light.svg` |
| `opencode.svg` / `opencode.png` | OpenCode | `upstream/opencode-logo-dark-square.svg` |
| `aidiy_hermes.svg` / `aidiy_hermes.png` | HERMES | `upstream/AiDiy.png` |

- 共通の外枠は `viewBox="0 0 120 120"`。上部の x=18、y=3、84×84px に原本を縦横比を維持して配置します。元のパス、グラデーション、色、viewBox は保持し、トレース・描き直し・切り抜きは行いません。Copilot は従来の暗色 UI 用 `#f0f6fc` を維持します。
- 名前帯は x=0、y=90、120×30px、白 `#ffffff`。名前は中央揃え・黒 `#000000`・22px 太字です。フォント指定は Arial / Liberation Sans / sans-serif で、フォントファイルの埋め込み・配布はありません。
- 40px 表示時はロゴの最大表示枠が28px、名前帯が10px、文字指定が約7.3pxです。長い OpenCode も省略せず表示します。より大きい表示では同じ SVG を等比拡大してください。
- ロゴ領域の背景は透明です。Copilot / Grok / OpenCode は明るい図形を含むため、暗色 UI 上で表示します。白い名前帯は1つだけで、元の図形と重なりません。
- Claude Code / Codex は LobeHub が配布する製品専用の第三者素材です。合成画像をベンダーの公式配布ファイルとは称しません。Agy は既存の独自ロケットで、公式ロゴではありません。
- Hermes の人物部分は既存の AiDiy PNG を無改変バイトの data URI として埋め込みます。人物は512×512pxのラスターで、ベクター化していません。ラベルのない原本の外に HERMES 帯を1つ追加しています。表示用 PNG は120×120pxの合成結果なので、原本とバイト同一ではありません。

SVG / PNG の外部ネットワーク参照はありません。保存原本を加工せず、生成時に SHA-256 を照合します。AiDiy 原本は既存 `frontend_web/public/icons/AiDiy.png` と同一です。

## 再生成

リポジトリのルートで、既存の Python 3 と Inkscape を使います。ネットワーク取得や追加パッケージの自動インストールは行いません。アプリ起動時に変換処理は不要です。

```sh
# 保存済み全 7 件から、名前帯つき SVG と 120×120px PNG を再生成。
python 'backend_diag/ui/src/アプリ起動/CLIアイコン/PNG生成.py'

# 指定した ID だけを再生成。
python 'backend_diag/ui/src/アプリ起動/CLIアイコン/PNG生成.py' copilot aidiy_hermes
```

7件とも、PNG生成には PATH 上の既存 Inkscape が必要です。原本のハッシュ照合後、共通枠・名前帯と合成して SVG を保存し、その SVG から RGBA PNG を出力・寸法検査します。元の viewBox を入れ子 SVG 内に残すため、パスやマスクなどの座標・縦横比は変わりません。Hermes は原本 PNG を埋め込んだ SVG から出力します。

Windows の checkout で原本 SVG が CRLF になった場合は、ハッシュ検査前に LF へ正規化します。AiDiy PNG は改行処理せず常にバイト単位で照合します。変換時の一時設定はこのフォルダ内で作成して終了時に削除します。生成処理は原本・ライセンスファイルを書き換えません。

配布 UI のビルド・静的ファイル同期は別の手順です。配布時は `LICENSE_ICONS.md`、`LICENSE-Octicons.txt`、`LICENSE-LobeHub.txt`、`LICENSE-OpenCode.txt` を同名のまま `static/` へ同梱し、相互の参照先を維持します。旧名 `CLI_LICENSES.txt` は使いません。
