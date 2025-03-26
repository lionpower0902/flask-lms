import sqlite3

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

# デモユーザー追加
c.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'admin', 'admin')")
c.execute("INSERT INTO users (username, password, role) VALUES ('teacher1', 'pass', 'teacher')")
c.execute("INSERT INTO users (username, password, role) VALUES ('student1', 'pass', 'student')")

conn.commit()
conn.close()
