/* ===================================================================
   CodeQuest - Global Scripts & Web Audio Engine
   =================================================================== */

// Global Audio Engine using Web Audio API
class SoundEngine {
  constructor() {
    this.audioCtx = null;
    this.audioUnavailable = false;
    this.muted = localStorage.getItem('cq_muted') === 'true';
  }

  init() {
    if (!this.audioCtx && !this.audioUnavailable) {
      try {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (AudioContext) {
          this.audioCtx = new AudioContext();
        } else {
          this.audioUnavailable = true;
        }
      } catch (e) {
        this.audioUnavailable = true;
        console.warn("Audio playback is unavailable:", e);
      }
    }
    if (this.audioCtx && this.audioCtx.state === 'suspended') {
      this.audioCtx.resume();
    }
  }

  toggleMute() {
    this.muted = !this.muted;
    localStorage.setItem('cq_muted', this.muted);
    this.updateSoundBtn();
    return this.muted;
  }

  updateSoundBtn() {
    const btn = document.getElementById('sound-toggle-btn');
    if (btn) {
      btn.innerHTML = this.muted ? '🔇' : '🔊';
      btn.title = this.muted ? 'Unmute Sound' : 'Mute Sound';
    }
  }

  playTone(freq, type, duration, startTime = 0, gainLevel = 0.15) {
    if (this.muted) return;
    this.init();
    if (!this.audioCtx) return;

    try {
      const osc = this.audioCtx.createOscillator();
      const gain = this.audioCtx.createGain();

      osc.type = type;
      osc.frequency.setValueAtTime(freq, this.audioCtx.currentTime + startTime);

      gain.gain.setValueAtTime(gainLevel, this.audioCtx.currentTime + startTime);
      gain.gain.exponentialRampToValueAtTime(0.0001, this.audioCtx.currentTime + startTime + duration);

      osc.connect(gain);
      gain.connect(this.audioCtx.destination);

      osc.start(this.audioCtx.currentTime + startTime);
      osc.stop(this.audioCtx.currentTime + startTime + duration);
    } catch (e) {
      console.warn("Audio playback error:", e);
    }
  }

  play(soundName) {
    if (this.muted) return;
    this.init();

    switch (soundName) {
      case 'click':
        this.playTone(600, 'sine', 0.05, 0, 0.08);
        break;
      case 'correct':
        // Two-tone cheerful major chord
        this.playTone(523.25, 'triangle', 0.12, 0, 0.18); // C5
        this.playTone(659.25, 'triangle', 0.15, 0.08, 0.18); // E5
        this.playTone(783.99, 'triangle', 0.28, 0.16, 0.2); // G5
        break;
      case 'incorrect':
        // Low buzzy error chord
        this.playTone(220, 'sawtooth', 0.2, 0, 0.15);
        this.playTone(196, 'sawtooth', 0.3, 0.1, 0.18);
        break;
      case 'streak':
        // Ascending rapid chime
        [440, 554, 659, 880].forEach((freq, idx) => {
          this.playTone(freq, 'sine', 0.12, idx * 0.06, 0.15);
        });
        break;
      case 'victory':
        // Fanfare chord sequence
        [523.25, 659.25, 783.99, 1046.50].forEach((freq, idx) => {
          this.playTone(freq, 'triangle', 0.35, idx * 0.1, 0.2);
        });
        break;
      case 'tick':
        this.playTone(900, 'sine', 0.03, 0, 0.04);
        break;
    }
  }
}

const sounds = new SoundEngine();

// Confetti Particle System
class ConfettiCannon {
  constructor() {
    this.canvas = document.getElementById('confetti-canvas');
    if (!this.canvas) {
      this.canvas = document.createElement('canvas');
      this.canvas.id = 'confetti-canvas';
      document.body.appendChild(this.canvas);
    }
    this.ctx = this.canvas.getContext('2d');
    this.particles = [];
    this.animating = false;
    this.resize();
    window.addEventListener('resize', () => this.resize());
  }

  resize() {
    this.canvas.width = window.innerWidth;
    this.canvas.height = window.innerHeight;
  }

  burst(count = 80) {
    const colors = ['#6366f1', '#ec4899', '#06b6d4', '#10b981', '#f59e0b', '#f87171', '#a855f7'];
    for (let i = 0; i < count; i++) {
      this.particles.push({
        x: window.innerWidth / 2 + (Math.random() - 0.5) * 200,
        y: window.innerHeight * 0.4,
        size: Math.random() * 8 + 4,
        color: colors[Math.floor(Math.random() * colors.length)],
        velX: (Math.random() - 0.5) * 16,
        velY: -(Math.random() * 14 + 6),
        gravity: 0.35,
        rotation: Math.random() * 360,
        rotSpeed: (Math.random() - 0.5) * 10,
        life: 1,
        decay: Math.random() * 0.015 + 0.01
      });
    }

    if (!this.animating) {
      this.animating = true;
      this.loop();
    }
  }

  loop() {
    if (!this.animating) return;
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    for (let i = this.particles.length - 1; i >= 0; i--) {
      const p = this.particles[i];
      p.x += p.velX;
      p.y += p.velY;
      p.velY += p.gravity;
      p.rotation += p.rotSpeed;
      p.life -= p.decay;

      if (p.life <= 0 || p.y > this.canvas.height) {
        this.particles.splice(i, 1);
        continue;
      }

      this.ctx.save();
      this.ctx.translate(p.x, p.y);
      this.ctx.rotate((p.rotation * Math.PI) / 180);
      this.ctx.fillStyle = p.color;
      this.ctx.globalAlpha = Math.max(0, p.life);
      this.ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size * 1.4);
      this.ctx.restore();
    }

    if (this.particles.length > 0) {
      requestAnimationFrame(() => this.loop());
    } else {
      this.animating = false;
      this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }
  }
}

const confetti = new ConfettiCannon();

// Document Ready Initialization
document.addEventListener('DOMContentLoaded', () => {
  // 1. Initialize sound button state
  sounds.updateSoundBtn();
  const soundBtn = document.getElementById('sound-toggle-btn');
  if (soundBtn) {
    soundBtn.addEventListener('click', () => {
      sounds.toggleMute();
      if (!sounds.muted) sounds.play('click');
    });
  }

  // 2. Play sound on button click
  document.querySelectorAll('.btn, .nav-link, .tier-btn').forEach(elem => {
    elem.addEventListener('click', () => {
      sounds.play('click');
    });
  });

  // 3. Mobile menu toggle
  const mobileToggle = document.getElementById('mobile-menu-toggle');
  const navLinks = document.getElementById('nav-links');
  if (mobileToggle && navLinks) {
    mobileToggle.addEventListener('click', () => {
      navLinks.classList.toggle('mobile-open');
    });
  }

  // 4. Auto-dismiss toasts after 5 seconds
  document.querySelectorAll('.toast').forEach(toast => {
    setTimeout(() => {
      toast.style.transition = 'opacity 0.5s ease-out, transform 0.5s ease-out';
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      setTimeout(() => toast.remove(), 500);
    }, 4500);
  });

  // 5. Avatar Selection in forms
  const avatarChoices = document.querySelectorAll('.avatar-choice');
  const avatarInput = document.getElementById('selected-avatar-input');
  if (avatarChoices.length && avatarInput) {
    avatarChoices.forEach(choice => {
      choice.addEventListener('click', () => {
        avatarChoices.forEach(c => c.classList.remove('selected'));
        choice.classList.add('selected');
        avatarInput.value = choice.dataset.avatar;
        sounds.play('click');
      });
    });
  }
});
