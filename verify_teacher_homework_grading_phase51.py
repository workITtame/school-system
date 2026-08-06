import unittest
from datetime import date
from app import create_app
from models import db, User, Teacher, Homework, Classes, Subject

class TestTeacherHomeworkGradingPhase51(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_homework_grading_workspace_lifecycle_and_security(self):
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

            # 2. Create Test Homework for Grading
            cls = Classes.query.filter_by(is_deleted=False).first()
            sub = Subject.query.filter_by(is_deleted=False).first()

            test_hw = Homework(
                title='واجب تصحيح تقييمي مرحلة 5.1',
                sub_id=sub.SubID if sub else 1,
                class_id=cls.CID if cls else 1,
                due_date=date.today(),
                status='بانتظار التصحيح'
            )
            db.session.add(test_hw)
            db.session.commit()
            hw_id = test_hw.id

            # 3. GET /homework/grading/workspace/<hw_id> (Grading Workspace API)
            ws_res = self.client.get(f'/homework/grading/workspace/{hw_id}')
            print(f"GET /homework/grading/workspace/{hw_id} status code: {ws_res.status_code}")
            self.assertEqual(ws_res.status_code, 200)
            ws_data = ws_res.get_json()
            self.assertEqual(ws_data.get('id'), hw_id)
            self.assertIn('students', ws_data)
            self.assertIn('total_submissions', ws_data)

            # 4. GET /homework/api/grading/submission/<hw_id>/<student_id>
            if ws_data.get('students') and len(ws_data['students']) > 0:
                target_st = ws_data['students'][0]
                student_id = target_st['student_id']

                sub_res = self.client.get(f'/homework/api/grading/submission/{hw_id}/{student_id}')
                print(f"GET /homework/api/grading/submission/{hw_id}/{student_id} status code: {sub_res.status_code}")
                self.assertEqual(sub_res.status_code, 200)
                sub_data = sub_res.get_json()
                self.assertEqual(sub_data.get('student_id'), student_id)

                # 5. POST /homework/api/grading/save (Save Grade & Feedback)
                save_payload = {
                    'homework_id': hw_id,
                    'student_id': student_id,
                    'grade': 9.5,
                    'feedback': 'عمل ممتازي وإجابة نموذجية دقيقة'
                }
                save_res = self.client.post('/homework/api/grading/save', json=save_payload)
                print(f"POST /homework/api/grading/save status code: {save_res.status_code}")
                self.assertEqual(save_res.status_code, 200)
                self.assertTrue(save_res.get_json().get('success'))

                # 6. POST /homework/api/grading/reopen/<hw_id>/<student_id>
                reopen_res = self.client.post(f'/homework/api/grading/reopen/{hw_id}/{student_id}')
                print(f"POST /homework/api/grading/reopen/{hw_id}/{student_id} status code: {reopen_res.status_code}")
                self.assertEqual(reopen_res.status_code, 200)

            # 7. POST /homework/api/grading/publish/<hw_id> (Publish All Grades)
            pub_res = self.client.post(f'/homework/api/grading/publish/{hw_id}')
            print(f"POST /homework/api/grading/publish/{hw_id} status code: {pub_res.status_code}")
            self.assertEqual(pub_res.status_code, 200)

            # 8. Out-of-Scope Security Check: Create homework for out-of-scope class
            out_hw = Homework(
                title='واجب خارج نطاق المعلم تصحيح',
                sub_id=99,
                class_id=9999,
                due_date=date.today(),
                status='منشور'
            )
            db.session.add(out_hw)
            db.session.commit()

            out_res = self.client.get(f'/homework/grading/workspace/{out_hw.id}')
            print(f"GET /homework/grading/workspace/{out_hw.id} (Out-of-Scope) status code: {out_res.status_code}")
            self.assertEqual(out_res.status_code, 403)

            # Cleanup
            db.session.delete(test_hw)
            db.session.delete(out_hw)
            db.session.commit()

if __name__ == '__main__':
    unittest.main()
