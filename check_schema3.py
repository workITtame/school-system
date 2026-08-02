import sqlite3
conn = sqlite3.connect('database.db')
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
for t in tables:
    name = t[0]
    cols = [r[1] for r in conn.execute(f"PRAGMA table_info('{name}')")]
    print(f"{name}: {cols}")
