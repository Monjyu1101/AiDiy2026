// X自己紹介.js - AiDiy自己紹介ページの動的機能

class AiDiySelfIntroduction {
    constructor() {
        this.particleCanvas = null;
        this.particleCtx = null;
        this.particles = [];
        this.animationId = null;
        this.typewriterTexts = [
            "System.initialize() → Ready",
            "Gemini Live API → Connected",
            "Claude Code SDK → Integrated",
            "WebSocket Channel → Active",
            "Development Cycle → Optimized",
            "Real-time Processing → Enabled",
            "Japanese-First Design → Complete",
            "Zero-Downtime Reload → Standby",
            "Multi-modal AI → Operational",
            "Welcome to the Future of Development"
        ];
        this.currentTextIndex = 0;
        this.typewriterSpeed = 50;
        this.countersAnimated = false;
        this.scrollElement = null;

        // 自動スクロール設定
        this.userInteracted = false;
        this.autoScrollDelayMs = 10000;
        this.autoScrollIntervalMs = 20;
        this.autoScrollStep = 1;
        this.autoScrollActive = false;
        this.autoScrollTimer = null;
        this.autoScrollStartTimer = null;
        this.autoScrollCancelEvents = ['wheel', 'touchstart', 'keydown', 'mousedown'];
        this.autoScrollCancelHandler = null;

        this.init();
    }

    init() {
        this.setupParticleCanvas();
        this.startParticleAnimation();
        this.setupTypewriter();
        this.setupScrollAnimations();
        this.setupCounterAnimations();
        this.setupInteractiveEffects();
        this.setupAutoScroll();
    }

    getScrollElement() {
        if (!this.scrollElement) {
            const scrollingElement = document.scrollingElement || document.documentElement || document.body;
            if (scrollingElement && scrollingElement.scrollHeight > scrollingElement.clientHeight) {
                this.scrollElement = scrollingElement;
            } else if (document.documentElement && document.documentElement.scrollHeight > document.documentElement.clientHeight) {
                this.scrollElement = document.documentElement;
            } else {
                this.scrollElement = document.body || scrollingElement;
            }
        }
        return this.scrollElement;
    }

    getScrollTop() {
        return window.pageYOffset
            || (document.documentElement ? document.documentElement.scrollTop : 0)
            || (document.body ? document.body.scrollTop : 0)
            || 0;
    }

    setScrollTop(value) {
        if (document.documentElement) {
            document.documentElement.scrollTop = value;
        }
        if (document.body) {
            document.body.scrollTop = value;
        }
        const scrollingElement = document.scrollingElement;
        if (scrollingElement && scrollingElement !== document.documentElement && scrollingElement !== document.body) {
            scrollingElement.scrollTop = value;
        }
        window.scrollTo(0, value);
    }


    setupParticleCanvas() {
        this.particleCanvas = document.getElementById('particles-bg');
        this.particleCtx = this.particleCanvas.getContext('2d');

        this.resizeCanvas();
        window.addEventListener('resize', () => this.resizeCanvas());

        // パーティクル初期化
        this.initParticles();
    }

    resizeCanvas() {
        this.particleCanvas.width = window.innerWidth;
        this.particleCanvas.height = window.innerHeight;
    }

    initParticles() {
        this.particles = [];
        const particleCount = Math.floor((window.innerWidth * window.innerHeight) / 12000);

        for (let i = 0; i < particleCount; i++) {
            this.particles.push({
                x: Math.random() * this.particleCanvas.width,
                y: Math.random() * this.particleCanvas.height,
                vx: (Math.random() - 0.5) * 0.5,
                vy: (Math.random() - 0.5) * 0.5,
                size: Math.random() * 2 + 1,
                opacity: Math.random() * 0.5 + 0.2,
                color: this.getRandomParticleColor(),
                pulseSpeed: Math.random() * 0.02 + 0.01,
                pulsePhase: Math.random() * Math.PI * 2
            });
        }
    }

    getRandomParticleColor() {
        const colors = [
            'rgba(0, 255, 255, ',
            'rgba(255, 0, 255, ',
            'rgba(255, 255, 0, ',
            'rgba(0, 255, 0, ',
            'rgba(255, 128, 0, '
        ];
        return colors[Math.floor(Math.random() * colors.length)];
    }

