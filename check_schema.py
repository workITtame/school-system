import sqlite3
conn = sqlite3.connect('database.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(Teacher);")
print([row[1] for row in cursor.fetchall()])
