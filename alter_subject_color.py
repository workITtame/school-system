import sqlite3
import random

def get_pastel_color():
    colors = [
        '#fecaca', '#fde68a', '#bbf7d0', '#bfdbfe', '#e9d5ff', 
        '#fbcfe8', '#fed7aa', '#d9f99d', '#a7f3d0', '#bae6fd',
        '#ddd6fe', '#fecdd3'
    ]
    return random.choice(colors)

def alter_db():
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(Subject)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'Color' not in columns:
            print("Adding Color column to Subject table...")
            cursor.execute("ALTER TABLE Subject ADD COLUMN Color VARCHAR(20) DEFAULT '#e2e8f0'")
            conn.commit()
            print("Column added successfully.")
            
            # Assign random pastel colors to existing subjects
            cursor.execute("SELECT SubID FROM Subject")
            subjects = cursor.fetchall()
            for sub in subjects:
                sub_id = sub[0]
                color = get_pastel_color()
                cursor.execute("UPDATE Subject SET Color = ? WHERE SubID = ?", (color, sub_id))
            conn.commit()
            print("Colors assigned to existing subjects.")
        else:
            print("Color column already exists.")
            
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    alter_db()
