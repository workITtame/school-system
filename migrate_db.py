"""
Database Schema Migration Script - Ensures all required columns exist in MySQL database
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
    try:
        if not column_exists(cursor, table, column):
            sql = f"ALTER TABLE `{table}` ADD COLUMN `{column}` {definition}"
            cursor.execute(sql)
            print(f"  Added column: {table}.{column}")
        else:
            pass
    except Exception as e:
        print(f"  Column warning ({table}.{column}): {e}")

def constraint_exists(cursor, table, constraint_name):
    cursor.execute(
        "SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND CONSTRAINT_NAME = %s",
        (table, constraint_name)
    )
    return cursor.fetchone()[0] > 0

def add_unique_constraint_if_missing(cursor, table, constraint_name, columns_sql):
    try:
        if not constraint_exists(cursor, table, constraint_name):
            sql = f"ALTER TABLE `{table}` ADD CONSTRAINT `{constraint_name}` UNIQUE ({columns_sql})"
            cursor.execute(sql)
            print(f"  Added unique constraint: {table}.{constraint_name}")
    except Exception as e:
        print(f"  Constraint warning ({table}.{constraint_name}): {e}")

def run_migrations():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        print("Starting database schema auto-migration...")

        # ── users ──────────────────────────────────────────────
        add_column_if_missing(cursor, 'users', 'failed_login_attempts', "INT DEFAULT 0")
        add_column_if_missing(cursor, 'users', 'locked_until', "DATETIME NULL")
        add_column_if_missing(cursor, 'users', 'last_login', "DATETIME NULL")
        add_column_if_missing(cursor, 'users', 'created_at', "DATETIME NULL")
        add_column_if_missing(cursor, 'users', 'updated_at', "DATETIME NULL")
        add_column_if_missing(cursor, 'users', 'is_deleted', "TINYINT(1) DEFAULT 0")

        # ── Teacher ──────────────────────────────────────────────
        add_column_if_missing(cursor, 'Teacher', 'Gender', "VARCHAR(10) NULL")
        add_column_if_missing(cursor, 'Teacher', 'Notes',  "TEXT NULL")
        add_column_if_missing(cursor, 'Teacher', 'Status', "VARCHAR(20) DEFAULT 'active'")
        add_column_if_missing(cursor, 'Teacher', 'TeacherTitle', "VARCHAR(50) NULL")
        add_column_if_missing(cursor, 'Teacher', 'created_at', "DATETIME NULL")
        add_column_if_missing(cursor, 'Teacher', 'updated_at', "DATETIME NULL")
        add_column_if_missing(cursor, 'Teacher', 'is_deleted', "TINYINT(1) DEFAULT 0")

        # ── Student ──────────────────────────────────────────────
        add_column_if_missing(cursor, 'Student', 'Status', "VARCHAR(20) DEFAULT 'active'")
        add_column_if_missing(cursor, 'Student', 'created_at', "DATETIME NULL")
        add_column_if_missing(cursor, 'Student', 'updated_at', "DATETIME NULL")
        add_column_if_missing(cursor, 'Student', 'is_deleted', "TINYINT(1) DEFAULT 0")

        # ── Classes ──────────────────────────────────────────────
        add_column_if_missing(cursor, 'Classes', 'Stage', "VARCHAR(50) NULL")
        add_column_if_missing(cursor, 'Classes', 'MaxStudents', "INT DEFAULT 40")
        add_column_if_missing(cursor, 'Classes', 'created_at', "DATETIME NULL")
        add_column_if_missing(cursor, 'Classes', 'updated_at', "DATETIME NULL")
        add_column_if_missing(cursor, 'Classes', 'is_deleted', "TINYINT(1) DEFAULT 0")

        # ── Sections ─────────────────────────────────────────────
        add_column_if_missing(cursor, 'Sections', 'MaxStudents', "INT DEFAULT 40")
        add_column_if_missing(cursor, 'Sections', 'created_at', "DATETIME NULL")
        add_column_if_missing(cursor, 'Sections', 'updated_at', "DATETIME NULL")
        add_column_if_missing(cursor, 'Sections', 'is_deleted', "TINYINT(1) DEFAULT 0")

        # ── Subject ──────────────────────────────────────────────
        add_column_if_missing(cursor, 'Subject', 'Type', "VARCHAR(50) NULL")
        add_column_if_missing(cursor, 'Subject', 'Department', "VARCHAR(50) NULL")
        add_column_if_missing(cursor, 'Subject', 'Status', "VARCHAR(20) DEFAULT 'active'")
        add_column_if_missing(cursor, 'Subject', 'WeeklyHours', "INT DEFAULT 0")
        add_column_if_missing(cursor, 'Subject', 'created_at', "DATETIME NULL")
        add_column_if_missing(cursor, 'Subject', 'updated_at', "DATETIME NULL")
        add_column_if_missing(cursor, 'Subject', 'is_deleted', "TINYINT(1) DEFAULT 0")

        # ── Lessons ──────────────────────────────────────────────
        add_column_if_missing(cursor, 'Lessons', 'StartTime', "VARCHAR(10) NULL")
        add_column_if_missing(cursor, 'Lessons', 'EndTime',   "VARCHAR(10) NULL")
        add_column_if_missing(cursor, 'Lessons', 'created_at', "DATETIME NULL")
        add_column_if_missing(cursor, 'Lessons', 'updated_at', "DATETIME NULL")
        add_column_if_missing(cursor, 'Lessons', 'is_deleted', "TINYINT(1) DEFAULT 0")

        # ── Terms ────────────────────────────────────────────────
        add_column_if_missing(cursor, 'Terms', 'AcademicYear', "VARCHAR(20) NULL")
        add_column_if_missing(cursor, 'Terms', 'created_at', "DATETIME NULL")
        add_column_if_missing(cursor, 'Terms', 'updated_at', "DATETIME NULL")
        add_column_if_missing(cursor, 'Terms', 'is_deleted', "TINYINT(1) DEFAULT 0")

        # ── ExamSchedule ─────────────────────────────────────────
        add_column_if_missing(cursor, 'ExamSchedule', 'T_ID',     "INT NULL")
        add_column_if_missing(cursor, 'ExamSchedule', 'Duration', "INT DEFAULT 60")
        add_column_if_missing(cursor, 'ExamSchedule', 'Location', "VARCHAR(100) NULL")
        add_column_if_missing(cursor, 'ExamSchedule', 'created_at', "DATETIME NULL")
        add_column_if_missing(cursor, 'ExamSchedule', 'updated_at', "DATETIME NULL")
        add_column_if_missing(cursor, 'ExamSchedule', 'is_deleted', "TINYINT(1) DEFAULT 0")

        # ── Marks ────────────────────────────────────────────────
        add_column_if_missing(cursor, 'Marks', 'MaxScore',   "DECIMAL(5,2) DEFAULT 100")
        add_column_if_missing(cursor, 'Marks', 'Percentage', "DECIMAL(5,2) NULL")
        add_column_if_missing(cursor, 'Marks', 'Notes',      "VARCHAR(255) NULL")
        add_column_if_missing(cursor, 'Marks', 'assessment_type', "VARCHAR(20) DEFAULT 'exam'")
        add_column_if_missing(cursor, 'Marks', 'created_at', "DATETIME NULL")
        add_column_if_missing(cursor, 'Marks', 'updated_at', "DATETIME NULL")
        add_column_if_missing(cursor, 'Marks', 'is_deleted', "TINYINT(1) DEFAULT 0")
        add_unique_constraint_if_missing(cursor, 'Marks', 'uq_student_exam_marks', "`SID`, `ExamID`")

        # ── DetailMarks ──────────────────────────────────────────
        add_column_if_missing(cursor, 'DetailMarks', 'MaxScore', "DECIMAL(5,2) DEFAULT 100")
        add_column_if_missing(cursor, 'DetailMarks', 'created_at', "DATETIME NULL")
        add_column_if_missing(cursor, 'DetailMarks', 'updated_at', "DATETIME NULL")
        add_column_if_missing(cursor, 'DetailMarks', 'is_deleted', "TINYINT(1) DEFAULT 0")

        conn.commit()
        cursor.close()
        conn.close()
        print("Database schema migration completed successfully!")
    except Exception as e:
        print(f"Migration warning: {e}")

if __name__ == '__main__':
    run_migrations()
