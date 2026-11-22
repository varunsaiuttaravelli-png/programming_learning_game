/* ===================================================================
   CodeQuest - Game Arena Engine
   Dynamic Question Renderers & Server Validation
   =================================================================== */

class GameArena {
  constructor(categorySlug, difficulty) {
    this.categorySlug = categorySlug;
    this.difficulty = difficulty;

    this.questions = [];
    this.currentIndex = 0;
    this.currentQuestion = null;

    this.sessionScore = 0;
    this.sessionCorrect = 0;
    this.currentStreak = 0;

    this.timer = null;
    this.timeLeft = 0;
    this.maxTime = 45;
    this.questionStartTime = 0;
    this.sessionStartTime = Date.now();

    this.selectedAnswer = null;
    this.answered = false;

    // Elements
    this.qIndexEl = document.getElementById('q-current-index');
    this.qTotalEl = document.getElementById('q-total-count');
    this.scoreValEl = document.getElementById('arena-score-val');
    this.accountPointsEl = document.getElementById('arena-total-points');
    this.accountPoints = this.accountPointsEl
      ? Number(this.accountPointsEl.textContent)
      : null;
    this.streakValEl = document.getElementById('arena-streak-val');
    this.timerValEl = document.getElementById('timer-val');
    this.timerBarFillEl = document.getElementById('timer-bar-fill');
    this.timerPillEl = document.getElementById('timer-pill');

    this.qCardEl = document.getElementById('question-card');
    this.qStepTitleEl = document.getElementById('q-step-title');
    this.qTitleEl = document.getElementById('q-title');
    this.qDescEl = document.getElementById('q-desc');
    this.qCodeWrapEl = document.getElementById('q-code-wrapper');
    this.qCodeEl = document.getElementById('q-code-content');
    this.interactionAreaEl = document.getElementById('interaction-area');

    this.feedbackBoxEl = document.getElementById('feedback-box');
    this.feedbackTitleEl = document.getElementById('feedback-title');
    this.feedbackDescEl = document.getElementById('feedback-desc');

    this.submitBtn = document.getElementById('submit-answer-btn');
    this.nextBtn = document.getElementById('next-question-btn');

    this.init();
  }

  async init() {
    this.submitBtn.addEventListener('click', () => this.submitAnswer());
    this.nextBtn.addEventListener('click', () => this.nextQuestion());

    try {
      const resp = await fetch(`/api/game/${this.categorySlug}/${this.difficulty}`);
      const data = await resp.json();

      if (data.questions && data.questions.length > 0) {
        this.questions = data.questions;
        this.qTotalEl.textContent = this.questions.length;
        this.loadQuestion(0);
      } else {
        this.showError('No questions found for this challenge.');
      }
    } catch (err) {
      console.error('Failed to load questions:', err);
      this.showError('Unable to load game questions. Please check connection and refresh.');
    }
  }

  showError(msg) {
    this.qCardEl.innerHTML = `
      <div style="text-align:center; padding: 2rem;">
        <div style="font-size: 3rem; margin-bottom: 1rem;">⚠️</div>
        <h3>Oops!</h3>
        <p style="color: var(--text-muted); margin: 1rem 0;">${msg}</p>
        <a href="/games" class="btn btn-primary">Return to Lobby</a>
      </div>
    `;
  }

  loadQuestion(index) {
    this.currentIndex = index;
    this.currentQuestion = this.questions[index];
    this.answered = false;
    this.selectedAnswer = null;

    // Reset controls
    this.submitBtn.style.display = 'inline-flex';
    this.submitBtn.disabled = true;
    this.nextBtn.style.display = 'none';
    this.feedbackBoxEl.className = 'feedback-box';
    this.feedbackBoxEl.style.display = 'none';

    // Update metadata
    this.qIndexEl.textContent = index + 1;
    this.qStepTitleEl.textContent = `Question ${index + 1} of ${this.questions.length} • ${this.currentQuestion.points} XP`;
    this.qTitleEl.textContent = this.currentQuestion.title;
    this.qDescEl.textContent = this.currentQuestion.description || '';

    // Code snippet
    if (this.currentQuestion.code_snippet && this.currentQuestion.code_snippet.trim()) {
      this.qCodeWrapEl.style.display = 'block';
      this.qCodeEl.textContent = this.currentQuestion.code_snippet;
    } else {
      this.qCodeWrapEl.style.display = 'none';
    }

    // Render interactive body based on type
    this.renderInteraction(this.currentQuestion);

    // Start Timer
    this.maxTime = this.currentQuestion.time_limit || 45;
    this.startTimer(this.maxTime);
  }

