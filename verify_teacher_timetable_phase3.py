import unittest
from app import create_app
from models import db, User, Teacher, SchoolTable

class TestTeacherTimetablePhase3(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_teacher_timetable_route_and_scoping(self):
        with self.client:
            # Login as teacher user
            teacher_user = User.query.filter_by(role='teacher').first()
            if not teacher_user:
                self.skipTest("No teacher user found in DB")

            with self.client.session_transaction() as sess:
                sess['user_id'] = teacher_user.id
                sess['_user_id'] = str(teacher_user.id)

            # 1. Test GET /timetable/ returns 200 OK
            res = self.client.get('/timetable/')
            print(f"GET /timetable/ status code for teacher: {res.status_code}")
            self.assertEqual(res.status_code, 200)

            # 2. Test GET /timetable/api/drawer/<id>
            teacher = Teacher.query.filter_by(user_id=teacher_user.id).first()
            if teacher:
                slot = SchoolTable.query.filter_by(TeacherID=teacher.TeacherID, is_deleted=False).first()
                if slot:
                    drawer_res = self.client.get(f'/timetable/api/drawer/{slot.TableID}')
                    print(f"GET /timetable/api/drawer/{slot.TableID} status code: {drawer_res.status_code}")
                    self.assertEqual(drawer_res.status_code, 200)

if __name__ == '__main__':
    unittest.main()
