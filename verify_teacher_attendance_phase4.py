import unittest
from app import create_app
from models import db, User, Teacher, SchoolTable, Attendance, Student, Classes, Sections, Subject, Days, Lessons

class TestTeacherAttendancePhase4(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_teacher_attendance_api_and_bulk_save(self):
        with self.client:
            # Login as teacher user
            teacher_user = User.query.filter_by(role='teacher').first()
            if not teacher_user:
                self.skipTest("No teacher user found in DB")

            with self.client.session_transaction() as sess:
                sess['user_id'] = teacher_user.id
                sess['_user_id'] = str(teacher_user.id)

            teacher = Teacher.query.filter_by(user_id=teacher_user.id).first()
            if not teacher:
                self.skipTest("No teacher record linked to user")

            # Create temporary test slot if needed
            slot = SchoolTable.query.filter_by(TeacherID=teacher.TeacherID, is_deleted=False).first()
            if not slot:
                cls = Classes.query.filter_by(is_deleted=False).first()
                sec = Sections.query.filter_by(is_deleted=False).first()
                sub = Subject.query.filter_by(is_deleted=False).first()
                day = Days.query.first()
                les = Lessons.query.first()
                slot = SchoolTable(
                    TeacherID=teacher.TeacherID,
                    CID=cls.CID if cls else 1,
                    SectionID=sec.SectionID if sec else 1,
                    SubID=sub.SubID if sub else 1,
                    DayID=day.DayID if day else 1,
                    LessonID=les.LessonID if les else 1,
                    is_deleted=False
                )
                db.session.add(slot)
                db.session.commit()

            # 1. Test GET /attendance/api/lesson/<slot_id>
            res = self.client.get(f'/attendance/api/lesson/{slot.SchoolTableID}')
            print(f"GET /attendance/api/lesson/{slot.SchoolTableID} status code: {res.status_code}")
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertIn('students', data)
            self.assertIn('stats', data)

            # 2. Test POST /attendance/api/save
            students = Student.query.filter_by(CID=slot.CID, is_deleted=False).all() if slot.CID else []
            if not students:
                students = Student.query.filter_by(is_deleted=False).limit(3).all()

            if students:
                payload = {
                    'slot_id': slot.SchoolTableID,
                    'attendance': [
                        {'student_id': s.SID, 'status': 'حاضر'} for s in students[:3]
                    ]
                }
                save_res = self.client.post('/attendance/api/save', json=payload)
                print(f"POST /attendance/api/save status code: {save_res.status_code}")
                self.assertEqual(save_res.status_code, 200)
                save_data = save_res.get_json()
                self.assertTrue(save_data.get('success'))

if __name__ == '__main__':
    unittest.main()