    startParticleAnimation() {
        const animate = () => {
            this.particleCtx.clearRect(0, 0, this.particleCanvas.width, this.particleCanvas.height);

            this.particles.forEach(particle => {
                // パーティクル移動
                particle.x += particle.vx;
                particle.y += particle.vy;

                // 画面端での反転
                if (particle.x < 0 || particle.x > this.particleCanvas.width) {
                    particle.vx *= -1;
                }
                if (particle.y < 0 || particle.y > this.particleCanvas.height) {
                    particle.vy *= -1;
                }

                // パルス効果
                particle.pulsePhase += particle.pulseSpeed;
                const pulseOpacity = particle.opacity + Math.sin(particle.pulsePhase) * 0.2;

                // パーティクル描画
                this.particleCtx.beginPath();
                this.particleCtx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
                this.particleCtx.fillStyle = particle.color + pulseOpacity + ')';
                this.particleCtx.fill();

                // グロー効果
                this.particleCtx.shadowBlur = 10;
                this.particleCtx.shadowColor = particle.color + '0.8)';
                this.particleCtx.fill();
                this.particleCtx.shadowBlur = 0;
            });

            // 接続線描画
            this.drawConnections();

            this.animationId = requestAnimationFrame(animate);
        };

        animate();
    }

    drawConnections() {
        for (let i = 0; i < this.particles.length; i++) {
            for (let j = i + 1; j < this.particles.length; j++) {
                const dx = this.particles[i].x - this.particles[j].x;
                const dy = this.particles[i].y - this.particles[j].y;
                const distance = Math.sqrt(dx * dx + dy * dy);

                if (distance < 120) {
                    const opacity = (120 - distance) / 120 * 0.1;
                    this.particleCtx.beginPath();
                    this.particleCtx.moveTo(this.particles[i].x, this.particles[i].y);
                    this.particleCtx.lineTo(this.particles[j].x, this.particles[j].y);
                    this.particleCtx.strokeStyle = `rgba(0, 255, 255, ${opacity})`;
                    this.particleCtx.lineWidth = 1;
                    this.particleCtx.stroke();
                }
            }
        }
    }

    setupTypewriter() {
        const typingElement = document.getElementById('typing-text');
        if (!typingElement) return;

        this.typeNextText();
    }

    typeNextText() {
        const typingElement = document.getElementById('typing-text');
        const currentText = this.typewriterTexts[this.currentTextIndex];
        let charIndex = 0;

        typingElement.textContent = '';

        const typeChar = () => {
            if (charIndex < currentText.length) {
                typingElement.textContent += currentText.charAt(charIndex);
                charIndex++;
                setTimeout(typeChar, this.typewriterSpeed);
            } else {
                setTimeout(() => {
                    this.currentTextIndex = (this.currentTextIndex + 1) % this.typewriterTexts.length;
                    setTimeout(() => this.typeNextText(), 1000);
                }, 3000);
            }
        };

        typeChar();
    }

    setupScrollAnimations() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animated');

