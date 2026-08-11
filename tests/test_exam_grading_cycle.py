"""
Test Suite: Exam & Grading Cycle Responsibility Separation & Data Integrity
"""
import unittest
import os
import sys
from datetime import date

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import db, Student, Subject, ExamSchedule, User, Teacher, Terms
from models.grade import Marks, DetailMarks, HomeworkMarks
from services.teacher_grading_workspace_service import save_grade as save_workspace_grade, get_workspace

class TestExamGradingCycle(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

        self.user = User.query.first()
        self.user_id = self.user.id if self.user else 1

        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(self.user_id)
            sess['user_id'] = self.user_id

        self.student = Student.query.get(1)
        if not self.student:
            self.student = Student(SID=1, SName="طالب الاختبارات", CID=1, SectionID=1)
            db.session.add(self.student)
            db.session.commit()

        self.subject = Subject.query.get(1)
        if not self.subject:
            self.subject = Subject(SubID=1, SubName="اللغة العربية", Type="أساسية", Status="نشط")
            db.session.add(self.subject)
            db.session.commit()

    def tearDown(self):
        self.app_context.pop()

    def test_01_exams_page_routes_and_buttons(self):
        """1. Access /exams/ and verify distinct route endpoints"""
        res = self.client.get('/exams/')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)

        # Verify buttons lead to distinct endpoints
        self.assertIn('/grades/manage', html, "Grade Management button must point to /grades/manage")
        self.assertIn('/grades/report', html, "Results statement button must point to /grades/report")

    def test_02_grading_workspace_correction_saves_in_marks(self):
        """2 & 3. Correction via Workspace saves in Marks & DetailMarks ONLY"""
        ex = ExamSchedule.query.filter_by(ScheduleID=1).first()
        if not ex:
            ex = ExamSchedule(ScheduleID=1, ExamName="اختبار المنتصف", SubID=self.subject.SubID, CID=self.student.CID or 1, ExamDate=date.today(), Status="منشور")
            db.session.add(ex)
            db.session.commit()

        initial_hm_count = HomeworkMarks.query.count()

        # Grade student 1 with score 88.0
        res = save_workspace_grade('exam', ex.ScheduleID, self.student.SID, self.user_id, 88.0, "إجابة نموذجية")
        self.assertTrue(res)

        # HomeworkMarks MUST NOT change
        self.assertEqual(HomeworkMarks.query.count(), initial_hm_count)

        # Marks MUST contain the grade
        m = Marks.query.filter_by(SID=self.student.SID, ExamID=ex.ScheduleID, assessment_type='exam').first()
        self.assertIsNotNone(m)
        self.assertEqual(float(m.Score), 88.0)
        self.assertEqual(m.assessment_type, 'exam')
        self.assertIsNone(m.HomeworkID)

    def test_03_no_duplicate_marks_on_reedit(self):
        """4. Editing existing grade updates row without creating duplicates"""
        ex_id = 1

        # Initial grade 85.0
        save_workspace_grade('exam', ex_id, self.student.SID, self.user_id, 85.0, None)
        count_1 = Marks.query.filter_by(SID=self.student.SID, ExamID=ex_id, assessment_type='exam').count()

        # Re-edit grade to 92.0
        save_workspace_grade('exam', ex_id, self.student.SID, self.user_id, 92.0, None)
        count_2 = Marks.query.filter_by(SID=self.student.SID, ExamID=ex_id, assessment_type='exam').count()

        self.assertEqual(count_1, 1)
        self.assertEqual(count_2, 1, "Re-editing grade must NOT create duplicate Marks records")

        m = Marks.query.filter_by(SID=self.student.SID, ExamID=ex_id, assessment_type='exam').first()
        self.assertEqual(float(m.Score), 92.0)

    def test_04_grade_management_and_results_pages_render(self):
        """5. /grades/manage and /grades/report render independently"""
        res_manage = self.client.get('/grades/manage')
        self.assertEqual(res_manage.status_code, 200)

        res_report = self.client.get('/grades/report')
        self.assertEqual(res_report.status_code, 200)

if __name__ == '__main__':
    unittest.main()
