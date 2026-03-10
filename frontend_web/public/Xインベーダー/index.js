// Xインベーダー改 - Retro 640x400 Canvas版（挙動は現行を踏襲）

class RetroInvadersGame {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.ctx.imageSmoothingEnabled = false;

        // 基本解像度（レトロ）
        this.gameWidth = 640;
        this.gameHeight = 400;

        // 状態
        this.gameStarted = false;
        this.gameRunning = false;
        this.gamePaused = false;

        // プレイヤー
        this.playerWidth = 24;   // 旧実装(60/960)比で縮尺
        this.playerHeight = 16;
        this.playerSpeed = 3;    // 旧5相当を400高へ縮尺
        this.playerX = (this.gameWidth - this.playerWidth) / 2;
        this.playerY = this.gameHeight - 32; // 下からオフセット

        // スコア等
        this.score = 0;
        this.lives = 3;
        this.wave = 1;

        // 弾丸
        this.bullets = [];
        this.enemyBullets = [];
        this.bulletSpeed = 3;        // 旧8→約3
        this.enemyBulletSpeed = 1.2; // 旧3→約1
        this.canShoot = true;
        this.shootCooldown = 150;

        // 敵
        this.invaders = [];
        this.invaderSpeed = 0.6; // 旧1→約0.6
        this.invaderDirection = 1;
        this.invaderDropDistance = 8; // 旧20→8
        this.invaderAnimFrame = 0; // 足の開閉アニメ（2フレーム）
        this.invaderAnimTick = 0;
        this.invaderAnimInterval = 400; // ms

        // パワーアップ / UFO / パーティクル
        this.powerups = [];
        this.ufos = [];
        this.particles = [];
        this.ufoSpeed = 1.2;
        this.ufoSpawnTimer = 0;
        this.ufoSpawnInterval = 15000;

        // バンカー（基地）
        this.bunkers = [];

        // 入力
        this.keys = {};

        // 星背景（軽量）
        this.stars = Array.from({ length: 40 }).map(() => ({
            x: Math.random() * this.gameWidth,
            y: Math.random() * this.gameHeight,
            d: Math.random() * 0.5 + 0.2,
        }));

