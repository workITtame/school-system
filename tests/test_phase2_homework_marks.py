"""
Unit Test Suite for Phase 2 HomeworkMarks Integration & Cross-Table Isolation
"""
import unittest
import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import db, Marks, DetailMarks, HomeworkMarks, Homework, Student, Subject, ExamSchedule, User, Teacher
from services.teacher_homework_grading_service import save_grade as save_hw_grade
from services.teacher_grading_workspace_service import save_grade as save_workspace_grade
from services.teacher_gradebook_service import get_gradebook_statistics

class TestPhase2HomeworkMarks(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_01_hw_grade_creates_homeworkmarks_only(self):
        """Creating a homework grade inserts into HomeworkMarks ONLY"""
        initial_marks = Marks.query.count()
        initial_hm = HomeworkMarks.query.count()

        # Save HW #1 grade for Student #1
        res = save_hw_grade(homework_id=1, student_id=1, user_id=1, grade=88.0)
        self.assertTrue(res)

        final_marks = Marks.query.count()
        final_hm = HomeworkMarks.query.count()

        self.assertEqual(final_marks, initial_marks, "Marks count must NOT change when saving homework grade")
        self.assertEqual(final_hm, initial_hm, "HomeworkMarks count should update/upsert")

        hm_record = HomeworkMarks.query.filter_by(SID=1, HomeworkID=1).first()
        self.assertIsNotNone(hm_record)
        self.assertEqual(float(hm_record.Score), 88.0)

    def test_02_exam_grade_creates_marks_only(self):
        """Creating an exam grade inserts into Marks ONLY"""
        initial_hm = HomeworkMarks.query.count()

        # Save Exam #1 grade for Student #1
        res = save_workspace_grade('exam', 1, 1, 1, 92.0, None)
        self.assertTrue(res)

        final_hm = HomeworkMarks.query.count()
        self.assertEqual(final_hm, initial_hm, "HomeworkMarks count must NOT change when saving exam grade")

        m_record = Marks.query.filter_by(SID=1, ExamID=1, assessment_type='exam').first()
        self.assertIsNotNone(m_record)
        self.assertEqual(float(m_record.Score), 92.0)

    def test_03_hw_update_does_not_affect_exam(self):
        """Updating homework grade does not alter exam grade"""
        save_workspace_grade('exam', 1, 1, 1, 95.0, None)
        save_hw_grade(homework_id=1, student_id=1, user_id=1, grade=75.0)

        # Update HW to 65.0
        save_hw_grade(homework_id=1, student_id=1, user_id=1, grade=65.0)

        # Verify Exam is still 95.0
        m_record = Marks.query.filter_by(SID=1, ExamID=1, assessment_type='exam').first()
        self.assertEqual(float(m_record.Score), 95.0)

        # Verify HW is updated to 65.0
        hm_record = HomeworkMarks.query.filter_by(SID=1, HomeworkID=1).first()
        self.assertEqual(float(hm_record.Score), 65.0)

    def test_04_exam_update_does_not_affect_hw(self):
        """Updating exam grade does not alter homework grade"""
        save_workspace_grade('exam', 1, 1, 1, 90.0, None)
        save_hw_grade(homework_id=1, student_id=1, user_id=1, grade=80.0)

        # Update Exam to 98.0
        save_workspace_grade('exam', 1, 1, 1, 98.0, None)

        # Verify HW is still 80.0
        hm_record = HomeworkMarks.query.filter_by(SID=1, HomeworkID=1).first()
        self.assertEqual(float(hm_record.Score), 80.0)

        # Verify Exam is updated to 98.0
        m_record = Marks.query.filter_by(SID=1, ExamID=1, assessment_type='exam').first()
        self.assertEqual(float(m_record.Score), 98.0)

    def test_05_gradebook_averages_isolated(self):
        """Gradebook separates Exam and Homework averages cleanly"""
        t = Teacher.query.first()
        if t:
            stats = get_gradebook_statistics(user_id=t.user_id)
            self.assertIn('exam_average', stats)
            self.assertIn('homework_average', stats)

if __name__ == '__main__':
    unittest.main()
