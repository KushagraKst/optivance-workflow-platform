import sqlite3
from datetime import datetime

def check_overdue_tasks():
    conn = sqlite3.connect('database/optivance.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    today = datetime.now().date()

    cur.execute("SELECT * FROM tasks WHERE status!='done'")
    tasks = cur.fetchall()

    for task in tasks:
        deadline = task['due_date']
        # Ensure deadline exists and is a valid date string before comparison
        if deadline and deadline < str(today):
            print(f"Reminder: Task '{task['title']}' is overdue!")


    conn.close()