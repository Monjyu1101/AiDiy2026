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

/** Node の fetch は通信エラーを cause に包むため、実際の接続先と原因も表示する。 */
export function 接続エラー詳細(target: URL, error: unknown): string {
  const details: string[] = [];
  let current = error;
  for (let depth = 0; current && depth < 4; depth++) {
    if (!(current instanceof Error)) { details.push(String(current)); break; }
    const code = (current as NodeJS.ErrnoException).code;
    details.push(`${code ? `${code}: ` : ''}${current.message}`);
    current = current.cause;
  }
  return `AIコアとの通信に失敗しました。接続先: ${target.origin}\n${details.join('\n')}`;
}
