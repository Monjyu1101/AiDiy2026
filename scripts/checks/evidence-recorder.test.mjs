import test from 'node:test';
import assert from 'node:assert/strict';
import fs, {mkdtemp, mkdir, copyFile, readFile, rm, readdir, writeFile, stat, utimes, rmdir} from 'node:fs/promises';
import {fork} from 'node:child_process';
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
  assert.equal(first.file, 'Diag-システム起動_101_起動直後画面.png');
  assert.equal(second.file, 'Diag-システム起動_101_起動直後画面_確認02.png');
  assert.equal(third.file, 'Diag-システム起動_101_起動直後画面_確認03.png');
  const folder = join(root, '_AIDIY/knowledge/images/セルフテスト,aidiy_diag,システム起動編');
  for (const row of [first, second, third]) assert.deepEqual(await readFile(join(folder, row.file)), bytes);
  assert.ok((await readdir(folder)).every(name => name.endsWith('.png')));
  const cache = join(root, '.aidiy_cache/selftest/セルフテスト,aidiy_diag,システム起動編');
  assert.equal((await readdir(cache)).filter(name => name.endsWith('__evidence.json')).length, 3);
  const next = await (await createEvidenceRecorder('20261023-first', 'system'))(entry);
  assert.equal(next.id, '102');
  assert.equal(next.file, 'Diag-システム起動_102_起動直後画面.png');
});

// 合成バイトだけを一時コピーへ保存する。実機画面・正式な証跡には触れない。
async function fixture(t) {
  const root = await mkdtemp(join(tmpdir(), 'aidiy-evidence-race-'));
  t.after(() => rm(root, {recursive: true, force: true}));
  const script = join(root, 'scripts/checks/実画面試験記録.mjs');
  await mkdir(join(root, 'scripts/checks'), {recursive: true});
  await copyFile(new URL('./実画面試験記録.mjs', import.meta.url), script);
  const {createEvidenceRecorder} = await import(pathToFileURL(script).href);
  const folder = join(root, '_AIDIY/knowledge/images/セルフテスト,aidiy_diag,システム起動編');
  const bytes = Buffer.from('89504e470d0a1a0a00000000', 'hex');
  const entry = {paragraph: 1, title: '並行記録画面', status: '観測', note: '合成試験',
    state: {screenshots: [{url: 'data:image/png;base64,' + bytes.toString('base64')}]}};
  const work = join(root, '.aidiy_cache/selftest/セルフテスト,aidiy_diag,システム起動編');
  const manifest = join(work, 'shared__evidence.json');
  return {root, script, folder, work, bytes, entry, manifest,
    recorder: options => createEvidenceRecorder('shared', 'system', options),
    rows: async () => JSON.parse(await readFile(manifest, 'utf8'))};
}

async function assertSaved(f, count) {
  const rows = await f.rows();
  assert.equal(rows.length, count);
  assert.deepEqual(rows.map(row => row.sequence), Array.from({length: count}, (_, i) => i + 1));
  assert.equal(new Set(rows.map(row => row.id)).size, count);
  assert.equal(new Set(rows.map(row => row.file)).size, count);
  for (const row of rows) assert.deepEqual(await readFile(join(f.folder, row.file)), f.bytes);
  return rows;
}

test('保存前に作成した2つの recorder が同じ実施IDへ順番に追記する', async t => {
  const f = await fixture(t);
  const first = await f.recorder();
  const second = await f.recorder();
  await first({...f.entry, note: 'first'});
  await second({...f.entry, note: 'second'});
  assert.deepEqual((await assertSaved(f, 2)).map(row => row.note), ['first', 'second']);
});

test('同じ recorder の同時呼び出しでID重複や共有一時ファイル競合が起きない', async t => {
  const f = await fixture(t);
  const record = await f.recorder();
  await Promise.all(Array.from({length: 8}, (_, i) => record({...f.entry, note: String(i)})));
  await assertSaved(f, 8);
  assert.deepEqual((await readdir(f.work)).filter(name => /\.(new|lock)$/.test(name)), []);
});

test('既存の古いロックを奪わず、待機失敗時もJSON・画像・一時ファイルを維持する', async t => {
  const f = await fixture(t);
  const record = await f.recorder({lockTimeoutMs: 0});
  await record(f.entry);
  const before = await readFile(f.manifest);
  await mkdir(f.manifest + '.lock');
  await utimes(f.manifest + '.lock', new Date(0), new Date(0));
  await writeFile(f.manifest + '.new', '既存の一時ファイル');
  await assert.rejects(record(f.entry), /ロック待機がタイムアウト/);
  assert.deepEqual(await readFile(f.manifest), before);
  assert.equal(await readFile(f.manifest + '.new', 'utf8'), '既存の一時ファイル');
  assert.ok((await stat(f.manifest + '.lock')).isDirectory());
  await assertSaved(f, 1);
  // 全 writer 停止確認後の手動回復を模擬する。
  await rmdir(f.manifest + '.lock');
  await record(f.entry);
  await assertSaved(f, 2);
});

