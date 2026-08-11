import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import unittest
from datetime import date
from app import create_app
from models import db, Student, Subject, Classes, Sections, ExamSchedule, Homework, User
from models.grade import Marks, DetailMarks
from services.teacher_grading_workspace_service import save_grade, get_workspace
from services.teacher_exam_service import get_exam_students, get_exam_details
from services.teacher_homework_grading_service import get_homework_grading_workspace
from services.teacher_gradebook_service import get_student_gradebook

class HomeworkExamIsolationTestCase(unittest.TestCase):
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

        # Setup base entities (Student #1 & Subject #1)
        self.student = Student.query.get(1)
        if not self.student:
            self.student = Student(SID=1, SName="طالب تجريبي", CID=1, SectionID=1)
            db.session.add(self.student)
            db.session.commit()

        self.subject = Subject.query.get(1)
        if not self.subject:
            self.subject = Subject(SubID=1, SubName="الرياضيات الإعتيادية", Type="أساسية", Status="نشط")
            db.session.add(self.subject)
            db.session.commit()

    def tearDown(self):
        self.app_context.pop()

    def test_task_4_and_5_unified_grading_workspace_isolation(self):
        print("\n" + "="*70)
        print(" RUNNING TASK 4 & 5: UNIFIED GRADING WORKSPACE ISOLATION TEST")
        print("="*70)

        # 1. Create/Ensure Exam #1 (ID = 1)
        ex = ExamSchedule.query.filter_by(ScheduleID=1).first()
        if not ex:
            ex = ExamSchedule(ScheduleID=1, ExamName="اختبار الرياضيات الأول", SubID=self.subject.SubID, CID=self.student.CID or 1, ExamDate=date.today(), Status="منشور")
            db.session.add(ex)
            db.session.commit()

        # 2. Create/Ensure Homework #1 (ID = 1)
        hw = Homework.query.filter_by(id=1).first()
        if not hw:
            hw = Homework(id=1, title="واجب الرياضيات رقم 1", sub_id=self.subject.SubID, class_id=self.student.CID or 1, section_id=self.student.SectionID or 1, due_date=date.today(), status="منشور")
            db.session.add(hw)
            db.session.commit()

        print(f"Exam ID: {ex.ScheduleID}, Homework ID: {hw.id}, Student ID: {self.student.SID}")
        self.assertEqual(ex.ScheduleID, 1)
        self.assertEqual(hw.id, 1)

        # Clean existing test marks for student 1 and subject 1
        Marks.query.filter_by(SID=self.student.SID, SubID=self.subject.SubID).delete()
        DetailMarks.query.filter_by(SID=self.student.SID, SubID=self.subject.SubID).delete()
        db.session.commit()

        # Step 1: Save Exam = 100
        print("\n--- Step 1: Save Exam #1 grade = 100 ---")
        save_grade('exam', ex.ScheduleID, self.student.SID, self.user_id, 100.0, "درجة نهائية كاملة")

        # Step 2: Save Homework = 80
        print("--- Step 2: Save Homework #1 grade = 80 ---")
        save_grade('homework', hw.id, self.student.SID, self.user_id, 80.0, "تسليم الواجب رقم 1")

        # Step 3: Verify DB state
        print("--- Step 3: Verify DB state for Exam #1 and Homework #1 ---")
        exam_mark = Marks.query.filter_by(SID=self.student.SID, SubID=self.subject.SubID, assessment_type='exam', assessment_id=ex.ScheduleID).first()
        self.assertIsNotNone(exam_mark)
        self.assertEqual(float(exam_mark.Score), 100.0)
        self.assertEqual(exam_mark.assessment_type, 'exam')
        self.assertEqual(exam_mark.ExamID, ex.ScheduleID)
        self.assertIsNone(exam_mark.HomeworkID)

        hw_mark = Marks.query.filter_by(SID=self.student.SID, SubID=self.subject.SubID, assessment_type='homework', HomeworkID=hw.id).first()
        self.assertIsNotNone(hw_mark)
        self.assertEqual(float(hw_mark.Score), 80.0)
        self.assertEqual(hw_mark.assessment_type, 'homework')
        self.assertEqual(hw_mark.HomeworkID, hw.id)
        self.assertIsNone(hw_mark.ExamID)

        # Step 4: Change Homework 80 -> 70
        print("--- Step 4: Change Homework #1 from 80 to 70 ---")
        save_grade('homework', hw.id, self.student.SID, self.user_id, 70.0, "تعديل درجة الواجب")

        exam_mark_after_hw = Marks.query.filter_by(SID=self.student.SID, SubID=self.subject.SubID, assessment_type='exam', assessment_id=ex.ScheduleID).first()
        hw_mark_after_hw = Marks.query.filter_by(SID=self.student.SID, SubID=self.subject.SubID, assessment_type='homework', HomeworkID=hw.id).first()
        self.assertEqual(float(exam_mark_after_hw.Score), 100.0) # Exam MUST remain 100!
        self.assertEqual(float(hw_mark_after_hw.Score), 70.0)   # Homework becomes 70!

        # Step 5: Change Exam 100 -> 90
        print("--- Step 5: Change Exam #1 from 100 to 90 ---")
        save_grade('exam', ex.ScheduleID, self.student.SID, self.user_id, 90.0, "تعديل درجة الاختبار")

        exam_mark_after_exam = Marks.query.filter_by(SID=self.student.SID, SubID=self.subject.SubID, assessment_type='exam', assessment_id=ex.ScheduleID).first()
        hw_mark_after_exam = Marks.query.filter_by(SID=self.student.SID, SubID=self.subject.SubID, assessment_type='homework', HomeworkID=hw.id).first()
        self.assertEqual(float(exam_mark_after_exam.Score), 90.0) # Exam becomes 90!
        self.assertEqual(float(hw_mark_after_exam.Score), 70.0)   # Homework MUST remain 70!

        # Step 6: Verify Exams Page Services (/exams/)
        print("--- Step 6: Verify /exams/ endpoints ---")
        exam_students = get_exam_students(ex.ScheduleID, self.user_id)
        target_exam_st = next((s for s in exam_students if s['student_id'] == self.student.SID), None)
        self.assertIsNotNone(target_exam_st)
        self.assertEqual(float(target_exam_st['score']), 90.0) # MUST BE 90, NOT 70!

        # Step 7: Verify Homework Page Services (/homework/)
        print("--- Step 7: Verify /homework/ endpoints ---")
        hw_ws = get_homework_grading_workspace(hw.id, self.user_id)
        target_hw_st = next((s for s in hw_ws['students'] if s['student_id'] == self.student.SID), None)
        self.assertIsNotNone(target_hw_st)
        self.assertEqual(float(target_hw_st['grade']), 70.0) # MUST BE 70, NOT 90!

        print("\n" + "="*70)
        print(" TASK 4 & 5 ISOLATION TEST PASSED 100% CLEANLY!")
        print("="*70 + "\n")

if __name__ == '__main__':
    unittest.main()
