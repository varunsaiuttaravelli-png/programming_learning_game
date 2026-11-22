# ⚡ CodeQuest: Programming Learning Game

**CodeQuest** is a full-stack, gamified web application designed to help students and beginners master Python programming through interactive games, quizzes, code reordering puzzles, debugging challenges, and an achievement rewards system.

---

## 🌟 Key Features

### 1. Interactive Programming Games (6 Modes)
- 💡 **Guess the Output:** Predict the exact printed or returned result of Python snippets (slices, arithmetic, mutability, closures).
- 🔍 **Find the Error:** Spot syntax traps, type mismatches, indexing bugs, and scoping issues.
- ⚡ **Code Quiz:** Rapid-fire multiple-choice questions assessing programming fundamentals.
- 🧩 **Arrange the Code (Parsons Puzzles):** Reorder scrambled code blocks into functioning Python programs with drag-and-drop or directional arrows.
- 🛠️ **Debugging Challenge:** Diagnose broken code snippets and identify the exact code patch required.
- ✏️ **Fill in the Blanks:** Complete missing Python keywords, operators, and method calls.

### 2. Difficulty Tiers & Level Progression
- 🌱 **Easy Tier (0 XP):** Variables, basic types, operators, and I/O. Unlocked by default.
- ⚔️ **Medium Tier (150 XP):** Conditionals, loops, functions, lists, and dicts. Automatically unlocks once the user earns 150 points.
- 🛡️ **Hard Tier (400 XP):** Algorithms, recursion, scoping rules, and advanced debugging. Unlocked at 400 points.

### 3. Gamification & Rewards
- **Dynamic XP Scoring:** Base points + time bonus for fast answers + streak multiplier (+5 for consecutive wins).
- **Streak Multiplier:** Real-time flame indicator tracking consecutive correct answers.
- **Ticking Timer:** Visual countdown timer per question with warning states under 10 seconds.
- **Badges & Achievements:** 12 unlockable badges (Speed Demon, Bug Hunter, Code Architect, Century Coder, etc.).
- **Live Sound Effects:** Built-in Web Audio API sound synthesis (correct chime, wrong buzz, tick, streak fanfare, victory music) with toggle mute.
- **Victory Particle Confetti:** Canvas physics-based confetti celebration upon completing challenges and unlocking badges.

### 4. Competitive Leaderboard
- Top 3 Podium with Gold, Silver, and Bronze badges and glowing avatars.
- Real-time ranking calculated directly from database points.
- Highlighted logged-in user row.

### 5. Robust Security & Server-Side Validation
- Secure password hashing using PBKDF2/SHA256 (`werkzeug.security`).
- Parameterized SQLite queries to prevent SQL injection.
- **Zero Frontend Cheating:** Answer keys and solutions are NEVER sent to the client browser. Answers are strictly validated server-side by Flask.
- Protected routes with `@login_required` and `@admin_required` decorators.

### 6. Admin Panel
- Live metrics: Total users, total questions, games played, and total XP distributed.
- Question management: Add new questions across all 6 formats, edit existing challenges, or delete them.
- User oversight: View all registered learners and their statistics.

---

## 📂 Project Structure

```text
programming_learning_game/
│
├── app.py                     # Main Flask application and REST API endpoints
├── db.py                      # SQLite database initialization, schema, and seed data
├── database.db                # SQLite database file
├── requirements.txt           # Python package dependencies
├── run.bat                    # Windows 1-click launcher script
├── README.md                  # Comprehensive documentation
│
├── templates/                 # Jinja2 HTML Templates
│   ├── base.html              # Base template with navigation, toast alerts & audio engine
│   ├── index.html             # Landing page with hero, live preview, and game cards
│   ├── login.html             # Gamified user login with demo account helpers
│   ├── register.html          # Registration form with interactive avatar selector
│   ├── dashboard.html         # User dashboard with stats, XP bar, badges, and progress
│   ├── games.html             # Games lobby with tier locks and quick launchers
│   ├── quiz.html              # Interactive Game Arena supporting all 6 modes
│   ├── leaderboard.html       # Global ranking podium and leaderboard table
│   ├── profile.html           # Profile customizer (avatar & bio) and match history
│   └── admin.html             # Admin dashboard with question CRUD and user inspector
│
└── static/                    # Frontend Static Assets
    ├── css/
    │   └── style.css          # Design system, dark mode, animations & glassmorphism
    ├── js/
    │   ├── script.js          # Web Audio synth, confetti particles, toasts & UI
    │   └── game.js            # Arena engine (Parsons drag-and-drop, timer, REST API)
    └── images/                # Static image assets
```

---

## 🚀 Quick Start & Installation

### Prerequisites
- Python 3.10, 3.11, 3.12, or 3.14 installed on Windows.

### 1. Install Dependencies
Open PowerShell or Command Prompt in the `programming_learning_game` directory and run:
```bash
pip install -r requirements.txt
```

### 2. Start the Server
Run the Flask server:
```bash
python app.py
```
*(Or double-click `run.bat` on Windows)*

### 3. Open in Browser
Visit:
```text
http://127.0.0.1:5000
```

---

## 🔑 Default Accounts

For testing both student and administrator capabilities, the following accounts are pre-seeded in the database:

| Role | Username | Password | Notes |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin` | `AdminPass123!` | Has access to `/admin` management panel |
| **Student** | `pycoder` | `Student123!` | Has 180 XP, badges unlocked, Medium tier open |

You can also create any new account using the **Sign Up Free** button on the home page!

---

## 🛠️ API Endpoints Summary

- `GET /api/game/<category_slug>/<difficulty>`: Fetches questions without leaking answers.
- `POST /api/game/submit-answer`: Validates submitted answer on the server, awards points, manages streaks, and checks badge criteria.
- `POST /api/game/complete-session`: Records session score, total time, and updates high score progress.
- `GET /admin/question/<id>/json`: Fetches question data for admin editing.
- `POST /admin/question/add`: Adds a new challenge to the database.
- `POST /admin/question/edit/<id>`: Updates an existing question.
- `POST /admin/question/delete/<id>`: Deletes a question.
