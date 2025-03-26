from flask import Flask, render_template, request, redirect, session, url_for, send_from_directory
from werkzeug.utils import secure_filename
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'mp4', 'pdf'}

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
        role = request.form['role']
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ? AND role = ?',
                            (username, password, role)).fetchone()
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
    app.run(debug=True)
