# CLI アイコンのライセンス・引用メモ

このフォルダの画像の引用元・加工内容・利用条件を整理します。製品名は起動対象の識別用であり、各社による AiDiy の提供・承認・提携を意味しません。画像の利用許諾は、商標に関する権利の許諾とは別です。

## GitHub Copilot

- 対象: `copilot.svg`、`copilot.png`、無改変原本 `upstream/copilot-24.svg`。
- 引用元: [GitHub 管理の primer/octicons / copilot-24.svg](https://github.com/primer/octicons/blob/f04253eb4088fb9869418771effb391fa13a2744/icons/copilot-24.svg)。固定版 `@primer/octicons-react@19.40.0`、commit `f04253eb4088fb9869418771effb391fa13a2744`。
- 原本 SHA-256: `eeafb3c2f333e04ccf7d031ae215f7adafaed4c6352556b0bf79496e048bcdd7`。
- ライセンス: [MIT License / Copyright (c) 2026 GitHub Inc.](https://github.com/primer/octicons/blob/f04253eb4088fb9869418771effb391fa13a2744/LICENSE)。取得したライセンス全文は [LICENSE-Octicons.txt](./LICENSE-Octicons.txt) に無改変で保存しています。
- 加工: 2 本のパス形状と 24 単位の viewBox は維持。SVG の出力寸法を 96px、色を暗色 UI 用の `#f0f6fc` とし、title / desc を追加。PNG は加工後 SVG から生成しています。
- 再配布時は MIT の著作権表示・許諾条項を保持してください。元図案に AiDiy 独自ライセンスを適用しません。
- 商標・ブランド参照: [GitHub ロゴ指針](https://brand.github.com/foundations/logo)、[Copilot ブランド指針](https://brand.github.com/brand-identity/copilot)。ここでは既存製品を識別する UI アイコンとして使い、現行の公式プロモーションロゴや承認表示とは称しません。
- 取得候補の記録は `frontend_web/public/X自己紹介/アイコン画像URL.md` にもありますが、今回採用した原本は上記 Octicons の固定コミットです。

## AiDiy / aidiy_hermes

- 対象: `aidiy_hermes.png`、`aidiy_hermes.svg`、固定原本 `upstream/AiDiy.png`。
- 引用元: リポジトリ既存の [`frontend_web/public/icons/AiDiy.png`](../../../../../frontend_web/public/icons/AiDiy.png)。`_icons/AiDiy.png` および `frontend_avatar/public/icons/AiDiy.png` ともバイト単位で同一です。スクリーンショット由来ではありません。
- 原本形式: PNG、512×512px、RGBA。SHA-256: `3b580e91b8e91a2accd55675c07f2b2b8c3c9cf85677da804ef6b74ae8267042`。
- 加工: PNG は原本を無改変コピー。SVG はその PNG を data URI として埋め込むラッパーのみで、実体はラスター画像です。ベクター化、トレース、色変更、描き直し、文字帯追加はしていません。
- リポジトリ内の利用条件: [AiDiy 公開利用ライセンス v1.1](../../../../../LICENSE)、`Copyright (c) 2014-2026 Mitsuo KONDOU and contributors`。非商用利用と再配布条件はライセンス本文に従ってください。画像固有の別ライセンス・生成元の追加証跡はこの作業では確認できていません。独立した外部再配布の権利確認が完了したという意味ではありません。
- `aidiy_hermes` に AiDiy アイコンを使う指定に従った再利用です。別製品の公式ロゴと誤認させる加工はしていません。

## Antigravity CLI / agy

- 対象: `agy.svg`、`agy.png`。
- 出典: AiDiy 向けに作成されたこのフォルダ既存の独自ピクトグラム（浮遊ロケット）。外部の公式ロゴや公式キャラクターの引用ではありません。
- 生成元: `agy.svg`。96 単位の viewBox。SVG の描き直し・差し替えは行っていません。PNG は保存済み SVG から生成します。
- ライセンス: リポジトリと同じ [AiDiy 公開利用ライセンス v1.1](../../../../../LICENSE)。`Copyright (c) 2014-2026 Mitsuo KONDOU and contributors`。再配布時はライセンス全文・著作権表示を含めてください。
- Antigravity の商標権その他の第三者権利を許諾するものではありません。

## Claude Code / Codex

取得日: 2026-10-20 UTC。両者は LobeHub の第三者アイコン集にある製品専用 SVG であり、OpenAI / Anthropic が直接配布した公式素材ではありません。固定版は `@lobehub/icons@6.0.0`、commit `8a1b2821bb768c484fe8da20c5e1838b6bf551a9` です。

### Claude Code

- 対象: `claude.svg`、`claude.png`。無改変原本: `upstream/claude-code-color-lobe.svg`。
- 引用元: [Lobe Icons / claudecode-color.svg](https://github.com/lobehub/lobe-icons/blob/8a1b2821bb768c484fe8da20c5e1838b6bf551a9/packages/static-svg/icons/claudecode-color.svg)。[製品との対応情報](https://github.com/lobehub/lobe-icons/blob/8a1b2821bb768c484fe8da20c5e1838b6bf551a9/src/ClaudeCode/index.mdx)。
- 原本 SHA-256: `670b3d8d749d0815ad8f7e62a59d51cb5e2053cb19403f3541a8aed7036a877f`。Git blob SHA: `ed1293c473d1b6fca5403f7abddaa9147fa46d72`。
- 形状・色: 24 単位の viewBox、ピクセルキャラクター。色 `#D97757` は原本のままです。SVG は全バイト無改変で保存。PNG への 96px 出力以外に加工はしていません。

### Codex

- 対象: `codex.svg`、`codex.png`。無改変原本: `upstream/codex-color-lobe.svg`。
- 引用元: [Lobe Icons / codex-color.svg](https://github.com/lobehub/lobe-icons/blob/8a1b2821bb768c484fe8da20c5e1838b6bf551a9/packages/static-svg/icons/codex-color.svg)。[製品との対応情報](https://github.com/lobehub/lobe-icons/blob/8a1b2821bb768c484fe8da20c5e1838b6bf551a9/src/Codex/index.mdx)。
- 原本 SHA-256: `4a2f43ce46b5b6e3722c95088f88d26ef91e6a8c2e598e70642a1c54367386e4`。Git blob SHA: `c77ccfdd9073d71cfbc3521dd7f31efb2455d916`。
- 形状・色: 24 単位の viewBox、白い角丸背景と青紫のグラデーションは原本のままです。SVG は全バイト無改変で保存。PNG への 96px 出力以外に加工はしていません。

### 利用条件と権利の区別

PNG 出力時に限り、Lobe SVG の `1em` viewport を描画用の一時コピーで 96px と明示します。viewBox・形状・色は変更せず、保存原本・配布 SVG は取得時の全バイトを維持します。

- 配布元のライセンス: [Lobe Icons MIT License](https://github.com/lobehub/lobe-icons/blob/8a1b2821bb768c484fe8da20c5e1838b6bf551a9/LICENSE)、`Copyright (c) 2023 LobeHub`。全文を [LICENSE-LobeHub.txt](./LICENSE-LobeHub.txt) と本メモ末尾に保持しています。
- ライセンス原文 SHA-256: `add9d7531d1b21646317a8958e38fc727506fa39d24bdecb44154d943c82753a`。調査した固定ツリーの対象 SVG・親ディレクトリに別の LICENSE / NOTICE / DISCLAIMER は確認されていませんが、第三者権利が存在しないという保証ではありません。
- 公式の権利条件: [OpenAI ブランド指針](https://openai.com/brand/)、[Anthropic 商標指針](https://www.anthropic.com/legal/trademark-guidelines)。LobeHub の MIT 表記を、両社の商標の包括的許諾・公認・提携の根拠にしません。
- Anthropic の指針は事前承認された資料での使用を規定しています。この CLI ランチャーへの個別許諾は取得していません。OpenAI の指針についても、この第三者素材と用途への個別の許諾を確認したものではありません。
- 実際の CLI の識別用として、画像と製品名キャプションを分離して表示します。文字帯・バッジの上書きや色変更、新しい合成ブランドは作りません。このメモは全配布・宣伝用途の適法性や許諾取得を保証しません。

## Grok

- 対象: `grok.svg`、`grok.png`。無改変原本: `upstream/Grok_Logomark_Light.svg`。
- 引用元: [公式ブランド指針](https://x.ai/legal/brand-guidelines) からリンクされる [SpaceXAI_Grok_Assets.zip](https://data.x.ai/logos/SpaceXAI_Grok_Assets.zip)。取得日: 2026-10-20 UTC。ZIP 内の `SpaceXAI_Grok_Assets/Grok_Logomark_Light.svg` を使用しています。
- 原本 SHA-256: `b20648e2f111d7fbc91f58b22d1e76e9885b68a163cb5a1010f7f11bf5840491`。配布 ZIP SHA-256: `db9129acd4efc4c2202d25afe31b70281a79f8507f75520ab5e6b3356895a7e9`。番号つきリリースはなく、取得時のハッシュで固定しています。
- 形状・色: 1024 単位の viewBox、公式の白い図形。SVG は全バイト無改変。PNG はそのままの形状・色で 96×96px に出力し、文字・装飾・他マークを合成しません。
- 利用条件: MIT / Apache / CC0 ではなく、上記の Brand Guidelines に基づく権利者のブランド素材です。指針はサービスを正確に指す利用、図案の無改変、誤認・公認・提携の暗示禁止などを規定し、許諾の撤回や再許諾の制限もあります。配布 ZIP に独立したライセンスファイルはありません。
- AiDiy 自身のマークとして使わず、Grok に関連する起動先の識別に限定します。第三者 CLI が権利者の公式ソフトウェアであると示すものではありません。商標等の権利は権利者に帰属し、AiDiy のソフトウェアライセンスによって再許諾しません。この記録だけで全配布・宣伝用途への許諾を保証するものではありません。

## OpenCode

- 対象: `opencode.svg`、`opencode.png`。無改変原本: `upstream/opencode-logo-dark-square.svg`。
- 引用元: [公式ブランドページ](https://opencode.ai/brand) と同じ素材を、[公式リポジトリの固定 SVG](https://github.com/anomalyco/opencode/blob/6e9c85390bc232866f83ca19dfb46bd9d39b7aa1/packages/console/app/src/asset/brand/opencode-logo-dark-square.svg) から取得。commit `6e9c85390bc232866f83ca19dfb46bd9d39b7aa1`。取得日: 2026-10-20 UTC。
- 原本 SHA-256: `d6a0e3b8a295f413543f41cb73957e670351b5cb088c8d9dbd186b9e9d633cca`。
- 形状・色: 元から正方形の 300×300px 版。暗い背景用の `#F1ECEC` / `#4B4646` を使用し、SVG は全バイト無改変で保存しています。PNG への 96px 出力以外に加工はありません。
- ライセンス: [MIT License](https://github.com/anomalyco/opencode/blob/6e9c85390bc232866f83ca19dfb46bd9d39b7aa1/LICENSE)、`Copyright (c) 2025 opencode`。全文を [LICENSE-OpenCode.txt](./LICENSE-OpenCode.txt) と本メモ末尾に保持します。原文 SHA-256: `625f0f619133f89bbbb2abe37369613dfa1885eba1e50d02170deb62bb42cb6b`。
- 確認したアイコンと親ディレクトリに別ライセンスの表記はありません。MIT は著作権上の利用条件であり、商標権・公式提携の許諾を意味しません。AiDiy は OpenCode チームが制作したものではなく、公式な提携・承認を示すものでもありません。

## 生成スクリプト

`PNG生成.py` の独自実装はリポジトリと同じ [AiDiy 公開利用ライセンス v1.1](../../../../../LICENSE) の対象です。実行方法・保存原本・生成物の関係は [README.md](./README.md) を参照してください。


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
