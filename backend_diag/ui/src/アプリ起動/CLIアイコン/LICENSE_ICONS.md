# CLI アイコンのライセンス・引用メモ

このフォルダの画像の引用元・加工内容・利用条件を整理します。製品名は起動対象の識別用であり、各社による AiDiy の提供・承認・提携を意味しません。画像の利用許諾は、商標に関する権利の許諾とは別です。

表示用7件は120×120pxの合成画像です。外部CLI6件は元の図形を上部84×84pxの枠内に等比配置し、重ならない下部120×30pxに白い帯と黒い名前を追加しています。HermesはAiDiy原本を120×120px全面に等比配置し、下部25%へ名称帯を重ねています。原本は `upstream/` に無改変で保持します。名前帯はアプリの識別用キャプションであり、権利者が制作・承認した新しいブランドロゴとは称しません。合成画像の作成・配布の包括的な商標許諾を取得したという意味ではありません。

## GitHub Copilot

- 対象: `copilot.svg`、`copilot.png`、無改変原本 `upstream/copilot-24.svg`。
- 引用元: [GitHub 管理の primer/octicons / copilot-24.svg](https://github.com/primer/octicons/blob/f04253eb4088fb9869418771effb391fa13a2744/icons/copilot-24.svg)。固定版 `@primer/octicons-react@19.40.0`、commit `f04253eb4088fb9869418771effb391fa13a2744`。
- 原本 SHA-256: `eeafb3c2f333e04ccf7d031ae215f7adafaed4c6352556b0bf79496e048bcdd7`。
- ライセンス: [MIT License / Copyright (c) 2026 GitHub Inc.](https://github.com/primer/octicons/blob/f04253eb4088fb9869418771effb391fa13a2744/LICENSE)。取得したライセンス全文は [LICENSE-Octicons.txt](./LICENSE-Octicons.txt) に無改変で保存しています。
- 加工: 2 本のパス形状と入れ子 SVG の24単位の viewBoxを維持。色は従来の暗色 UI 用 `#f0f6fc` のままです。120×120pxの表示枠に等比配置し、図形の外に白帯・黒字の Copilot を追加。PNG はこの合成 SVG から120×120pxで生成しています。
- 再配布時は MIT の著作権表示・許諾条項を保持してください。元図案に AiDiy 独自ライセンスを適用しません。
- 商標・ブランド参照: [GitHub ロゴ指針](https://brand.github.com/foundations/logo)、[Copilot ブランド指針](https://brand.github.com/brand-identity/copilot)。ここでは既存製品を識別する UI アイコンとして使い、現行の公式プロモーションロゴや承認表示とは称しません。
- 取得候補の記録は `frontend_web/public/X自己紹介/アイコン画像URL.md` にもありますが、今回採用した原本は上記 Octicons の固定コミットです。

## AiDiy / aidiy_hermes

- 対象: `aidiy_hermes.png`、`aidiy_hermes.svg`、固定原本 `upstream/AiDiy.png`。
- 引用元: リポジトリ既存の [`frontend_web/public/icons/AiDiy.png`](../../../../../frontend_web/public/icons/AiDiy.png)。`_icons/AiDiy.png` および `frontend_avatar/public/icons/AiDiy.png` ともバイト単位で同一です。スクリーンショット由来ではありません。
- 原本形式: PNG、512×512px、RGBA。SHA-256: `3b580e91b8e91a2accd55675c07f2b2b8c3c9cf85677da804ef6b74ae8267042`。
- 加工: SVG の人物部分は原本 PNG の全バイトを data URI として無改変で埋め込んだラスター画像です。人物は等比縮小のみで、ベクター化・トレース・色変更・描き直し・切り抜きはしていません。原本を120×120px全面へ配置し、下部25%へ白帯・黒字の HERMES を1つ重ねます。文字は23pxで左右に余白を設けます。表示用 PNG は合成 SVG から生成した120×120pxの派生画像であり、原本とバイト同一ではありません。
- リポジトリ内の利用条件: [AiDiy 公開利用ライセンス v1.1](../../../../../LICENSE)、`Copyright (c) 2014-2026 Mitsuo KONDOU and contributors`。非商用利用と再配布条件はライセンス本文に従ってください。画像固有の別ライセンス・生成元の追加証跡はこの作業では確認できていません。独立した外部再配布の権利確認が完了したという意味ではありません。
- `aidiy_hermes` に AiDiy アイコンを使う指定に従った再利用です。別製品の公式ロゴと誤認させる加工はしていません。

## Antigravity CLI / agy

- 対象: `agy.svg`、`agy.png`。無改変原本: `upstream/antigravity-logo-mark.svg`。
- 引用元: [Google Antigravity 公式サイト](https://antigravity.google/) のヘッダーに埋め込まれた虹色の山形マーク（背景なし、180単位の viewBox）。取得日: 2026-10-20 UTC。ページ内の SVG 要素をそのまま保存し、末尾に改行1つを付けています。番号つきリリースはなく、取得時のハッシュで固定しています。
- 原本 SHA-256: `db3b1dd11fddd2680cc2b5785dbd79f03e1fb305c871b466c3485b4383fd957a`。
- 形状・色: viewBox、パス、マスク、ぼかしフィルター、色は入れ子 SVG 内にそのまま保持します。トリミングはしていません。表示用 SVG は共通枠に等比配置し、図形の外の白帯に黒字の Agy を追加。PNG は合成 SVG をブラウザで描画した120×120pxの透過出力で、公式配布ファイルそのものではありません。
- 利用条件: Google の製品ロゴであり、MIT 等のオープンライセンスは付いていません。商標その他の権利は Google に帰属します。Antigravity CLI の起動先の識別だけに使い、AiDiy 自身のマークとしては使いません。公式な提携・承認を示すものではなく、AiDiy のソフトウェアライセンスによって再許諾しません。この記録は、全配布・宣伝用途への許諾を保証するものではありません。

## Claude Code / Codex

取得日: 2026-10-20 UTC。両者は LobeHub の第三者アイコン集にある製品専用 SVG であり、OpenAI / Anthropic が直接配布した公式素材ではありません。固定版は `@lobehub/icons@6.0.0`、commit `8a1b2821bb768c484fe8da20c5e1838b6bf551a9` です。

### Claude Code

- 対象: `claude.svg`、`claude.png`。無改変原本: `upstream/claude-code-color-lobe.svg`。
- 引用元: [Lobe Icons / claudecode-color.svg](https://github.com/lobehub/lobe-icons/blob/8a1b2821bb768c484fe8da20c5e1838b6bf551a9/packages/static-svg/icons/claudecode-color.svg)。[製品との対応情報](https://github.com/lobehub/lobe-icons/blob/8a1b2821bb768c484fe8da20c5e1838b6bf551a9/src/ClaudeCode/index.mdx)。
- 原本 SHA-256: `670b3d8d749d0815ad8f7e62a59d51cb5e2053cb19403f3541a8aed7036a877f`。Git blob SHA: `ed1293c473d1b6fca5403f7abddaa9147fa46d72`。
- 形状・色: 24単位の viewBox、ピクセルキャラクター、色 `#D97757` は入れ子 SVG 内に原本のまま保持します。表示用 SVG は共通枠に等比配置し、図形の外の白帯に黒字の Claude を追加。PNG は合成結果の120×120px出力です。保存原本は全バイト無改変です。

### Codex

- 対象: `codex.svg`、`codex.png`。無改変原本: `upstream/codex-color-lobe.svg`。
- 引用元: [Lobe Icons / codex-color.svg](https://github.com/lobehub/lobe-icons/blob/8a1b2821bb768c484fe8da20c5e1838b6bf551a9/packages/static-svg/icons/codex-color.svg)。[製品との対応情報](https://github.com/lobehub/lobe-icons/blob/8a1b2821bb768c484fe8da20c5e1838b6bf551a9/src/Codex/index.mdx)。
- 原本 SHA-256: `4a2f43ce46b5b6e3722c95088f88d26ef91e6a8c2e598e70642a1c54367386e4`。Git blob SHA: `c77ccfdd9073d71cfbc3521dd7f31efb2455d916`。
- 形状・色: 24単位の viewBox、白い角丸背景と青紫のグラデーションは入れ子 SVG 内に原本のまま保持します。表示用 SVG は共通枠に等比配置し、図形の外の白帯に黒字の Codex を追加。PNG は合成結果の120×120px出力です。保存原本は全バイト無改変です。

### 利用条件と権利の区別

合成時は Lobe SVG の `1em` viewport を入れ子 SVG の84×84px枠に明示します。原本の viewBox・全パス・色・縦横比を保持し、識別用の名前帯を外側に追加します。`upstream/` の保存原本は取得時の全バイトを維持しますが、配布 SVG はこの合成処理をした派生物です。

- 配布元のライセンス: [Lobe Icons MIT License](https://github.com/lobehub/lobe-icons/blob/8a1b2821bb768c484fe8da20c5e1838b6bf551a9/LICENSE)、`Copyright (c) 2023 LobeHub`。全文を [LICENSE-LobeHub.txt](./LICENSE-LobeHub.txt) と本メモ末尾に保持しています。
- ライセンス原文 SHA-256: `add9d7531d1b21646317a8958e38fc727506fa39d24bdecb44154d943c82753a`。調査した固定ツリーの対象 SVG・親ディレクトリに別の LICENSE / NOTICE / DISCLAIMER は確認されていませんが、第三者権利が存在しないという保証ではありません。
- 公式の権利条件: [OpenAI ブランド指針](https://openai.com/brand/)、[Anthropic 商標指針](https://www.anthropic.com/legal/trademark-guidelines)。LobeHub の MIT 表記を、両社の商標の包括的許諾・公認・提携の根拠にしません。
- Anthropic の指針は事前承認された資料での使用を規定しています。この CLI ランチャーへの個別許諾は取得していません。OpenAI の指針についても、この第三者素材と用途への個別の許諾を確認したものではありません。
- 実際の CLI の識別用として、図形と製品名キャプションを同じ SVG 内の重ならない領域に配置します。図形への文字・バッジの上書きや色変更は行いません。公式の複合ロゴとは称しません。このメモは全配布・宣伝用途の適法性や許諾取得を保証しません。

## Grok

- 対象: `grok.svg`、`grok.png`。無改変原本: `upstream/Grok_Logomark_Light.svg`。
- 引用元: [公式ブランド指針](https://x.ai/legal/brand-guidelines) からリンクされる [SpaceXAI_Grok_Assets.zip](https://data.x.ai/logos/SpaceXAI_Grok_Assets.zip)。取得日: 2026-10-20 UTC。ZIP 内の `SpaceXAI_Grok_Assets/Grok_Logomark_Light.svg` を使用しています。
- 原本 SHA-256: `b20648e2f111d7fbc91f58b22d1e76e9885b68a163cb5a1010f7f11bf5840491`。配布 ZIP SHA-256: `db9129acd4efc4c2202d25afe31b70281a79f8507f75520ab5e6b3356895a7e9`。番号つきリリースはなく、取得時のハッシュで固定しています。
- 形状・色: 1024単位の viewBoxと公式の白い図形は入れ子 SVG 内にそのまま保持。保存原本は全バイト無改変です。表示用 SVG は共通枠に等比配置し、図形に重ならない白帯に黒字の Grok を追加したアプリ用派生画像です。PNG は合成結果の120×120px出力で、公式配布ファイルそのものではありません。
- 利用条件: MIT / Apache / CC0 ではなく、上記の Brand Guidelines に基づく権利者のブランド素材です。指針はサービスを正確に指す利用、図案の無改変、誤認・公認・提携の暗示禁止などを規定し、許諾の撤回や再許諾の制限もあります。配布 ZIP に独立したライセンスファイルはありません。
- AiDiy 自身のマークとして使わず、Grok に関連する起動先の識別に限定します。第三者 CLI が権利者の公式ソフトウェアであると示すものではありません。商標等の権利は権利者に帰属し、AiDiy のソフトウェアライセンスによって再許諾しません。この記録だけで全配布・宣伝用途への許諾を保証するものではありません。

## OpenCode

- 対象: `opencode.svg`、`opencode.png`。無改変原本: `upstream/opencode-logo-dark-square.svg`。
- 引用元: [公式ブランドページ](https://opencode.ai/brand) と同じ素材を、[公式リポジトリの固定 SVG](https://github.com/anomalyco/opencode/blob/6e9c85390bc232866f83ca19dfb46bd9d39b7aa1/packages/console/app/src/asset/brand/opencode-logo-dark-square.svg) から取得。commit `6e9c85390bc232866f83ca19dfb46bd9d39b7aa1`。取得日: 2026-10-20 UTC。
- 原本 SHA-256: `d6a0e3b8a295f413543f41cb73957e670351b5cb088c8d9dbd186b9e9d633cca`。
- 形状・色: 元から正方形の300×300px版。暗い背景用の `#F1ECEC` / `#4B4646`、viewBox、図形、マスク・クリップは入れ子 SVG 内に維持し、保存原本は全バイト無改変です。表示用 SVG は共通枠に等比配置し、図形の外の白帯に黒字の OpenCode を追加。PNG は合成結果の120×120px出力です。
- ライセンス: [MIT License](https://github.com/anomalyco/opencode/blob/6e9c85390bc232866f83ca19dfb46bd9d39b7aa1/LICENSE)、`Copyright (c) 2025 opencode`。全文を [LICENSE-OpenCode.txt](./LICENSE-OpenCode.txt) と本メモ末尾に保持します。原文 SHA-256: `625f0f619133f89bbbb2abe37369613dfa1885eba1e50d02170deb62bb42cb6b`。
- 確認したアイコンと親ディレクトリに別ライセンスの表記はありません。MIT は著作権上の利用条件であり、商標権・公式提携の許諾を意味しません。AiDiy は OpenCode チームが制作したものではなく、公式な提携・承認を示すものでもありません。

## 生成方法

生成スクリプトは同梱していません。合成の仕様・保存原本・生成物の関係は [README.md](./README.md) を参照してください。


## 再配布用の MIT 表示全文

本メモだけを配布物へコピーしても、次の著作権表示・許諾条項を欠落させないでください。各節の本文は同名のライセンスファイルと同一です。

### GitHub Octicons

```text
MIT License

Copyright (c) 2026 GitHub Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### LobeHub / Claude Code・Codex

```text
MIT License

Copyright (c) 2023 LobeHub

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### OpenCode

```text
MIT License

Copyright (c) 2025 opencode

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
