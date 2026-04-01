from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import sqlite3
import hashlib
import os
from functools import wraps
from datetime import timedelta

app = Flask(__name__)
app.secret_key = 'college_voting_secret_key_2026'

def log_activity(action, details='', roll_number='Guest'):
    try:
        ip = request.remote_addr
        conn = get_db()
        conn.execute(
            "INSERT INTO activity_log (roll_number, action, details, ip_address) VALUES (?,?,?,?,?)",
            (roll_number, action, details, ip)
        )
        conn.commit()
        conn.close()
    except:
        pass

# Session expires after 1 day
app.permanent_session_lifetime = timedelta(days=1)

DB_PATH = 'voting.db'

# ─────────────────────────────────────────
#  Database Initialization
# ─────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        roll_number TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        has_voted INTEGER DEFAULT 0,
        voted_at TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS activity_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        roll_number TEXT,
        action TEXT NOT NULL,
        details TEXT,
        ip_address TEXT,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        position TEXT NOT NULL,
        department TEXT NOT NULL,
        manifesto TEXT,
        symbol TEXT,
        image TEXT,
        vote_count INTEGER DEFAULT 0,
        UNIQUE(name,position)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS votes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        roll_number TEXT NOT NULL,
        candidate_id INTEGER NOT NULL,
        position TEXT NOT NULL,
        voted_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS election_settings (
        id INTEGER PRIMARY KEY DEFAULT 1,
        election_name TEXT DEFAULT 'Student Council Election 2024',
        voting_open INTEGER DEFAULT 1
    )''')

    # Insert default admin
    admin_pass = hashlib.sha256('spartanze'.encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO admins (username, password) VALUES (?, ?)", ('admin', admin_pass))

    # Insert election settings
    c.execute("INSERT OR IGNORE INTO election_settings (id, election_name, voting_open) VALUES (1, 'Student Council Election 2026', 1)")

    # Insert sample candidates
    candidates = [
        ('SURIYA', 'President', 'Computer Science', 'I will build a stronger, more connected student community with modern tech initiatives.', '🦁','suriya.jpg.png'),
        ('SARUGEH', 'President', 'Electronics', 'Empowering every student voice with transparency and actionable change.', '🌟','sarugesh.jpg.jpg'),
         ]
    for c_data in candidates:
        conn.execute("INSERT OR IGNORE INTO candidates (name, position, department, manifesto, symbol,image) VALUES (?,?,?,?,?,?)", c_data)

    conn.commit()
    conn.close()

# ─────────────────────────────────────────
#  Auth Decorators
# ─────────────────────────────────────────

def student_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'student_roll' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ─────────────────────────────────────────
#  Public Routes
# ─────────────────────────────────────────
# Render deployment fix
@app.route('/')
def home():
    return render_template('home.html')

# ─────────────────────────────────────────
#  Student Auth
# ─────────────────────────────────────────

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        roll = request.form['roll_number'].strip().upper()
        name = request.form['name'].strip()
        dept = request.form['department'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        confirm = request.form['confirm_password']

        if password != confirm:
            return jsonify({'success': False, 'message': 'Passwords do not match!'})

        if len(password) < 6:
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters!'})

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO students (roll_number, name, department, email, password) VALUES (?, ?, ?, ?, ?)",
                (roll, name, dept, email, hash_password(password))
            )
            conn.commit()
            log_activity('REGISTER', f'New student registered: {roll}', roll)
            return jsonify({'success': True, 'message': 'Registration successful! Please login.'})
        except sqlite3.IntegrityError as e:
            if 'roll_number' in str(e):
                return jsonify({'success': False, 'message': 'Roll number already registered!'})
            return jsonify({'success': False, 'message': 'Email already registered!'})
        finally:
            conn.close()

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        roll = request.form['roll_number'].strip().upper()
        password = request.form['password']

        conn = get_db()
        student = conn.execute(
            "SELECT * FROM students WHERE roll_number = ? AND password = ?",
            (roll, hash_password(password))
        ).fetchone()
        conn.close()

        if student:
            session.permanent=True
            session['student_roll'] = student['roll_number']
            session['student_name'] = student['name']
            session['has_voted'] = bool(student['has_voted'])
            log_activity('LOGIN', f'Student logged in', roll)
            return jsonify({'success': True, 'has_voted': bool(student['has_voted'])})
        else:
            log_activity('LOGIN_FAILED', f'Failed login attempt: {roll}', roll)
            return jsonify({'success': False, 'message': 'Invalid Roll Number or Password!'})

    return render_template('login.html')

@app.route('/logout')
def logout():
     log_activity('LOGOUT', 'Student logged out', session.get('student_roll', 'Unknown'))
     session.clear()
     return redirect(url_for('home'))




# ─────────────────────────────────────────
#  Voting Routes
# ─────────────────────────────────────────

@app.route('/vote')
@student_required
def vote():
    if session.get('has_voted'):
        return redirect(url_for('thank_you'))

    conn = get_db()
    settings = conn.execute("SELECT * FROM election_settings WHERE id=1").fetchone()
    candidates_raw = conn.execute("SELECT * FROM candidates ORDER BY position, name").fetchall()
    conn.close()

    # Group by position
    positions = {}
    for c in candidates_raw:
        pos = c['position']
        if pos not in positions:
            positions[pos] = []
        positions[pos].append(dict(c))

    return render_template('vote.html',
                           positions=positions,
                           student_name=session['student_name'],
                           election_name=settings['election_name'] if settings else 'Student Council Election')

@app.route('/submit_vote', methods=['POST'])
@student_required
def submit_vote():
    if session.get('has_voted'):
        return jsonify({'success': False, 'message': 'You have already voted!'})

    data = request.get_json()
    votes = data.get('votes', {})  # {position: candidate_id}

    conn = get_db()
    roll = session['student_roll']

    # Double-check in DB
    student = conn.execute("SELECT has_voted FROM students WHERE roll_number=?", (roll,)).fetchone()
    if student['has_voted']:
        conn.close()
        return jsonify({'success': False, 'message': 'You have already voted!'})

    try:
        for position, candidate_id in votes.items():
            conn.execute(
                "INSERT INTO votes (roll_number, candidate_id, position) VALUES (?, ?, ?)",
                (roll, candidate_id, position)
            )
            conn.execute(
                "UPDATE candidates SET vote_count = vote_count + 1 WHERE id = ?",
                (candidate_id,)
            )

        conn.execute(
            "UPDATE students SET has_voted=1, voted_at=? WHERE roll_number=?",
            (datetime.now().isoformat(), roll)
        )
        conn.commit()
        session['has_voted'] = True
        log_activity('VOTE', f'Student voted successfully', roll)
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': 'Voting failed. Please try again.'})
    finally:
        conn.close()

@app.route('/thank_you')
@student_required
def thank_you():
    return render_template('thank_you.html', student_name=session['student_name'])

# ─────────────────────────────────────────
#  Admin Routes
# ─────────────────────────────────────────

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        admin = conn.execute(
            "SELECT * FROM admins WHERE username=? AND password=?",
            (username, hash_password(password))
        ).fetchone()
        conn.close()

        if admin:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            log_activity('ADMIN_LOGIN', f'Admin logged in: {username}', 'ADMIN')
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Invalid credentials!'})

    return render_template('admin_login.html')

   

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    return redirect(url_for('home'))

@app.route('/admin/results')
@admin_required
def admin_results():
    conn = get_db()
    candidates = conn.execute(
        "SELECT * FROM candidates ORDER BY position, vote_count DESC"
    ).fetchall()
    total_students = conn.execute("SELECT COUNT(*) as cnt FROM students").fetchone()['cnt']
    total_voted = conn.execute("SELECT COUNT(*) as cnt FROM students WHERE has_voted=1").fetchone()['cnt']
    settings = conn.execute("SELECT * FROM election_settings WHERE id=1").fetchone()
    conn.close()

    positions = {}
    for c in candidates:
        pos = c['position']
        if pos not in positions:
            positions[pos] = []
        positions[pos].append(dict(c))

    turnout = round((total_voted / total_students * 100), 1) if total_students > 0 else 0

    return render_template('results.html',
                           positions=positions,
                           total_students=total_students,
                           total_voted=total_voted,
                           turnout=turnout,
                           election_name=settings['election_name'])

@app.route('/admin/activity')
@admin_required
def admin_activity():
    conn = get_db()
    logs = conn.execute(
        "SELECT * FROM activity_log ORDER BY timestamp DESC LIMIT 100"
    ).fetchall()
    conn.close()
    return render_template('activity.html', logs=logs)

@app.route('/admin/toggle_voting', methods=['POST'])
@admin_required
def toggle_voting():
    conn = get_db()
    current = conn.execute("SELECT voting_open FROM election_settings WHERE id=1").fetchone()
    new_val = 0 if current['voting_open'] else 1
    conn.execute("UPDATE election_settings SET voting_open=? WHERE id=1", (new_val,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'voting_open': bool(new_val)})

app.jinja_env.filters['enumerate'] = enumerate

#Fix for Renderdatabase
with app.app_context():
    init_db()

if __name__ == '__main__':
    init_db()
    app.run(debug=False,host='0.0.0.0',port=int(os.environ.get('PORT',5000)))