                    // カウンターアニメーション
                    if (entry.target.classList.contains('stat-item') && !this.countersAnimated) {
                        this.animateCounters();
                        this.countersAnimated = true;
                    }
                }
            });
        }, observerOptions);

        document.querySelectorAll('.animate-on-scroll').forEach(element => {
            observer.observe(element);
        });
    }

    setupCounterAnimations() {
        // 初期化時は何もしない - スクロール時に実行
    }

    animateCounters() {
        document.querySelectorAll('.stat-number').forEach(counter => {
            const target = parseInt(counter.dataset.count);
            const duration = 2000;
            const startTime = performance.now();

            const updateCounter = (currentTime) => {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);

                // イージング関数（ease-out）
                const easeOut = 1 - Math.pow(1 - progress, 3);
                const currentValue = Math.floor(target * easeOut);

                counter.textContent = currentValue;

                if (progress < 1) {
                    requestAnimationFrame(updateCounter);
                } else {
                    counter.textContent = target;
                }
            };

            requestAnimationFrame(updateCounter);
        });
    }

    setupInteractiveEffects() {
        // フィーチャーカードホバー効果
        document.querySelectorAll('.feature-card').forEach(card => {
            card.addEventListener('mouseenter', () => {
                this.createHoverParticles(card);
            });
        });

        // 哲学アイテムホバー効果
        document.querySelectorAll('.philosophy-item').forEach(item => {
            item.addEventListener('mouseenter', () => {
                this.createRippleEffect(item);
            });
        });

        // 拡張性アイテムホバー効果
        document.querySelectorAll('.expansion-item').forEach(item => {
            item.addEventListener('mouseenter', () => {
                this.createPulseEffect(item);
            });
        });

        // サイバーボタン効果
        document.querySelectorAll('.cyber-button').forEach(button => {
            button.addEventListener('click', (e) => {
                this.createClickEffect(e.target, e.clientX, e.clientY);
            });
        });
    }

    createHoverParticles(element) {
        const rect = element.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;

        for (let i = 0; i < 8; i++) {
            const particle = document.createElement('div');
            particle.className = 'hover-particle';
            particle.style.cssText = `
                position: fixed;
                width: 4px;
                height: 4px;
                background: #00ffff;
                border-radius: 50%;
                pointer-events: none;
                z-index: 1000;
                left: ${centerX}px;
                top: ${centerY}px;
                animation: hover-particle-${i} 1.5s ease-out forwards;
            `;

            document.body.appendChild(particle);

            setTimeout(() => {
                particle.remove();
            }, 1500);
        }

        // 動的キーフレーム作成
        this.createHoverParticleAnimations();
    }

    createHoverParticleAnimations() {
        if (document.getElementById('hover-particle-styles')) return;

        const style = document.createElement('style');
        style.id = 'hover-particle-styles';

        let keyframes = '';
        for (let i = 0; i < 8; i++) {
            const angle = (i / 8) * Math.PI * 2;
            const distance = 100;
            const x = Math.cos(angle) * distance;
            const y = Math.sin(angle) * distance;

            keyframes += `
                @keyframes hover-particle-${i} {
                    0% { opacity: 1; transform: translate(0, 0) scale(1); }
                    100% { opacity: 0; transform: translate(${x}px, ${y}px) scale(0); }
                }
            `;
        }

        style.textContent = keyframes;
        document.head.appendChild(style);
    }

    createRippleEffect(element) {
        const rect = element.getBoundingClientRect();
        const ripple = document.createElement('div');
        ripple.style.cssText = `
            position: absolute;
            width: 0;
            height: 0;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(255, 0, 255, 0.3), transparent);
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            animation: ripple-expand 0.8s ease-out;
            pointer-events: none;
        `;

        element.style.position = 'relative';
        element.appendChild(ripple);

        setTimeout(() => {
            ripple.remove();
        }, 800);
    }

    createPulseEffect(element) {
        element.style.animation = 'pulse-glow 0.6s ease-in-out';

        setTimeout(() => {
            element.style.animation = '';
        }, 600);
    }

    createClickEffect(element, clickX, clickY) {
        for (let i = 0; i < 12; i++) {
            const spark = document.createElement('div');
            spark.style.cssText = `
                position: fixed;
                width: 3px;
                height: 3px;
                background: #00ffff;
                border-radius: 50%;
                pointer-events: none;
                z-index: 10000;
                left: ${clickX}px;
                top: ${clickY}px;
                animation: click-spark-${i} 0.8s ease-out forwards;
            `;

            document.body.appendChild(spark);

            setTimeout(() => {
                spark.remove();
            }, 800);
        }

        this.createClickSparkAnimations(clickX, clickY);
    }

    createClickSparkAnimations(centerX, centerY) {
        if (document.getElementById('click-spark-styles')) {
            document.getElementById('click-spark-styles').remove();
        }

        const style = document.createElement('style');
        style.id = 'click-spark-styles';

        let keyframes = '';
        for (let i = 0; i < 12; i++) {
            const angle = (i / 12) * Math.PI * 2;
            const distance = 50 + Math.random() * 50;
            const x = Math.cos(angle) * distance;
            const y = Math.sin(angle) * distance;

            keyframes += `
                @keyframes click-spark-${i} {
                    0% { opacity: 1; transform: translate(0, 0) scale(1); }
                    100% { opacity: 0; transform: translate(${x}px, ${y}px) scale(0); }
                }
            `;
        }

        style.textContent = keyframes;
        document.head.appendChild(style);
    }

    // 自動スクロール機能のセットアップ
    setupAutoScroll() {
        // 初期遅延を3秒に変更
        this.autoScrollDelayMs = 3000;

        this.autoScrollCancelHandler = () => {
            this.stopAutoScroll();

            if (this.autoScrollStartTimer) {
                clearTimeout(this.autoScrollStartTimer);
            }

            this.autoScrollStartTimer = setTimeout(() => {
                this.startAutoScroll();
            }, this.autoScrollDelayMs);
        };

        this.autoScrollCancelEvents.forEach((eventName) => {
            window.addEventListener(eventName, this.autoScrollCancelHandler, { passive: true });
        });

        // 初期タイマー開始
        this.autoScrollCancelHandler();
    }

    startAutoScroll() {
        if (this.autoScrollActive) return;

        this.autoScrollActive = true;
        this.showAutoScrollNotification('自動スクロール開始しました', 1500);

        this.autoScrollTimer = setInterval(() => {
            const previousScrollY = this.getScrollTop();
            this.setScrollTop(previousScrollY + this.autoScrollStep);
            const currentScrollY = this.getScrollTop();

            if (currentScrollY === previousScrollY) {
                this.stopAutoScroll();
            }
        }, this.autoScrollIntervalMs);
    }

    stopAutoScroll() {
        if (this.autoScrollTimer) {
            clearInterval(this.autoScrollTimer);
            this.autoScrollTimer = null;
        }
        this.autoScrollActive = false;
    }

    // 自動スクロール通知の表示
    showAutoScrollNotification(message, duration = 2000) {
        // 既存の通知があれば削除
        const existing = document.querySelector('.auto-scroll-notification');
        if (existing) {
            existing.remove();
        }

        const notification = document.createElement('div');
        notification.className = 'auto-scroll-notification';
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(0, 0, 0, 0.8);
            color: #00ffff;
            padding: 10px 20px;
            border-radius: 25px;
            border: 1px solid #00ffff;
            font-family: 'Orbitron', monospace;
            font-size: 0.9rem;
            font-weight: bold;
            z-index: 10000;
            animation: notification-fade-in 0.3s ease-out;
            backdrop-filter: blur(10px);
            box-shadow: 0 0 20px rgba(0, 255, 255, 0.3);
        `;

        document.body.appendChild(notification);

        // フェードアウトアニメーション
        setTimeout(() => {
            notification.style.animation = 'notification-fade-out 0.3s ease-in forwards';
        }, duration - 300);

        // 削除
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, duration);
    }

    // クリーンアップ
    destroy() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }

        this.stopAutoScroll();
        if (this.autoScrollStartTimer) {
            clearTimeout(this.autoScrollStartTimer);
            this.autoScrollStartTimer = null;
        }
        if (this.autoScrollCancelHandler) {
            this.autoScrollCancelEvents.forEach((eventName) => {
                window.removeEventListener(eventName, this.autoScrollCancelHandler, { passive: true });
            });
        }
        window.removeEventListener('resize', this.resizeCanvas);
    }
}

// 追加のCSSアニメーション
document.addEventListener('DOMContentLoaded', () => {
    // 動的CSSアニメーション追加
    const additionalStyles = `
        <style>
        @keyframes ripple-expand {
            0% { width: 0; height: 0; opacity: 0.8; }
            100% { width: 200px; height: 200px; opacity: 0; }
        }
        
        @keyframes pulse-glow {
            0%, 100% { box-shadow: 0 0 20px rgba(255, 255, 0, 0.3); }
            50% { box-shadow: 0 0 40px rgba(255, 255, 0, 0.8); }
        }
        
        .cyber-particle {
            position: fixed;
            width: 4px;
            height: 4px;
            border-radius: 50%;
            pointer-events: none;
            z-index: 1000;
            animation: cyber-float 3s ease-in-out infinite;
        }
        
        @keyframes cyber-float {
            0% { 
                opacity: 1; 
                transform: translateY(0) rotate(0deg); 
            }
            50% { 
                opacity: 0.7; 
                transform: translateY(-100px) rotate(180deg); 
            }
            100% { 
                opacity: 0; 
                transform: translateY(-200px) rotate(360deg); 
            }
        }
        
        .pass-message {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: linear-gradient(45deg, #ff00ff, #00ffff);
            color: #000;
            padding: 20px 40px;
            border-radius: 10px;
            font-family: 'Orbitron', monospace;
            font-size: 1.5rem;
            font-weight: bold;
            z-index: 10000;
            animation: pass-message-show 1.5s ease-in-out;
            text-shadow: 0 0 10px rgba(255, 255, 255, 0.8);
            box-shadow: 0 0 30px rgba(255, 0, 255, 0.5);
        }
        
        @keyframes pass-message-show {
            0% { opacity: 0; transform: translate(-50%, -50%) scale(0.5); }
            50% { opacity: 1; transform: translate(-50%, -50%) scale(1.2); }
            100% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
        }
        
        /* スムーズスクロール */
        html {
            scroll-behavior: smooth;
        }
        
        /* セクション間の視覚効果 */
        .section::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, #00ffff, transparent);
            opacity: 0.3;
        }
        
        /* ホバー時のテキストシャドウ効果 */
        .feature-title:hover,
        .philosophy-title:hover {
            text-shadow: 0 0 20px currentColor;
            transition: text-shadow 0.3s ease;
        }
        
        /* 自動スクロール通知アニメーション */
        @keyframes notification-fade-in {
            0% {
                opacity: 0;
                transform: translateX(100px) scale(0.8);
            }
            100% {
                opacity: 1;
                transform: translateX(0) scale(1);
            }
        }
        
        @keyframes notification-fade-out {
            0% {
                opacity: 1;
                transform: translateX(0) scale(1);
            }
            100% {
                opacity: 0;
                transform: translateX(100px) scale(0.8);
            }
        }

        /* モバイル最適化 */
        @media (max-width: 768px) {
            .cyber-particle {
                width: 2px;
                height: 2px;
            }
            
            .pass-message {
                font-size: 1rem;
                padding: 15px 30px;
            }
            
            .auto-scroll-notification {
                top: 10px !important;
                right: 10px !important;
                font-size: 0.8rem !important;
                padding: 8px 16px !important;
            }
        }
        </style>
    `;

    document.head.insertAdjacentHTML('beforeend', additionalStyles);

    // メインクラス初期化
    const aiDiyIntro = new AiDiySelfIntroduction();

    // 動的背景エフェクト（追加）
    setInterval(() => {
        if (Math.random() < 0.1) {
            createRandomGlow();
        }
    }, 2000);

    function createRandomGlow() {
        const glow = document.createElement('div');
        glow.className = 'random-glow';
        glow.style.position = 'fixed';
        glow.style.width = Math.random() * 200 + 100 + 'px';
        glow.style.height = Math.random() * 200 + 100 + 'px';
        glow.style.background = `radial-gradient(circle, rgba(${Math.floor(Math.random() * 255)}, ${Math.floor(Math.random() * 255)}, 255, 0.1), transparent)`;
        glow.style.borderRadius = '50%';
        glow.style.left = Math.random() * window.innerWidth + 'px';
        glow.style.top = Math.random() * window.innerHeight + 'px';
        glow.style.pointerEvents = 'none';
        glow.style.zIndex = '-1';
        glow.style.animation = 'glow-fade 4s ease-out forwards';

        document.body.appendChild(glow);

        setTimeout(() => {
            glow.remove();
        }, 4000);
    }

    // 追加のキーフレーム
    document.head.insertAdjacentHTML('beforeend', `
        <style>
        @keyframes glow-fade {
            0% { opacity: 0; transform: scale(0.5); }
            50% { opacity: 1; transform: scale(1); }
            100% { opacity: 0; transform: scale(1.5); }
        }
        </style>
    `);

    // パフォーマンス監視（デバッグ用）
    let frameCount = 0;
    let lastTime = performance.now();

    function monitorPerformance() {
        frameCount++;
        const currentTime = performance.now();

        if (currentTime - lastTime >= 1000) {
            const fps = frameCount;
            frameCount = 0;
            lastTime = currentTime;

            // パフォーマンスが低い場合はエフェクトを削減
            if (fps < 30) {
                document.documentElement.style.setProperty('--animation-speed', '0.5');
            }
        }

        requestAnimationFrame(monitorPerformance);
    }

    // パフォーマンス監視開始（デバッグ時のみ）
    // monitorPerformance();

    // ページ離脱時のクリーンアップ
    window.addEventListener('beforeunload', () => {
        if (aiDiyIntro) {
            aiDiyIntro.destroy();
        }
    });
});
