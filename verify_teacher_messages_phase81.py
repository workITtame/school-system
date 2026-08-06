import unittest
from app import create_app
from models import db, User, Teacher, Student

class TestTeacherMessagesPhase81(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_teacher_student_communication_workspace_phase81(self):
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

            # 2. GET /messages/ (HTML Workspace View)
            page_res = self.client.get('/messages/')
            print(f"GET /messages/ status code: {page_res.status_code}")
            self.assertEqual(page_res.status_code, 200)
            self.assertIn(b'studentProfileDrawer', page_res.data)
            self.assertIn(b'smartSuggestionsBar', page_res.data)

            # 3. GET /messages/api/list
            list_res = self.client.get('/messages/api/list')
            print(f"GET /messages/api/list status code: {list_res.status_code}")
            self.assertEqual(list_res.status_code, 200)
            list_data = list_res.get_json()
            self.assertIn('conversations', list_data)

            if list_data['conversations'] and len(list_data['conversations']) > 0:
                conv_id = list_data['conversations'][0]['conversation_id']

                # 4. GET /messages/api/conversation/<id>
                c_res = self.client.get(f'/messages/api/conversation/{conv_id}')
                print(f"GET /messages/api/conversation/{conv_id} status code: {c_res.status_code}")
                self.assertEqual(c_res.status_code, 200)

                # 5. GET /messages/api/student/<id> (8-Tab Student Profile Payload)
                st_res = self.client.get(f'/messages/api/student/{conv_id}')
                print(f"GET /messages/api/student/{conv_id} status code: {st_res.status_code}")
                self.assertEqual(st_res.status_code, 200)
                st_data = st_res.get_json()
                self.assertIn('profile', st_data)
                self.assertIn('recent_activity', st_data)
                self.assertIn('notifications', st_data)

                # 6. POST /messages/api/pin
                pin_res = self.client.post('/messages/api/pin', json={'conversation_id': conv_id})
                self.assertEqual(pin_res.status_code, 200)

                # 7. POST /messages/api/schedule
                sch_res = self.client.post('/messages/api/schedule', json={
                    'conversation_id': conv_id,
                    'message': 'رسالة مجدولة تجريبية',
                    'schedule_time': '2026-08-07 09:00'
                })
                self.assertEqual(sch_res.status_code, 200)

            # 8. GET /messages/api/templates
            tmpl_res = self.client.get('/messages/api/templates')
            print(f"GET /messages/api/templates status code: {tmpl_res.status_code}")
            self.assertEqual(tmpl_res.status_code, 200)
            tmpl_data = tmpl_res.get_json()
            self.assertIn('templates', tmpl_data)

            # 9. Out-of-Scope Security Check (403 Forbidden)
            out_st = Student(
                SName='طالب خارج نطاق المعلم رسايل 8.1',
                CID=9999,
                SectionID=99,
                Gender='M'
            )
            db.session.add(out_st)
            db.session.commit()

            out_res = self.client.get(f'/messages/api/student/{out_st.SID}')
            print(f"GET Out-of-Scope Student Profile status code: {out_res.status_code}")
            self.assertEqual(out_res.status_code, 403)

            # Cleanup
            db.session.delete(out_st)
            db.session.commit()

if __name__ == '__main__':
    unittest.main()
