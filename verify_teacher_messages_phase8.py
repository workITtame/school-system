import unittest
from app import create_app
from models import db, User, Teacher, Student

class TestTeacherMessagesPhase8(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_teacher_messages_complete_lifecycle_and_security(self):
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

            # 2. GET /messages/ (HTML View)
            page_res = self.client.get('/messages/')
            print(f"GET /messages/ status code: {page_res.status_code}")
            self.assertEqual(page_res.status_code, 200)
            self.assertIn(b'conversationListContainer', page_res.data)
            self.assertIn(b'chatWorkspaceContainer', page_res.data)

            # 3. GET /messages/api/list (JSON Conversations List)
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
                c_data = c_res.get_json()
                self.assertIn('messages', c_data)
                self.assertIn('student', c_data)

                # 5. POST /messages/api/send
                send_res = self.client.post('/messages/api/send', json={
                    'conversation_id': conv_id,
                    'message': 'رسالة تجريبية لاختبار مرحلة الرسائل 8'
                })
                print(f"POST /messages/api/send status code: {send_res.status_code}")
                self.assertEqual(send_res.status_code, 200)

                # 6. POST /messages/api/read
                read_res = self.client.post('/messages/api/read', json={'conversation_id': conv_id})
                self.assertEqual(read_res.status_code, 200)

                # 7. POST /messages/api/archive
                arc_res = self.client.post('/messages/api/archive', json={'conversation_id': conv_id})
                self.assertEqual(arc_res.status_code, 200)

            # 8. POST /messages/api/bulk
            bulk_res = self.client.post('/messages/api/bulk', json={
                'student_ids': [1, 2],
                'message': 'إشعار جماعي تجريبي لاختبار Phase 8'
            })
            print(f"POST /messages/api/bulk status code: {bulk_res.status_code}")
            self.assertEqual(bulk_res.status_code, 200)

            # 9. GET /messages/api/search
            srch_res = self.client.get('/messages/api/search?q=أحمد')
            print(f"GET /messages/api/search status code: {srch_res.status_code}")
            self.assertEqual(srch_res.status_code, 200)

            # 10. Out-of-Scope Security Check (403 Forbidden)
            out_st = Student(
                SName='طالب خارج نطاق المعلم رسائل 8',
                CID=9999,
                SectionID=99,
                Gender='M'
            )
            db.session.add(out_st)
            db.session.commit()

            out_res = self.client.get(f'/messages/api/conversation/{out_st.SID}')
            print(f"GET Out-of-Scope Conversation status code: {out_res.status_code}")
            self.assertEqual(out_res.status_code, 403)

            # Cleanup
            db.session.delete(out_st)
            db.session.commit()

if __name__ == '__main__':
    unittest.main()
