/*!
 * -*- coding: utf-8 -*-
 *
 * -------------------------------------------------------------------------
 * COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
 * Licensed under "AiDiy 公開利用ライセンス v1.1".
 * Commercial use requires prior written consent from all copyright holders.
 * See LICENSE for full terms. Thank you for keeping the rules.
 * https://github.com/monjyu1101/AiDiy2026
 * -------------------------------------------------------------------------
 */

// 内容追加時と、入力欄・ストリーム枠による表示領域の伸縮後に末尾へ揃える。
export function 最下部追従(表示領域: HTMLElement[]): () => void {
  let 再表示予約済み = false;
  const 末尾へ移動 = () => {
    for (const 領域 of 表示領域) {
      if (!領域.hidden) 領域.scrollTop = 領域.scrollHeight;
    }
  };
  const 最下部表示 = () => {
    末尾へ移動();
    if (再表示予約済み) return;
    再表示予約済み = true;
    requestAnimationFrame(() => {
      再表示予約済み = false;
      末尾へ移動();
    });
  };
  const サイズ監視 = new ResizeObserver(最下部表示);
  for (const 領域 of 表示領域) サイズ監視.observe(領域);
  return 最下部表示;
}
