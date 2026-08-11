"""
سكريبت ترحيل قاعدة البيانات - يضيف الحقول الجديدة إلى الجداول الموجودة
شغّل هذا السكريبت مرة واحدة فقط بعد تحديث النماذج
"""
import pymysql
from config import Config

def get_connection():
    from urllib.parse import urlparse
    uri = Config.SQLALCHEMY_DATABASE_URI
    parsed = urlparse(uri)
    return pymysql.connect(
        host=parsed.hostname or '127.0.0.1',
        user=parsed.username or 'root',
        password=parsed.password or '',
        port=parsed.port or 3306,
        database=parsed.path.lstrip('/'),
        charset='utf8mb4'
    )

def column_exists(cursor, table, column):
    cursor.execute(
        "SELECT COUNT(*) FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND COLUMN_NAME = %s",
        (table, column)
    )
    return cursor.fetchone()[0] > 0

def add_column_if_missing(cursor, table, column, definition):
    if not column_exists(cursor, table, column):
        sql = f"ALTER TABLE `{table}` ADD COLUMN `{column}` {definition}"
        cursor.execute(sql)
        print(f"  ✅ أُضيف العمود: {table}.{column}")
    else:
        print(f"  ⏭  موجود مسبقاً: {table}.{column}")

def constraint_exists(cursor, table, constraint_name):
    cursor.execute(
        "SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND CONSTRAINT_NAME = %s",
        (table, constraint_name)
    )
    return cursor.fetchone()[0] > 0

def add_unique_constraint_if_missing(cursor, table, constraint_name, columns_sql):
    if not constraint_exists(cursor, table, constraint_name):
        sql = f"ALTER TABLE `{table}` ADD CONSTRAINT `{constraint_name}` UNIQUE ({columns_sql})"
        cursor.execute(sql)
        print(f"  ✅ أُضيفت الحماية المستقلة: {table}.{constraint_name}")
    else:
        print(f"  ⏭  موجود مسبقاً: {table}.{constraint_name}")

def run_migrations():
    conn = get_connection()
    cursor = conn.cursor()
    
    print("\n🔄 بدء ترحيل قاعدة البيانات...\n")

    # ── Teacher ──────────────────────────────────────────────
    print("📋 جدول Teacher:")
    add_column_if_missing(cursor, 'Teacher', 'Gender', "VARCHAR(10) NULL COMMENT 'ذكر/أنثى'")
    add_column_if_missing(cursor, 'Teacher', 'Notes',  "TEXT NULL COMMENT 'ملاحظات'")

    # ── Classes ──────────────────────────────────────────────
    print("\n📋 جدول Classes:")
    add_column_if_missing(cursor, 'Classes', 'MaxStudents', "INT DEFAULT 40 COMMENT 'الحد الأقصى للطلاب'")

    # ── Sections ─────────────────────────────────────────────
    print("\n📋 جدول Sections:")
    add_column_if_missing(cursor, 'Sections', 'MaxStudents', "INT DEFAULT 40 COMMENT 'الحد الأقصى للطلاب في الشعبة'")

    # ── Subject ──────────────────────────────────────────────
    print("\n📋 جدول Subject:")
    add_column_if_missing(cursor, 'Subject', 'WeeklyHours', "INT DEFAULT 0 COMMENT 'الحصص الأسبوعية'")

    # ── Lessons ──────────────────────────────────────────────
    print("\n📋 جدول Lessons:")
    add_column_if_missing(cursor, 'Lessons', 'StartTime', "VARCHAR(10) NULL COMMENT 'وقت البداية'")
    add_column_if_missing(cursor, 'Lessons', 'EndTime',   "VARCHAR(10) NULL COMMENT 'وقت النهاية'")

    # ── Terms ────────────────────────────────────────────────
    print("\n📋 جدول Terms:")
    add_column_if_missing(cursor, 'Terms', 'AcademicYear', "VARCHAR(20) NULL COMMENT 'السنة الدراسية'")

    # ── ExamSchedule ─────────────────────────────────────────
    print("\n📋 جدول ExamSchedule:")
    add_column_if_missing(cursor, 'ExamSchedule', 'T_ID',     "INT NULL")
    add_column_if_missing(cursor, 'ExamSchedule', 'Duration', "INT DEFAULT 60 COMMENT 'مدة الامتحان بالدقائق'")
    add_column_if_missing(cursor, 'ExamSchedule', 'Location', "VARCHAR(100) NULL COMMENT 'قاعة الامتحان'")

    # ── Marks ────────────────────────────────────────────────
    print("\n📋 جدول Marks:")
    add_column_if_missing(cursor, 'Marks', 'MaxScore',   "DECIMAL(5,2) DEFAULT 100 COMMENT 'الدرجة الكاملة'")
    add_column_if_missing(cursor, 'Marks', 'Percentage', "DECIMAL(5,2) NULL COMMENT 'النسبة المئوية'")
    add_column_if_missing(cursor, 'Marks', 'Notes',      "VARCHAR(255) NULL COMMENT 'ملاحظات المعلم'")
    add_unique_constraint_if_missing(cursor, 'Marks', 'uq_student_exam_marks', "`SID`, `ExamID`")

    # ── DetailMarks ──────────────────────────────────────────
    print("\n📋 جدول DetailMarks:")
    add_column_if_missing(cursor, 'DetailMarks', 'MaxScore', "DECIMAL(5,2) DEFAULT 100")

    conn.commit()
    cursor.close()
    conn.close()
    print("\n✅ اكتمل الترحيل بنجاح!\n")

if __name__ == '__main__':
    run_migrations()
