import sqlite3
conn = sqlite3.connect('database.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tables:", cursor.fetchall())
cursor.execute("PRAGMA table_info(Teacher);")
print("Teacher columns:", [row[1] for row in cursor.fetchall()])
cursor.execute("PRAGMA table_info(teachers);")
print("teachers columns:", [row[1] for row in cursor.fetchall()])
