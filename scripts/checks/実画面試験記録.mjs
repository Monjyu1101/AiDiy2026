// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
/** Computer Use が返した実画面を保存する。UI操作・認証・シェル実行は行わない。 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { createHash, randomUUID } from 'node:crypto';
import { setTimeout as delay } from 'node:timers/promises';
import { fileURLToPath } from 'node:url';

const BOOK_NAMES = Object.freeze({
  system: 'Diag-システム起動',
  apps: 'Diag-アプリ起動',
  environment: 'Diag-環境確認',
  ide: 'IDE',
});
const BOOK_DOCUMENTS = Object.freeze({
  system: 'セルフテスト,aidiy_diag,システム起動編',
  apps: 'セルフテスト,aidiy_diag,アプリ起動編',
  environment: 'セルフテスト,aidiy_diag,環境確認編',
  ide: 'セルフテスト,aidiy_ide,操作編',
});

async function readRecords(manifest) {
  let records;
  try { records = JSON.parse(await fs.readFile(manifest, 'utf8')); }
  catch (error) { if (error.code !== 'ENOENT') throw error; records = []; }
  if (!Array.isArray(records)) throw new Error('evidence.json は配列にしてください');
  return records;
}

// mkdir は同一プロセスの別 recorder と別プロセスの双方を排他する。
// 時刻や PID だけで古いロックを奪うと、停止中の writer の再開時に記録を失う。
// 異常終了で残った場合も自動削除しない。全 writer の停止を確認してから
// エラーに表示された空の .lock ディレクトリのみを手動で削除して再実行する。
async function withManifestLock(manifest, timeoutMs, action) {
  const lock = manifest + '.lock';
  const start = performance.now();
  for (;;) {
    try { await fs.mkdir(lock); break; }
    catch (error) {
      if (error.code !== 'EEXIST') throw error;
      if (performance.now() - start >= timeoutMs) {
        throw new Error(`証跡の保存ロック待機がタイムアウトしました: ${lock}。全 writer の停止を確認してから残存ロックを確認してください`);
      }
      await delay(Math.min(25, timeoutMs - (performance.now() - start)));
    }
  }
  try { return await action(); }
  finally { await fs.rmdir(lock); }
}

async function replaceManifest(manifest, records) {
  // 他の呼び出し・前回の異常終了が残した一時ファイルには触れない。
  const temporary = manifest + '.' + randomUUID() + '.new';
  const handle = await fs.open(temporary, 'wx');
  try {
    try { await handle.writeFile(JSON.stringify(records, null, 2) + '\n', 'utf8'); }
    finally { await handle.close(); }
    await fs.rename(temporary, manifest);
  } finally {
    await fs.rm(temporary, { force: true });
  }
}

// 参照元Markdownの名前で保存先を決め、画像名は内容を先頭にする。
// 実施IDは記録JSONで保持し、同じ場面の再撮影は確認番号で区別する。
// 例: createEvidenceRecorder('20261019-1039-computer-use', 'environment', { toPng })
export async function createEvidenceRecorder(runId, book = 'environment', { toPng, lockTimeoutMs = 10000 } = {}) {
  const prefix = BOOK_NAMES[book];
  if (!prefix) throw new Error('冊子は system / apps / environment / ide を指定してください');
  if (typeof runId !== 'string' || !/^[\p{L}\p{N}][\p{L}\p{N}_-]{0,100}$/u.test(runId)) throw new Error('実施IDは日付・時刻などの名前を指定してください（パスは不可）');
  if (!Number.isFinite(lockTimeoutMs) || lockTimeoutMs < 0) throw new Error('ロック待機時間は0以上の有限数にしてください');
  const images = fileURLToPath(new URL('../../_AIDIY/knowledge/images/', import.meta.url));
  const root = path.join(images, BOOK_DOCUMENTS[book]);
  await fs.mkdir(root, { recursive: true });
  const manifest = path.join(root, `${runId}__evidence.json`);
  await readRecords(manifest);
  return async function record({ paragraph, title, state, status, note, screenshot = 0 }) {
    if (!Number.isInteger(paragraph) || paragraph < 0 || paragraph > 9) throw new Error('段落番号は0〜9');
    if (!['✅ OK', '❌ NG', '⏸ 未実施', '観測'].includes(status)) throw new Error('判定を明示してください');
    if (!title || [...title].some(c => '<>:"/\\|?*'.includes(c) || c.charCodeAt(0) < 32)) throw new Error('画面名に使用できない文字があります');
    if (!note?.trim()) throw new Error('確認した事実または未実施理由が必要です');
    const shot = state?.screenshots?.[screenshot];
    if (!/^data:image\/(png|jpeg);base64,/.test(shot?.url ?? '')) throw new Error('実画面の画像がありません');
    const raw = Buffer.from(shot.url.slice(shot.url.indexOf(',') + 1), 'base64');
    const bytes = shot.url.startsWith('data:image/png;') ? raw : await toPng?.(raw);
    if (!bytes || bytes.subarray(0, 8).toString('hex') !== '89504e470d0a1a0a') throw new Error('JPEG画面には toPng エンコーダーを渡してください');
    return withManifestLock(manifest, lockTimeoutMs, async () => {
      const records = await readRecords(manifest);
      const sequence = 1 + Math.max(0, ...records.filter(r => r.paragraph === paragraph).map(r => r.sequence));
      if (sequence > 99) throw new Error('段落内の証跡は99件まで');
      const id = String(paragraph) + String(sequence).padStart(2, '0');
      const stem = prefix + '_' + id + '_' + title.replace(/画面$/u, '') + '画面';
      let file = stem + '.png';
      for (let confirmation = 2; ; confirmation++) {
        try {
          await fs.writeFile(path.join(root, file), bytes, { flag: 'wx' });
          break;
        } catch (error) {
          if (error.code !== 'EEXIST') throw error;
          file = stem + '_確認' + String(confirmation).padStart(2, '0') + '.png';
        }
      }
      const row = { book, id, paragraph, sequence, file, title, status, note, time: new Date().toISOString(), window: state.window, width: shot.width, height: shot.height, sha256: createHash('sha256').update(bytes).digest('hex'), accessibility: state.accessibility };
      records.push(row);
      await replaceManifest(manifest, records);
      return row;
    });
  };
}
