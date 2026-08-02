import sqlite3

def alter_db():
    conn = sqlite3.connect('instance/school.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE Student ADD COLUMN Status VARCHAR(20) DEFAULT 'نشط'")
        print("Added Status to Student")
    except Exception as e:
        print(e)
        
    try:
        cursor.execute("ALTER TABLE Teacher ADD COLUMN Status VARCHAR(20) DEFAULT 'نشط'")
        print("Added Status to Teacher")
    except Exception as e:
        print(e)
        
    try:
        cursor.execute("ALTER TABLE Classes ADD COLUMN Stage VARCHAR(50)")
        print("Added Stage to Classes")
    except Exception as e:
        print(e)
        
    try:
        cursor.execute("ALTER TABLE Subject ADD COLUMN Type VARCHAR(50)")
        cursor.execute("ALTER TABLE Subject ADD COLUMN Department VARCHAR(50)")
        cursor.execute("ALTER TABLE Subject ADD COLUMN Status VARCHAR(20) DEFAULT 'نشط'")
        print("Added Type, Department, Status to Subject")
    except Exception as e:
        print(e)

    conn.commit()
    conn.close()
    
if __name__ == '__main__':
    alter_db()
