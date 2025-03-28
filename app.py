from flask import Flask, render_template, request, redirect, session, url_for, send_from_directory
from werkzeug.utils import secure_filename
import sqlite3
import os
from datetime import datetime

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # users テーブル作成
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    )
    ''')

    # courses テーブル作成
    c.execute('''
    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        filename TEXT NOT NULL,
        uploaded_at TEXT
    )
    ''')

    # logs テーブル作成
    c.execute('''
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        filename TEXT,
        watched_at TEXT
    )
    ''')

    # 初期ユーザーが存在しなければ追加
    user_check = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if user_check == 0:
        c.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'admin', 'admin')")
        c.execute("INSERT INTO users (username, password, role) VALUES ('teacher1', 'pass', 'teacher')")
        c.execute("INSERT INTO users (username, password, role) VALUES ('student1', 'pass', 'student')")

    conn.commit()
    conn.close()


app = Flask(__name__)
app.secret_key = 'your_secret_key'
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'mp4', 'pdf'}

init_db()  # アプリ起動時に1度だけ実行


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    courses = conn.execute('SELECT * FROM courses').fetchall()
    conn.close()
    return render_template('dashboard.html', courses=courses)

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

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title']
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            conn = get_db_connection()
            conn.execute('INSERT INTO courses (title, filename, uploaded_at) VALUES (?, ?, ?)',
                         (title, filename, datetime.now()))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))
    return render_template('upload.html')

@app.route('/watch/<filename>')
def watch(filename):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    # 簡易ログ記録
    conn = get_db_connection()
    conn.execute('INSERT INTO logs (user_id, filename, watched_at) VALUES (?, ?, ?)',
                 (session['user_id'], filename, datetime.now()))
    conn.commit()
    conn.close()
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)), debug=True)
