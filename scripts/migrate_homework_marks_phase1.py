"""
PHASE 1 Migration Script: HomeworkMarks Safe Migration & Backup
"""
import os
import sys
from datetime import datetime

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import db, Marks, HomeworkMarks, Homework, Student, Subject
from sqlalchemy import text
from scripts.backup_database import backup_database

def run_phase1_migration():
    app = create_app()
    with app.app_context():
        print("==================================================")
        print("PHASE 1 — HOMEWORKMARKS MIGRATION START")
        print("==================================================")

        # 1. AUDIT CHECK
        with db.engine.connect() as conn:
            total_marks = conn.execute(text("SELECT COUNT(*) FROM marks")).scalar()
            exam_marks_count = conn.execute(text("SELECT COUNT(*) FROM marks WHERE assessment_type = 'exam' OR (assessment_type IS NULL AND ExamID IS NOT NULL)")).scalar()
            hw_marks_count = conn.execute(text("SELECT COUNT(*) FROM marks WHERE (assessment_type = 'homework' OR HomeworkID IS NOT NULL)")).scalar()

            # Check orphans
            orphans = conn.execute(text("SELECT * FROM marks WHERE (assessment_type = 'homework' OR HomeworkID IS NOT NULL) AND (HomeworkID IS NULL OR HomeworkID NOT IN (SELECT id FROM homework))")).fetchall()
            if orphans:
                print(f"[FAIL] Found {len(orphans)} orphan homework marks! Migration NOT READY.")
                return False

            # Check duplicates
            dups = conn.execute(text("SELECT SID, HomeworkID, COUNT(*) as cnt FROM marks WHERE (assessment_type = 'homework' OR HomeworkID IS NOT NULL) GROUP BY SID, HomeworkID HAVING cnt > 1")).fetchall()
            if dups:
                print(f"[FAIL] Found {len(dups)} duplicate homework marks! Migration NOT READY.")
                return False

        print(f"[AUDIT PASS] Total Marks: {total_marks}, Exam Marks: {exam_marks_count}, Homework Marks: {hw_marks_count}")

        # 2. BACKUP
        backup_success, backup_path = backup_database()
        if not backup_success:
            print("[FAIL] Database backup failed. Migration STOPPED.")
            return False

        # 3. CREATE HOMEWORKMARKS TABLE
        print("[MIGRATION] Creating HomeworkMarks table in MySQL...")
        db.create_all()

        # 4. VERIFY TABLE CREATION
        with db.engine.connect() as conn:
            table_check = conn.execute(text("SHOW TABLES LIKE 'HomeworkMarks'")).fetchall()
            if not table_check:
                print("[FAIL] Table HomeworkMarks was not created.")
                return False

        # 5. IDEMPOTENT DATA MIGRATION IN TRANSACTION
        print("[MIGRATION] Copying Homework Marks from Marks to HomeworkMarks...")
        source_hw_marks = Marks.query.filter(
            (Marks.assessment_type == 'homework') | (Marks.HomeworkID.isnot(None))
        ).all()

        migrated_count = 0
        skipped_count = 0

        try:
            for mark in source_hw_marks:
                # Check if already migrated
                existing = HomeworkMarks.query.filter_by(
                    SID=mark.SID,
                    HomeworkID=mark.HomeworkID
                ).first()

                if existing:
                    # Update fields if already exists
                    existing.SubID = mark.SubID
                    existing.TeacherID = mark.TeacherID
                    existing.Score = mark.Score
                    existing.MaxScore = mark.MaxScore or 100
                    existing.Percentage = mark.Percentage
                    existing.Grade = mark.Grade
                    existing.T_ID = mark.T_ID
                    existing.Notes = mark.Notes
                    existing.is_deleted = mark.is_deleted
                    skipped_count += 1
                else:
                    new_hm = HomeworkMarks(
                        SID=mark.SID,
                        SubID=mark.SubID,
                        HomeworkID=mark.HomeworkID,
                        TeacherID=mark.TeacherID,
                        Score=mark.Score,
                        MaxScore=mark.MaxScore or 100,
                        Percentage=mark.Percentage,
                        Grade=mark.Grade,
                        T_ID=mark.T_ID,
                        Notes=mark.Notes,
                        is_deleted=mark.is_deleted,
                        created_at=mark.created_at or datetime.utcnow(),
                        updated_at=mark.updated_at or datetime.utcnow()
                    )
                    db.session.add(new_hm)
                    migrated_count += 1

            db.session.commit()
            print(f"[MIGRATION SUCCESS] Copied: {migrated_count}, Existing/Updated: {skipped_count}")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"[FAIL] Error during data migration: {e}")
            return False

def rollback_phase1_migration():
    """Rollback function to safely drop HomeworkMarks table if requested."""
    app = create_app()
    with app.app_context():
        print("[ROLLBACK] Dropping HomeworkMarks table...")
        with db.engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS HomeworkMarks"))
            conn.commit()
        print("[ROLLBACK COMPLETE] HomeworkMarks table dropped. Marks table remained 100% untouched.")

if __name__ == '__main__':
    success = run_phase1_migration()
    if not success:
        sys.exit(1)
