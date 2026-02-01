// index.js - AiDiy_next 自己紹介ページの動的機能

class AiDiyIntroduction {
    constructor() {
        this.particleCanvas = null;
        this.particleCtx = null;
        this.particles = [];
        this.animationId = null;
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
            "Welcome to AiDiy_next"
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
        this.setupParticleCanvas();
        this.startParticleAnimation();
        this.setupTypewriter();
        this.setupScrollAnimations();
        this.setupInteractiveEffects();
        this.setupAutoScroll();
    }

    setupParticleCanvas() {
        this.particleCanvas = document.getElementById('particles-bg');
        this.particleCtx = this.particleCanvas.getContext('2d');

        this.resizeCanvas();
        window.addEventListener('resize', () => this.resizeCanvas());

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
                particle.x += particle.vx;
                particle.y += particle.vy;

                if (particle.x < 0 || particle.x > this.particleCanvas.width) {
                    particle.vx *= -1;
                }
                if (particle.y < 0 || particle.y > this.particleCanvas.height) {
                    particle.vy *= -1;
                }

                particle.pulsePhase += particle.pulseSpeed;
                const pulseOpacity = particle.opacity + Math.sin(particle.pulsePhase) * 0.2;

                this.particleCtx.beginPath();
                this.particleCtx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
                this.particleCtx.fillStyle = particle.color + pulseOpacity + ')';
                this.particleCtx.fill();

                this.particleCtx.shadowBlur = 10;
                this.particleCtx.shadowColor = particle.color + '0.8)';
                this.particleCtx.fill();
                this.particleCtx.shadowBlur = 0;
            });

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

    setupInteractiveEffects() {
        document.querySelectorAll('.feature-card').forEach(card => {
            card.addEventListener('mouseenter', () => {
                this.createHoverParticles(card);
            });
        });

        document.querySelectorAll('.architecture-item').forEach(item => {
            item.addEventListener('mouseenter', () => {
                this.createRippleEffect(item);
            });
        });

        document.querySelectorAll('.expansion-item').forEach(item => {
            item.addEventListener('mouseenter', () => {
                this.createPulseEffect(item);
            });
        });

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

        this.createClickSparkAnimations();
    }

    createClickSparkAnimations() {
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
