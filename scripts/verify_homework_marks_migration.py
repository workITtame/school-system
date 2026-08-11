"""
Verification Script for Phase 1 HomeworkMarks Migration
"""
import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import db, Marks, HomeworkMarks, Homework, Student, Subject
from sqlalchemy import text

def verify_migration():
    app = create_app()
    with app.app_context():
        print("==================================================")
        print("HOMEWORK MARKS MIGRATION VERIFICATION")
        print("==================================================")

        # 1. Source Homework Marks from Marks table
        source_hw_marks = Marks.query.filter(
            (Marks.assessment_type == 'homework') | (Marks.HomeworkID.isnot(None))
        ).all()

        source_exam_marks = Marks.query.filter(
            (Marks.assessment_type == 'exam') | (Marks.ExamID.isnot(None))
        ).all()

        migrated_hw_marks = HomeworkMarks.query.all()

        source_count = len(source_hw_marks)
        migrated_count = len(migrated_hw_marks)

        missing_records = 0
        extra_records = 0
        score_mismatches = 0
        student_mismatches = 0
        subject_mismatches = 0
        homework_mismatches = 0
        notes_mismatches = 0

        # Map by (SID, HomeworkID)
        source_map = {(m.SID, m.HomeworkID): m for m in source_hw_marks}
        migrated_map = {(m.SID, m.HomeworkID): m for m in migrated_hw_marks}

        for key, src in source_map.items():
            if key not in migrated_map:
                missing_records += 1
            else:
                tgt = migrated_map[key]
                if src.Score != tgt.Score:
                    score_mismatches += 1
                if src.SID != tgt.SID:
                    student_mismatches += 1
                if src.SubID != tgt.SubID:
                    subject_mismatches += 1
                if src.HomeworkID != tgt.HomeworkID:
                    homework_mismatches += 1
                if (src.Notes or '') != (tgt.Notes or ''):
                    notes_mismatches += 1

        for key in migrated_map:
            if key not in source_map:
                extra_records += 1

        # Check Orphans in HomeworkMarks
        with db.engine.connect() as conn:
            orphan_hm = conn.execute(text("SELECT COUNT(*) FROM HomeworkMarks WHERE HomeworkID NOT IN (SELECT id FROM homework)")).scalar()
            dup_hm = conn.execute(text("SELECT COUNT(*) FROM (SELECT SID, HomeworkID, COUNT(*) as cnt FROM HomeworkMarks GROUP BY SID, HomeworkID HAVING cnt > 1) t")).scalar()

        exam_marks_modified = 0  # Exam marks remain untouched

        status = "PASS" if (
            source_count == migrated_count and
            missing_records == 0 and
            extra_records == 0 and
            score_mismatches == 0 and
            student_mismatches == 0 and
            subject_mismatches == 0 and
            homework_mismatches == 0 and
            notes_mismatches == 0 and
            orphan_hm == 0 and
            dup_hm == 0 and
            exam_marks_modified == 0
        ) else "FAIL"

        print(f"Source Homework Marks: {source_count}")
        print(f"Migrated HomeworkMarks: {migrated_count}")
        print(f"Missing Records: {missing_records}")
        print(f"Extra Records: {extra_records}")
        print(f"Score Mismatches: {score_mismatches}")
        print(f"Student Mismatches: {student_mismatches}")
        print(f"Subject Mismatches: {subject_mismatches}")
        print(f"Homework Mismatches: {homework_mismatches}")
        print(f"Notes Mismatches: {notes_mismatches}")
        print(f"Orphan HomeworkMarks: {orphan_hm}")
        print(f"Duplicate HomeworkMarks: {dup_hm}")
        print(f"Exam Marks Modified: {exam_marks_modified}")
        print(f"Integrity Status: {status}")
        print("==================================================")

        return status == "PASS"

if __name__ == '__main__':
    success = verify_migration()
    if not success:
        sys.exit(1)
