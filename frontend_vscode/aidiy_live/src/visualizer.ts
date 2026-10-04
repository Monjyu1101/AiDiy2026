type Channel = 'input' | 'output';
type Cloud = { level: number; energy: number; target: Float32Array; bands: Float32Array; color: string };

/** 実音声のスペクトルを円周へ配置。描画は音声送信・エコー減衰から独立する。 */
export class AudioCloud {
  private context: CanvasRenderingContext2D | null;
  private channels: Record<Channel, Cloud> = {
    input: { level: 0, energy: 0, target: new Float32Array(48), bands: new Float32Array(48), color: '255, 83, 110' },
    output: { level: 0, energy: 0, target: new Float32Array(48), bands: new Float32Array(48), color: '105, 220, 255' },
  };
  private width = 0;
  private height = 0;
  private frame = 0;
  private last = 0;
  private time = 0;
  private disposed = false;
  private reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
  private observer: ResizeObserver;

  constructor(private canvas: HTMLCanvasElement) {
    this.context = canvas.getContext('2d');
    this.observer = new ResizeObserver(() => this.resize());
    this.observer.observe(canvas);
    document.addEventListener('visibilitychange', this.visibility);
    this.resize(); this.visibility();
  }
  level(kind: Channel, value: number) { this.channels[kind].level = value; }
  spectrum(kind: Channel, values: Uint8Array) {
    const cloud = this.channels[kind];
    // 対数配置で、声の低域～高域を小さな円でも見分けられるようにする。
    for (let i = 0; i < cloud.target.length; i++) {
      const bin = Math.floor(Math.pow(Math.max(1, values.length - 1), i / (cloud.target.length - 1)));
      cloud.target[i] = values.length ? (values[bin] || 0) / 255 : 0;
    }
  }
  private resize() {
    const bounds = this.canvas.getBoundingClientRect();
    this.width = bounds.width; this.height = bounds.height;
    const ratio = Math.min(2, window.devicePixelRatio || 1);
    this.canvas.width = Math.round(this.width * ratio); this.canvas.height = Math.round(this.height * ratio);
    this.context?.setTransform(ratio, 0, 0, ratio, 0, 0);
  }
  private visibility = () => {
    if (this.frame) cancelAnimationFrame(this.frame);
    this.frame = 0; this.last = 0;
    if (!document.hidden && !this.disposed && this.context) this.frame = requestAnimationFrame(this.draw);
  };
  private draw = (stamp: number) => {
    if (this.disposed || !this.context) return;
    const delta = this.last ? Math.min(.05, (stamp - this.last) / 1000) : 1 / 60;
    this.last = stamp;
    if (!this.reducedMotion.matches) this.time += delta;
    const ctx = this.context, radius = Math.min(this.width * .29, this.height * .22, 150);
    const x = this.width / 2, y = this.height * .53;
    ctx.clearRect(0, 0, this.width, this.height);
    ctx.globalCompositeOperation = 'lighter';
    for (const [kind, cloud] of Object.entries(this.channels)) {
      const follow = 1 - Math.exp(-delta * 10);
      cloud.energy += (cloud.level - cloud.energy) * follow;
      for (let i = 0; i < cloud.bands.length; i++) cloud.bands[i] += (cloud.target[i] - cloud.bands[i]) * follow;
      const sign = kind === 'output' ? 1 : -1, energy = cloud.energy;
      const glow = ctx.createRadialGradient(x, y, radius * .55, x, y, radius * 1.55);
      glow.addColorStop(0, `rgba(${cloud.color}, 0)`);
      glow.addColorStop(.5, `rgba(${cloud.color}, ${.015 + energy * .055})`);
      glow.addColorStop(1, `rgba(${cloud.color}, 0)`);
      ctx.fillStyle = glow; ctx.fillRect(0, 0, this.width, this.height);
      // 細い複数の輪郭を重ね、音量で広がる半透明の雲にする。
      for (let strand = 0; strand < 9; strand++) {
        ctx.beginPath();
        for (let point = 0; point <= 240; point++) {
          const angle = point / 240 * Math.PI * 2;
          const position = (1 - Math.cos(angle * 2)) / 2 * (cloud.bands.length - 1);
          const band = Math.floor(position), fraction = position - band;
          const frequency = cloud.bands[band] * (1 - fraction) + cloud.bands[Math.min(band + 1, cloud.bands.length - 1)] * fraction;
          const wave = Math.sin(angle * 3 + this.time * sign * .65 + strand * .31)
            + Math.sin(angle * 7 - this.time * .8 + strand * .52) * .5
            + Math.sin(angle * 13 + this.time * .45 + strand * .7) * .25;
          const distance = radius + sign * 6 + (strand - 4) * 1.9 + wave * (3 + energy * 12)
            + frequency * energy * (18 + strand * 2);
          const px = x + Math.cos(angle) * distance, py = y + Math.sin(angle) * distance;
          if (!point) ctx.moveTo(px, py); else ctx.lineTo(px, py);
        }
        ctx.closePath();
        ctx.lineWidth = strand === 4 ? 1.1 : .65;
        ctx.strokeStyle = `rgba(${cloud.color}, ${(.08 + energy * .32) * (strand === 4 ? 1.5 : 1)})`;
        ctx.shadowColor = `rgba(${cloud.color}, .65)`;
        ctx.shadowBlur = strand === 4 ? 9 : 0;
        ctx.stroke();
      }
      ctx.shadowBlur = 0;
    }
    ctx.globalCompositeOperation = 'source-over';
    this.frame = requestAnimationFrame(this.draw);
  };
  dispose() {
    this.disposed = true;
    if (this.frame) cancelAnimationFrame(this.frame);
    this.observer.disconnect(); document.removeEventListener('visibilitychange', this.visibility);
  }
}
