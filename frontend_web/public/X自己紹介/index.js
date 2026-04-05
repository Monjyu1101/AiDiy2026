// index.js - AiDiy 自己紹介ページの動的機能

class AiDiyIntroduction {
    constructor() {
        this.typewriterTexts = [
            "FastAPI Dual Server → Ready",
            "Vue 3 + Vite + TypeScript → Active",
            "4 Parallel Code Agents → Running",
            "Gemini Live API → Connected",
            "Claude SDK → Integrated",
            "WebSocket Channel → Active",
            "Japanese-First Design → Complete",
            "qTubler System → Operational",
            "JWT Authentication → Secured",
            "Welcome to AiDiy"
        ];
        this.currentTextIndex = 0;
        this.typewriterSpeed = 50;
        this.countersAnimated = false;

        // 自動スクロール設定
        this.autoScrollEnabled = false;
        this.scrollTimeout = null;
        this.userInteracted = false;
        this.autoScrollSpeed = 1;
        this.expectedScrollY = 0;

        this.init();
    }

    init() {
        this.setupTitleAnimation();
        this.setupTypewriter();
        this.setupScrollAnimations();
        this.setupAutoScroll();
    }

    setupTitleAnimation() {
        const leftEl   = document.getElementById('title-left');
        const rightEl  = document.getElementById('title-right');
        const assembly = document.getElementById('hero-title-assembly');
        const flashEl  = document.getElementById('title-flash');
        const finalEl  = document.getElementById('hero-title-final');
        if (!leftEl || !finalEl) return;

        // slideIn: delay 0.2s + duration 0.75s = ends ~0.95s → wait a beat → 1.05s
        setTimeout(() => {
            // 両パーツをフラッシュアウト
            leftEl.classList.add('merging');
            rightEl.classList.add('merging');
            if (flashEl) flashEl.classList.add('active');

            // アセンブリを隠して最終タイトルを登場させる
            setTimeout(() => {
                if (assembly) assembly.style.visibility = 'hidden';
                finalEl.classList.add('revealed');
            }, 350);
        }, 1050);
    }

