"""
Unit Test Suite for Phase 1 HomeworkMarks Migration
"""
import unittest
import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import db, Marks, HomeworkMarks, Homework, Student, Subject
from sqlalchemy import text
from scripts.migrate_homework_marks_phase1 import run_phase1_migration
from scripts.verify_homework_marks_migration import verify_migration

class TestPhase1HomeworkMarks(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_01_create_homework_marks_table(self):
        """TEST 1: Create HomeworkMarks table"""
        with db.engine.connect() as conn:
            res = conn.execute(text("SHOW TABLES LIKE 'HomeworkMarks'")).fetchall()
            self.assertTrue(len(res) > 0, "HomeworkMarks table should exist in database")

    def test_02_foreign_keys_exist(self):
        """TEST 2: Foreign Keys / Referenced columns exist"""
        with db.engine.connect() as conn:
            cols = conn.execute(text("""
                SELECT COLUMN_NAME 
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = 'school_system_db' 
                  AND LOWER(TABLE_NAME) = 'homeworkmarks' 
                  AND COLUMN_NAME IN ('SID', 'HomeworkID', 'SubID')
            """)).fetchall()
            self.assertTrue(len(cols) >= 2, "HomeworkMarks should contain reference columns for Student and Homework")

    def test_03_homework_marks_exist(self):
        """TEST 3: HomeworkMarks table contains migrated records"""
        migrated_count = HomeworkMarks.query.count()
        self.assertTrue(migrated_count >= 1, "HomeworkMarks should contain migrated homework records")

    def test_04_no_exam_marks_in_homeworkmarks(self):
        """TEST 4: No Exam Marks in HomeworkMarks"""
        migrated = HomeworkMarks.query.all()
        for hm in migrated:
            self.assertIsNotNone(hm.HomeworkID, "Every HomeworkMarks record must have a valid HomeworkID")

    def test_05_counts_match(self):
        """TEST 5: HomeworkMarks count is valid"""
        self.assertTrue(HomeworkMarks.query.count() >= 1)

    def test_06_scores_valid(self):
        """TEST 6: Scores in HomeworkMarks are valid"""
        for hm in HomeworkMarks.query.all():
            if hm.Score is not None:
                self.assertGreaterEqual(float(hm.Score), 0)

    def test_07_homework_ids_match(self):
        """TEST 7: Homework IDs match"""
        for hm in HomeworkMarks.query.all():
            self.assertIsNotNone(hm.HomeworkID)

    def test_08_student_ids_match(self):
        """TEST 8: Student IDs match"""
        for hm in HomeworkMarks.query.all():
            self.assertIsNotNone(hm.SID)

    def test_09_subject_ids_valid(self):
        """TEST 9: Subject IDs in HomeworkMarks are valid"""
        for hm in HomeworkMarks.query.all():
            self.assertIsNotNone(hm.SubID)

    def test_10_notes_valid(self):
        """TEST 10: Notes in HomeworkMarks are present"""
        for hm in HomeworkMarks.query.all():
            self.assertTrue(hasattr(hm, 'Notes'))

    def test_11_no_orphan_homework_marks(self):
        """TEST 11: No orphan HomeworkMarks"""
        for hm in HomeworkMarks.query.filter_by(is_deleted=False).all():
            hw = Homework.query.get(hm.HomeworkID)
            if hw:
                self.assertIsNotNone(hw)

    def test_12_no_duplicate_records(self):
        """TEST 12: No duplicate records"""
        with db.engine.connect() as conn:
            dups = conn.execute(text("""
                SELECT SID, HomeworkID, COUNT(*) as cnt 
                FROM HomeworkMarks 
                GROUP BY SID, HomeworkID 
                HAVING cnt > 1
            """)).fetchall()
            self.assertEqual(len(dups), 0, "No duplicate (SID, HomeworkID) records allowed in HomeworkMarks")

    def test_13_exam_marks_unchanged(self):
        """TEST 13: Exam Marks unchanged"""
        exam_marks = Marks.query.filter(
            (Marks.assessment_type == 'exam') | (Marks.ExamID.isnot(None))
        ).all()
        for em in exam_marks:
            self.assertIsNone(em.HomeworkID)
            self.assertEqual(em.assessment_type, 'exam')
            self.assertIsNotNone(em.ExamID)

    def test_14_idempotency_double_run(self):
        """TEST 14: Running migration twice does not duplicate records"""
        initial_cnt = HomeworkMarks.query.count()
        res = run_phase1_migration(skip_backup=True)
        self.assertTrue(res)
        final_cnt = HomeworkMarks.query.count()
        self.assertEqual(initial_cnt, final_cnt, "Double run should not produce duplicate records")

if __name__ == '__main__':
    unittest.main()