  renderInteraction(q) {
    this.interactionAreaEl.innerHTML = '';
    const qData = q.question_data || {};
    const qType = qData.type || 'mcq';

    if (qType === 'parsons') {
      this.renderParsonsProblem(qData);
    } else if (qType === 'fill_blank') {
      this.renderFillBlankProblem(qData);
    } else {
      // Default: Multiple choice (used in Code Quiz, Guess Output, Find Error, Debug Fix)
      this.renderMultipleChoice(qData);
    }
  }

  // 1. Multiple Choice Renderer
  renderMultipleChoice(qData) {
    const options = qData.options || [];
    const container = document.createElement('div');
    container.className = 'options-grid';

    const letters = ['A', 'B', 'C', 'D', 'E', 'F'];

    options.forEach((opt, idx) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'option-btn';
      btn.dataset.value = typeof opt === 'object' ? opt.value : opt;

      const optText = typeof opt === 'object' ? opt.label : opt;
      btn.innerHTML = `
        <span style="display:flex; align-items:center; gap:0.75rem;">
          <span style="width:28px; height:28px; border-radius:6px; background:rgba(255,255,255,0.08); display:flex; align-items:center; justify-content:center; font-weight:700; font-size:0.85rem; color:var(--text-muted);">${letters[idx] || (idx+1)}</span>
          <span>${this.escapeHtml(optText)}</span>
        </span>
        <span class="opt-status-icon"></span>
      `;

      btn.addEventListener('click', () => {
        if (this.answered) return;
        sounds.play('click');
        container.querySelectorAll('.option-btn').forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
        this.selectedAnswer = btn.dataset.value;
        this.submitBtn.disabled = false;
      });

      container.appendChild(btn);
    });

