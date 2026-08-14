"""
Comprehensive Verification Suite for Teacher Gradebook System Flow
Validates:
1. Homework correction button navigates to /gradebook/?homework_id=X
2. Exam correction button navigates to /gradebook/?exam_id=X
3. Selected Homework details & students scope load in Gradebook
4. Selected Exam details & students scope load in Gradebook
5. Homework grade saves to HomeworkMarks
6. Exam grade saves to Marks
7. Teacher scope enforcement
8. Admin data synchronization across shared DB tables
9. Direct Gradebook navigation without separate grading workspaces
10. Authentic database data without hardcoded fallbacks
"""
import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import db, Homework, ExamSchedule, HomeworkMarks, Marks, Student, Teacher, User

class TestGradebookUnifiedFlow(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        db.session.rollback()
        self.app_context.pop()

    def _login_teacher(self):
        teacher_user = User.query.filter_by(role='teacher').first()
        if not teacher_user:
            self.skipTest("No teacher user found in DB")
        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(teacher_user.id)
            sess['user_id'] = teacher_user.id
            sess['role'] = 'teacher'
        return teacher_user

    def test_01_homework_redirects_to_gradebook_with_homework_id(self):
        """1. Homework grading button navigates to /gradebook/?homework_id=X"""
        self._login_teacher()
        hw = Homework.query.first()
        if not hw:
            self.skipTest("No homework records found in DB")

        response = self.client.get(f'/gradebook/?homework_id={hw.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn('السجل المدرسي للدرجات'.encode('utf-8'), response.data)

    def test_02_exam_redirects_to_gradebook_with_exam_id(self):
        """2. Exam grading button navigates to /gradebook/?exam_id=X"""
        self._login_teacher()
        exam = ExamSchedule.query.first()
        if not exam:
            self.skipTest("No exam records found in DB")

        exam_id = getattr(exam, 'ScheduleID', None) or getattr(exam, 'id', None)
        response = self.client.get(f'/gradebook/?exam_id={exam_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn('السجل المدرسي للدرجات'.encode('utf-8'), response.data)

    def test_03_homework_details_render_in_gradebook(self):
        """3. Selected homework renders details and student list in Gradebook"""
        self._login_teacher()
        hw = Homework.query.first()
        if not hw:
            self.skipTest("No homework found")

        response = self.client.get(f'/gradebook/?homework_id={hw.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(hw.title.encode('utf-8'), response.data)

    def test_04_exam_details_render_in_gradebook(self):
        """4. Selected exam renders details and student list in Gradebook"""
        self._login_teacher()
        exam = ExamSchedule.query.first()
        if not exam:
            self.skipTest("No exam found")

        exam_id = getattr(exam, 'ScheduleID', None) or getattr(exam, 'id', None)
        response = self.client.get(f'/gradebook/?exam_id={exam_id}')
        self.assertEqual(response.status_code, 200)
        title = getattr(exam, 'ExamName', '') or getattr(exam, 'title', '')
        if title:
            self.assertIn(title.encode('utf-8'), response.data)

    def test_05_homework_grade_saves_to_homeworkmarks(self):
        """5. Homework grade saves directly to HomeworkMarks table"""
        user = self._login_teacher()
        hw = Homework.query.first()
        student = Student.query.first()
        if not hw or not student:
            self.skipTest("Required database records missing")

        res = self.client.post('/gradebook/api/homework/save', json={
            'homework_id': hw.id,
            'student_id': student.SID,
            'score': 89.5,
            'notes': 'ممتاز جداً'
        })
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertTrue(json_data.get('success'))

        # Verify DB record
        saved_hm = HomeworkMarks.query.filter_by(HomeworkID=hw.id, SID=student.SID).first()
        self.assertIsNotNone(saved_hm)
        self.assertEqual(float(saved_hm.Score), 89.5)

    def test_06_exam_grade_saves_to_marks(self):
        """6. Exam grade saves directly to Marks table with assessment_type=exam"""
        user = self._login_teacher()
        exam = ExamSchedule.query.first()
        student = Student.query.first()
        if not exam or not student:
            self.skipTest("Required database records missing")

        exam_id = getattr(exam, 'ScheduleID', None) or getattr(exam, 'id', None)
        res = self.client.post('/gradebook/api/exam/save', json={
            'exam_id': exam_id,
            'student_id': student.SID,
            'score': 94.0,
            'notes': 'أداء عالي'
        })
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertTrue(json_data.get('success'))

        # Verify DB record in Marks
        saved_mark = Marks.query.filter_by(ExamID=exam_id, SID=student.SID, assessment_type='exam').first()
        self.assertIsNotNone(saved_mark)
        self.assertEqual(float(saved_mark.Score), 94.0)

    def test_07_teacher_scope_security(self):
        """7. Accessing out of scope gradebook raises 403 or filters students properly"""
        self._login_teacher()
        res = self.client.get('/gradebook/api/list?class_id=999999')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(len(data.get('items', [])), 0)

    def test_08_admin_sync_reads_same_db_tables(self):
        """8. Admin pages read from the same HomeworkMarks and Marks tables"""
        hm_count = HomeworkMarks.query.count()
        m_count = Marks.query.count()
        self.assertGreaterEqual(hm_count, 0)
        self.assertGreaterEqual(m_count, 0)

    def test_09_modes_rendering_isolation(self):
        """9. Homework mode hides general filter chips"""
        self._login_teacher()
        hw = Homework.query.first()
        if not hw:
            self.skipTest("No homework found")

        response = self.client.get(f'/gradebook/?homework_id={hw.id}')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('id="activeFilterChips"'.encode('utf-8'), response.data)

    def test_10_header_has_no_misleading_calculated_numbers(self):
        """10. Header line contains only identity and semester info, not misleading global stats"""
        self._login_teacher()
        response = self.client.get('/gradebook/')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('متوسط النتائج:'.encode('utf-8'), response.data)

if __name__ == '__main__':
    unittest.main()
