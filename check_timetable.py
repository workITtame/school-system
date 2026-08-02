import pymysql

try:
    connection = pymysql.connect(
        host='127.0.0.1',
        user='root',
        password='',
        database='school_system_db'
    )
    with connection.cursor() as cursor:
        cursor.execute("DESCRIBE SchoolTable;")
        columns = cursor.fetchall()
        print("SchoolTable Columns:", [col[0] for col in columns])
        
        cursor.execute("SHOW INDEX FROM SchoolTable;")
        indexes = cursor.fetchall()
        print("SchoolTable Indexes:", [(idx[2], idx[4]) for idx in indexes])
    connection.close()
except Exception as e:
    print("Error:", e)
