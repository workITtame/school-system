"""
Phase 4 Unit Test Suite: Complete Homework Lifecycle & Isolation Verification
"""
import unittest
import os
import sys
from datetime import date

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import db, Student, Subject, Homework, ExamSchedule, User, Teacher
from models.grade import Marks, HomeworkMarks, DetailMarks
from services.teacher_homework_service import (
    create_teacher_homework,
    publish_homework,
    delete_teacher_homework,
    get_teacher_homeworks
)
from services.teacher_homework_grading_service import (
    save_grade as save_hw_grade,
    get_homework_grading_workspace
)
from services.teacher_grading_workspace_service import save_grade as save_workspace_grade
from services.teacher_gradebook_service import get_gradebook_statistics

class TestHomeworkLifecycle(unittest.TestCase):
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
            self.student = Student(SID=1, SName="طالب التجربة", CID=1, SectionID=1)
            db.session.add(self.student)
            db.session.commit()

        self.subject = Subject.query.get(1)
        if not self.subject:
            self.subject = Subject(SubID=1, SubName="العلوم العامة", Type="أساسية", Status="نشط")
            db.session.add(self.subject)
            db.session.commit()

    def tearDown(self):
        self.app_context.pop()

    def test_01_create_homework(self):
        """1. Create Homework"""
        hw_id = create_teacher_homework(
            user_id=self.user_id,
            title="واجب العلوم الاختباري",
            sub_id=self.subject.SubID,
            class_id=self.student.CID or 1,
            section_id=self.student.SectionID or 1,
            due_date=date.today(),
            description="اختبار دورة الواجبات",
            status="مسودة"
        )
        self.assertIsNotNone(hw_id)
        hw = Homework.query.get(hw_id)
        self.assertEqual(hw.title, "واجب العلوم الاختباري")
        self.assertEqual(hw.status, "مسودة")

    def test_02_publish_homework(self):
        """2. Publish Homework"""
        hw_id = create_teacher_homework(
            user_id=self.user_id,
            title="واجب الفيزياء الاختباري",
            sub_id=self.subject.SubID,
            class_id=self.student.CID or 1,
            due_date=date.today(),
            status="مسودة"
        )
        res = publish_homework(hw_id, self.user_id)
        self.assertTrue(res)
        hw = Homework.query.get(hw_id)
        self.assertEqual(hw.status, "منشور")

    def test_03_teacher_grading_creates_homeworkmarks(self):
        """3 & 4. Teacher Grades Homework -> Stores in HomeworkMarks"""
        hw_id = create_teacher_homework(
            user_id=self.user_id,
            title="واجب الكيمياء الاختباري",
            sub_id=self.subject.SubID,
            class_id=self.student.CID or 1,
            due_date=date.today(),
            status="منشور"
        )

        res = save_hw_grade(
            homework_id=hw_id,
            student_id=self.student.SID,
            user_id=self.user_id,
            grade=85.0,
            feedback="عمل جيد جداً"
        )
        self.assertTrue(res)

        hm = HomeworkMarks.query.filter_by(SID=self.student.SID, HomeworkID=hw_id).first()
        self.assertIsNotNone(hm)
        self.assertEqual(float(hm.Score), 85.0)

        # Verify Marks count did NOT increase
        m = Marks.query.filter_by(HomeworkID=hw_id).first()
        self.assertIsNone(m, "Homework grade must NOT exist inside Marks table")

    def test_04_gradebook_and_isolation(self):
        """5 & 6. Gradebook Separation and Exam Isolation Test"""
        save_workspace_grade('exam', 1, self.student.SID, self.user_id, 95.0, None)
        save_hw_grade(1, self.student.SID, self.user_id, 75.0, "تقييم الواجب")

        # Verify initial values
        m_exam = Marks.query.filter_by(SID=self.student.SID, ExamID=1, assessment_type='exam').first()
        hm_hw = HomeworkMarks.query.filter_by(SID=self.student.SID, HomeworkID=1).first()

        self.assertIsNotNone(m_exam)
        self.assertIsNotNone(hm_hw)
        self.assertEqual(float(m_exam.Score), 95.0)
        self.assertEqual(float(hm_hw.Score), 75.0)

        # Update HW to 60.0
        save_hw_grade(1, self.student.SID, self.user_id, 60.0, "تعديل تقييم الواجب")
        m_exam_after = Marks.query.filter_by(SID=self.student.SID, ExamID=1, assessment_type='exam').first()
        hm_hw_after = HomeworkMarks.query.filter_by(SID=self.student.SID, HomeworkID=1).first()

        self.assertEqual(float(m_exam_after.Score), 95.0, "Exam grade MUST remain 95.0")
        self.assertEqual(float(hm_hw_after.Score), 60.0, "Homework grade MUST update to 60.0")

        # Update Exam to 90.0
        save_workspace_grade('exam', 1, self.student.SID, self.user_id, 90.0, None)
        m_exam_final = Marks.query.filter_by(SID=self.student.SID, ExamID=1, assessment_type='exam').first()
        hm_hw_final = HomeworkMarks.query.filter_by(SID=self.student.SID, HomeworkID=1).first()

        self.assertEqual(float(m_exam_final.Score), 90.0, "Exam grade MUST update to 90.0")
        self.assertEqual(float(hm_hw_final.Score), 60.0, "Homework grade MUST remain 60.0")

    def test_05_delete_homework_safety(self):
        """7. Delete Homework cleans up HomeworkMarks safely"""
        hw_id = create_teacher_homework(
            user_id=self.user_id,
            title="واجب المؤقت للحذف",
            sub_id=self.subject.SubID,
            class_id=self.student.CID or 1,
            due_date=date.today()
        )
        save_hw_grade(hw_id, self.student.SID, self.user_id, 90.0, "ممتاز")
        self.assertIsNotNone(HomeworkMarks.query.filter_by(HomeworkID=hw_id).first())

        res = delete_teacher_homework(hw_id, self.user_id)
        self.assertTrue(res)
        self.assertIsNone(Homework.query.get(hw_id))
        self.assertIsNone(HomeworkMarks.query.filter_by(HomeworkID=hw_id).first())

if __name__ == '__main__':
    unittest.main()
