import sqlite3
import os

os.makedirs("database", exist_ok=True)

conn = sqlite3.connect("database/optivance.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS data_points (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    value INTEGER,
    date TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    status TEXT,
    due_date TEXT,
    team_id INTEGER,
    assigned_by INTEGER,
    assigned_to INTEGER
)
""")



conn.commit()
conn.close()

print("Database created successfully!")