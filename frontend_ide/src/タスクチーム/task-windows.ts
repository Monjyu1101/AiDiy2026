// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1". See LICENSE for full terms.
import { qMessage } from './utils/qAlert';
export async function openTaskDialog(payload: Record<string, unknown>) {
  try {
    const result = await window.aidiyWindow?.taskWindows('dialog', payload);
    if (result?.ok === false) throw Error(result.error || '編集ウィンドウを開けません。');
  } catch (error) { await qMessage(error instanceof Error ? error.message : '編集ウィンドウを開けません。', 'error'); }
}
