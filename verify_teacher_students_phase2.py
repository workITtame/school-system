import unittest
from app import create_app
from models import db, User, Teacher, Student, Classes, Sections, SchoolTable, Subject

class TestTeacherStudentsPhase2(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_teacher_students_route_and_scoping(self):
        with self.client:
            # Login as teacher user
            teacher_user = User.query.filter_by(role='teacher').first()
            if not teacher_user:
                self.skipTest("No teacher user found in DB")

            with self.client.session_transaction() as sess:
                sess['user_id'] = teacher_user.id
                sess['_user_id'] = str(teacher_user.id)

            # 1. Test GET /students/ returns 200 OK
            res = self.client.get('/students/')
            print(f"GET /students/ status code for teacher: {res.status_code}")
            self.assertEqual(res.status_code, 200)

            # 2. Test GET /students/api/drawer/<id> for valid student
            teacher = Teacher.query.filter_by(user_id=teacher_user.id).first()
            if teacher:
                slots = SchoolTable.query.filter_by(TeacherID=teacher.TeacherID, is_deleted=False).all()
                cids = [s.CID for s in slots if s.CID]
                if cids:
                    st = Student.query.filter(Student.CID.in_(cids), Student.is_deleted == False).first()
                    if st:
                        drawer_res = self.client.get(f'/students/api/drawer/{st.SID}')
                        print(f"GET /students/api/drawer/{st.SID} status code: {drawer_res.status_code}")
                        self.assertEqual(drawer_res.status_code, 200)

            # 3. Test GET /students/add returns 403 Forbidden for teacher
            add_res = self.client.get('/students/add')
            print(f"GET /students/add status code for teacher: {add_res.status_code}")
            self.assertEqual(add_res.status_code, 403)

if __name__ == '__main__':
    unittest.main()
