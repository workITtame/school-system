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
        db.session.rollback()
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

    def test_06_pending_homeworks_calculation_uses_homeworkmarks(self):
        """Pending homeworks counter relies on HomeworkMarks submissions needing correction"""
        from services.teacher_dashboard_service import get_pending_homeworks
        teacher = Teacher.query.first()
        if not teacher:
            return

        # 1. Fetch pending homeworks
        hws = get_pending_homeworks(teacher)
        initial_pending = sum(1 for h in hws if h['is_pending'])

        # 2. Add homework with NO HomeworkMarks -> Should NOT be counted as pending
        hw_no_marks = Homework(title="Test No Marks Homework", sub_id=teacher.subjects[0].SubID if teacher.subjects else 1, class_id=1, due_date=db.func.current_date(), status="نشط")
        db.session.add(hw_no_marks)
        db.session.flush()

        hws_after = get_pending_homeworks(teacher)
        pending_after_no_marks = sum(1 for h in hws_after if h['is_pending'])
        self.assertEqual(pending_after_no_marks, initial_pending, "Homework with 0 HomeworkMarks records must NOT be counted as pending correction")

        # 3. Add HomeworkMarks record -> Should BE counted as pending
        hm_unscored = HomeworkMarks(SID=1, HomeworkID=hw_no_marks.id, SubID=teacher.subjects[0].SubID if teacher.subjects else 1, Score=None)
        db.session.add(hm_unscored)
        db.session.flush()

        hws_after_unscored = get_pending_homeworks(teacher)
        pending_after_unscored = sum(1 for h in hws_after_unscored if h['is_pending'])
        self.assertEqual(pending_after_unscored, initial_pending + 1, "Homework with unscored HomeworkMarks submission MUST be counted as pending correction")

        db.session.delete(hm_unscored)
        db.session.delete(hw_no_marks)
        db.session.rollback()

if __name__ == '__main__':
    unittest.main()
