import pymysql

try:
    connection = pymysql.connect(
        host='127.0.0.1',
        user='root',
        password='',
        database='school_system_db'
    )
    with connection.cursor() as cursor:
        cursor.execute("SELECT TeacherID, TeacherName, is_deleted FROM Teacher;")
        rows = cursor.fetchall()
        for row in rows:
            print(row)
    connection.close()
except Exception as e:
    print("Error:", e)