        this.bindEvents();
        this.updateDisplay();
        this.loop = this.loop.bind(this);
    }

    bindEvents() {
        document.addEventListener('keydown', (e) => {
            this.keys[e.code] = true;
            if (e.code === 'Space' && this.gameRunning) {
                e.preventDefault();
                this.shoot();
            }
            if (e.code === 'KeyP' && this.gameStarted) this.togglePause();
        });
        document.addEventListener('keyup', (e) => { this.keys[e.code] = false; });

        $('#start-btn').on('click', () => this.startGame());
        $('#restart-btn').on('click', () => this.restartGame());
        $('#menu-btn').on('click', () => this.showMenu());
    }

    startGame() {
        $('#start-overlay').addClass('hidden');
        this.gameStarted = true;
        this.gameRunning = true;
        this.resetGame();
        this.createInvaders();
        requestAnimationFrame(this.loop);
    }

    restartGame() {
        $('#over-overlay').addClass('hidden');
        this.gameRunning = true;
        this.resetGame();
        this.createInvaders();
        requestAnimationFrame(this.loop);
    }

    showMenu() {
        $('#over-overlay').addClass('hidden');
        $('#start-overlay').removeClass('hidden');
        this.gameStarted = false;
        this.gameRunning = false;
    }

    resetGame() {
        this.score = 0;
        this.lives = 3;
        this.wave = 1;
        this.bullets = [];
        this.enemyBullets = [];
        this.invaders = [];
        this.powerups = [];
        this.ufos = [];
        this.particles = [];
        this.playerX = (this.gameWidth - this.playerWidth) / 2;
        this.invaderSpeed = 0.6;
        this.ufoSpawnTimer = 0;
        this.createBunkers();
        this.updateDisplay();
    }

    createInvaders() {
        const rows = 7; // もう少し多く
        const cols = 13; // 左右詰めて列数増
        const startX = 8; // 左右マージンを詰める
        const startY = 40;
        const spacingX = 24; // 現在の半分の間隔（横）
        const spacingY = 16; // 現在の半分の間隔（縦）
        this.invaders = [];
        for (let r = 0; r < rows; r++) {
            for (let c = 0; c < cols; c++) {
                const inv = {
                    x: startX + c * spacingX,
                    y: startY + r * spacingY,
                    w: 16, h: 12, // 8x6ドット（px=2）に整合
                    type: r < 2 ? 1 : (r < 4 ? 2 : 3),
                };
                this.invaders.push(inv);
            }
        }
    }

    loop() {
        if (!this.gameRunning) return;
        this.update();
        this.render();
        requestAnimationFrame(this.loop);
    }

    update() {
        if (this.gamePaused) return;

        // 背景星
        for (const s of this.stars) {
            s.y += s.d; if (s.y > this.gameHeight) s.y = 0;
        }

        // 入力
        if (this.keys['ArrowLeft'] || this.keys['KeyA']) this.playerX -= this.playerSpeed;
        if (this.keys['ArrowRight'] || this.keys['KeyD']) this.playerX += this.playerSpeed;
        this.playerX = Math.max(0, Math.min(this.gameWidth - this.playerWidth, this.playerX));

        // 自弾
        this.bullets = this.bullets.filter(b => {
            b.y -= this.bulletSpeed; return b.y > -20;
        });

        // 敵弾
        this.enemyBullets = this.enemyBullets.filter(b => {
            b.y += this.enemyBulletSpeed; return b.y < this.gameHeight + 20;
        });

        // 敵移動
        if (this.invaders.length) {
            let hitEdge = false;
            for (const inv of this.invaders) {
                inv.x += this.invaderSpeed * this.invaderDirection;
                if (inv.x <= 0 || inv.x + inv.w >= this.gameWidth) hitEdge = true;
            }
            if (hitEdge) {
                this.invaderDirection *= -1;
                for (const inv of this.invaders) inv.y += this.invaderDropDistance;
            }
            // ランダム射撃
            if (Math.random() < 0.002 * this.invaders.length) this.enemyShoot();
        }

        // エイリアンの足アニメ（開閉）
        this.invaderAnimTick += 16.67;
        if (this.invaderAnimTick >= this.invaderAnimInterval) {
            this.invaderAnimTick = 0;
            this.invaderAnimFrame = (this.invaderAnimFrame + 1) % 2;
        }

        // パワーアップ落下
        this.powerups = this.powerups.filter(p => { p.y += 1.0; return p.y < this.gameHeight + 10; });

        // UFO
        this.ufoSpawnTimer += 16.67;
        if (this.ufoSpawnTimer >= this.ufoSpawnInterval && this.ufos.length === 0) {
            this.createUfo(); this.ufoSpawnTimer = 0;
        }
        this.ufos = this.ufos.filter(u => {
            u.x += u.dir * this.ufoSpeed; return (u.x > -60 && u.x < this.gameWidth + 60);
        });

        // パーティクル
        this.particles = this.particles.filter(p => { p.ttl -= 16; p.x += p.vx; p.y += p.vy; return p.ttl > 0; });

        // 衝突
        this.handleCollisions();
        this.checkGameState();
    }

    shoot() {
        if (!this.canShoot) return;
        this.bullets.push({ x: this.playerX + Math.floor(this.playerWidth/2) - 1, y: this.playerY - 6, w: 2, h: 6 });
        this.canShoot = false; setTimeout(() => this.canShoot = true, this.shootCooldown);
        this.muzzle(this.playerX + Math.floor(this.playerWidth/2), this.playerY - 6);
    }

    enemyShoot() {
        const s = this.invaders[Math.floor(Math.random() * this.invaders.length)];
        this.enemyBullets.push({ x: s.x + Math.floor(s.w/2) - 1, y: s.y + s.h, w: 2, h: 6 });
    }

    createUfo() {
        const fromLeft = Math.random() < 0.5;
        // ドット絵サイズ（12列*2px=24, 6行*2px=12）
        this.ufos.push({ x: fromLeft ? -40 : this.gameWidth + 40, y: 24, w: 24, h: 12, dir: fromLeft ? 1 : -1 });
    }

    createPowerup(x, y) {
        this.powerups.push({ x, y, w: 8, h: 8, type: 'rapid' });
    }

    collectPowerup(p) {
        this.addScore(50); this.shootCooldown = 50; setTimeout(() => this.shootCooldown = 150, 5000);
        this.explode(p.x, p.y, true);
    }

    muzzle(x, y) { this.particles.push({ x, y, vx: 0, vy: -0.3, ttl: 120, c: '#7fffd4', s: 2 }); }

    explode(x, y, big = false) {
        const n = big ? 18 : 10;
        for (let i = 0; i < n; i++) {
            const a = Math.random() * Math.PI * 2; const sp = Math.random() * (big ? 2.0 : 1.4);
            this.particles.push({ x, y, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp, ttl: 500, c: big ? '#ff0' : '#ffa500', s: 2 });
        }
    }

    aabb(a, b) {
        return a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;
    }

    handleCollisions() {
        // 自弾 vs バンカー
        for (let i = this.bullets.length - 1; i >= 0; i--) {
            const b = this.bullets[i];
            let hit = false;
            const cx = b.x + b.w/2, cy = b.y + b.h/2;
            for (const bunker of this.bunkers) {
                const bw = bunker.cols * bunker.px, bh = bunker.rows * bunker.px;
                if (cx >= bunker.x && cx < bunker.x + bw && cy >= bunker.y && cy < bunker.y + bh) {
                    // セル占有チェック（ドットが残っている所だけ当たり）
                    const ccol = Math.floor((cx - bunker.x) / bunker.px);
                    const crow = Math.floor((cy - bunker.y) / bunker.px);
                    if (crow >= 0 && crow < bunker.rows && ccol >= 0 && ccol < bunker.cols && bunker.cells[crow][ccol]) {
                        this.erodeBunkerAt(bunker, cx, cy);
                        this.bullets.splice(i, 1);
                        hit = true;
                        break;
                    }
                }
            }
            if (hit) continue;
        }

        // 自弾 vs 敵
        for (let i = this.bullets.length - 1; i >= 0; i--) {
            const b = this.bullets[i];
            for (let j = this.invaders.length - 1; j >= 0; j--) {
                const inv = this.invaders[j];
                if (this.aabb(b, inv)) {
                    this.explode(inv.x + inv.w/2, inv.y + inv.h/2);
                    const pts = inv.type * 10; this.addScore(pts);
                    if (Math.random() < 0.10) this.createPowerup(inv.x + inv.w/2, inv.y + inv.h/2);
                    this.bullets.splice(i, 1); this.invaders.splice(j, 1); break;
                }
            }
        }

        // 自弾 vs UFO
        for (let i = this.bullets.length - 1; i >= 0; i--) {
            const b = this.bullets[i];
            for (let j = this.ufos.length - 1; j >= 0; j--) {
                const u = this.ufos[j];
                if (this.aabb(b, u)) {
                    const bonus = [50,100,150,200,300][Math.floor(Math.random()*5)];
                    this.addScore(bonus); this.explode(u.x + u.w/2, u.y + u.h/2, true);
                    this.bullets.splice(i, 1); this.ufos.splice(j, 1); break;
                }
            }
        }

        // 敵弾 vs バンカー
        for (let i = this.enemyBullets.length - 1; i >= 0; i--) {
            const b = this.enemyBullets[i];
            let hit = false;
            const cx = b.x + b.w/2, cy = b.y + b.h/2;
            for (const bunker of this.bunkers) {
                const bw = bunker.cols * bunker.px, bh = bunker.rows * bunker.px;
                if (cx >= bunker.x && cx < bunker.x + bw && cy >= bunker.y && cy < bunker.y + bh) {
                    // セル占有チェック（ドットが残っている所だけ当たり）
                    const ccol = Math.floor((cx - bunker.x) / bunker.px);
                    const crow = Math.floor((cy - bunker.y) / bunker.px);
                    if (crow >= 0 && crow < bunker.rows && ccol >= 0 && ccol < bunker.cols && bunker.cells[crow][ccol]) {
                        this.erodeBunkerAt(bunker, cx, cy);
                        this.enemyBullets.splice(i, 1);
                        hit = true;
                        break;
                    }
                }
            }
            if (hit) continue;
        }

        // 敵弾 vs プレイヤー
        const playerBox = { x: this.playerX, y: this.playerY, w: this.playerWidth, h: this.playerHeight };
        for (let i = this.enemyBullets.length - 1; i >= 0; i--) {
            if (this.aabb(this.enemyBullets[i], playerBox)) {
                this.explode(this.playerX + this.playerWidth/2, this.playerY + this.playerHeight/2);
                this.enemyBullets.splice(i, 1); this.loseLife();
            }
        }

        // プレイヤー vs パワーアップ
        for (let i = this.powerups.length - 1; i >= 0; i--) {
            if (this.aabb(this.powerups[i], playerBox)) { this.collectPowerup(this.powerups[i]); this.powerups.splice(i, 1); }
        }

        // 敵が下まで到達
        for (const inv of this.invaders) if (inv.y + inv.h > this.gameHeight - 56) { this.gameOver(); break; }
    }

    checkGameState() {
        if (this.invaders.length === 0) this.nextWave();
    }

    nextWave() {
        this.wave++; this.invaderSpeed += 0.3; this.updateDisplay();
        // 少し間を空けて再配置
        setTimeout(() => this.createInvaders(), 600);
    }

    addScore(p) { this.score += p; this.updateDisplay(); }
    loseLife() { this.lives--; this.updateDisplay(); if (this.lives <= 0) this.gameOver(); }

    gameOver() {
        this.gameRunning = false; $('#final-score').text(this.score); $('#over-overlay').removeClass('hidden');
    }

    togglePause() {
        this.gamePaused = !this.gamePaused;
    }

    updateDisplay() {
        $('#score').text(this.score); $('#lives').text(this.lives); $('#wave').text(this.wave);
    }

    // 描画
    clear() { this.ctx.fillStyle = '#000'; this.ctx.fillRect(0, 0, this.gameWidth, this.gameHeight); }

    drawStars() {
        const c = this.ctx;
        c.fillStyle = '#88a';
        for (const s of this.stars) c.fillRect(s.x|0, s.y|0, 1, 1);
    }

    drawPlayer() {
        const c = this.ctx; const x = this.playerX|0, y = this.playerY|0, w = this.playerWidth, h = this.playerHeight;
        c.fillStyle = '#00ff66';
        // 簡単なドット絵（台形風）
        c.fillRect(x+2, y+4, w-4, h-4);
        c.fillRect(x+4, y+2, w-8, 2);
        c.fillRect(x+Math.floor(w/2)-2, y, 4, 2);
    }

    drawInvader(inv) {
        const c = this.ctx; c.fillStyle = inv.type === 1 ? '#ff66aa' : (inv.type === 2 ? '#ffaa33' : '#9966ff');
        const x = inv.x|0, y = inv.y|0;
        const px = 2; // ドットサイズ
        // 8x6の2フレーム（足開閉）
        const open = [
            0b00111100,
            0b01111110,
            0b11111111,
            0b11011011,
            0b00111100,
            0b01000010,
        ];
        const closed = [
            0b00111100,
            0b01111110,
            0b11111111,
            0b11011011,
            0b01111110,
            0b00100100,
        ];
        const pat = this.invaderAnimFrame === 0 ? open : closed;
        for (let r = 0; r < pat.length; r++) {
            for (let col = 0; col < 8; col++) if (pat[r] & (1 << (7-col))) c.fillRect(x + col*px, y + r*px, px, px);
        }
    }

    drawBullet(b, enemy=false) {
        const c = this.ctx; c.fillStyle = enemy ? '#ff4488' : '#7fffd4';
        c.fillRect(b.x|0, b.y|0, b.w|0, b.h|0);
    }

    drawUfo(u) {
        const c = this.ctx; const x = u.x|0, y = u.y|0; const px = 2;
        // 12x6 対称パターン（左右完全対称）
        const pat = [
            0b000001100000, //   dome tip
            0b000111111000, //  dome
            0b001111111100, // body
            0b011111111110, // widest body
            0b001111111100, // body
            0b000001100000, // small feet/glow
        ];
        for (let r = 0; r < pat.length; r++) {
            for (let col = 0; col < 12; col++) if (pat[r] & (1 << (11-col))) {
                // 色分け（上部はドーム色、中央は本体、最下段はアクセント）
                if (r <= 1) c.fillStyle = '#cc88ff';
                else if (r <= 4) c.fillStyle = '#ff66ff';
                else c.fillStyle = '#ff22aa';
                c.fillRect(x + col*px, y + r*px, px, px);
            }
        }
    }
    drawPowerup(p) { const c = this.ctx; c.fillStyle = '#ffee00'; c.fillRect((p.x-4)|0, (p.y-4)|0, 8, 8); }
    drawParticles() {
        const c = this.ctx; for (const p of this.particles) { c.fillStyle = p.c || '#fff'; c.fillRect(p.x|0, p.y|0, p.s||1, p.s||1); }
    }

    // バンカー作成・描画・破壊
    createBunkers() {
        const px = 2;
        const cols = 18; // 36px 幅（18列×2px）
        const rows = 8;  // 少し分厚く（16px 高）
        // 上面左右のみ斜め切れ込み、下面は角ばった矩形（やや厚め）
        const pat = [
            0b000001111111000000, // bevel 1
            0b000111111111110000, // bevel 2
            0b001111111111111000, // bevel 3
            0b111111111111111111, // flat bottom section
            0b111111111111111111,
            0b111111111111111111,
            0b111111111111111111,
            0b111111111111111111,
        ];
        const y = this.gameHeight - 96;
        const spacing = this.gameWidth / 5;
        this.bunkers = [];
        for (let i = 1; i <= 4; i++) {
            const x = Math.floor(spacing * i - (cols*px)/2);
            const cells = Array.from({ length: rows }, (_, r) => (
                Array.from({ length: cols }, (_, c) => (pat[r] & (1 << (cols-1-c))) !== 0)
            ));
            this.bunkers.push({ x, y, cols, rows, px, cells });
        }
    }

    drawBunkers() {
        const c = this.ctx; c.fillStyle = '#ffffff';
        for (const b of this.bunkers) {
            for (let r = 0; r < b.rows; r++) {
                for (let col = 0; col < b.cols; col++) {
                    if (b.cells[r][col]) c.fillRect(b.x + col*b.px, b.y + r*b.px, b.px, b.px);
                }
            }
        }
    }

    erodeBunkerAt(bunker, x, y) {
        // 弾の中心座標からセルを削る
        const ccol = Math.floor((x - bunker.x) / bunker.px);
        const crow = Math.floor((y - bunker.y) / bunker.px);
        const rad = 3; // 薄型に合わせ削り半径を少し拡大
        for (let r = -rad; r <= rad; r++) {
            for (let col = -rad; col <= rad; col++) {
                const rr = crow + r, cc = ccol + col;
                if (rr >= 0 && rr < bunker.rows && cc >= 0 && cc < bunker.cols) bunker.cells[rr][cc] = false;
            }
        }
    }

    render() {
        this.clear();
        this.drawStars();
        // エンティティ
        this.drawBunkers();
        for (const inv of this.invaders) this.drawInvader(inv);
        for (const b of this.bullets) this.drawBullet(b, false);
        for (const b of this.enemyBullets) this.drawBullet(b, true);
        for (const u of this.ufos) this.drawUfo(u);
        for (const p of this.powerups) this.drawPowerup(p);
        this.drawParticles();
        this.drawPlayer();
    }
}

$(function() {
    const game = new RetroInvadersGame(document.getElementById('game-canvas'));
    // グローバルに露出しないが、必要なら window.game = game; でデバッグ可
});
