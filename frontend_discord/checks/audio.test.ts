import { test } from 'node:test';
import assert from 'node:assert/strict';
import OpusScript from 'opusscript';
import { Discord音声出力, 音声入力ミキサー, 入力PCM変換, 出力PCM変換, 出力バッファ上限 } from '../src/audio';

test('48kHz stereo → 16/24kHz mono、24kHz mono → 48kHz stereo のレートと音量を検証', () => {
  const stereo = Buffer.alloc(3840);
  for (let i = 0; i < stereo.length; i += 4) { stereo.writeInt16LE(1000, i); stereo.writeInt16LE(3000, i + 2); }
  for (const rate of [16000, 24000]) {
    const pcm = 入力PCM変換(stereo, rate);
    assert.equal(pcm.length, rate * .02 * 2);
    for (let i = 0; i < pcm.length; i += 2) assert.equal(pcm.readInt16LE(i), 2000);
  }
  const output = 出力PCM変換(入力PCM変換(stereo, 24000));
  assert.equal(output.length, 3840);
  assert.equal(output.readInt16LE(3000), 2000);
});

test('同時話者を混合してクリップし、無音フレームと有界バッファを維持する', () => {
  const mixer = new 音声入力ミキサー();
  const pcm = Buffer.alloc(3840);
  for (let i = 0; i < pcm.length; i += 2) pcm.writeInt16LE(30000, i);
  mixer.追加('one', pcm); mixer.追加('two', pcm);
  assert.equal(mixer.フレーム(16000).readInt16LE(0), 32767);
  assert.ok(mixer.フレーム(16000).equals(Buffer.alloc(640)));
  mixer.追加('one', Buffer.concat(Array(30).fill(pcm)));
  for (let i = 0; i < 12; i++) mixer.フレーム(24000);
  assert.ok(mixer.フレーム(24000).equals(Buffer.alloc(960)));
});

test('20ms未満のチャンクは続きが届くまで保持し、発話末尾だけ待機後に無音で埋める', context => {
  let now = 1000;
  context.mock.method(Date, 'now', () => now);
  const stream = new Discord音声出力();
  const encoder = new OpusScript(48000, 2, OpusScript.Application.AUDIO);
  const packets: Buffer[] = [];
  stream.push = (packet: Buffer) => { packets.push(packet); return true; };
  try {
    const pcm = Buffer.alloc(960 * 2);
    for (let i = 0; i < pcm.length / 2; i++) pcm.writeInt16LE(Math.round(8000 * Math.sin(i * Math.PI * 2 * 440 / 24000)), i * 2);
    stream.追加(pcm.subarray(0, 480));
    stream._read();
    assert.deepEqual(packets.shift(), Buffer.from([0xf8, 0xff, 0xfe]), '不足分を無音で埋めて音声を消費しない');
    stream.追加(pcm.subarray(480, 1440));
    stream._read();
    assert.deepEqual(packets.shift(), encoder.encode(出力PCM変換(pcm.subarray(0, 960)), 960));
    stream._read();
    assert.deepEqual(packets.shift(), Buffer.from([0xf8, 0xff, 0xfe]));
    stream.追加(pcm.subarray(1440));
    stream._read();
    assert.deepEqual(packets.shift(), encoder.encode(出力PCM変換(pcm.subarray(960)), 960));
    stream.追加(pcm.subarray(0, 480));
    stream._read();
    assert.deepEqual(packets.shift(), Buffer.from([0xf8, 0xff, 0xfe]));
    now += 60;
    stream._read();
    const tail = Buffer.alloc(960);
    pcm.copy(tail, 0, 0, 480);
    assert.deepEqual(packets.shift(), encoder.encode(出力PCM変換(tail), 960));
    stream._read();
    assert.deepEqual(packets.shift(), Buffer.from([0xf8, 0xff, 0xfe]));
  } finally { stream.destroy(); encoder.delete(); }
});

test('再生側の要求ごとに20msのOpusを即座に供給し、余計な無音や送出待ちを挟まない', () => {
  const stream = new Discord音声出力();
  const decoder = new OpusScript(48000, 2, OpusScript.Application.AUDIO);
  try {
    const pcm = Buffer.alloc(960 * 50);
    for (let i = 0; i < pcm.length / 2; i++) pcm.writeInt16LE(Math.round(8000 * Math.sin(i * Math.PI * 2 * 440 / 24000)), i * 2);
    stream.追加(pcm);
    for (let i = 0; i < 50; i++) {
      const opus = stream.read();
      assert.ok(opus, '再生側が要求した時点で、待機せずフレームを渡す');
      assert.notDeepEqual(opus, Buffer.from([0xf8, 0xff, 0xfe]));
      assert.equal(decoder.decode(opus).length, 3840);
    }
    assert.deepEqual(stream.read(), Buffer.from([0xf8, 0xff, 0xfe]));
    stream.追加(Buffer.alloc(24000 * 2 * 30)); // 30秒分の先行受信は長い応答として許容する
    assert.throws(() => stream.追加(Buffer.alloc(出力バッファ上限)), /上限/);
    assert.throws(() => stream.追加(Buffer.alloc(1)), /上限/);
  } finally { stream.destroy(); decoder.delete(); }
  assert.equal(stream.destroyed, true);
});