test('factory後に壊れたJSONを検出し、画像を追加せずロックを解放する', async t => {
  const f = await fixture(t);
  const record = await f.recorder();
  await record(f.entry);
  await writeFile(f.manifest, '{broken');
  const before = await readdir(f.folder);
  await assert.rejects(record(f.entry), SyntaxError);
  assert.equal(await readFile(f.manifest, 'utf8'), '{broken');
  assert.deepEqual(await readdir(f.folder), before);
});

test('manifest置換失敗後も既存JSON・画像を保持し、次の保存が成功する', async t => {
  const f = await fixture(t);
  const record = await f.recorder();
  const first = await record(f.entry);
  const before = await readFile(f.manifest);
  const rename = fs.rename;
  t.mock.method(fs, 'rename', async (source, destination) => {
    if (destination === f.manifest) throw Object.assign(new Error('合成rename失敗'), {code: 'EIO'});
    return rename(source, destination);
  });
  await assert.rejects(record({...f.entry, note: 'failed'}), /合成rename失敗/);
  t.mock.restoreAll();
  assert.deepEqual(await readFile(f.manifest), before);
  assert.deepEqual(await readFile(join(f.folder, first.file)), f.bytes);
  const failedImage = 'Diag-システム起動_102_並行記録画面.png';
  assert.deepEqual(await readFile(join(f.folder, failedImage)), f.bytes);
  assert.deepEqual((await readdir(f.work)).filter(name => /\.(new|lock)$/.test(name)), []);
  const retry = await record({...f.entry, note: 'retry'});
  assert.equal(retry.id, '102');
  assert.match(retry.file, /_確認02\.png$/);
  assert.deepEqual((await assertSaved(f, 2)).map(row => row.note), ['合成試験', 'retry']);
  assert.deepEqual(await readFile(join(f.folder, failedImage)), f.bytes);
});

async function childRecorder(t, f, hold = false) {
  const childScript = join(f.root, 'child.mjs');
  await writeFile(childScript, `
    import fs from 'node:fs/promises';
    const {createEvidenceRecorder} = await import(process.argv[2]);
    const entry = JSON.parse(process.argv[3]);
    const record = await createEvidenceRecorder('shared', 'system');
    const mkdir = fs.mkdir;
    fs.mkdir = async (...args) => {
      try { return await mkdir(...args); }
      catch (error) { if (error.code === 'EEXIST') process.send('blocked'); throw error; }
    };
    if (process.argv[4] === 'hold') {
      const rename = fs.rename;
      fs.rename = async (...args) => {
        const released = new Promise(resolve => process.once('message', resolve));
        process.send('committing');
        await released;
        return rename(...args);
      };
    }
    process.once('message', async () => {
      try { await record(entry); process.send('saved'); process.disconnect(); }
      catch (error) { console.error(error); process.exit(1); }
    });
    process.send('ready');
  `);
  const child = fork(childScript, [pathToFileURL(f.script).href, JSON.stringify(f.entry), hold ? 'hold' : ''],
    {execArgv: [], stdio: ['ignore', 'ignore', 'pipe', 'ipc']});
  let stderr = '';
  child.stderr.on('data', bytes => { stderr += bytes; });
  const messages = new Set();
  const waiters = new Map();
  child.on('message', message => { messages.add(message); waiters.get(message)?.(); });
  const exited = new Promise(resolve => child.once('exit', (code, signal) => resolve({code, signal})));
  t.after(async () => { if (child.exitCode === null && child.signalCode === null) child.kill(); await exited; });
  const wait = message => messages.has(message) ? Promise.resolve() : new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('子プロセス待機: ' + message + ' ' + stderr)), 5000);
    waiters.set(message, () => { clearTimeout(timer); resolve(); });
  });
  await wait('ready');
  return {child, wait, exited};
}

test('別プロセスでもcommit中のロックを待ち、最新JSONへ追記する', async t => {
  const f = await fixture(t);
  const first = await childRecorder(t, f, true);
  const second = await childRecorder(t, f);
  first.child.send('start');
  await first.wait('committing');
  second.child.send('start');
  await second.wait('blocked');
  first.child.send('release');
  await Promise.all([first.wait('saved'), second.wait('saved')]);
  assert.equal((await first.exited).code, 0);
  assert.equal((await second.exited).code, 0);
  await assertSaved(f, 2);
});

test('writer異常終了後のロック・一時ファイル・画像は自動削除せず安全に再開する', async t => {
  const f = await fixture(t);
  const record = await f.recorder({lockTimeoutMs: 0});
  await record(f.entry);
  const before = await readFile(f.manifest);
  const writer = await childRecorder(t, f, true);
  writer.child.send('start');
  await writer.wait('committing');
  writer.child.kill('SIGKILL');
  await writer.exited;
  const names = await readdir(f.work);
  const temporary = names.find(name => name.endsWith('.new'));
  assert.ok(temporary);
  const tempBefore = await readFile(join(f.work, temporary));
  await assert.rejects(record(f.entry), /ロック待機がタイムアウト/);
  assert.deepEqual(await readFile(f.manifest), before);
  assert.deepEqual(await readdir(f.work), names);
  await rmdir(f.manifest + '.lock');
  await record(f.entry);
  await assertSaved(f, 2);
  assert.deepEqual(await readFile(join(f.work, temporary)), tempBefore);
});
