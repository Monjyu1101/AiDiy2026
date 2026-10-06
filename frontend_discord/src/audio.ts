import { Readable } from 'node:stream';
import OpusScript from 'opusscript';

const FRAME_BYTES = 960 * 2 * 2; // Discord: 48kHz / stereo / PCM16、20ms

export function 入力PCM変換(stereo: Buffer, rate: number): Buffer {
  if (rate !== 16000 && rate !== 24000) throw new Error('入力レートが不正です。');
  const step = 48000 / rate;
  const count = Math.floor(stereo.length / 4 / step);
  const output = Buffer.alloc(count * 2);
  for (let i = 0; i < count; i++) {
    let sum = 0;
    for (let j = 0; j < step; j++) {
      const offset = (i * step + j) * 4;
      sum += stereo.readInt16LE(offset) + stereo.readInt16LE(offset + 2);
    }
    output.writeInt16LE(Math.round(sum / (step * 2)), i * 2);
  }
  return output;
}

export function 出力PCM変換(mono: Buffer): Buffer {
  if (mono.length % 2) throw new Error('PCM16 のバイト数が不正です。');
  const output = Buffer.alloc(mono.length * 4);
  for (let i = 0; i < mono.length / 2; i++) {
    const sample = mono.readInt16LE(i * 2);
    for (let j = 0; j < 4; j++) output.writeInt16LE(sample, i * 8 + j * 2);
  }
  return output;
}

// 複数話者を同じ20ms枠に混ぜる。無音も送信し、LiveAI の VAD が発話終了を検出できるようにする。
export class 音声入力ミキサー {
  private queues = new Map<string, Buffer>();
  追加(user: string, pcm: Buffer) {
    const pending = Buffer.concat([this.queues.get(user) ?? Buffer.alloc(0), pcm]);
    this.queues.set(user, pending.subarray(-FRAME_BYTES * 12)); // 遅延を240ms以内に制限
  }
  削除(user: string) { this.queues.delete(user); }
  フレーム(rate: number): Buffer {
    const mixed = new Int32Array(FRAME_BYTES / 2);
    for (const [user, queue] of this.queues) {
      const size = Math.min(FRAME_BYTES, queue.length - queue.length % 2);
      for (let i = 0; i < size / 2; i++) mixed[i] += queue.readInt16LE(i * 2);
      if (size >= queue.length) this.queues.delete(user);
      else this.queues.set(user, queue.subarray(size));
    }
    const pcm = Buffer.alloc(FRAME_BYTES);
    for (let i = 0; i < mixed.length; i++) pcm.writeInt16LE(Math.max(-32768, Math.min(32767, mixed[i])), i * 2);
    return 入力PCM変換(pcm, rate);
  }
}

// Opus を直接供給するため FFmpeg は不要。20ms の送出間隔は AudioPlayer が管理する。
export class Discord音声出力 extends Readable {
  private pcm: Buffer = Buffer.alloc(0);
  private lastAudioAt = 0;
  private encoder = new OpusScript(48000, 2, OpusScript.Application.AUDIO);
  constructor() { super({ objectMode: true, highWaterMark: 2 }); }
  追加(pcm: Buffer) {
    if (this.destroyed) return;
    if (pcm.length % 2 || this.pcm.length + pcm.length > 24000 * 2 * 15) throw new Error('AI 音声の再生バッファ上限を超えました。');
    if (pcm.length) this.lastAudioAt = Date.now();
    this.pcm = Buffer.concat([this.pcm, pcm]);
  }
  override _read() {
    if (this.destroyed) return;
    try {
      // チャンク境界を発話末尾と扱わない。続きは最大60ms待ち、末尾の端数だけ無音で埋める。
      if (!this.pcm.length || this.pcm.length < 960 && Date.now() - this.lastAudioAt < 60) {
        this.push(Buffer.from([0xf8, 0xff, 0xfe])); return;
      }
      const frame = Buffer.alloc(960); // 24kHz mono、20ms
      this.pcm.copy(frame, 0, 0, 960);
      this.pcm = this.pcm.subarray(Math.min(960, this.pcm.length));
      // ここでも20ms待つとエンコード時間分だけ遅れ、AudioPlayer が無音を挟んでしまう。
      this.push(this.encoder.encode(出力PCM変換(frame), 960));
    } catch { this.destroy(new Error('Discord 音声の変換に失敗しました。')); }
  }
  override _destroy(error: Error | null, callback: (error?: Error | null) => void) {
    this.pcm = Buffer.alloc(0); this.encoder.delete(); callback(error);
  }
}
