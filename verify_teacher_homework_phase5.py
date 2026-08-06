import unittest
from datetime import date
from app import create_app
from models import db, User, Teacher, Homework, Classes, Subject, SchoolTable

class TestTeacherHomeworkPhase5(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_teacher_homework_lifecycle_and_security(self):
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

            # 2. GET /homework/ (Teacher Workspace Page)
            res = self.client.get('/homework/')
            print(f"GET /homework/ status code: {res.status_code}")
            self.assertEqual(res.status_code, 200)

            # 3. GET /homework/api/list
            list_res = self.client.get('/homework/api/list')
            print(f"GET /homework/api/list status code: {list_res.status_code}")
            self.assertEqual(list_res.status_code, 200)
            list_data = list_res.get_json()
            self.assertTrue(list_data.get('success'))

            # 4. Create Homework API: POST /homework/api/create
            cls = Classes.query.filter_by(is_deleted=False).first()
            sub = Subject.query.filter_by(is_deleted=False).first()

            create_payload = {
                'title': 'واجب رياضي تجريبي مرحلة 5',
                'sub_id': sub.SubID if sub else 1,
                'class_id': cls.CID if cls else 1,
                'due_date': '2026-12-31',
                'description': 'وصف الواجب التجريبي لاختبار دورة الحياة بالكامل',
                'status': 'مسودة'
            }
            create_res = self.client.post('/homework/api/create', json=create_payload)
            print(f"POST /homework/api/create status code: {create_res.status_code}")
            self.assertEqual(create_res.status_code, 200)
            create_data = create_res.get_json()
            self.assertTrue(create_data.get('success'))
            created_hw_id = create_data.get('homework_id')

            # 5. GET /homework/api/details/<created_hw_id>
            details_res = self.client.get(f'/homework/api/details/{created_hw_id}')
            print(f"GET /homework/api/details/{created_hw_id} status code: {details_res.status_code}")
            self.assertEqual(details_res.status_code, 200)
            details_data = details_res.get_json()
            self.assertEqual(details_data.get('id'), created_hw_id)
            self.assertIn('students', details_data)

            # 6. Publish Homework: POST /homework/api/publish/<created_hw_id>
            pub_res = self.client.post(f'/homework/api/publish/{created_hw_id}')
            print(f"POST /homework/api/publish/{created_hw_id} status code: {pub_res.status_code}")
            self.assertEqual(pub_res.status_code, 200)

            # 7. Close Homework: POST /homework/api/close/<created_hw_id>
            close_res = self.client.post(f'/homework/api/close/{created_hw_id}')
            print(f"POST /homework/api/close/{created_hw_id} status code: {close_res.status_code}")
            self.assertEqual(close_res.status_code, 200)

            # 8. Out-of-Scope Security Check: Create homework for out-of-scope class, then attempt GET (MUST return 403 Forbidden)
            out_hw = Homework(
                title='واجب مادة خارج الصلاحيات',
                sub_id=99,
                class_id=999,
                due_date=date.today(),
                status='منشور'
            )
            db.session.add(out_hw)
            db.session.commit()

            out_res = self.client.get(f'/homework/api/details/{out_hw.id}')
            print(f"GET /homework/api/details/{out_hw.id} (Out-of-Scope) status code: {out_res.status_code}")
            self.assertEqual(out_res.status_code, 403)

            # Cleanup out_hw
            db.session.delete(out_hw)
            db.session.commit()

            # 9. Delete Homework API: POST /homework/api/delete/<created_hw_id>
            del_res = self.client.post(f'/homework/api/delete/{created_hw_id}')
            print(f"POST /homework/api/delete/{created_hw_id} status code: {del_res.status_code}")
            self.assertEqual(del_res.status_code, 200)

if __name__ == '__main__':
    unittest.main()
