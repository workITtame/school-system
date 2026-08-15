import sys
import os

sys.path.insert(0, r'c:\Users\Lenovo\OneDrive\Desktop\school-system\school-system\school-system')
from app import create_app
from models import db, User, Student, Teacher, Classes, Sections, Subject, Homework, ExamSchedule, Attendance, Marks, Notification, Message, Terms, Days, Lessons, School
from sqlalchemy import inspect, text, func

app = create_app()
app.config['TESTING'] = True

audit_results = {
    'db_tables': [],
    'schema_discrepancies': [],
    'hardcoded_findings': [],
    'route_findings': [],
    'rbac_findings': [],
    'legacy_findings': [],
    'orphan_records': []
}

def run_db_audit():
    with app.app_context():
        inspector = inspect(db.engine)
        table_names = inspector.get_table_names()
        audit_results['db_tables'] = table_names
        
        # Check orphan records in Attendance, Marks, Homework, Student
        with db.engine.connect() as conn:
            # 1. Attendance without valid Student
            orphans_att = conn.execute(text("SELECT COUNT(*) FROM attendance WHERE SID NOT IN (SELECT SID FROM student WHERE is_deleted=0 OR is_deleted=1)")).scalar()
            if orphans_att > 0:
                audit_results['orphan_records'].append(f"Attendance records with invalid SID: {orphans_att}")

            # 2. Marks without valid Student
            orphans_marks = conn.execute(text("SELECT COUNT(*) FROM marks WHERE SID NOT IN (SELECT SID FROM student)")).scalar()
            if orphans_marks > 0:
                audit_results['orphan_records'].append(f"Marks records with invalid SID: {orphans_marks}")

            # 3. Student without valid Class
            orphans_st_class = conn.execute(text("SELECT COUNT(*) FROM student WHERE CID IS NOT NULL AND CID NOT IN (SELECT CID FROM classes)")).scalar()
            if orphans_st_class > 0:
                audit_results['orphan_records'].append(f"Student records with non-existent CID: {orphans_st_class}")

            # 4. Check for score > max_score or negative scores in Marks
            invalid_scores = conn.execute(text("SELECT COUNT(*) FROM marks WHERE Score < 0 OR (MaxScore IS NOT NULL AND MaxScore > 0 AND Score > MaxScore)")).scalar()
            if invalid_scores > 0:
                audit_results['schema_discrepancies'].append(f"Marks table has {invalid_scores} rows where Score < 0 or Score > MaxScore")

        print(f"[OK] DB Tables Found ({len(table_names)}): {', '.join(table_names)}")
        print(f"[OK] Orphan Records Audit Completed: {len(audit_results['orphan_records'])} issues found.")

if __name__ == '__main__':
    run_db_audit()
