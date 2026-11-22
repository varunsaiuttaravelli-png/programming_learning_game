import sqlite3
import os
import json
from werkzeug.security import generate_password_hash

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        total_points INTEGER DEFAULT 0,
        games_completed INTEGER DEFAULT 0,
        streak INTEGER DEFAULT 0,
        highest_streak INTEGER DEFAULT 0,
        is_admin INTEGER DEFAULT 0,
        avatar TEXT DEFAULT 'coder1',
        bio TEXT DEFAULT 'Eager code explorer ready to conquer Python!',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Categories Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slug TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        icon TEXT NOT NULL,
        color TEXT NOT NULL,
        sort_order INTEGER DEFAULT 0
    )
    ''')

    # Questions Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_slug TEXT NOT NULL,
        difficulty TEXT NOT NULL, -- 'easy', 'medium', 'hard'
        title TEXT NOT NULL,
        description TEXT,
        code_snippet TEXT,
        question_data TEXT NOT NULL, -- JSON string
        correct_answer TEXT NOT NULL, -- JSON string or plain text
        explanation TEXT,
        points INTEGER DEFAULT 20,
        time_limit INTEGER DEFAULT 45,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_slug) REFERENCES categories (slug) ON DELETE CASCADE
    )
    ''')

    # Game Sessions Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS game_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        category_slug TEXT NOT NULL,
        difficulty TEXT NOT NULL,
        score_earned INTEGER DEFAULT 0,
        questions_count INTEGER DEFAULT 0,
        correct_count INTEGER DEFAULT 0,
        time_taken_seconds INTEGER DEFAULT 0,
        completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    )
    ''')

    # User Answers Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        user_id INTEGER NOT NULL,
        question_id INTEGER NOT NULL,
        user_answer TEXT,
        is_correct INTEGER DEFAULT 0,
        points_awarded INTEGER DEFAULT 0,
        answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (question_id) REFERENCES questions (id) ON DELETE CASCADE
    )
    ''')

    # Achievements Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS achievements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        icon TEXT NOT NULL,
        badge_color TEXT DEFAULT '#6366f1',
        points_requirement INTEGER DEFAULT 0
    )
    ''')

    # User Achievements Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_achievements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        achievement_id INTEGER NOT NULL,
        unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, achievement_id),
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (achievement_id) REFERENCES achievements (id) ON DELETE CASCADE
    )
    ''')

    # User Progress Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        category_slug TEXT NOT NULL,
        difficulty TEXT NOT NULL,
        high_score INTEGER DEFAULT 0,
        times_played INTEGER DEFAULT 0,
        last_played TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, category_slug, difficulty),
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    )
    ''')

    conn.commit()
    seed_initial_data(conn)
    conn.close()

def seed_initial_data(conn):
    cursor = conn.cursor()

    # 1. Seed Categories
    categories = [
        ('guess_output', 'Guess the Output', 'Predict the exact output of Python code snippets.', '💡', '#8b5cf6', 1),
        ('find_error', 'Find the Error', 'Spot bugs, syntax flaws, and runtime traps in code.', '🔍', '#ef4444', 2),
        ('code_quiz', 'Code Quiz', 'Test your programming fundamentals with rapid-fire questions.', '⚡', '#3b82f6', 3),
        ('arrange_code', 'Arrange the Code', 'Reorder scrambled lines into functional Python programs.', '🧩', '#10b981', 4),
        ('debugging', 'Debugging Challenge', 'Diagnose broken code and supply the exact code fix.', '🛠️', '#f59e0b', 5),
        ('fill_blanks', 'Fill in the Blanks', 'Complete missing Python keywords, operators, and methods.', '✏️', '#ec4899', 6)
    ]
    cursor.executemany('''
    INSERT OR IGNORE INTO categories (slug, name, description, icon, color, sort_order)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', categories)

    # 2. Seed Achievements
    achievements = [
        ('first_code', 'First Code', 'Answer your very first question correctly!', '🌱', '#10b981', 10),
        ('speed_coder', 'Speed Demon', 'Answer a question in under 10 seconds.', '⚡', '#f59e0b', 20),
        ('streak_3', 'On Fire', 'Achieve a winning streak of 3 correct answers.', '🔥', '#ef4444', 30),
        ('streak_5', 'Unstoppable', 'Achieve a 5-question winning streak.', '💥', '#ec4899', 50),
        ('puzzle_master', 'Code Architect', 'Successfully arrange code in the correct sequence.', '🧩', '#8b5cf6', 30),
        ('bug_hunter', 'Bug Hunter', 'Correctly identify or fix errors in debugging challenges.', '🐞', '#06b6d4', 30),
        ('century_club', 'Century Coder', 'Reach 100 total XP points.', '🥉', '#d97706', 100),
        ('half_thousand', 'Silver Specialist', 'Reach 250 total XP points.', '🥈', '#64748b', 250),
        ('grandmaster', 'Python Champion', 'Reach 500 total XP points.', '🥇', '#eab308', 500),
        ('level_unlocked_medium', 'Level Up: Medium', 'Unlock the Medium difficulty tier.', '🚀', '#3b82f6', 150),
        ('level_unlocked_hard', 'Level Up: Hard', 'Unlock the Hard difficulty tier.', '👑', '#a855f7', 400),
        ('game_veteran', 'Game Veteran', 'Complete 10 game sessions.', '🎖️', '#14b8a6', 200)
    ]
    cursor.executemany('''
    INSERT OR IGNORE INTO achievements (code, title, description, icon, badge_color, points_requirement)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', achievements)

    # 3. Seed Users (Admin & Demo Student)
    admin_pw = generate_password_hash('AdminPass123!')
    student_pw = generate_password_hash('Student123!')

    cursor.execute('''
    INSERT OR IGNORE INTO users (id, username, email, password_hash, total_points, games_completed, streak, highest_streak, is_admin, avatar, bio)
    VALUES (1, 'admin', 'admin@codequest.dev', ?, 750, 15, 6, 8, 1, 'admin_robot', 'Platform Administrator & Master Instructor')
    ''', (admin_pw,))

    cursor.execute('''
    INSERT OR IGNORE INTO users (id, username, email, password_hash, total_points, games_completed, streak, highest_streak, is_admin, avatar, bio)
    VALUES (2, 'pycoder', 'student@codequest.dev', ?, 180, 6, 3, 4, 0, 'coder1', 'Curious Python apprentice leveling up daily!')
    ''', (student_pw,))

    # Give demo achievements to student
    cursor.execute('INSERT OR IGNORE INTO user_achievements (user_id, achievement_id) VALUES (2, 1)')
    cursor.execute('INSERT OR IGNORE INTO user_achievements (user_id, achievement_id) VALUES (2, 3)')
    cursor.execute('INSERT OR IGNORE INTO user_achievements (user_id, achievement_id) VALUES (2, 7)')
    cursor.execute('INSERT OR IGNORE INTO user_achievements (user_id, achievement_id) VALUES (2, 10)')

    # Check if questions already exist
    cursor.execute("SELECT COUNT(*) FROM questions")
    count = cursor.fetchone()[0]
    if count == 0:
        seed_questions(cursor)

    conn.commit()

def seed_questions(cursor):
    questions_data = [
        # ==========================================
        # 1. GUESS THE OUTPUT (Easy, Medium, Hard)
        # ==========================================
        {
            "category_slug": "guess_output",
            "difficulty": "easy",
            "title": "String Multiplication",
            "description": "What will be printed when repeating a string with the multiplication operator?",
            "code_snippet": "word = 'Go!'\nprint(word * 3)",
            "question_data": json.dumps({
                "type": "mcq",
                "options": ["Go!Go!Go!", "Go! 3", "Error", "Go! * 3"]
            }),
            "correct_answer": "Go!Go!Go!",
            "explanation": "In Python, multiplying a string by an integer n repeats the string n times without spaces.",
            "points": 20,
            "time_limit": 30
        },
        {
            "category_slug": "guess_output",
            "difficulty": "easy",
            "title": "List Index Slicing",
            "description": "Evaluate the output of this Python list slice.",
            "code_snippet": "fruits = ['apple', 'banana', 'cherry', 'date']\nprint(fruits[1:3])",
            "question_data": json.dumps({
                "type": "mcq",
                "options": ["['banana', 'cherry']", "['apple', 'banana']", "['banana', 'cherry', 'date']", "['cherry', 'date']"]
            }),
            "correct_answer": "['banana', 'cherry']",
            "explanation": "Slicing `[start:stop]` includes the element at start index (1 -> 'banana') and excludes the stop index (3 -> excludes 'date').",
            "points": 20,
            "time_limit": 30
        },
        {
            "category_slug": "guess_output",
            "difficulty": "easy",
            "title": "Integer Division Operator",
            "description": "What is the result of using the floor division operator `//` in Python?",
            "code_snippet": "result = 19 // 4\nprint(result)",
            "question_data": json.dumps({
                "type": "mcq",
                "options": ["4", "4.75", "5", "3"]
            }),
            "correct_answer": "4",
            "explanation": "`//` performs floor division, rounding down to the nearest integer. 19 / 4 is 4.75, so floor division yields 4.",
            "points": 20,
            "time_limit": 30
        },
        {
            "category_slug": "guess_output",
            "difficulty": "medium",
            "title": "List Comprehension Filter",
            "description": "What will this list comprehension produce?",
            "code_snippet": "nums = [1, 2, 3, 4, 5, 6]\nevens_squared = [x**2 for x in nums if x % 2 == 0]\nprint(evens_squared)",
            "question_data": json.dumps({
                "type": "mcq",
                "options": ["[4, 16, 36]", "[1, 9, 25]", "[2, 4, 6]", "[4, 8, 12]"]
            }),
            "correct_answer": "[4, 16, 36]",
            "explanation": "The condition `x % 2 == 0` filters even numbers (2, 4, 6), and `x**2` squares them: 2^2=4, 4^2=16, 6^2=36.",
            "points": 35,
            "time_limit": 40
        },
        {
            "category_slug": "guess_output",
            "difficulty": "medium",
            "title": "Dictionary `.get()` Fallback",
            "description": "What does the dictionary `.get()` method output when a key is absent?",
            "code_snippet": "hero = {'name': 'Cipher', 'level': 42}\nscore = hero.get('score', 100)\nprint(score)",
            "question_data": json.dumps({
                "type": "mcq",
                "options": ["100", "None", "KeyError", "42"]
            }),
            "correct_answer": "100",
            "explanation": "`dict.get(key, default)` returns the default value if the key does not exist, rather than raising a KeyError.",
            "points": 35,
            "time_limit": 35
        },
        {
            "category_slug": "guess_output",
            "difficulty": "hard",
            "title": "Default Mutable Argument Trap",
            "description": "What happens when using a mutable list as a default parameter in Python?",
            "code_snippet": "def append_item(item, items=[]):\n    items.append(item)\n    return items\n\nprint(append_item('A'))\nprint(append_item('B'))",
            "question_data": json.dumps({
                "type": "mcq",
                "options": ["['A'] then ['A', 'B']", "['A'] then ['B']", "['B'] then ['A', 'B']", "TypeError"]
            }),
            "correct_answer": "['A'] then ['A', 'B']",
            "explanation": "Python default arguments are evaluated once when the function is defined. The list `items` persists across calls!",
            "points": 50,
            "time_limit": 45
        },
        {
            "category_slug": "guess_output",
            "difficulty": "hard",
            "title": "Recursion Return Value",
            "description": "Trace the recursive execution of this function.",
            "code_snippet": "def mystery(n):\n    if n <= 1:\n        return 1\n    return n * mystery(n - 2)\n\nprint(mystery(5))",
            "question_data": json.dumps({
                "type": "mcq",
                "options": ["15", "120", "5", "8"]
            }),
            "correct_answer": "15",
            "explanation": "mystery(5) = 5 * mystery(3) = 5 * (3 * mystery(1)) = 5 * 3 * 1 = 15.",
            "points": 50,
            "time_limit": 45
        },

        # ==========================================
        # 2. FIND THE ERROR (Easy, Medium, Hard)
        # ==========================================
        {
            "category_slug": "find_error",
            "difficulty": "easy",
            "title": "Missing Colon in If Statement",
            "description": "Identify the syntax error in this basic conditional snippet.",
            "code_snippet": "score = 85\nif score >= 50\n    print('You passed!')",
            "question_data": json.dumps({
                "type": "error_spot",
                "line_count": 3,
                "options": [
                    "Line 2: Missing colon ':' at the end of the if statement",
                    "Line 1: Variables cannot be assigned integer values directly",
                    "Line 3: print must use single quotes inside brackets without indentation",
                    "Line 2: The comparison operator '>=' is invalid in Python"
                ]
            }),
            "correct_answer": "Line 2: Missing colon ':' at the end of the if statement",
            "explanation": "In Python, control flow statements like `if`, `for`, `while`, `def`, and `class` must end with a colon `:`. ",
            "points": 20,
            "time_limit": 30
        },
        {
            "category_slug": "find_error",
            "difficulty": "easy",
            "title": "String Concatenation Type Mismatch",
            "description": "What error occurs when running this code?",
            "code_snippet": "age = 15\nmessage = 'I am ' + age + ' years old'\nprint(message)",
            "question_data": json.dumps({
                "type": "error_spot",
                "line_count": 3,
                "options": [
                    "TypeError: can only concatenate str (not 'int') to str",
                    "SyntaxError: invalid syntax in assignment",
                    "ValueError: age cannot be inside message",
                    "NameError: name 'age' is not defined"
                ]
            }),
            "correct_answer": "TypeError: can only concatenate str (not 'int') to str",
            "explanation": "You cannot concatenate a string and an integer directly using `+`. You must convert with `str(age)` or use f-strings `f'I am {age} years old'`.",
            "points": 20,
            "time_limit": 30
        },
        {
            "category_slug": "find_error",
            "difficulty": "medium",
            "title": "Index Out of Bounds in Loop",
            "description": "Find the subtle off-by-one bug causing a runtime crash.",
            "code_snippet": "colors = ['red', 'green', 'blue']\nfor i in range(len(colors) + 1):\n    print(colors[i])",
            "question_data": json.dumps({
                "type": "error_spot",
                "line_count": 3,
                "options": [
                    "IndexError: list index out of range when i reaches 3",
                    "TypeError: len() cannot be passed to range()",
                    "SyntaxError: invalid for loop syntax",
                    "ValueError: 'red' is not an integer"
                ]
            }),
            "correct_answer": "IndexError: list index out of range when i reaches 3",
            "explanation": "The list has 3 items (indices 0, 1, 2). `range(len(colors) + 1)` loops up to index 3, which doesn't exist, triggering `IndexError`.",
            "points": 35,
            "time_limit": 40
        },
        {
            "category_slug": "find_error",
            "difficulty": "medium",
            "title": "Assignment Instead of Equality Check",
            "description": "What is wrong with the condition in this function?",
            "code_snippet": "def check_status(is_online):\n    if is_online = True:\n        return 'Active'\n    return 'Offline'",
            "question_data": json.dumps({
                "type": "error_spot",
                "line_count": 5,
                "options": [
                    "SyntaxError: invalid syntax because '=' is used instead of '=='",
                    "TypeError: is_online cannot be compared to boolean",
                    "NameError: 'Active' is not defined",
                    "IndentationError: return statement is not indented properly"
                ]
            }),
            "correct_answer": "SyntaxError: invalid syntax because '=' is used instead of '=='",
            "explanation": "A single `=` is an assignment operator and cannot be used in a conditional check; Python expects `==` or simply `if is_online:`.",
            "points": 35,
            "time_limit": 35
        },
        {
            "category_slug": "find_error",
            "difficulty": "hard",
            "title": "UnboundLocalError with Global Scope",
            "description": "Why does this function raise an error upon execution?",
            "code_snippet": "counter = 0\n\ndef increment():\n    counter += 1\n    return counter\n\nincrement()",
            "question_data": json.dumps({
                "type": "error_spot",
                "line_count": 7,
                "options": [
                    "UnboundLocalError: local variable 'counter' referenced before assignment",
                    "SyntaxError: += cannot be used inside functions",
                    "TypeError: counter is an immutable integer",
                    "ZeroDivisionError: counter started at zero"
                ]
            }),
            "correct_answer": "UnboundLocalError: local variable 'counter' referenced before assignment",
            "explanation": "Assigning to `counter` inside the function marks it as a local variable. Since it hasn't been defined locally yet, reading it before assignment raises `UnboundLocalError`. Use `global counter` to fix it.",
            "points": 50,
            "time_limit": 45
        },
        {
            "category_slug": "find_error",
            "difficulty": "hard",
            "title": "Mutating a List During Iteration",
            "description": "What problem occurs when modifying a list while iterating over it?",
            "code_snippet": "numbers = [1, 2, 3, 4, 5]\nfor num in numbers:\n    if num % 2 == 0:\n        numbers.remove(num)\nprint(numbers)",
            "question_data": json.dumps({
                "type": "error_spot",
                "line_count": 5,
                "options": [
                    "Logic Bug: Items are skipped because iteration index shifts when items are removed",
                    "SyntaxError: remove() method cannot be called in for loop",
                    "MemoryError: infinite loop created",
                    "ValueError: num is not in numbers"
                ]
            }),
            "correct_answer": "Logic Bug: Items are skipped because iteration index shifts when items are removed",
            "explanation": "Modifying a collection while iterating over it causes the internal index pointer to shift, skipping elements. A list comprehension or iterating over a copy `numbers[:]` is required.",
            "points": 50,
            "time_limit": 45
        },

        # ==========================================
        # 3. CODE QUIZ (Easy, Medium, Hard)
        # ==========================================
        {
            "category_slug": "code_quiz",
            "difficulty": "easy",
            "title": "Function Definition Keyword",
            "description": "Which keyword is used to declare a function in Python?",
            "code_snippet": None,
            "question_data": json.dumps({
                "type": "mcq",
                "options": ["def", "func", "function", "define"]
            }),
            "correct_answer": "def",
            "explanation": "In Python, the `def` keyword (short for define) is used to create user-defined functions.",
            "points": 20,
            "time_limit": 25
        },
        {
            "category_slug": "code_quiz",
            "difficulty": "easy",
            "title": "Immutable Data Types",
            "description": "Which of the following standard Python data types is IMMUTABLE (cannot be changed after creation)?",
            "code_snippet": None,
            "question_data": json.dumps({
                "type": "mcq",
                "options": ["tuple", "list", "dict", "set"]
            }),
            "correct_answer": "tuple",
            "explanation": "Tuples are immutable sequences in Python. Lists, dictionaries, and sets are mutable.",
            "points": 20,
            "time_limit": 25
        },
        {
            "category_slug": "code_quiz",
            "difficulty": "easy",
            "title": "Boolean Evaluation",
            "description": "What does `bool([])` evaluate to in Python?",
            "code_snippet": "print(bool([]))",
            "question_data": json.dumps({
                "type": "mcq",
                "options": ["False", "True", "None", "Error"]
            }),
            "correct_answer": "False",
            "explanation": "Empty collections (empty list `[]`, empty string `\"\"`, empty tuple `()`, empty dict `{}`) have a 'falsy' truth value in Python.",
            "points": 20,
            "time_limit": 25
        },
        {
            "category_slug": "code_quiz",
            "difficulty": "medium",
            "title": "List Method Distinction",
            "description": "What is the key difference between `list.append(x)` and `list.extend(x)`?",
            "code_snippet": None,
            "question_data": json.dumps({
                "type": "mcq",
                "options": [
                    "append adds its argument as a single element; extend iterates over its argument adding each item",
                    "append only works on numbers; extend only works on strings",
                    "extend modifies the list in place, while append returns a new copy",
                    "There is no difference; they are aliases"
                ]
            }),
            "correct_answer": "append adds its argument as a single element; extend iterates over its argument adding each item",
            "explanation": "If you pass `[1, 2]` to `.append()`, you get a nested list `[[1, 2]]`. With `.extend()`, `1` and `2` are added individually.",
            "points": 35,
            "time_limit": 35
        },
        {
            "category_slug": "code_quiz",
            "difficulty": "medium",
            "title": "Variable Argument Packing",
            "description": "What data type does `*args` unpack into inside a Python function?",
            "code_snippet": "def demo(*args):\n    print(type(args))",
            "question_data": json.dumps({
                "type": "mcq",
                "options": ["tuple", "list", "dict", "set"]
            }),
            "correct_answer": "tuple",
            "explanation": "Positional arguments captured by `*args` are gathered into an immutable tuple.",
            "points": 35,
            "time_limit": 30
        },
        {
            "category_slug": "code_quiz",
            "difficulty": "hard",
            "title": "Dictionary Average Lookup Complexity",
            "description": "What is the average time complexity for searching a key in a Python dictionary (hash table)?",
            "code_snippet": None,
            "question_data": json.dumps({
                "type": "mcq",
                "options": ["O(1)", "O(n)", "O(log n)", "O(n log n)"]
            }),
            "correct_answer": "O(1)",
            "explanation": "Python dictionaries are implemented using hash tables, giving them an average case lookup time complexity of O(1) (constant time).",
            "points": 50,
            "time_limit": 35
        },
        {
            "category_slug": "code_quiz",
            "difficulty": "hard",
            "title": "Python Context Managers",
            "description": "Which two special dunder methods must a class implement to support the `with` statement?",
            "code_snippet": None,
            "question_data": json.dumps({
                "type": "mcq",
                "options": [
                    "__enter__ and __exit__",
                    "__start__ and __stop__",
                    "__open__ and __close__",
                    "__init__ and __del__"
                ]
            }),
            "correct_answer": "__enter__ and __exit__",
            "explanation": "The Context Manager protocol in Python requires the `__enter__()` and `__exit__()` magic methods.",
            "points": 50,
            "time_limit": 35
        },

        # ==========================================
        # 4. ARRANGE THE CODE (Parsons puzzles)
        # ==========================================
        {
            "category_slug": "arrange_code",
            "difficulty": "easy",
            "title": "Print Even Numbers",
            "description": "Arrange the scrambled lines to create a program that prints even numbers from 1 to 10.",
            "code_snippet": None,
            "question_data": json.dumps({
                "type": "parsons",
                "scrambled_lines": [
                    {"id": "l1", "text": "    print(num)"},
                    {"id": "l2", "text": "for num in range(1, 11):"},
                    {"id": "l3", "text": "        print('Done!')"},
                    {"id": "l4", "text": "    if num % 2 == 0:"}
                ]
            }),
            "correct_answer": json.dumps(["l2", "l4", "l1", "l3"]),
            "explanation": "The loop iterates through 1 to 10 (`l2`), checks if the number is even (`l4`), prints the even number (`l1`), and prints 'Done!' (`l3`).",
            "points": 20,
            "time_limit": 60
        },
        {
            "category_slug": "arrange_code",
            "difficulty": "easy",
            "title": "Calculate List Sum",
            "description": "Arrange the lines in order to compute the sum of items in a list without using the built-in `sum()` function.",
            "code_snippet": None,
            "question_data": json.dumps({
                "type": "parsons",
                "scrambled_lines": [
                    {"id": "l1", "text": "print('Total:', total)"},
                    {"id": "l2", "text": "numbers = [10, 20, 30, 40]"},
                    {"id": "l3", "text": "    total += n"},
                    {"id": "l4", "text": "total = 0"},
                    {"id": "l5", "text": "for n in numbers:"}
                ]
            }),
            "correct_answer": json.dumps(["l2", "l4", "l5", "l3", "l1"]),
            "explanation": "Define numbers (`l2`), initialize accumulator total to 0 (`l4`), loop through each element (`l5`), add it (`l3`), and finally print the result (`l1`).",
            "points": 20,
            "time_limit": 60
        },
        {
            "category_slug": "arrange_code",
            "difficulty": "medium",
            "title": "Palindrome String Checker",
            "description": "Arrange the code blocks to build a clean palindrome testing function.",
            "code_snippet": None,
            "question_data": json.dumps({
                "type": "parsons",
                "scrambled_lines": [
                    {"id": "l1", "text": "    return clean_text == clean_text[::-1]"},
                    {"id": "l2", "text": "def is_palindrome(text):"},
                    {"id": "l3", "text": "print(is_palindrome('Racecar'))"},
                    {"id": "l4", "text": "    clean_text = text.lower()"}
                ]
            }),
            "correct_answer": json.dumps(["l2", "l4", "l1", "l3"]),
            "explanation": "Define the function `is_palindrome` (`l2`), convert text to lowercase (`l4`), compare it to its reversed slice (`l1`), and test it with 'Racecar' (`l3`).",
            "points": 35,
            "time_limit": 70
        },
        {
            "category_slug": "arrange_code",
            "difficulty": "medium",
            "title": "Factorial with While Loop",
            "description": "Construct a function calculating factorial using an iterative approach.",
            "code_snippet": None,
            "question_data": json.dumps({
                "type": "parsons",
                "scrambled_lines": [
                    {"id": "l1", "text": "        result *= n"},
                    {"id": "l2", "text": "def factorial(n):"},
                    {"id": "l3", "text": "        n -= 1"},
                    {"id": "l4", "text": "    result = 1"},
                    {"id": "l5", "text": "    while n > 1:"},
                    {"id": "l6", "text": "    return result"}
                ]
            }),
            "correct_answer": json.dumps(["l2", "l4", "l5", "l1", "l3", "l6"]),
            "explanation": "Function header (`l2`) -> init `result = 1` (`l4`) -> while condition (`l5`) -> multiply (`l1`) -> decrement `n` (`l3`) -> return `result` (`l6`).",
            "points": 35,
            "time_limit": 75
        },
        {
            "category_slug": "arrange_code",
            "difficulty": "hard",
            "title": "Binary Search Algorithm",
            "description": "Assemble the core binary search loop in the correct logical execution sequence.",
            "code_snippet": None,
            "question_data": json.dumps({
                "type": "parsons",
                "scrambled_lines": [
                    {"id": "l1", "text": "        elif arr[mid] < target: low = mid + 1"},
                    {"id": "l2", "text": "def binary_search(arr, target):"},
                    {"id": "l3", "text": "        mid = (low + high) // 2"},
                    {"id": "l4", "text": "    low, high = 0, len(arr) - 1"},
                    {"id": "l5", "text": "    while low <= high:"},
                    {"id": "l6", "text": "        if arr[mid] == target: return mid"},
                    {"id": "l7", "text": "        else: high = mid - 1"},
                    {"id": "l8", "text": "    return -1"}
                ]
            }),
            "correct_answer": json.dumps(["l2", "l4", "l5", "l3", "l6", "l1", "l7", "l8"]),
            "explanation": "Header (`l2`) -> bounds init (`l4`) -> while loop (`l5`) -> mid calculation (`l3`) -> found check (`l6`) -> search right half (`l1`) -> search left half (`l7`) -> return -1 not found (`l8`).",
            "points": 50,
            "time_limit": 90
        },

        # ==========================================
        # 5. DEBUGGING CHALLENGE (Easy, Medium, Hard)
        # ==========================================
        {
            "category_slug": "debugging",
            "difficulty": "easy",
            "title": "Fix Area Calculator",
            "description": "The function below produces wrong results because of improper arithmetic or parameter usage. Choose the correct fix.",
            "code_snippet": "def calculate_rectangle_area(width, height):\n    # Bug: adding instead of multiplying\n    area = width + height\n    return area",
            "question_data": json.dumps({
                "type": "debug_fix",
                "options": [
                    "Change 'area = width + height' to 'area = width * height'",
                    "Change 'return area' to 'return width'",
                    "Change parameters to '(width, height = 0)'",
                    "Change 'area = width + height' to 'area = (width + height) * 2'"
                ]
            }),
            "correct_answer": "Change 'area = width + height' to 'area = width * height'",
            "explanation": "The area of a rectangle is width multiplied by height (`width * height`). Adding them computes half the perimeter.",
            "points": 20,
            "time_limit": 35
        },
        {
            "category_slug": "debugging",
            "difficulty": "easy",
            "title": "Fix Vowel Counter",
            "description": "This function is supposed to count vowels, but case sensitivity causes it to miss capital vowels. How should it be fixed?",
            "code_snippet": "def count_vowels(word):\n    vowels = 'aeiou'\n    count = 0\n    for char in word:\n        if char in vowels:\n            count += 1\n    return count",
            "question_data": json.dumps({
                "type": "debug_fix",
                "options": [
                    "Change 'for char in word:' to 'for char in word.lower():'",
                    "Change 'count = 0' to 'count = 1'",
                    "Change 'char in vowels' to 'char == vowels'",
                    "Remove the return statement"
                ]
            }),
            "correct_answer": "Change 'for char in word:' to 'for char in word.lower():'",
            "explanation": "Converting the input word or each character to lowercase ensures uppercase vowels ('A', 'E', 'I', 'O', 'U') match against `'aeiou'`.",
            "points": 20,
            "time_limit": 35
        },
        {
            "category_slug": "debugging",
            "difficulty": "medium",
            "title": "Fix Max Finder with Negative Numbers",
            "description": "This function fails when given a list containing only negative numbers (e.g. `[-5, -12, -3]`). What is the bug?",
            "code_snippet": "def find_max(numbers):\n    max_val = 0\n    for num in numbers:\n        if num > max_val:\n            max_val = num\n    return max_val",
            "question_data": json.dumps({
                "type": "debug_fix",
                "options": [
                    "Initialize max_val = numbers[0] instead of 0",
                    "Change 'num > max_val' to 'num < max_val'",
                    "Add 'max_val += num' inside loop",
                    "Sort the list in reverse order"
                ]
            }),
            "correct_answer": "Initialize max_val = numbers[0] instead of 0",
            "explanation": "Initializing with 0 means any negative maximum (like -3) will never be greater than 0, wrongly returning 0. Starting with `numbers[0]` (or `-float('inf')`) fixes this.",
            "points": 35,
            "time_limit": 40
        },
        {
            "category_slug": "debugging",
            "difficulty": "medium",
            "title": "Fix Frequency Counter Dictionary",
            "description": "The function crashes with `KeyError` when an item is encountered for the first time. What is the proper fix?",
            "code_snippet": "def count_frequency(items):\n    freq = {}\n    for item in items:\n        freq[item] += 1\n    return freq",
            "question_data": json.dumps({
                "type": "debug_fix",
                "options": [
                    "Use freq[item] = freq.get(item, 0) + 1",
                    "Initialize freq = [] instead of {}",
                    "Change 'for item in items:' to 'for item in range(items):'",
                    "Add 'freq.clear()' before loop"
                ]
            }),
            "correct_answer": "Use freq[item] = freq.get(item, 0) + 1",
            "explanation": "Accessing `freq[item]` before the key exists triggers a `KeyError`. Using `freq.get(item, 0)` provides a safe default value of 0.",
            "points": 35,
            "time_limit": 40
        },
        {
            "category_slug": "debugging",
            "difficulty": "hard",
            "title": "Fix Recursive Fibonacci Infinite Recursion",
            "description": "This recursive Fibonacci implementation causes `RecursionError: maximum recursion depth exceeded`. What is missing?",
            "code_snippet": "def fib(n):\n    if n == 1:\n        return 1\n    return fib(n - 1) + fib(n - 2)",
            "question_data": json.dumps({
                "type": "debug_fix",
                "options": [
                    "Missing base case for n <= 0 (e.g. if n <= 0: return 0)",
                    "Return statement should multiply instead of add",
                    "Change 'fib(n - 1)' to 'fib(n + 1)'",
                    "The function needs to be a lambda function"
                ]
            }),
            "correct_answer": "Missing base case for n <= 0 (e.g. if n <= 0: return 0)",
            "explanation": "Calling `fib(2)` invokes `fib(0)`, which keeps recursing into negative numbers infinitely (`fib(-1)`, `fib(-2)`, etc.) without reaching `n == 1`. Base case for `n <= 0` is required.",
            "points": 50,
            "time_limit": 50
        },

        # ==========================================
        # 6. FILL IN THE BLANKS (Easy, Medium, Hard)
        # ==========================================
        {
            "category_slug": "fill_blanks",
            "difficulty": "easy",
            "title": "Complete the Greeting Function",
            "description": "Fill in the missing keyword to define a function and output a message.",
            "code_snippet": "___ greet(name):\n    message = f'Hello, {name}!'\n    ___ message",
            "question_data": json.dumps({
                "type": "fill_blank",
                "blanks_count": 2,
                "options": [
                    {"label": "def, return", "value": "def, return"},
                    {"label": "func, send", "value": "func, send"},
                    {"label": "function, print", "value": "function, print"},
                    {"label": "def, yield", "value": "def, yield"}
                ]
            }),
            "correct_answer": "def, return",
            "explanation": "In Python, functions are defined with `def` and pass back values with `return`.",
            "points": 20,
            "time_limit": 30
        },
        {
            "category_slug": "fill_blanks",
            "difficulty": "easy",
            "title": "For Loop Range Statement",
            "description": "Fill in the missing keywords to loop 5 times from 0 to 4.",
            "code_snippet": "___ i ___ range(5):\n    print(i)",
            "question_data": json.dumps({
                "type": "fill_blank",
                "blanks_count": 2,
                "options": [
                    {"label": "for, in", "value": "for, in"},
                    {"label": "loop, from", "value": "loop, from"},
                    {"label": "while, in", "value": "while, in"},
                    {"label": "iterate, through", "value": "iterate, through"}
                ]
            }),
            "correct_answer": "for, in",
            "explanation": "Python's standard iteration syntax is `for <variable> in <iterable>:`.",
            "points": 20,
            "time_limit": 25
        },
        {
            "category_slug": "fill_blanks",
            "difficulty": "medium",
            "title": "Exception Handling Blocks",
            "description": "Fill in the keywords used to catch runtime errors gracefully.",
            "code_snippet": "___:\n    num = int(user_input)\n___ ValueError:\n    print('Please enter a valid integer!')",
            "question_data": json.dumps({
                "type": "fill_blank",
                "blanks_count": 2,
                "options": [
                    {"label": "try, except", "value": "try, except"},
                    {"label": "attempt, catch", "value": "attempt, catch"},
                    {"label": "do, handle", "value": "do, handle"},
                    {"label": "try, catch", "value": "try, catch"}
                ]
            }),
            "correct_answer": "try, except",
            "explanation": "Python uses `try` and `except` blocks for exception handling (unlike Java/JS which use try/catch).",
            "points": 35,
            "time_limit": 35
        },
        {
            "category_slug": "fill_blanks",
            "difficulty": "medium",
            "title": "Adding to a List",
            "description": "Fill in the list method used to insert a new element at the end of a list.",
            "code_snippet": "inventory = ['sword', 'shield']\ninventory.___( 'potion' )",
            "question_data": json.dumps({
                "type": "fill_blank",
                "blanks_count": 1,
                "options": [
                    {"label": "append", "value": "append"},
                    {"label": "push", "value": "push"},
                    {"label": "add", "value": "add"},
                    {"label": "insert_last", "value": "insert_last"}
                ]
            }),
            "correct_answer": "append",
            "explanation": "In Python, lists use the `.append()` method to add an item to the end.",
            "points": 35,
            "time_limit": 30
        },
        {
            "category_slug": "fill_blanks",
            "difficulty": "hard",
            "title": "Generator Function Keyword",
            "description": "What keyword turns a normal function into a generator that produces a sequence lazily?",
            "code_snippet": "def count_up_to(max_val):\n    count = 1\n    while count <= max_val:\n        ___ count\n        count += 1",
            "question_data": json.dumps({
                "type": "fill_blank",
                "blanks_count": 1,
                "options": [
                    {"label": "yield", "value": "yield"},
                    {"label": "return", "value": "return"},
                    {"label": "generate", "value": "generate"},
                    {"label": "emit", "value": "emit"}
                ]
            }),
            "correct_answer": "yield",
            "explanation": "The `yield` statement pauses the function and saves its state, resuming when `next()` is called on the generator.",
            "points": 50,
            "time_limit": 40
        },
        {
            "category_slug": "fill_blanks",
            "difficulty": "hard",
            "title": "Index and Item Enumeration",
            "description": "Fill in the built-in function that yields both the index and the item during iteration.",
            "code_snippet": "items = ['gold', 'silver', 'bronze']\nfor idx, item in ___(items):\n    print(f'Place {idx + 1}: {item}')",
            "question_data": json.dumps({
                "type": "fill_blank",
                "blanks_count": 1,
                "options": [
                    {"label": "enumerate", "value": "enumerate"},
                    {"label": "zip", "value": "zip"},
                    {"label": "index", "value": "index"},
                    {"label": "counter", "value": "counter"}
                ]
            }),
            "correct_answer": "enumerate",
            "explanation": "`enumerate(iterable, start=0)` returns pairs of (index, element) during loop iteration.",
            "points": 50,
            "time_limit": 35
        }
    ]

    for q in questions_data:
        cursor.execute('''
        INSERT INTO questions (
            category_slug, difficulty, title, description,
            code_snippet, question_data, correct_answer,
            explanation, points, time_limit
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            q["category_slug"], q["difficulty"], q["title"], q["description"],
            q["code_snippet"], q["question_data"], q["correct_answer"],
            q["explanation"], q["points"], q["time_limit"]
        ))

if __name__ == '__main__':
    print("Initializing database...")
    init_db()
    print("Database initialized successfully at", DATABASE_PATH)
