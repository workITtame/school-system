import unittest
from app import create_app
from models import db, User, Teacher, Subject, Classes, Sections, Days, Lessons, Terms, SchoolTable

class TimetableCreatorTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        with self.app.app_context():
            admin = User.query.filter_by(role='admin').first()
            self.admin_id = admin.id if admin else 1

            teacher = Teacher.query.filter_by(is_deleted=False).first()
            subject = Subject.query.filter_by(is_deleted=False).first()
            school_class = Classes.query.filter_by(is_deleted=False).first()
            section = Sections.query.filter_by(is_deleted=False).first()
            day = Days.query.first()
            lesson = Lessons.query.first()
            term = Terms.query.first()

            self.teacher_id = teacher.TeacherID
            self.sub_id = subject.SubID
            self.c_id = school_class.CID
            self.sec_id = section.SectionID
            self.day_id = day.DayID
            self.lesson_id = lesson.LessonID
            self.term_id = term.T_ID if term else None

            # Clean test slot
            SchoolTable.query.filter_by(TeacherID=self.teacher_id, DayID=self.day_id, LessonID=self.lesson_id).delete()
            db.session.commit()

    def test_timetable_builder_access_and_apis(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.admin_id
            sess['_user_id'] = str(self.admin_id)

        # 1. GET Builder Page
        res = self.client.get('/timetable/builder')
        self.assertEqual(res.status_code, 200)

        # 2. POST Assign Slot
        res_assign = self.client.post('/timetable/api/assign-slot', json={
            'class_id': self.c_id,
            'section_id': self.sec_id,
            'day_id': self.day_id,
            'lesson_id': self.lesson_id,
            'subject_id': self.sub_id,
            'teacher_id': self.teacher_id,
            'term_id': self.term_id
        })
        self.assertEqual(res_assign.status_code, 200)
        data_assign = res_assign.get_json()
        self.assertTrue(data_assign.get('success'))
        slot_id = data_assign['slot']['slot_id']

        # 3. Check Conflict
        res_conflict = self.client.post('/timetable/api/check-conflict', json={
            'teacher_id': self.teacher_id,
            'day_id': self.day_id,
            'lesson_id': self.lesson_id,
            'class_id': self.c_id + 999,
            'section_id': self.sec_id + 999
        })
        self.assertEqual(res_conflict.status_code, 200)
        self.assertTrue(res_conflict.get_json().get('has_conflict'))

        # 4. Delete Slot
        res_del = self.client.post(f'/timetable/api/delete-slot/{slot_id}')
        self.assertEqual(res_del.status_code, 200)
        self.assertTrue(res_del.get_json().get('success'))

if __name__ == '__main__':
    unittest.main()
