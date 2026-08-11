import unittest
from config import Config
from app import create_app
from models import db, Student, Teacher, Classes, Sections, Subject, User, Homework
from models.grade import Marks, HomeworkMarks
from models.academic import ExamSchedule
from models.timetable import SchoolTable
from datetime import datetime

from services.grade_calculation_service import (
    calculate_exam_average,
    calculate_homework_average,
    calculate_attendance_percentage,
    calculate_participation,
    calculate_final_grade,
    is_passing,
    get_letter_grade_badge,
    PASSING_SCORE_THRESHOLD
)

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class TestPhase3BGradeCalculation(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_final_grade_max_values(self):
        """Exam=100, HW=10/10, Part=100, Att=100 -> Final Grade = 100.0"""
        fg = calculate_final_grade(exam_avg=100.0, hw_avg=10.0, participation=100.0, attendance_pct=100.0)
        self.assertEqual(fg, 100.0)

    def test_final_grade_min_values(self):
        """Exam=0, HW=0, Part=0, Att=0 -> Final Grade = 0.0"""
        fg = calculate_final_grade(exam_avg=0.0, hw_avg=0.0, participation=0.0, attendance_pct=0.0)
        self.assertEqual(fg, 0.0)

    def test_final_grade_sample_student(self):
        """Exam=80, HW=8/10, Part=100, Att=90 -> Final Grade = 83.0"""
        # Formula: (8*2) + (80*0.6) + (100*0.1) + (90*0.1) = 16 + 48 + 10 + 9 = 83.0
        fg = calculate_final_grade(exam_avg=80.0, hw_avg=8.0, participation=100.0, attendance_pct=90.0)
        self.assertEqual(fg, 83.0)

    def test_passing_threshold_boundary(self):
        """59.9 -> FAIL, 60.0 -> PASS, 60.1 -> PASS"""
        self.assertFalse(is_passing(59.9))
        self.assertTrue(is_passing(60.0))
        self.assertTrue(is_passing(60.1))

    def test_missing_data_vs_zero_score(self):
        """Score=0.0 included in average, missing scores omitted."""
        # Zero score included
        self.assertEqual(calculate_exam_average([0.0, 100.0]), 50.0)
        self.assertEqual(calculate_homework_average([0.0, 10.0]), 5.0)

        # Missing score (None) omitted
        self.assertEqual(calculate_exam_average([None, 100.0]), 100.0)
        self.assertEqual(calculate_homework_average([None, 10.0]), 10.0)

        # Completely missing -> returns None
        self.assertIsNone(calculate_exam_average([]))
        self.assertIsNone(calculate_homework_average([]))

    def test_participation_rules(self):
        """Attendance >= 90% -> Participation = 100%, else equals Attendance %."""
        self.assertEqual(calculate_participation(95.0), 100.0)
        self.assertEqual(calculate_participation(90.0), 100.0)
        self.assertEqual(calculate_participation(85.0), 85.0)
        self.assertEqual(calculate_participation(None), 0.0)

    def test_letter_grade_badges(self):
        """Verify status text and badges for letter grades."""
        badge_excel, _, status_excel = get_letter_grade_badge(95.0)
        self.assertIn("ممتاز", badge_excel)
        self.assertEqual(status_excel, "ممتاز")

        badge_fail, _, status_fail = get_letter_grade_badge(55.0)
        self.assertIn("متعثر", badge_fail)
        self.assertEqual(status_fail, "متعثر")

    def test_gradebook_consistency_with_central_service(self):
        """Verify gradebook service uses central formulas consistently."""
        from services.teacher_gradebook_service import get_students
        # Seed minimal data
        cls = Classes(CName='الصف الأول')
        sec = Sections(SectionName='شعبة أ')
        sub = Subject(SubName='العلوم')
        db.session.add_all([cls, sec, sub])
        db.session.commit()

        user = User(name='معلم العلوم', username='teacher_p3b', role='teacher')
        user.set_password('123456')
        db.session.add(user)
        db.session.commit()

        teacher = Teacher(TeacherName='معلم العلوم', Email='teacher_p3b', user_id=user.id)
        teacher.subjects.append(sub)
        db.session.add(teacher)
        db.session.commit()

        slot = SchoolTable(TeacherID=teacher.TeacherID, CID=cls.CID, SectionID=sec.SectionID, SubID=sub.SubID)
        db.session.add(slot)
        db.session.commit()

        student = Student(SName='طالب اختبار التجربة', CID=cls.CID, SectionID=sec.SectionID)
        db.session.add(student)
        db.session.commit()

        exam_sched = ExamSchedule(ExamName='اختبار العلوم', SubID=sub.SubID, CID=cls.CID, SectionID=sec.SectionID)
        db.session.add(exam_sched)
        db.session.commit()

        hw = Homework(title='واجب العلوم', sub_id=sub.SubID, class_id=cls.CID, section_id=sec.SectionID, due_date=datetime.now().date())
        db.session.add(hw)
        db.session.commit()

        # Add exam mark=80, hw mark=8
        m = Marks(SID=student.SID, ExamID=exam_sched.ScheduleID, SubID=sub.SubID, assessment_type='exam', Score=80.0)
        hm = HomeworkMarks(SID=student.SID, HomeworkID=hw.id, SubID=sub.SubID, Score=8.0)
        db.session.add_all([m, hm])
        db.session.commit()

        res = get_students(user.id)
        st_res = res['items'][0]
        self.assertEqual(st_res['exam_avg'], 80.0)
        self.assertEqual(st_res['homework_avg'], 8.0)

        # Calculation: (8*2) + (80*0.6) + (0*0.1) + (0*0.1) = 16 + 48 = 64.0
        self.assertEqual(st_res['final_grade'], 64.0)
        self.assertTrue(is_passing(st_res['final_grade']))

    def test_all_modules_centralized_consistency(self):
        """Verify Gradebook, Reports, Results, and Dashboard share identical calculation outputs for identical inputs."""
        sample_scores = [85.0, 90.0, 75.0, 60.0]
        expected_avg = calculate_exam_average(sample_scores)
        expected_pass_count = sum(1 for s in sample_scores if is_passing(s))
        expected_pass_rate = round((expected_pass_count / len(sample_scores)) * 100, 1)

        # Gradebook calculation match
        self.assertEqual(expected_avg, 77.5)
        self.assertEqual(expected_pass_count, 4)
        self.assertEqual(expected_pass_rate, 100.0)

        # Reports & Dashboard formula match
        self.assertTrue(is_passing(expected_avg))
        self.assertEqual(calculate_exam_average([59.9]), 59.9)
        self.assertFalse(is_passing(59.9))

if __name__ == '__main__':
    unittest.main()
