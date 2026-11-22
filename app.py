import os
import json
import sqlite3
from functools import wraps
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify, abort
)
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db_connection, init_db

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'codequest-super-secret-key-2026')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Ensure database exists
if not os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')):
    init_db()

# -------------------------------------------------------------
# Helpers & Decorators
# -------------------------------------------------------------

def get_current_user():
    if 'user_id' not in session:
        return None
    conn = get_db_connection()
    user = conn.execute(
        'SELECT * FROM users WHERE id = ?', (session['user_id'],)
    ).fetchone()
    conn.close()
    return user

def calculate_level_info(points):
    """Calculates user level title, level number, and progress percentage to next tier."""
    if points < 150:
        level_num = 1
        level_title = "Novice Coder"
        next_target = 150
        prev_target = 0
        badge_icon = "🌱"
    elif points < 400:
        level_num = 2
        level_title = "Code Warrior"
        next_target = 400
        prev_target = 150
        badge_icon = "⚔️"
    elif points < 800:
        level_num = 3
        level_title = "Python Knight"
        next_target = 800
        prev_target = 400
        badge_icon = "🛡️"
    else:
        level_num = 4
        level_title = "Code Grandmaster"
        next_target = points + 200
        prev_target = 800
        badge_icon = "👑"

    if next_target > prev_target:
        progress_pct = min(100, max(0, int(((points - prev_target) / (next_target - prev_target)) * 100)))
    else:
        progress_pct = 100

    return {
        "level_num": level_num,
        "level_title": level_title,
        "next_target": next_target,
        "prev_target": prev_target,
        "progress_pct": progress_pct,
        "badge_icon": badge_icon,
        "medium_unlocked": points >= 150,
        "hard_unlocked": points >= 400
    }

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page and track your progress!', 'warning')
            return redirect(url_for('login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in as an administrator.', 'warning')
            return redirect(url_for('login', next=request.path))
        user = get_current_user()
        if not user or not user['is_admin']:
            flash('Admin access is required to view that page.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_user_context():
    user = get_current_user()
    level_info = calculate_level_info(user['total_points']) if user else None
    return dict(current_user=user, level_info=level_info)

# -------------------------------------------------------------
# Authentication Routes
# -------------------------------------------------------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        avatar = request.form.get('avatar', 'coder1')

        errors = []
        if not username or len(username) < 3 or len(username) > 25:
            errors.append('Username must be between 3 and 25 characters.')
        if not email or '@' not in email or '.' not in email:
            errors.append('Please provide a valid email address.')
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters long.')
        if password != confirm_password:
            errors.append('Passwords do not match.')

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('register.html', username=username, email=email)

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check existing user
        existing_user = cursor.execute(
            'SELECT id FROM users WHERE username = ? OR email = ?',
            (username, email)
        ).fetchone()

        if existing_user:
            conn.close()
            flash('Username or email is already taken. Please choose another or login.', 'danger')
            return render_template('register.html', username=username, email=email)

        password_hash = generate_password_hash(password)
        cursor.execute('''
        INSERT INTO users (username, email, password_hash, avatar, bio)
        VALUES (?, ?, ?, ?, ?)
        ''', (username, email, password_hash, avatar, 'Ready to learn coding with games!'))
        conn.commit()
        new_user_id = cursor.lastrowid
        conn.close()

        session['user_id'] = new_user_id
        session['username'] = username
        flash(f'Welcome aboard, {username}! Your coding journey begins now.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        login_id = request.form.get('login_id', '').strip()
        password = request.form.get('password', '')

        if not login_id or not password:
            flash('Please enter both your username/email and password.', 'warning')
            return render_template('login.html', login_id=login_id)

        conn = get_db_connection()
        cursor = conn.cursor()
        user = cursor.execute(
            'SELECT * FROM users WHERE username = ? OR email = ?',
            (login_id, login_id.lower())
        ).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash(f'Welcome back, {user["username"]}!', 'success')
            next_url = request.args.get('next')
            return redirect(next_url or url_for('dashboard'))
        else:
            flash('Invalid username/email or password. Please try again.', 'danger')
            return render_template('login.html', login_id=login_id)

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have successfully logged out. See you next time!', 'info')
    return redirect(url_for('index'))

# -------------------------------------------------------------
# Main Pages
# -------------------------------------------------------------

@app.route('/')
def index():
    conn = get_db_connection()
    categories = conn.execute('SELECT * FROM categories ORDER BY sort_order').fetchall()
    top_players = conn.execute(
        'SELECT username, total_points, avatar, games_completed FROM users ORDER BY total_points DESC LIMIT 3'
    ).fetchall()
    total_questions = conn.execute('SELECT COUNT(*) FROM questions').fetchone()[0]
    total_users = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    conn.close()

    return render_template(
        'index.html',
        categories=categories,
        top_players=top_players,
        total_questions=total_questions,
        total_users=total_users
    )

@app.route('/dashboard')
@login_required
def dashboard():
    user = get_current_user()
    conn = get_db_connection()

    # User's achievements
    achievements = conn.execute('''
    SELECT a.*, ua.unlocked_at
    FROM achievements a
    LEFT JOIN user_achievements ua ON a.id = ua.achievement_id AND ua.user_id = ?
    ORDER BY ua.unlocked_at DESC NULLS LAST, a.points_requirement ASC
    ''', (user['id'],)).fetchall()

    # Categories and progress
    categories = conn.execute('SELECT * FROM categories ORDER BY sort_order').fetchall()

    progress_rows = conn.execute('''
    SELECT category_slug, difficulty, high_score, times_played
    FROM user_progress
    WHERE user_id = ?
    ''', (user['id'],)).fetchall()

    progress_map = {}
    for p in progress_rows:
        key = f"{p['category_slug']}_{p['difficulty']}"
        progress_map[key] = p

    # Recent activity
    recent_sessions = conn.execute('''
    SELECT gs.*, c.name as category_name, c.icon as category_icon
    FROM game_sessions gs
    JOIN categories c ON gs.category_slug = c.slug
    WHERE gs.user_id = ?
    ORDER BY gs.completed_at DESC
    LIMIT 5
    ''', (user['id'],)).fetchall()

    # User ranking
    rank_row = conn.execute('''
    SELECT COUNT(*) + 1 as rank
    FROM users
    WHERE total_points > ?
    ''', (user['total_points'],)).fetchone()
    user_rank = rank_row['rank'] if rank_row else 1

    conn.close()

    level_info = calculate_level_info(user['total_points'])

    return render_template(
        'dashboard.html',
        user=user,
        level_info=level_info,
        achievements=achievements,
        categories=categories,
        progress_map=progress_map,
        recent_sessions=recent_sessions,
        user_rank=user_rank
    )

@app.route('/games')
def games_lobby():
    conn = get_db_connection()
    categories = conn.execute('SELECT * FROM categories ORDER BY sort_order').fetchall()
    
    user = get_current_user()
    user_points = user['total_points'] if user else 0
    level_info = calculate_level_info(user_points)

    # Fetch question count per category and difficulty
    counts_rows = conn.execute('''
    SELECT category_slug, difficulty, COUNT(*) as q_count
    FROM questions
    GROUP BY category_slug, difficulty
    ''').fetchall()

    counts = {}
    for r in counts_rows:
        key = f"{r['category_slug']}_{r['difficulty']}"
        counts[key] = r['q_count']

    conn.close()

    return render_template(
        'games.html',
        categories=categories,
        counts=counts,
        level_info=level_info
    )

@app.route('/game/<category_slug>/<difficulty>')
def play_game(category_slug, difficulty):
    difficulty = difficulty.lower()
    if difficulty not in ['easy', 'medium', 'hard']:
        flash('Invalid difficulty level requested.', 'danger')
        return redirect(url_for('games_lobby'))

    conn = get_db_connection()
    category = conn.execute(
        'SELECT * FROM categories WHERE slug = ?', (category_slug,)
    ).fetchone()

    if not category:
        conn.close()
        flash('Game category not found.', 'danger')
        return redirect(url_for('games_lobby'))

    user = get_current_user()
    user_points = user['total_points'] if user else 0
    level_info = calculate_level_info(user_points)

    # Check lock status
    if difficulty == 'medium' and not level_info['medium_unlocked']:
        conn.close()
        flash('Medium tier is locked! You need at least 150 points to unlock it.', 'warning')
        return redirect(url_for('games_lobby'))
    elif difficulty == 'hard' and not level_info['hard_unlocked']:
        conn.close()
        flash('Hard tier is locked! You need at least 400 points to unlock it.', 'warning')
        return redirect(url_for('games_lobby'))

    # Check question availability
    q_count = conn.execute(
        'SELECT COUNT(*) FROM questions WHERE category_slug = ? AND difficulty = ?',
        (category_slug, difficulty)
    ).fetchone()[0]
    conn.close()

    if q_count == 0:
        flash(f'No questions available yet for {category["name"]} at {difficulty.capitalize()} level.', 'info')
        return redirect(url_for('games_lobby'))

    return render_template(
        'quiz.html',
        category=category,
        difficulty=difficulty,
        q_count=q_count
    )

@app.route('/leaderboard')
def leaderboard():
    conn = get_db_connection()
    users = conn.execute('''
    SELECT id, username, total_points, games_completed, highest_streak, avatar, bio,
           (SELECT COUNT(*) FROM user_achievements ua WHERE ua.user_id = users.id) as badge_count
    FROM users
    ORDER BY total_points DESC, games_completed DESC
    LIMIT 50
    ''').fetchall()
    conn.close()

    leaderboard_data = []
    for rank, u in enumerate(users, start=1):
        lvl = calculate_level_info(u['total_points'])
        leaderboard_data.append({
            'rank': rank,
            'id': u['id'],
            'username': u['username'],
            'total_points': u['total_points'],
            'games_completed': u['games_completed'],
            'highest_streak': u['highest_streak'],
            'avatar': u['avatar'],
            'bio': u['bio'],
            'badge_count': u['badge_count'],
            'level_title': lvl['level_title'],
            'badge_icon': lvl['badge_icon']
        })

    return render_template('leaderboard.html', players=leaderboard_data)

@app.route('/profile')
@login_required
def profile():
    user = get_current_user()
    conn = get_db_connection()

    # All achievements with user unlocked state
    achievements = conn.execute('''
    SELECT a.*, ua.unlocked_at
    FROM achievements a
    LEFT JOIN user_achievements ua ON a.id = ua.achievement_id AND ua.user_id = ?
    ORDER BY a.points_requirement ASC
    ''', (user['id'],)).fetchall()

    # Match history
    sessions = conn.execute('''
    SELECT gs.*, c.name as category_name, c.icon as category_icon
    FROM game_sessions gs
    JOIN categories c ON gs.category_slug = c.slug
    WHERE gs.user_id = ?
    ORDER BY gs.completed_at DESC
    LIMIT 20
    ''', (user['id'],)).fetchall()

    # Category performance breakdown
    cat_stats = conn.execute('''
    SELECT c.name, c.icon, c.slug,
           COALESCE(SUM(up.times_played), 0) as total_plays,
           COALESCE(MAX(up.high_score), 0) as top_score
    FROM categories c
    LEFT JOIN user_progress up ON c.slug = up.category_slug AND up.user_id = ?
    GROUP BY c.slug
    ORDER BY c.sort_order
    ''', (user['id'],)).fetchall()

    conn.close()

    level_info = calculate_level_info(user['total_points'])

    return render_template(
        'profile.html',
        user=user,
        level_info=level_info,
        achievements=achievements,
        sessions=sessions,
        cat_stats=cat_stats
    )

@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    user = get_current_user()
    avatar = request.form.get('avatar', user['avatar'])
    bio = request.form.get('bio', user['bio']).strip()[:150]

    valid_avatars = ['coder1', 'coder2', 'coder3', 'coder4', 'coder5', 'admin_robot']
    if avatar not in valid_avatars:
        avatar = 'coder1'

    conn = get_db_connection()
    conn.execute(
        'UPDATE users SET avatar = ?, bio = ? WHERE id = ?',
        (avatar, bio, user['id'])
    )
    conn.commit()
    conn.close()

    flash('Profile updated successfully!', 'success')
    return redirect(url_for('profile'))

# -------------------------------------------------------------
# Admin Management Panel
# -------------------------------------------------------------

@app.route('/admin')
@admin_required
def admin_panel():
    conn = get_db_connection()
    
    questions = conn.execute('''
    SELECT q.*, c.name as category_name, c.icon as category_icon
    FROM questions q
    JOIN categories c ON q.category_slug = c.slug
    ORDER BY q.id DESC
    ''').fetchall()

    users = conn.execute('''
    SELECT id, username, email, total_points, games_completed, is_admin, created_at, avatar
    FROM users
    ORDER BY created_at DESC
    ''').fetchall()

    categories = conn.execute('SELECT * FROM categories ORDER BY sort_order').fetchall()

    # Aggregates
    stats = {
        'total_users': conn.execute('SELECT COUNT(*) FROM users').fetchone()[0],
        'total_questions': conn.execute('SELECT COUNT(*) FROM questions').fetchone()[0],
        'total_games': conn.execute('SELECT COUNT(*) FROM game_sessions').fetchone()[0],
        'total_xp': conn.execute('SELECT COALESCE(SUM(total_points), 0) FROM users').fetchone()[0]
    }

    conn.close()

    return render_template(
        'admin.html',
        questions=questions,
        users=users,
        categories=categories,
        stats=stats
    )

@app.route('/admin/question/add', methods=['POST'])
@admin_required
def admin_add_question():
    category_slug = request.form.get('category_slug')
    difficulty = request.form.get('difficulty')
    title = request.form.get('title')
    description = request.form.get('description')
    code_snippet = request.form.get('code_snippet')
    q_type = request.form.get('q_type', 'mcq')
    points = int(request.form.get('points', 20))
    time_limit = int(request.form.get('time_limit', 45))
    explanation = request.form.get('explanation')

    # Construct question_data & correct_answer based on type
    if q_type == 'mcq' or q_type == 'debug_fix':
        opts_raw = request.form.get('options', '')
        options = [o.strip() for o in opts_raw.split('\n') if o.strip()]
        question_data = json.dumps({"type": q_type, "options": options})
        correct_answer = request.form.get('correct_answer', '').strip()
    elif q_type == 'parsons':
        lines_raw = request.form.get('parsons_lines', '')
        lines = [l.strip() for l in lines_raw.split('\n') if l.strip()]
        scrambled = [{"id": f"l{i+1}", "text": text} for i, text in enumerate(lines)]
        # Correct order string comma separated or json array
        correct_order_ids = [item["id"] for item in scrambled]
        question_data = json.dumps({"type": "parsons", "scrambled_lines": scrambled})
        correct_answer = json.dumps(correct_order_ids)
    elif q_type == 'fill_blank':
        opts_raw = request.form.get('options', '')
        options_list = [o.strip() for o in opts_raw.split('\n') if o.strip()]
        options = [{"label": o, "value": o} for o in options_list]
        question_data = json.dumps({"type": "fill_blank", "options": options})
        correct_answer = request.form.get('correct_answer', '').strip()
    else:
        question_data = json.dumps({"type": "text"})
        correct_answer = request.form.get('correct_answer', '').strip()

    conn = get_db_connection()
    conn.execute('''
    INSERT INTO questions (
        category_slug, difficulty, title, description, code_snippet,
        question_data, correct_answer, explanation, points, time_limit
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        category_slug, difficulty, title, description,
        code_snippet if code_snippet and code_snippet.strip() else None,
        question_data, correct_answer, explanation, points, time_limit
    ))
    conn.commit()
    conn.close()

    flash('New question successfully added to the game repository!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/question/delete/<int:q_id>', methods=['POST'])
@admin_required
def admin_delete_question(q_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM questions WHERE id = ?', (q_id,))
    conn.commit()
    conn.close()
    flash('Question deleted successfully.', 'info')
    return redirect(url_for('admin_panel'))

@app.route('/admin/question/<int:q_id>/json')
@admin_required
def admin_get_question_json(q_id):
    conn = get_db_connection()
    q = conn.execute('SELECT * FROM questions WHERE id = ?', (q_id,)).fetchone()
    conn.close()
    if not q:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({
        'id': q['id'],
        'category_slug': q['category_slug'],
        'difficulty': q['difficulty'],
        'title': q['title'],
        'description': q['description'],
        'code_snippet': q['code_snippet'],
        'question_data': json.loads(q['question_data']),
        'correct_answer': q['correct_answer'],
        'explanation': q['explanation'],
        'points': q['points'],
        'time_limit': q['time_limit']
    })

@app.route('/admin/question/edit/<int:q_id>', methods=['POST'])
@admin_required
def admin_edit_question(q_id):
    category_slug = request.form.get('category_slug')
    difficulty = request.form.get('difficulty')
    title = request.form.get('title')
    description = request.form.get('description')
    code_snippet = request.form.get('code_snippet')
    points = int(request.form.get('points', 20))
    time_limit = int(request.form.get('time_limit', 45))
    explanation = request.form.get('explanation')
    correct_answer = request.form.get('correct_answer')

    conn = get_db_connection()
    conn.execute('''
    UPDATE questions
    SET category_slug = ?, difficulty = ?, title = ?, description = ?,
        code_snippet = ?, points = ?, time_limit = ?, explanation = ?, correct_answer = ?
    WHERE id = ?
    ''', (
        category_slug, difficulty, title, description,
        code_snippet if code_snippet and code_snippet.strip() else None,
        points, time_limit, explanation, correct_answer, q_id
    ))
    conn.commit()
    conn.close()

    flash(f'Question #{q_id} updated successfully!', 'success')
    return redirect(url_for('admin_panel'))

# -------------------------------------------------------------
# REST APIs for Gameplay & Dynamic Evaluation
# -------------------------------------------------------------

@app.route('/api/game/<category_slug>/<difficulty>', methods=['GET'])
def api_get_questions(category_slug, difficulty):
    conn = get_db_connection()
    rows = conn.execute('''
    SELECT id, category_slug, difficulty, title, description,
           code_snippet, question_data, points, time_limit
    FROM questions
    WHERE category_slug = ? AND difficulty = ?
    ORDER BY RANDOM()
    ''', (category_slug, difficulty.lower())).fetchall()
    conn.close()

    if not rows:
        return jsonify({'error': 'No questions found for this configuration'}), 404

    questions = []
    for r in rows:
        q_data = json.loads(r['question_data'])
        # For parsons, shuffle the lines so user receives them in scrambled order
        if q_data.get('type') == 'parsons' and 'scrambled_lines' in q_data:
            import random
            shuffled = list(q_data['scrambled_lines'])
            random.shuffle(shuffled)
            q_data['scrambled_lines'] = shuffled

        questions.append({
            'id': r['id'],
            'category_slug': r['category_slug'],
            'difficulty': r['difficulty'],
            'title': r['title'],
            'description': r['description'],
            'code_snippet': r['code_snippet'],
            'question_data': q_data,
            'points': r['points'],
            'time_limit': r['time_limit']
        })

    return jsonify({'questions': questions, 'count': len(questions)})

@app.route('/api/game/submit-answer', methods=['POST'])
def api_submit_answer():
    data = request.get_json() or {}
    question_id = data.get('question_id')
    user_answer = data.get('user_answer')
    time_taken = data.get('time_taken', 0)

    if not question_id:
        return jsonify({'error': 'Question ID is required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    question = cursor.execute(
        'SELECT * FROM questions WHERE id = ?', (question_id,)
    ).fetchone()

    if not question:
        conn.close()
        return jsonify({'error': 'Question not found'}), 404

    # Server-Side Verification: Compare user_answer to correct_answer
    is_correct = False
    raw_correct = question['correct_answer']

    q_data = json.loads(question['question_data'])
    q_type = q_data.get('type', 'mcq')

    if q_type == 'parsons':
        try:
            expected_list = json.loads(raw_correct)
            # user_answer can be a list or json string
            if isinstance(user_answer, str):
                user_list = json.loads(user_answer)
            else:
                user_list = user_answer
            is_correct = (user_list == expected_list)
        except Exception:
            is_correct = False
    else:
        # Standard string comparison (case-insensitive & stripped where appropriate)
        norm_expected = str(raw_correct).strip()
        norm_user = str(user_answer).strip() if user_answer is not None else ""
        is_correct = (norm_expected.lower() == norm_user.lower())

    points_awarded = 0
    new_total_points = 0
    current_streak = 0
    newly_unlocked = []

    user_id = session.get('user_id')

    if user_id:
        user = cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        if user:
            current_streak = user['streak']

            if is_correct:
                base_points = question['points']
                # Fast answer bonus: if answered in first half of time_limit, +5 bonus
                time_bonus = 5 if (time_taken > 0 and time_taken <= (question['time_limit'] / 2)) else 0
                streak_bonus = min(20, (current_streak * 2))  # Streak multiplier
                points_awarded = base_points + time_bonus + streak_bonus

                current_streak += 1
                highest_streak = max(user['highest_streak'], current_streak)
            else:
                # Wrong answer penalty: small deduction, but score never goes negative
                points_awarded = -5
                current_streak = 0
                highest_streak = user['highest_streak']

            # Update user stats in DB
            new_total_points = max(0, user['total_points'] + points_awarded)
            cursor.execute('''
            UPDATE users
            SET total_points = ?, streak = ?, highest_streak = ?
            WHERE id = ?
            ''', (new_total_points, current_streak, highest_streak, user_id))

            # Record answer in user_answers
            cursor.execute('''
            INSERT INTO user_answers (
                user_id, question_id, user_answer, is_correct, points_awarded
            ) VALUES (?, ?, ?, ?, ?)
            ''', (
                user_id, question_id,
                json.dumps(user_answer) if isinstance(user_answer, (list, dict)) else str(user_answer),
                1 if is_correct else 0,
                points_awarded
            ))

            # ---------------------------------------------
            # Check Achievement Triggers
            # ---------------------------------------------
            def check_and_award_badge(code):
                ach = cursor.execute('SELECT id, title, icon FROM achievements WHERE code = ?', (code,)).fetchone()
                if ach:
                    already = cursor.execute(
                        'SELECT id FROM user_achievements WHERE user_id = ? AND achievement_id = ?',
                        (user_id, ach['id'])
                    ).fetchone()
                    if not already:
                        cursor.execute(
                            'INSERT INTO user_achievements (user_id, achievement_id) VALUES (?, ?)',
                            (user_id, ach['id'])
                        )
                        newly_unlocked.append({
                            'code': code,
                            'title': ach['title'],
                            'icon': ach['icon']
                        })

            if is_correct:
                check_and_award_badge('first_code')
                if time_taken > 0 and time_taken <= 10:
                    check_and_award_badge('speed_coder')
                if current_streak >= 3:
                    check_and_award_badge('streak_3')
                if current_streak >= 5:
                    check_and_award_badge('streak_5')
                if q_type == 'parsons':
                    check_and_award_badge('puzzle_master')
                if question['category_slug'] in ['find_error', 'debugging']:
                    check_and_award_badge('bug_hunter')

            # Points milestone badges
            if new_total_points >= 100:
                check_and_award_badge('century_club')
            if new_total_points >= 150:
                check_and_award_badge('level_unlocked_medium')
            if new_total_points >= 250:
                check_and_award_badge('half_thousand')
            if new_total_points >= 400:
                check_and_award_badge('level_unlocked_hard')
            if new_total_points >= 500:
                check_and_award_badge('grandmaster')

            conn.commit()

    conn.close()

    return jsonify({
        'is_correct': is_correct,
        'points_awarded': points_awarded,
        'new_total_points': new_total_points,
        'streak': current_streak,
        'correct_answer': raw_correct,
        'explanation': question['explanation'],
        'newly_unlocked_achievements': newly_unlocked
    })

@app.route('/api/game/complete-session', methods=['POST'])
def api_complete_session():
    data = request.get_json() or {}
    category_slug = data.get('category_slug')
    difficulty = data.get('difficulty')
    score_earned = data.get('score_earned', 0)
    questions_count = data.get('questions_count', 0)
    correct_count = data.get('correct_count', 0)
    time_taken_seconds = data.get('time_taken_seconds', 0)

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'status': 'guest_mode', 'message': 'Log in to save high scores!'})

    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Insert session record
    cursor.execute('''
    INSERT INTO game_sessions (
        user_id, category_slug, difficulty, score_earned,
        questions_count, correct_count, time_taken_seconds
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id, category_slug, difficulty, score_earned,
        questions_count, correct_count, time_taken_seconds
    ))

    # 2. Update user completed games count
    cursor.execute('''
    UPDATE users SET games_completed = games_completed + 1 WHERE id = ?
    ''', (user_id,))

    # 3. Update category progress & high score
    cursor.execute('''
    INSERT INTO user_progress (user_id, category_slug, difficulty, high_score, times_played, last_played)
    VALUES (?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
    ON CONFLICT(user_id, category_slug, difficulty) DO UPDATE SET
        high_score = MAX(high_score, ?),
        times_played = times_played + 1,
        last_played = CURRENT_TIMESTAMP
    ''', (user_id, category_slug, difficulty, score_earned, score_earned))

    # 4. Check for veteran achievement (10 games completed)
    games_completed = cursor.execute(
        'SELECT games_completed FROM users WHERE id = ?', (user_id,)
    ).fetchone()[0]

    new_badges = []
    if games_completed >= 10:
        ach = cursor.execute("SELECT id, title, icon FROM achievements WHERE code = 'game_veteran'").fetchone()
        if ach:
            already = cursor.execute(
                'SELECT id FROM user_achievements WHERE user_id = ? AND achievement_id = ?',
                (user_id, ach['id'])
            ).fetchone()
            if not already:
                cursor.execute(
                    'INSERT INTO user_achievements (user_id, achievement_id) VALUES (?, ?)',
                    (user_id, ach['id'])
                )
                new_badges.append({'code': 'game_veteran', 'title': ach['title'], 'icon': ach['icon']})

    conn.commit()
    conn.close()

    return jsonify({
        'status': 'success',
        'games_completed': games_completed,
        'new_badges': new_badges
    })

# -------------------------------------------------------------
# Error Handlers
# -------------------------------------------------------------

@app.errorhandler(404)
def page_not_found(e):
    return render_template('base.html', not_found=True), 404

@app.errorhandler(500)
def internal_server_error(e):
    return "<h3>Internal Server Error</h3><p>Something went wrong on the server.</p>", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"[SERVER] Starting Programming Learning Game on http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