    this.interactionAreaEl.appendChild(container);
  }

  // 2. Parsons Problem (Arrange Code) Renderer
  renderParsonsProblem(qData) {
    const lines = qData.scrambled_lines || [];
    const container = document.createElement('div');
    container.className = 'parsons-container';

    const instruction = document.createElement('div');
    instruction.className = 'parsons-instruction';
    instruction.innerHTML = '<span>↕️ Use the Up/Down arrows or drag lines to place them in the correct execution order:</span>';
    container.appendChild(instruction);

    const list = document.createElement('div');
    list.id = 'parsons-list';
    list.style.display = 'flex';
    list.style.flexDirection = 'column';
    list.style.gap = '0.6rem';

    lines.forEach((line) => {
      const item = document.createElement('div');
      item.className = 'parsons-line';
      item.dataset.id = line.id;
      item.draggable = true;

      item.innerHTML = `
        <div class="parsons-handle">
          <span class="parsons-grip">☰</span>
          <code>${this.escapeHtml(line.text)}</code>
        </div>
        <div class="parsons-arrows">
          <button type="button" class="btn-arrow move-up" title="Move Up">▲</button>
          <button type="button" class="btn-arrow move-down" title="Move Down">▼</button>
        </div>
      `;

      // Arrow movement listeners
      item.querySelector('.move-up').addEventListener('click', (e) => {
        e.stopPropagation();
        if (this.answered) return;
        const prev = item.previousElementSibling;
        if (prev) {
          list.insertBefore(item, prev);
          sounds.play('click');
        }
      });

      item.querySelector('.move-down').addEventListener('click', (e) => {
        e.stopPropagation();
        if (this.answered) return;
        const next = item.nextElementSibling;
        if (next) {
          list.insertBefore(next, item);
          sounds.play('click');
        }
      });

      // Drag and Drop
      item.addEventListener('dragstart', () => {
        if (this.answered) return;
        item.classList.add('dragging');
      });

      item.addEventListener('dragend', () => {
        item.classList.remove('dragging');
      });

      list.appendChild(item);
    });

    list.addEventListener('dragover', (e) => {
      e.preventDefault();
      if (this.answered) return;
      const draggingItem = list.querySelector('.dragging');
      if (!draggingItem) return;

      const siblings = [...list.querySelectorAll('.parsons-line:not(.dragging)')];
      const nextSibling = siblings.find(sib => {
        return e.clientY <= sib.getBoundingClientRect().top + sib.offsetHeight / 2;
      });

      list.insertBefore(draggingItem, nextSibling);
    });

    container.appendChild(list);
    this.interactionAreaEl.appendChild(container);

    // For parsons, button is always enabled because order is already editable
    this.submitBtn.disabled = false;
  }

  // 3. Fill in the Blank Renderer
  renderFillBlankProblem(qData) {
    const options = qData.options || [];
    const container = document.createElement('div');
    container.className = 'options-grid';

    options.forEach((opt, idx) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'option-btn';
      const val = typeof opt === 'object' ? opt.value : opt;
      const label = typeof opt === 'object' ? opt.label : opt;
      btn.dataset.value = val;

      btn.innerHTML = `
        <span style="display:flex; align-items:center; gap:0.75rem;">
          <span style="width:28px; height:28px; border-radius:6px; background:rgba(236,72,153,0.15); color:var(--secondary); display:flex; align-items:center; justify-content:center; font-weight:700;">${idx+1}</span>
          <span style="font-family:var(--font-code);">${this.escapeHtml(label)}</span>
        </span>
        <span class="opt-status-icon"></span>
      `;

      btn.addEventListener('click', () => {
        if (this.answered) return;
        sounds.play('click');
        container.querySelectorAll('.option-btn').forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
        this.selectedAnswer = btn.dataset.value;
        this.submitBtn.disabled = false;
      });

      container.appendChild(btn);
    });

    this.interactionAreaEl.appendChild(container);
  }

  startTimer(duration) {
    clearInterval(this.timer);
    this.timeLeft = duration;
    this.questionStartTime = Date.now();

    this.updateTimerDisplay();

    this.timer = setInterval(() => {
      this.timeLeft--;
      this.updateTimerDisplay();

      if (this.timeLeft <= 10 && this.timeLeft > 0) {
        sounds.play('tick');
      }

      if (this.timeLeft <= 0) {
        clearInterval(this.timer);
        if (!this.answered) {
          // Time expired, auto-submit timeout
          this.submitAnswer(true);
        }
      }
    }, 1000);
  }

  updateTimerDisplay() {
    this.timerValEl.textContent = `${this.timeLeft}s`;
    const pct = Math.max(0, (this.timeLeft / this.maxTime) * 100);
    this.timerBarFillEl.style.width = `${pct}%`;

    if (this.timeLeft <= 10) {
      this.timerPillEl.classList.add('warning');
      this.timerBarFillEl.style.background = 'var(--rose)';
    } else {
      this.timerPillEl.classList.remove('warning');
      this.timerBarFillEl.style.background = 'var(--cyan)';
    }
  }

  async submitAnswer(isTimeout = false) {
    if (this.answered) return;
    this.answered = true;
    clearInterval(this.timer);

    const timeTaken = Math.round((Date.now() - this.questionStartTime) / 1000);

    // Extract answer
    let finalAnswer = this.selectedAnswer;
    const qData = this.currentQuestion.question_data || {};

    if (qData.type === 'parsons') {
      const lines = [...this.interactionAreaEl.querySelectorAll('.parsons-line')];
      finalAnswer = lines.map(l => l.dataset.id);
    }

    if (isTimeout) {
      finalAnswer = "__TIMEOUT__";
    }

    this.submitBtn.disabled = true;

    try {
      const response = await fetch('/api/game/submit-answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question_id: this.currentQuestion.id,
          user_answer: finalAnswer,
          time_taken: timeTaken
        })
      });

      const result = await response.json();
      this.handleAnswerResult(result);
    } catch (err) {
      console.error('Error submitting answer:', err);
      this.handleAnswerResult({
        is_correct: false,
        points_awarded: 0,
        explanation: 'Connection error while communicating with verification server.',
        newly_unlocked_achievements: []
      });
    }
  }

  handleAnswerResult(result) {
    const isCorrect = result.is_correct;

    if (this.accountPointsEl && Number.isFinite(result.new_total_points)) {
      const previousPoints = this.accountPoints;
      this.accountPoints = result.new_total_points;
      this.accountPointsEl.textContent = this.accountPoints;

      if (previousPoints < 150 && this.accountPoints >= 150) {
        this.showTierUnlockToast('Medium');
      }
      if (previousPoints < 400 && this.accountPoints >= 400) {
        this.showTierUnlockToast('Hard');
      }
    }

    if (isCorrect) {
      sounds.play('correct');
      this.sessionScore += result.points_awarded;
      this.sessionCorrect++;
      this.currentStreak = result.streak || (this.currentStreak + 1);

      if (this.currentStreak >= 3) {
        setTimeout(() => sounds.play('streak'), 350);
      }
    } else {
      sounds.play('incorrect');
      this.currentStreak = 0;
    }

    // Update Stats Display
    this.scoreValEl.textContent = this.sessionScore;
    this.streakValEl.textContent = this.currentStreak;

    // Visual markup on options
    const optionButtons = this.interactionAreaEl.querySelectorAll('.option-btn');
    optionButtons.forEach(btn => {
      btn.disabled = true;
      if (btn.classList.contains('selected')) {
        btn.classList.add(isCorrect ? 'correct' : 'incorrect');
      }
      // If user got it wrong, highlight the correct one
      if (!isCorrect && btn.dataset.value === String(result.correct_answer)) {
        btn.classList.add('correct');
      }
    });

    // If parsons problem
    if (this.currentQuestion.question_data.type === 'parsons') {
      const list = this.interactionAreaEl.querySelector('#parsons-list');
      if (list) {
        list.style.borderColor = isCorrect ? 'var(--emerald)' : 'var(--rose)';
      }
    }

    // Render Explanation Box
    this.feedbackBoxEl.className = `feedback-box ${isCorrect ? 'correct' : 'incorrect'}`;
    this.feedbackTitleEl.innerHTML = isCorrect
      ? '🎉 Correct! Awesome Job!'
      : '❌ Not quite right!';
    this.feedbackDescEl.textContent = result.explanation || '';
    this.feedbackBoxEl.style.display = 'block';

    // Badge Unlocks popup
    if (result.newly_unlocked_achievements && result.newly_unlocked_achievements.length > 0) {
      result.newly_unlocked_achievements.forEach(ach => {
        this.showAchievementToast(ach);
      });
    }

    // Switch buttons
    this.submitBtn.style.display = 'none';
    this.nextBtn.style.display = 'inline-flex';
    this.nextBtn.textContent = (this.currentIndex < this.questions.length - 1)
      ? 'Next Question →'
      : 'Finish Challenge 🏆';
  }

  showAchievementToast(ach) {
    confetti.burst(50);
    const toast = document.createElement('div');
    toast.className = 'toast toast-warning';
    toast.style.background = 'rgba(245, 158, 11, 0.95)';
    toast.innerHTML = `
      <div style="font-size:1.8rem;">${ach.icon}</div>
      <div>
        <div style="font-weight:700; font-size:0.8rem; text-transform:uppercase; letter-spacing:0.5px;">Badge Unlocked!</div>
        <div style="font-weight:800; font-size:1.05rem;">${ach.title}</div>
      </div>
    `;
    const container = document.querySelector('.toast-container') || document.body;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 400);
    }, 4500);
  }

  showTierUnlockToast(tier) {
    const toast = document.createElement('div');
    toast.className = 'toast toast-success';
    toast.innerHTML = `
      <div style="font-size:1.8rem;">🔓</div>
      <div>
        <div style="font-weight:700; font-size:0.8rem; text-transform:uppercase; letter-spacing:0.5px;">Level unlocked!</div>
        <div style="font-weight:800; font-size:1.05rem;">${tier} tier is now available</div>
        <div style="font-size:0.85rem;">Return to the game lobby to play it.</div>
      </div>
    `;
    const container = document.querySelector('.toast-container') || document.body;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 400);
    }, 4500);
  }

  nextQuestion() {
    sounds.play('click');
    if (this.currentIndex < this.questions.length - 1) {
      this.loadQuestion(this.currentIndex + 1);
    } else {
      this.finishSession();
    }
  }

  async finishSession() {
    clearInterval(this.timer);
    sounds.play('victory');
    confetti.burst(120);

    const totalTime = Math.round((Date.now() - this.sessionStartTime) / 1000);
    const accuracy = Math.round((this.sessionCorrect / this.questions.length) * 100);

    // Send complete-session payload
    try {
      await fetch('/api/game/complete-session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          category_slug: this.categorySlug,
          difficulty: this.difficulty,
          score_earned: this.sessionScore,
          questions_count: this.questions.length,
          correct_count: this.sessionCorrect,
          time_taken_seconds: totalTime
        })
      });
    } catch (e) {
      console.warn("Failed to save final session record:", e);
    }

    // Render Victory Screen
    this.qCardEl.innerHTML = `
      <div class="victory-card">
        <div class="victory-trophy">🏆</div>
        <h2 style="font-size:2.2rem; margin-bottom:0.5rem;">Challenge Completed!</h2>
        <p style="color:var(--text-muted); font-size:1.05rem;">Great effort leveling up your Python skills!</p>

        <div class="victory-score-pill">
          <span>⚡</span>
          <span>+${this.sessionScore} XP Earned</span>
        </div>

        <div class="summary-stats-grid">
          <div class="glass-card" style="padding:1.2rem; text-align:center;">
            <div style="font-size:0.82rem; color:var(--text-dim); text-transform:uppercase;">Accuracy</div>
            <div style="font-size:1.8rem; font-weight:800; color:var(--emerald);">${accuracy}%</div>
          </div>
          <div class="glass-card" style="padding:1.2rem; text-align:center;">
            <div style="font-size:0.82rem; color:var(--text-dim); text-transform:uppercase;">Correct</div>
            <div style="font-size:1.8rem; font-weight:800; color:#fff;">${this.sessionCorrect} / ${this.questions.length}</div>
          </div>
          <div class="glass-card" style="padding:1.2rem; text-align:center;">
            <div style="font-size:0.82rem; color:var(--text-dim); text-transform:uppercase;">Time Taken</div>
            <div style="font-size:1.8rem; font-weight:800; color:var(--cyan);">${totalTime}s</div>
          </div>
        </div>

        <div style="display:flex; justify-content:center; gap:1rem; flex-wrap:wrap; margin-top:1.5rem;">
          <a href="/game/${this.categorySlug}/${this.difficulty}" class="btn btn-outline">Play Again 🔄</a>
          <a href="/games" class="btn btn-cyan">Choose Another Game 🎮</a>
          <a href="/dashboard" class="btn btn-primary">Go to Dashboard 📊</a>
        </div>
      </div>
    `;

    // Hide controls
    document.querySelector('.arena-controls').style.display = 'none';
  }

  escapeHtml(text) {
    if (!text) return '';
    return text
      .toString()
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
}

// Auto-instantiate if on quiz page
document.addEventListener('DOMContentLoaded', () => {
  const arenaEl = document.querySelector('[data-game-arena]');
  if (arenaEl) {
    const category = arenaEl.dataset.category;
    const difficulty = arenaEl.dataset.difficulty;
    window.gameInstance = new GameArena(category, difficulty);
  }
});
