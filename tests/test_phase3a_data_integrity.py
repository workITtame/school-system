import unittest
from app import create_app
from models import db, Student, Teacher, Classes, Sections, Subject, User, TypeExams, Homework
from models.grade import Marks, DetailMarks, HomeworkMarks
from models.academic import ExamSchedule
from models.timetable import SchoolTable
from sqlalchemy.exc import IntegrityError

from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class TestPhase3ADataIntegrity(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Seed Class and Section
        self.cls = Classes(CName='الصف الأول الثانوي')
        self.sec = Sections(SectionName='شعبة أ')
        db.session.add_all([self.cls, self.sec])
        db.session.commit()

        # Seed Subject
        self.subject = Subject(SubName='الرياضيات الأكاديمية')
        db.session.add(self.subject)
        db.session.commit()

        # Seed Teacher User and Profile
        self.teacher_user = User(name='معلم الرياضيات', username='teacher_p3a', role='teacher')
        self.teacher_user.set_password('123456')
        db.session.add(self.teacher_user)
        db.session.commit()

        self.teacher = Teacher(
            TeacherName='معلم الرياضيات',
            Email='teacher_p3a',
            user_id=self.teacher_user.id,
            Status='نشط'
        )
        self.teacher.subjects.append(self.subject)
        db.session.add(self.teacher)
        db.session.commit()

        # Seed Timetable Slot
        self.slot = SchoolTable(
            TeacherID=self.teacher.TeacherID,
            CID=self.cls.CID,
            SectionID=self.sec.SectionID,
            SubID=self.subject.SubID
        )
        db.session.add(self.slot)
        db.session.commit()

        # Seed Students (In Scope & Out of Scope)
        self.student1 = Student(SName='طالب 1 - داخل النطاق', CID=self.cls.CID, SectionID=self.sec.SectionID)
        self.student2 = Student(SName='طالب 2 - داخل النطاق', CID=self.cls.CID, SectionID=self.sec.SectionID)
        self.out_student = Student(SName='طالب 3 - خارج النطاق', CID=999, SectionID=999)
        db.session.add_all([self.student1, self.student2, self.out_student])
        db.session.commit()

        # Seed ExamSchedule
        self.exam_sched = ExamSchedule(
            ExamName='اختبار الرياضيات الأول',
            SubID=self.subject.SubID,
            CID=self.cls.CID,
            SectionID=self.sec.SectionID,
            Status='منشور'
        )
        db.session.add(self.exam_sched)
        db.session.commit()

        from datetime import datetime
        # Seed Homework
        self.homework = Homework(
            title='واجب الجبر الأسبوعي',
            sub_id=self.subject.SubID,
            class_id=self.cls.CID,
            section_id=self.sec.SectionID,
            due_date=datetime.now().date(),
            status='منشور'
        )
        db.session.add(self.homework)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_marks_database_unique_constraint(self):
        """Verify unique constraint uq_student_exam_marks on (SID, ExamID)."""
        mark1 = Marks(
            SID=self.student1.SID,
            ExamID=self.exam_sched.ScheduleID,
            SubID=self.subject.SubID,
            TeacherID=self.teacher.TeacherID,
            assessment_type='exam',
            Score=95.0
        )
        db.session.add(mark1)
        db.session.commit()

        # Attempt duplicate (SID, ExamID)
        duplicate_mark = Marks(
            SID=self.student1.SID,
            ExamID=self.exam_sched.ScheduleID,
            SubID=self.subject.SubID,
            TeacherID=self.teacher.TeacherID,
            assessment_type='exam',
            Score=88.0
        )
        db.session.add(duplicate_mark)
        with self.assertRaises(IntegrityError):
            db.session.commit()
        db.session.rollback()

    def test_marks_valid_combinations(self):
        """Verify different students in same Exam and same student in different Exams are allowed."""
        mark_st1 = Marks(
            SID=self.student1.SID,
            ExamID=self.exam_sched.ScheduleID,
            SubID=self.subject.SubID,
            assessment_type='exam',
            Score=90.0
        )
        mark_st2 = Marks(
            SID=self.student2.SID,
            ExamID=self.exam_sched.ScheduleID,
            SubID=self.subject.SubID,
            assessment_type='exam',
            Score=85.0
        )
        db.session.add_all([mark_st1, mark_st2])
        db.session.commit()

        self.assertEqual(Marks.query.count(), 2)

    def test_gradebook_real_data_no_mock_values(self):
        """Verify Gradebook derives values from Marks and HomeworkMarks without pseudo SID values."""
        from services.teacher_gradebook_service import get_students, get_gradebook_statistics

        # 1. Initially no grades in DB
        res_empty = get_students(self.teacher_user.id)
        items_empty = res_empty['items']
        self.assertEqual(len(items_empty), 2)
        st1_data = next(i for i in items_empty if i['student_id'] == self.student1.SID)
        self.assertEqual(st1_data['homework_avg'], '—')
        self.assertEqual(st1_data['exam_avg'], '—')

        # 2. Insert real Exam Mark & Homework Mark
        exam_mark = Marks(
            SID=self.student1.SID,
            ExamID=self.exam_sched.ScheduleID,
            SubID=self.subject.SubID,
            TeacherID=self.teacher.TeacherID,
            assessment_type='exam',
            Score=92.0
        )
        hw_mark = HomeworkMarks(
            SID=self.student1.SID,
            HomeworkID=self.homework.id,
            SubID=self.subject.SubID,
            TeacherID=self.teacher.TeacherID,
            Score=88.0
        )
        db.session.add_all([exam_mark, hw_mark])
        db.session.commit()

        # 3. Gradebook reflects DB update dynamically
        res_updated = get_students(self.teacher_user.id)
        st1_updated = next(i for i in res_updated['items'] if i['student_id'] == self.student1.SID)
        self.assertEqual(st1_updated['exam_avg'], 92.0)
        self.assertEqual(st1_updated['homework_avg'], 88.0)

        # Verify statistics KPI
        kpi = get_gradebook_statistics(self.teacher_user.id)
        self.assertEqual(kpi['exam_average'], 92.0)
        self.assertEqual(kpi['homework_average'], 88.0)

    def test_teacher_scope_isolation_in_gradebook(self):
        """Verify out-of-scope student is omitted from teacher's gradebook."""
        from services.teacher_gradebook_service import get_students
        res = get_students(self.teacher_user.id)
        student_ids = [s['student_id'] for s in res['items']]
        self.assertIn(self.student1.SID, student_ids)
        self.assertIn(self.student2.SID, student_ids)
        self.assertNotIn(self.out_student.SID, student_ids)

if __name__ == '__main__':
    unittest.main()