    _spawnImpactParticles() {
        const cx = window.innerWidth / 2;
        const cy = (() => {
            const el = document.getElementById('hero-title-assembly');
            if (!el) return window.innerHeight * 0.35;
            const r = el.getBoundingClientRect();
            return r.top + r.height / 2;
        })();

        const COLORS = ['#00ffff', '#ff00ff', '#ffff00', '#ffffff', '#00ff88'];
        const count = 28;

        for (let i = 0; i < count; i++) {
            const angle  = (i / count) * Math.PI * 2 + (Math.random() - 0.5) * 0.5;
            const speed  = 80 + Math.random() * 140;
            const dx     = Math.cos(angle) * speed;
            const dy     = Math.sin(angle) * speed;
            const color  = COLORS[Math.floor(Math.random() * COLORS.length)];
            const sz     = 3 + Math.random() * 4;
            const dur    = 700 + Math.random() * 400;

            const dot = document.createElement('div');
            dot.style.cssText = `
                position:fixed; border-radius:50%; pointer-events:none; z-index:9999;
                width:${sz}px; height:${sz}px;
                background:${color};
                box-shadow:0 0 8px ${color};
                left:${cx}px; top:${cy}px;
            `;
            document.body.appendChild(dot);

            const start = performance.now();
            const tick = (now) => {
                const p = Math.min(1, (now - start) / dur);
                const e = 1 - p * p;
                dot.style.transform = `translate(${dx * p}px, ${dy * p}px)`;
                dot.style.opacity   = String(e);
                if (p < 1) requestAnimationFrame(tick);
                else dot.remove();
            };
            requestAnimationFrame(tick);
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

    animateCounters() {
        document.querySelectorAll('.stat-number').forEach(counter => {
            const target = parseInt(counter.dataset.count);
            const duration = 2000;
            const startTime = performance.now();

            const updateCounter = (currentTime) => {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);
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

    setupAutoScroll() {
        setTimeout(() => {
            if (!this.userInteracted) {
                this.startAutoScroll();
            }
        }, 10000);

        this.setupUserInteractionDetection();
    }

    setupUserInteractionDetection() {
        const events = ['wheel', 'touchstart', 'touchmove', 'keydown', 'click'];

        events.forEach(eventName => {
            window.addEventListener(eventName, () => {
                if (this.autoScrollEnabled) {
                    this.userInteracted = true;
                    this.stopAutoScroll();
                }
            }, { passive: true });
        });

        window.addEventListener('scroll', () => {
            if (!this.autoScrollEnabled) return;

            const currentScrollY = window.scrollY;
            const diff = Math.abs(currentScrollY - this.expectedScrollY);

            if (diff > 10) {
                this.userInteracted = true;
                this.stopAutoScroll();
            }
        }, { passive: true });
    }

    startAutoScroll() {
        if (this.scrollTimeout || this.userInteracted) return;

        this.autoScrollEnabled = true;
        this.expectedScrollY = window.scrollY;

        this.showNotification('自動スクロール開始', 2000);

        const scrollInterval = 21;

        const autoScroll = () => {
            if (!this.autoScrollEnabled) {
                clearTimeout(this.scrollTimeout);
                return;
            }

            const previousScrollY = window.scrollY;
            window.scrollBy(0, this.autoScrollSpeed);
            const currentScrollY = window.scrollY;

            this.expectedScrollY = currentScrollY;

            if (previousScrollY === currentScrollY) {
                this.showNotification('最下部に到達', 2000);
                this.stopAutoScroll();
                return;
            }

            this.scrollTimeout = setTimeout(autoScroll, scrollInterval);
        };

        autoScroll();
    }

    stopAutoScroll() {
        if (this.scrollTimeout) {
            clearTimeout(this.scrollTimeout);
            this.scrollTimeout = null;
        }

        if (this.autoScrollEnabled && this.userInteracted) {
            this.showNotification('自動スクロール停止', 1500);
        }

        this.autoScrollEnabled = false;
    }

    showNotification(message, duration = 2000) {
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

        setTimeout(() => {
            notification.style.animation = 'notification-fade-out 0.3s ease-in forwards';
        }, duration - 300);

        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, duration);
    }

    destroy() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }

        this.stopAutoScroll();
        window.removeEventListener('resize', this.resizeCanvas);
    }
}

// 追加のCSSアニメーション
$(document).ready(function() {
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

        html {
            scroll-behavior: smooth;
        }

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

        .feature-title:hover,
        .architecture-title:hover {
            text-shadow: 0 0 20px currentColor;
            transition: text-shadow 0.3s ease;
        }

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

        @media (max-width: 768px) {
            .auto-scroll-notification {
                top: 10px !important;
                right: 10px !important;
                font-size: 0.8rem !important;
                padding: 8px 16px !important;
            }
        }
        </style>
    `;

    $('head').append(additionalStyles);

    const aiDiyIntro = new AiDiyIntroduction();

    // 動的背景エフェクト
    setInterval(() => {
        if (Math.random() < 0.1) {
            createRandomGlow();
        }
    }, 2000);

    function createRandomGlow() {
        const glow = $('<div class="random-glow"></div>');
        glow.css({
            position: 'fixed',
            width: Math.random() * 200 + 100 + 'px',
            height: Math.random() * 200 + 100 + 'px',
            background: `radial-gradient(circle, rgba(${Math.floor(Math.random() * 255)}, ${Math.floor(Math.random() * 255)}, 255, 0.1), transparent)`,
            borderRadius: '50%',
            left: Math.random() * window.innerWidth + 'px',
            top: Math.random() * window.innerHeight + 'px',
            pointerEvents: 'none',
            zIndex: -1,
            animation: 'glow-fade 4s ease-out forwards'
        });

        $('body').append(glow);

        setTimeout(() => {
            glow.remove();
        }, 4000);
    }

    $('head').append(`
        <style>
        @keyframes glow-fade {
            0% { opacity: 0; transform: scale(0.5); }
            50% { opacity: 1; transform: scale(1); }
            100% { opacity: 0; transform: scale(1.5); }
        }
        </style>
    `);

    window.addEventListener('beforeunload', () => {
        if (aiDiyIntro) {
            aiDiyIntro.destroy();
        }
    });
});
