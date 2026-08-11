"""
Phase 2 Cleanup Pre-Flight and Safe Legacy Homework Marks Removal Script
"""
import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import db, Marks, HomeworkMarks
from sqlalchemy import text
from scripts.backup_database import backup_database

def run_phase2_cleanup():
    app = create_app()
    with app.app_context():
        print("==================================================")
        print("PHASE 2 CLEANUP PRE-FLIGHT START")
        print("==================================================")

        hm_count = HomeworkMarks.query.count()
        legacy_hw_in_marks = Marks.query.filter(
            (Marks.assessment_type == 'homework') | (Marks.HomeworkID.isnot(None))
        ).count()
        exam_marks_count = Marks.query.filter(
            (Marks.assessment_type == 'exam') | (Marks.ExamID.isnot(None))
        ).count()

        print(f"HomeworkMarks count: {hm_count}")
        print(f"Legacy Homework Marks in Marks: {legacy_hw_in_marks}")
        print(f"Exam Marks in Marks: {exam_marks_count}")

        if hm_count < legacy_hw_in_marks:
            print("[FAIL] HomeworkMarks has fewer records than legacy homework marks in Marks. STOPPING.")
            return False

        # Take fresh backup
        backup_success, backup_path = backup_database()
        if not backup_success:
            print("[FAIL] Pre-cleanup backup failed. STOPPING.")
            return False

        # Execute Safe Legacy Cleanup
        print("\n[CLEANUP] Removing legacy homework records from Marks table...")
        try:
            with db.engine.connect() as conn:
                conn.execute(text("DELETE FROM marks WHERE assessment_type = 'homework' OR HomeworkID IS NOT NULL"))
                conn.commit()
            print("[CLEANUP SUCCESS] Legacy homework marks deleted from Marks table.")
        except Exception as e:
            print(f"[FAIL] Error deleting legacy marks: {e}")
            return False

        # Final Verification
        remaining_marks = Marks.query.count()
        remaining_hw_in_marks = Marks.query.filter(
            (Marks.assessment_type == 'homework') | (Marks.HomeworkID.isnot(None))
        ).count()
        remaining_exam_marks = Marks.query.filter(
            (Marks.assessment_type == 'exam') | (Marks.ExamID.isnot(None))
        ).count()

        print("\n==================================================")
        print("PHASE 2 CLEANUP POST-VERIFICATION")
        print("==================================================")
        print(f"Total Marks remaining: {remaining_marks}")
        print(f"Exam Marks in Marks: {remaining_exam_marks}")
        print(f"Homework Marks in Marks: {remaining_hw_in_marks}")
        print(f"HomeworkMarks in HomeworkMarks: {HomeworkMarks.query.count()}")
        print("==================================================")

        return remaining_hw_in_marks == 0 and remaining_exam_marks == exam_marks_count

if __name__ == '__main__':
    success = run_phase2_cleanup()
    if not success:
        sys.exit(1)
