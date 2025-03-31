# Flask app entrypoint - simplified version for port binding fix

from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def index():
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)), debug=True)
from flask import Flask, render_template, request, redirect, session, url_for, send_from_directory
from werkzeug.utils import secure_filename
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = 'static/uploads'
ASSIGNMENT_FOLDER = 'static/assignments'
SUBMISSION_FOLDER = 'static/submissions'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ASSIGNMENT_FOLDER'] = ASSIGNMENT_FOLDER
app.config['SUBMISSION_FOLDER'] = SUBMISSION_FOLDER
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt', 'zip'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        filename TEXT NOT NULL,
        uploaded_at TEXT
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        filename TEXT,
        watched_at TEXT
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        due_date TEXT,
        file_name TEXT,
        uploaded_by INTEGER
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        assignment_id INTEGER,
        student_id INTEGER,
        file_name TEXT,
        submitted_at TEXT
    )
    ''')

    user_check = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if user_check == 0:
        c.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'admin', 'admin')")
        c.execute("INSERT INTO users (username, password, role) VALUES ('teacher1', 'pass', 'teacher')")
        c.execute("INSERT INTO users (username, password, role) VALUES ('student1', 'pass', 'student')")

    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('assignments'))

@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', 
                            (username, password)).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['role'] = user['role']
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/assignments')
def assignments():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    all_assignments = conn.execute('SELECT * FROM assignments').fetchall()
    conn.close()
    return render_template('assignment_list.html', assignments=all_assignments)

@app.route('/assignments/upload', methods=['GET', 'POST'])
def upload_assignment():
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        due_date = request.form['due_date']
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['ASSIGNMENT_FOLDER'], filename)
            file.save(filepath)
            conn = get_db_connection()
            conn.execute('INSERT INTO assignments (title, description, due_date, file_name, uploaded_by) VALUES (?, ?, ?, ?, ?)',
                         (title, description, due_date, filename, session['user_id']))
            conn.commit()
            conn.close()
            return redirect(url_for('assignments'))
    return render_template('upload_assignment.html')

@app.route('/assignments/submit/<int:assignment_id>', methods=['GET', 'POST'])
def submit_assignment(assignment_id):
    if 'user_id' not in session or session['role'] != 'student':
        return redirect(url_for('login'))
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['SUBMISSION_FOLDER'], filename)
            file.save(filepath)
            conn = get_db_connection()
            conn.execute('INSERT INTO submissions (assignment_id, student_id, file_name, submitted_at) VALUES (?, ?, ?, ?)',
                         (assignment_id, session['user_id'], filename, datetime.now()))
            conn.commit()
            conn.close()
            return redirect(url_for('assignments'))
    return render_template('submit_assignment.html', assignment_id=assignment_id)
