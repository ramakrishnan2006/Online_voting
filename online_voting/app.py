from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "vote123"

# Database create
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        roll TEXT UNIQUE,
        password TEXT,
        voted INTEGER DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS votes(
        candidate TEXT,
        count INTEGER
    )
    """)

    cursor.execute("SELECT * FROM votes")
    data = cursor.fetchall()

    if len(data) == 0:
        cursor.execute("INSERT INTO votes VALUES ('RAM',0)")
        cursor.execute("INSERT INTO votes VALUES ('SURIYA',0)")

    conn.commit()
    conn.close()


def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def home():

    conn = get_db()

    ram = conn.execute(
        "SELECT count FROM votes WHERE candidate='RAM'"
    ).fetchone()

    suriya = conn.execute(
        "SELECT count FROM votes WHERE candidate='SURIYA'"
    ).fetchone()

    conn.close()

    return render_template(
        "index.html",
        ram_votes=ram['count'],
        suriya_votes=suriya['count']
    )
@app.route('/register', methods=['GET','POST'])
def register():

    if request.method == 'POST':

        name = request.form['name']
        roll = request.form['roll']
        password = request.form['password']

        # Password must be same as roll number
        if password != roll:
            return "Password must be same as Roll Number"

        conn = get_db()

        try:
            conn.execute(
                "INSERT INTO users (name,roll,password,voted) VALUES (?,?,?,0)",
                (name,roll,password)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return "Roll Number already registered"

        conn.close()
        return redirect('/login')

    return render_template("register.html")


@app.route('/login', methods=['GET','POST'])
def login():

    if request.method == 'POST':

        roll = request.form['roll']
        password = request.form['password']

        # Password must be same as roll number
        if password != roll:
            return "Invalid password"

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE roll=? AND password=?",
            (roll,password)
        ).fetchone()

        conn.close()

        if user:
            session['roll'] = roll
            return redirect('/vote')

        return "Invalid Roll Number or Password"

    return render_template("login.html")


@app.route('/vote', methods=['GET','POST'])
def vote():

    if 'roll' not in session:
        return redirect('/login')

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE roll=?",
        (session['roll'],)
    ).fetchone()

    if user['voted'] == 1:
        conn.close()
        return redirect('/result')

    if request.method == 'POST':
        candidate = request.form['candidate']

        conn.execute(
            "UPDATE votes SET count = count + 1 WHERE candidate=?",
            (candidate,)
        )
        conn.execute(
            "UPDATE users SET voted=1 WHERE roll=?",
            (session['roll'],)
        )
        conn.commit()
        conn.close()
        return redirect('/thankyou')

    conn.close()
    return render_template("vote.html")


@app.route('/result')
def result():
    conn = get_db()
    ram = conn.execute(
        "SELECT count FROM votes WHERE candidate='RAM'"
    ).fetchone()
    suriya = conn.execute(
        "SELECT count FROM votes WHERE candidate='SURIYA'"
    ).fetchone()
    conn.close()

    return render_template(
        "result.html",
        ram_votes=ram['count'],
        suriya_votes=suriya['count']
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True)