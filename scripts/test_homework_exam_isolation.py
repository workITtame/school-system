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

        # Setup base entities
        self.student = Student.query.filter_by(is_deleted=False).first()
        if not self.student:
            self.student = Student(SName="طالب تجريبي", CID=1, SectionID=1)
            db.session.add(self.student)
            db.session.commit()

        self.subject = Subject.query.filter_by(Status='نشط').first()
        if not self.subject:
            self.subject = Subject(SubName="الرياضيات الإعتيادية", Type="أساسية", Status="نشط")
            db.session.add(self.subject)
            db.session.commit()

    def tearDown(self):
        self.app_context.pop()

    def test_complete_homework_exam_isolation(self):
        print("\n" + "="*70)
        print(" RUNNING CRITICAL HOMEWORK & EXAM ISOLATION TEST SUITE")
        print("="*70)

        # 1. Create Exam #1 (ID = 1 if possible or specific ScheduleID)
        ex = ExamSchedule.query.filter_by(ScheduleID=1).first()
        if not ex:
            ex = ExamSchedule(ScheduleID=1, ExamName="اختبار الرياضيات الأول", SubID=self.subject.SubID, CID=self.student.CID or 1, ExamDate=date.today(), Status="منشور")
            db.session.add(ex)
            db.session.commit()

        # 2. Create Homework #1 (ID = 1 if possible or specific ID)
        hw = Homework.query.filter_by(id=1).first()
        if not hw:
            hw = Homework(id=1, title="واجب الرياضيات رقم 1", sub_id=self.subject.SubID, class_id=self.student.CID or 1, section_id=self.student.SectionID or 1, due_date=date.today(), status="منشور")
            db.session.add(hw)
            db.session.commit()

        print(f"Test Exam ID: {ex.ScheduleID}, Test Homework ID: {hw.id}, Student ID: {self.student.SID}")
        self.assertEqual(ex.ScheduleID, 1)
        self.assertEqual(hw.id, 1)

        # Clean existing test marks for this student and subject
        Marks.query.filter_by(SID=self.student.SID, SubID=self.subject.SubID).delete()
        DetailMarks.query.filter_by(SID=self.student.SID, SubID=self.subject.SubID).delete()
        db.session.commit()

        # Step A: Save Exam #1 grade = 70
        print("\n--- Step A: Grade Exam #1 with 70 ---")
        save_grade('exam', ex.ScheduleID, self.student.SID, self.user_id, 70.0, "أداء ممتاز بالاختبار")

        exam_mark = Marks.query.filter_by(SID=self.student.SID, SubID=self.subject.SubID, assessment_type='exam', ExamID=ex.ScheduleID).first()
        self.assertIsNotNone(exam_mark)
        self.assertEqual(float(exam_mark.Score), 70.0)
        self.assertEqual(exam_mark.assessment_type, 'exam')
        self.assertEqual(exam_mark.ExamID, ex.ScheduleID)
        self.assertIsNone(exam_mark.HomeworkID)

        # Step B: Save Homework #1 grade = 90
        print("--- Step B: Grade Homework #1 with 90 ---")
        save_grade('homework', hw.id, self.student.SID, self.user_id, 90.0, "حل واجب ممتاز")

        hw_mark = Marks.query.filter_by(SID=self.student.SID, SubID=self.subject.SubID, assessment_type='homework', HomeworkID=hw.id).first()
        self.assertIsNotNone(hw_mark)
        self.assertEqual(float(hw_mark.Score), 90.0)
        self.assertEqual(hw_mark.assessment_type, 'homework')
        self.assertEqual(hw_mark.HomeworkID, hw.id)
        self.assertIsNone(hw_mark.ExamID)

        # Verify DB Records Isolation
        print("--- Step C: DB Verification of Exam #1 vs Homework #1 ---")
        exam_mark_refreshed = Marks.query.filter_by(SID=self.student.SID, SubID=self.subject.SubID, assessment_type='exam', ExamID=ex.ScheduleID).first()
        self.assertEqual(float(exam_mark_refreshed.Score), 70.0)
        self.assertIsNone(exam_mark_refreshed.HomeworkID)

        hw_mark_refreshed = Marks.query.filter_by(SID=self.student.SID, SubID=self.subject.SubID, assessment_type='homework', HomeworkID=hw.id).first()
        self.assertEqual(float(hw_mark_refreshed.Score), 90.0)
        self.assertIsNone(hw_mark_refreshed.ExamID)

        # Step D: UI & Service Filtering Check
        print("--- Step D: Checking Service & UI Isolation ---")
        exam_students = get_exam_students(ex.ScheduleID, self.user_id)
        target_exam_st = next((s for s in exam_students if s['student_id'] == self.student.SID), None)
        self.assertIsNotNone(target_exam_st)
        self.assertEqual(float(target_exam_st['score']), 70.0) # MUST BE 70, NOT 90!

        hw_ws = get_homework_grading_workspace(hw.id, self.user_id)
        target_hw_st = next((s for s in hw_ws['students'] if s['student_id'] == self.student.SID), None)
        self.assertIsNotNone(target_hw_st)
        self.assertEqual(float(target_hw_st['grade']), 90.0) # MUST BE 90, NOT 70!

        # Step E: Update Homework 90 -> 80
        print("--- Step E: Update Homework #1 from 90 to 80 ---")
        save_grade('homework', hw.id, self.student.SID, self.user_id, 80.0, "تعديل الدرجة")
        exam_mark_after_hw_update = Marks.query.filter_by(SID=self.student.SID, SubID=self.subject.SubID, assessment_type='exam', ExamID=ex.ScheduleID).first()
        self.assertEqual(float(exam_mark_after_hw_update.Score), 70.0) # Exam score MUST stay 70!

        # Step F: Update Exam 70 -> 75
        print("--- Step F: Update Exam #1 from 70 to 75 ---")
        save_grade('exam', ex.ScheduleID, self.student.SID, self.user_id, 75.0, "تعديل درجة الاختبار")
        hw_mark_after_exam_update = Marks.query.filter_by(SID=self.student.SID, SubID=self.subject.SubID, assessment_type='homework', HomeworkID=hw.id).first()
        self.assertEqual(float(hw_mark_after_exam_update.Score), 80.0) # Homework score MUST stay 80!

        # Step G: Delete Homework #1 Isolation Check
        print("--- Step G: Delete Homework #1 & Verify Exam #1 Intact ---")
        db.session.delete(hw)
        db.session.commit()
        exam_mark_after_hw_delete = Marks.query.filter_by(SID=self.student.SID, SubID=self.subject.SubID, assessment_type='exam', ExamID=ex.ScheduleID).first()
        self.assertIsNotNone(exam_mark_after_hw_delete)
        self.assertEqual(float(exam_mark_after_hw_delete.Score), 75.0)

        # Step H: Malformed Input Error Test (Phase 17)
        print("--- Step H: Testing Malformed Inputs & Non-500 Errors ---")
        res1 = self.client.post('/grading/api/save', json={'source_type': 'homework', 'source_id': 1, 'student_id': self.student.SID, 'exam_id': 1, 'grade': 90})
        self.assertEqual(res1.status_code, 400) # Rejects exam_id for homework

        res2 = self.client.post('/grading/api/save', json={'source_type': 'invalid_type', 'source_id': 99999, 'student_id': self.student.SID, 'grade': 90})
        self.assertEqual(res2.status_code, 400)

        res3 = self.client.post('/grading/api/save', json={'source_type': 'homework', 'source_id': 'abc', 'student_id': self.student.SID, 'grade': 90})
        self.assertEqual(res3.status_code, 400)

        print("\n" + "="*70)
        print(" ALL ISOLATION & REGRESSION TESTS PASSED 100% CLEANLY!")
        print("="*70 + "\n")

if __name__ == '__main__':
    unittest.main()
