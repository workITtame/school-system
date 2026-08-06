import unittest
from app import create_app
from models import db, User, Teacher, SchoolTable, Classes, Student, Attendance

class TestTeacherAttendancePermissionsAndActions(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_teacher_scope_permissions_and_actions(self):
        with self.client:
            # 1. Login as Teacher User
            teacher_user = User.query.filter_by(role='teacher').first()
            if not teacher_user:
                self.skipTest("No teacher user found in DB")

            with self.client.session_transaction() as sess:
                sess['user_id'] = teacher_user.id
                sess['_user_id'] = str(teacher_user.id)

            teacher = Teacher.query.filter_by(user_id=teacher_user.id).first()
            if not teacher:
                self.skipTest("No teacher linked to user")

            # 2. Test GET /attendance/ (verify teacher scope dropdowns)
            res = self.client.get('/attendance/')
            print(f"GET /attendance/ status code: {res.status_code}")
            self.assertEqual(res.status_code, 200)

            # 3. Test out-of-scope class access: GET /attendance/?class_id=9999 (MUST return 403 Forbidden)
            out_res = self.client.get('/attendance/?class_id=9999')
            print(f"GET /attendance/?class_id=9999 status code: {out_res.status_code}")
            self.assertEqual(out_res.status_code, 403)

            # 4. Test Lesson Workspace Drawer API access
            slot = SchoolTable.query.filter_by(TeacherID=teacher.TeacherID, is_deleted=False).first()
            if slot:
                drawer_res = self.client.get(f'/timetable/api/drawer/{slot.SchoolTableID}')
                print(f"GET /timetable/api/drawer/{slot.SchoolTableID} status code: {drawer_res.status_code}")
                self.assertEqual(drawer_res.status_code, 200)
                drawer_data = drawer_res.get_json()
                self.assertIn('students', drawer_data)

            # 5. Test out-of-scope drawer access: GET /timetable/api/drawer/9999 (MUST return 403 Forbidden)
            out_drawer = self.client.get('/timetable/api/drawer/9999')
            print(f"GET /timetable/api/drawer/9999 status code: {out_drawer.status_code}")
            self.assertEqual(out_drawer.status_code, 403)

            # 6. Test Bulk Save API
            if slot:
                students = Student.query.filter_by(CID=slot.CID, is_deleted=False).all()
                if not students:
                    students = Student.query.filter(Student.is_deleted == False, Student.CID.isnot(None)).limit(3).all()
                
                payload = {
                    'slot_id': slot.SchoolTableID,
                    'attendance': [
                        {'student_id': s.SID, 'status': 'حاضر'} for s in students
                    ]
                }
                save_res = self.client.post('/attendance/api/save', json=payload)
                print(f"POST /attendance/api/save status code: {save_res.status_code}")
                self.assertEqual(save_res.status_code, 200)
                save_data = save_res.get_json()
                self.assertTrue(save_data.get('success'))

if __name__ == '__main__':
    unittest.main()
