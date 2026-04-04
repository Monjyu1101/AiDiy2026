class XSelfIntro {
  constructor() {
    this.canvas = document.getElementById('bg');
    this.ctx = this.canvas ? this.canvas.getContext('2d') : null;
    this.progress = document.getElementById('progress');
    this.cursor = document.getElementById('cursor');
    this.signal = document.getElementById('signal');
    this.feed = document.getElementById('feed');
    this.reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    this.particles = [];
    this.rafId = 0;
    this.signalTimer = 0;
    this.feedTimer = 0;
    this.signalIndex = 0;
    this.feedIndex = 0;
    this.signals = [
      '日本語テーブル名、API、JSON、画面が一直線につながる。',
      'FastAPI 2 サーバーで Core 系と Apps 系を切り分ける。',
      'frontend_avatar は Electron と Web の両方で動く。',
      'AI コアは音声、画像、コード支援を WebSocket で束ねる。',
      'VRM アバターは口パクとモーションで会話体験を拡張する。'
    ];
    this.feeds = [
      'C系: 権限、利用者、採番で共通基盤を構築',
      'M系: 商品、車両、工程など業務マスタを整理',
      'T系: 配車、生産、入出庫、棚卸をトランザクション管理',
      'V系: DB VIEW を使わず、生 SQL で JOIN 表示を実装',
      'S系: 週表示 / 日表示のスケジューラーを提供',
      'A系: AI コアと会話履歴で対話基盤を形成',
      'X系: ゲームや紹介ページで実験実装を展開',
      '音声処理: 入力 16kHz、出力 24kHz のリアルタイム連携',
      'アバター: Three.js + VRM + VRMA で 3D 表示',
      'Web UI: qTubler と共通ダイアログで管理画面を統一'
    ];
    this.init();
  }

  init() {
    this.setupCanvas();
    this.setupReveal();
    this.setupCounters();
    this.setupSignal();
    this.setupFeed();
    this.setupTilt();
    this.setupPointer();
    this.updateProgress();
    window.addEventListener('resize', () => this.resizeCanvas(), { passive: true });
    window.addEventListener('scroll', () => this.updateProgress(), { passive: true });
  }

  setupCanvas() {
    if (!this.canvas || !this.ctx) return;
    this.resizeCanvas();
    const count = Math.max(34, Math.min(110, Math.floor(window.innerWidth * window.innerHeight / 18000)));
    this.particles = Array.from({ length: count }, () => ({
      x: Math.random() * this.canvas.width,
      y: Math.random() * this.canvas.height,
      vx: (Math.random() - 0.5) * 0.22,
      vy: (Math.random() - 0.5) * 0.22,
      r: Math.random() * 2 + 1,
      o: Math.random() * 0.4 + 0.1,
      c: ['100,230,255', '255,185,90', '145,255,203', '255,122,89'][Math.floor(Math.random() * 4)]
    }));
    this.draw();
  }

  resizeCanvas() {
    if (!this.canvas) return;
    this.canvas.width = window.innerWidth;
    this.canvas.height = window.innerHeight;
  }

  draw() {
    if (!this.ctx || !this.canvas) return;
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    this.particles.forEach((p) => {
      if (!this.reduce) {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < -20) p.x = this.canvas.width + 20;
        if (p.x > this.canvas.width + 20) p.x = -20;
        if (p.y < -20) p.y = this.canvas.height + 20;
        if (p.y > this.canvas.height + 20) p.y = -20;
      }
      this.ctx.beginPath();
      this.ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      this.ctx.fillStyle = `rgba(${p.c},${p.o})`;
      this.ctx.shadowBlur = 16;
      this.ctx.shadowColor = `rgba(${p.c},.18)`;
      this.ctx.fill();
      this.ctx.shadowBlur = 0;
    });
    for (let i = 0; i < this.particles.length; i += 1) {
      for (let j = i + 1; j < this.particles.length; j += 1) {
        const a = this.particles[i];
        const b = this.particles[j];
        const d = Math.hypot(a.x - b.x, a.y - b.y);
        if (d > 130) continue;
        this.ctx.beginPath();
        this.ctx.moveTo(a.x, a.y);
        this.ctx.lineTo(b.x, b.y);
        this.ctx.strokeStyle = `rgba(100,230,255,${(1 - d / 130) * 0.08})`;
        this.ctx.stroke();
      }
    }
    if (!this.reduce) this.rafId = requestAnimationFrame(() => this.draw());
  }

  setupReveal() {
    const items = document.querySelectorAll('.reveal');
    if (this.reduce || !('IntersectionObserver' in window)) {
      items.forEach((el) => el.classList.add('on'));
      return;
    }
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('on');
        io.unobserve(entry.target);
      });
    }, { threshold: 0.14, rootMargin: '0px 0px -8% 0px' });
    items.forEach((el) => io.observe(el));
  }

  setupCounters() {
    const run = (el) => {
      if (el.dataset.done) return;
      el.dataset.done = '1';
      const target = Number(el.dataset.count || '0');
      if (this.reduce) {
        el.textContent = String(target);
        return;
      }
      const start = performance.now();
      const step = (t) => {
        const p = Math.min(1, (t - start) / 1400);
        const v = Math.round(target * (1 - (1 - p) ** 3));
        el.textContent = String(v);
        if (p < 1) requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    };
    const nodes = document.querySelectorAll('[data-count]');
    if (this.reduce || !('IntersectionObserver' in window)) {
      nodes.forEach(run);
      return;
    }
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        run(entry.target);
        io.unobserve(entry.target);
      });
    }, { threshold: 0.4 });
    nodes.forEach((el) => io.observe(el));
  }

  setupSignal() {
    if (!this.signal) return;
    if (this.reduce) {
      this.signal.textContent = this.signals[0];
      return;
    }
    const type = () => {
      const text = this.signals[this.signalIndex];
      let i = 0;
      this.signal.textContent = '';
      const tick = () => {
        this.signal.textContent = text.slice(0, i);
        i += 1;
        if (i <= text.length) {
          this.signalTimer = window.setTimeout(tick, 32);
        } else {
          this.signalIndex = (this.signalIndex + 1) % this.signals.length;
          this.signalTimer = window.setTimeout(type, 1800);
        }
      };
      tick();
    };
    type();
  }

  setupFeed() {
    if (!this.feed) return;
    const push = () => {
      const li = document.createElement('li');
      const t = document.createElement('span');
      const c = document.createElement('span');
      t.className = 'time';
      c.className = 'copy';
      t.textContent = `00:${String((this.feedIndex * 7 + 12) % 60).padStart(2, '0')}`;
      c.textContent = this.feeds[this.feedIndex % this.feeds.length];
      li.append(t, c);
      this.feed.prepend(li);
      while (this.feed.children.length > 6) this.feed.removeChild(this.feed.lastElementChild);
      this.feedIndex += 1;
    };
    for (let i = 0; i < 4; i += 1) push();
    if (!this.reduce) this.feedTimer = window.setInterval(push, 2200);
  }

  setupTilt() {
    if (this.reduce || !window.matchMedia('(hover: hover)').matches) return;
    document.querySelectorAll('[data-tilt]').forEach((el) => {
      el.addEventListener('pointermove', (e) => {
        const r = el.getBoundingClientRect();
        const px = (e.clientX - r.left) / r.width;
        const py = (e.clientY - r.top) / r.height;
        el.style.transform = `perspective(1200px) rotateX(${(0.5 - py) * 10}deg) rotateY(${(px - 0.5) * 10}deg) translateY(-2px)`;
      });
      el.addEventListener('pointerleave', () => { el.style.transform = ''; });
    });
  }

  setupPointer() {
    if (!this.cursor || !window.matchMedia('(hover: hover)').matches) return;
    window.addEventListener('pointermove', (e) => {
      this.cursor.style.opacity = '1';
      this.cursor.style.transform = `translate3d(${e.clientX}px,${e.clientY}px,0)`;
    }, { passive: true });
    window.addEventListener('pointerleave', () => { this.cursor.style.opacity = '0'; }, { passive: true });
  }

  updateProgress() {
    if (!this.progress) return;
    const total = document.documentElement.scrollHeight - window.innerHeight;
    this.progress.style.width = `${total > 0 ? (window.scrollY / total) * 100 : 0}%`;
  }
}

window.addEventListener('DOMContentLoaded', () => new XSelfIntro());
