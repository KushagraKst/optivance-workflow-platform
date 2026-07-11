import sqlite3

conn = sqlite3.connect('database/optivance.db')
cur = conn.cursor()

# Clear old data
cur.execute("DELETE FROM data_points")

data = [(i * 10 + 100, f"2024-01-{str(i+1).zfill(2)}") for i in range(30)]

cur.executemany("INSERT INTO data_points (value, date) VALUES (?, ?)", data)

conn.commit()
conn.close()

print("Data inserted successfully!")