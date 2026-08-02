import pymysql

try:
    connection = pymysql.connect(
        host='127.0.0.1',
        user='root',
        password='',
        database='school_system_db'
    )
    with connection.cursor() as cursor:
        cursor.execute("DESCRIBE Teacher;")
        columns = cursor.fetchall()
        print("Teacher Columns:", [col[0] for col in columns])
    connection.close()
except Exception as e:
    print("Error:", e)
