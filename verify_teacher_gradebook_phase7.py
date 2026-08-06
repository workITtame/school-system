import unittest
from datetime import date
from app import create_app
from models import db, User, Teacher, Student, Classes, Subject, Sections

class TestTeacherGradebookPhase7(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_teacher_gradebook_complete_lifecycle_and_security(self):
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
                self.skipTest("No teacher model found")

            # 2. GET /grades/ (HTML View)
            page_res = self.client.get('/grades/')
            print(f"GET /grades/ status code: {page_res.status_code}")
            self.assertEqual(page_res.status_code, 200)

            # 3. GET /grades/api/list (JSON Student Gradebook List)
            list_res = self.client.get('/grades/api/list')
            print(f"GET /grades/api/list status code: {list_res.status_code}")
            self.assertEqual(list_res.status_code, 200)
            list_data = list_res.get_json()
            self.assertIn('items', list_data)

            if list_data['items'] and len(list_data['items']) > 0:
                st_id = list_data['items'][0]['student_id']

                # 4. GET /grades/api/student/<id> (Student Gradebook Drawer Details)
                st_res = self.client.get(f'/grades/api/student/{st_id}')
                print(f"GET /grades/api/student/{st_id} status code: {st_res.status_code}")
                self.assertEqual(st_res.status_code, 200)
                st_data = st_res.get_json()
                self.assertIn('final_grade', st_data)

            # 5. GET /grades/api/statistics
            stat_res = self.client.get('/grades/api/statistics')
            print(f"GET /grades/api/statistics status code: {stat_res.status_code}")
            self.assertEqual(stat_res.status_code, 200)

            # 6. POST /grades/api/recalculate
            recalc_res = self.client.post('/grades/api/recalculate')
            print(f"POST /grades/api/recalculate status code: {recalc_res.status_code}")
            self.assertEqual(recalc_res.status_code, 200)

            # 7. POST /grades/api/publish
            pub_res = self.client.post('/grades/api/publish')
            print(f"POST /grades/api/publish status code: {pub_res.status_code}")
            self.assertEqual(pub_res.status_code, 200)

            # 8. POST /grades/api/notify
            notif_res = self.client.post('/grades/api/notify')
            print(f"POST /grades/api/notify status code: {notif_res.status_code}")
            self.assertEqual(notif_res.status_code, 200)

            # 9. POST /grades/api/export
            exp_res = self.client.post('/grades/api/export', json={'format': 'csv'})
            print(f"POST /grades/api/export status code: {exp_res.status_code}")
            self.assertEqual(exp_res.status_code, 200)

            # 10. Out-of-Scope Security Check
            out_st = Student(
                SName='طالب خارج نطاق المعلم درجات 7',
                CID=9999,
                SectionID=99,
                Gender='M'
            )
            db.session.add(out_st)
            db.session.commit()

            out_res = self.client.get(f'/grades/api/student/{out_st.SID}')
            print(f"GET Out-of-Scope Student Gradebook status code: {out_res.status_code}")
            self.assertEqual(out_res.status_code, 403)

            # Cleanup
            db.session.delete(out_st)
            db.session.commit()

if __name__ == '__main__':
    unittest.main()
