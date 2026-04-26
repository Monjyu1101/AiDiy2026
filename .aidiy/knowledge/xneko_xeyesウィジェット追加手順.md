# xeyes・xneko ウィジェット追加手順

## このメモを使う場面
- `AIコア.vue` の `表示選択` に新しいウィジェット（時計・ゲーム・マスコット等）を追加したい
- xeyes・xneko のようなインタラクティブウィジェットを新規作成したい

## 関連ファイル
- `frontend_avatar/src/components/AIコア.vue` — `表示選択` の管理
- `frontend_avatar/src/components/AIコア_xneko.vue` — スプライトアニメーションの参考実装
- `frontend_avatar/src/components/AIコア_xeyes.vue` — CPU 連動演出・オプションパネルの参考実装
- `frontend_avatar/public/oneko.gif` / `xneko_chatora.gif` / `xneko_mike.gif` — スプライトシート

## 表示選択への追加手順（AIコア.vue）

```typescript
// 1. 型に追加
type 表示選択型 = 'アバター' | 'カレンダーα' | 'xneko(猫)' | 'xeyes(目)' |
                 'アナログ時計' | 'デジタル時計' | 'カレンダー' | '無し' | '新ウィジェット名'

// 2. import 追加
import NewWidget from './AIコア_新ウィジェット.vue'

// 3. select の option 追加
<option value="新ウィジェット名">新ウィジェット名</option>

// 4. 表示 computed または v-if 追加
<component :is="NewWidget" v-if="表示選択 === '新ウィジェット名'"
           :controls-visible="controlsVisible" />
```

## ウィジェットコンポーネントの基本構造

```vue
<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'

const props = withDefaults(defineProps<{ controlsVisible?: boolean }>(), { controlsVisible: true })
// controlsVisible=false のときはオプションパネルや補助 UI を隠す
</script>

<template>
  <div class="widget-stage">
    <!-- メイン表示領域 -->
    <div class="widget-main">...</div>

    <!-- オプションパネル（controlsVisible=true のときのみ表示） -->
    <div v-if="props.controlsVisible" class="widget-options">
      <!-- ラジオ・チェックボックスなどのオプション -->
    </div>
  </div>
</template>

<style scoped>
.widget-stage {
  position: absolute;
  inset: 0;
  z-index: 2;
  overflow: hidden;
  background: transparent;
}
/* オプションパネルは右下固定 */
.widget-options {
  position: absolute;
  right: 8px;
  bottom: 8px;
  z-index: 4;
  padding: 5px 8px;
  border: 1px solid rgba(255, 255, 255, 0.28);
  background: rgba(4, 8, 14, 0.50);
  backdrop-filter: blur(6px);
  color: #ffffff;
  font-size: 10px;
  pointer-events: all;
  user-select: none;
}
</style>
```

## xneko スプライトシートの追加

新しい猫デザインを追加する場合は PNG（白背景）から Python + Pillow で変換する。

```python
# 白背景フラッドフィル除去 → 256×128 にリサイズ → GIF 変換
# 詳細は アバター表示とVRMA.md の「xneko デザイン切替」を参照
```

スプライトシートの仕様: `256×128 px`、8列×4行の 32px グリッド、パレット GIF、透過インデックス=255

## Electron / Web デュアルモード対応

OS カーソル位置が必要な場合（xeyes のような）:
- **Electron**: `window.desktopApi?.getWindowPointerSnapshot(role)` IPC で OS カーソル位置を取得
- **Web**: `stageRef.value?.addEventListener('pointermove', ...)` で画面内座標を追う

CPU 使用率が必要な場合:
- **Electron**: `window.desktopApi?.getSystemCpuUsage()` IPC
- **Web**: ブラウザには対応 API がないため `0` を返す（または非表示にする）

どちらも `window.desktopApi?.xxx` の optional chaining で分岐を自動処理できる。

## 再発しやすい注意点

- `v-if` と `v-for` を**同一要素に書かない** — `<template v-if>` でラップする（Vue 3 の警告対象）
- アニメーションフレームは `onBeforeUnmount` で必ず `cancelAnimationFrame` する
- `setInterval` は `onBeforeUnmount` で `clearInterval` する
- オプションパネルの `pointer-events: all` を忘れるとクリックが透過して操作できない
- `controlsVisible=false` のときにオプションパネルが消えることを確認する（ボタン非表示モード時）
