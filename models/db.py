import sqlite3
import os

def init_db():
    os.makedirs('database', exist_ok=True)
    conn = sqlite3.connect('database/optivance.db')
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS teams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER,
        name TEXT,
        leader_id INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT,
        company_id INTEGER,
        team_id INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS invites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token TEXT UNIQUE,
        company_id INTEGER,
        team_id INTEGER,
        is_used INTEGER DEFAULT 0
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        team_id INTEGER,
        assigned_by INTEGER,
        assigned_to INTEGER,
        title TEXT,
        status TEXT,
        priority TEXT,
        due_date TEXT
    )
    """)

    # Keep data_points just in case
    cur.execute("""
    CREATE TABLE IF NOT EXISTS data_points (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        value INTEGER,
        date TEXT
    )
    """)

    # Keep data_points just in case
    cur.execute("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        plan TEXT,
        start_date TEXT,
        end_date TEXT,
        active INTEGER DEFAULT 1,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    # Add subscription_id column to users if not exists (SQLite ignores if already present)
    try:
        cur.execute("ALTER TABLE users ADD COLUMN subscription_id INTEGER")
    except sqlite3.OperationalError:
        pass
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id)
    """)

    # Create app_admin if not exists
    cur.execute("SELECT id FROM users WHERE role='app_admin'")
    if not cur.fetchone():
        cur.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)", 
                    ("App Admin", "admin@optivance.com", "admin", "app_admin"))

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully.")