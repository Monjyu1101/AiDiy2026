import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp, mkdir, copyFile, readFile, rm} from 'node:fs/promises';
import {join} from 'node:path';
import {tmpdir} from 'node:os';
import {pathToFileURL} from 'node:url';

test('証跡画像は内容順の名前を使い、再撮影でも旧画像を上書きしない', async t => {
  const root = await mkdtemp(join(tmpdir(), 'aidiy-evidence-name-'));
  t.after(() => rm(root, {recursive: true, force: true}));
  const script = join(root, 'scripts/checks/実画面試験記録.mjs');
  await mkdir(join(root, 'scripts/checks'), {recursive: true});
  await copyFile(new URL('./実画面試験記録.mjs', import.meta.url), script);
  const {createEvidenceRecorder} = await import(pathToFileURL(script).href);
  const bytes = Buffer.from('89504e470d0a1a0a00000000', 'hex');
  const entry = {paragraph: 1, title: '起動直後画面', status: '観測', note: '命名の合成試験',
    state: {screenshots: [{url: 'data:image/png;base64,' + bytes.toString('base64')}]} };
  const first = await (await createEvidenceRecorder('20261023-first', 'system'))(entry);
  const second = await (await createEvidenceRecorder('20261024-second', 'system'))(entry);
  const third = await (await createEvidenceRecorder('20261024-third', 'system'))(entry);
  assert.equal(first.file, 'aidiy_diag-システム起動_101_起動直後画面.png');
  assert.equal(second.file, 'aidiy_diag-システム起動_101_起動直後画面_確認02.png');
  assert.equal(third.file, 'aidiy_diag-システム起動_101_起動直後画面_確認03.png');
  const folder = join(root, '_AIDIY/knowledge/images/セルフテスト,aidiy_diag,システム起動編');
  for (const row of [first, second, third]) assert.deepEqual(await readFile(join(folder, row.file)), bytes);
  const next = await (await createEvidenceRecorder('20261023-first', 'system'))(entry);
  assert.equal(next.id, '102');
  assert.equal(next.file, 'aidiy_diag-システム起動_102_起動直後画面.png');
});
