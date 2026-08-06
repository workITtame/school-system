import unittest
from app import create_app
from models import db, User, Teacher, Student

class TestAdminTeacherCommunicationPhase10(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_admin_teacher_communication_center_phase10(self):
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

            # 2. GET /admin-communication/ (HTML View)
            page_res = self.client.get('/admin-communication/')
            print(f"GET /admin-communication/ status code: {page_res.status_code}")
            self.assertEqual(page_res.status_code, 200)
            self.assertIn(b'adminCommTabContent', page_res.data)
            self.assertIn(b'adminCommMainTabs', page_res.data)

            # 3. GET /admin-communication/api/announcements
            anc_res = self.client.get('/admin-communication/api/announcements')
            print(f"GET /admin-communication/api/announcements status code: {anc_res.status_code}")
            self.assertEqual(anc_res.status_code, 200)
            anc_data = anc_res.get_json()
            self.assertIn('announcements', anc_data)

            # 4. GET /admin-communication/api/messages
            msg_res = self.client.get('/admin-communication/api/messages')
            print(f"GET /admin-communication/api/messages status code: {msg_res.status_code}")
            self.assertEqual(msg_res.status_code, 200)

            # 5. GET /admin-communication/api/requests
            req_res = self.client.get('/admin-communication/api/requests')
            print(f"GET /admin-communication/api/requests status code: {req_res.status_code}")
            self.assertEqual(req_res.status_code, 200)

            # 6. GET /admin-communication/api/tasks
            tsk_res = self.client.get('/admin-communication/api/tasks')
            print(f"GET /admin-communication/api/tasks status code: {tsk_res.status_code}")
            self.assertEqual(tsk_res.status_code, 200)

            # 7. GET /admin-communication/api/conversation/501
            conv_res = self.client.get('/admin-communication/api/conversation/501')
            print(f"GET /admin-communication/api/conversation/501 status code: {conv_res.status_code}")
            self.assertEqual(conv_res.status_code, 200)

            # 8. POST /admin-communication/api/send
            send_res = self.client.post('/admin-communication/api/send', json={'message': 'رسالة تجريبية للإدارة'})
            print(f"POST /admin-communication/api/send status code: {send_res.status_code}")
            self.assertEqual(send_res.status_code, 200)

            # 9. POST /admin-communication/api/request
            cr_res = self.client.post('/admin-communication/api/request', json={
                'request_type': 'إجازة اعتيادية',
                'title': 'عنوان طلب تجريبي Phase 10',
                'description': 'شرح الطلب التجريبي المقدم للإدارة'
            })
            print(f"POST /admin-communication/api/request status code: {cr_res.status_code}")
            self.assertEqual(cr_res.status_code, 200)

            # 10. POST /admin-communication/api/acknowledge
            ack_res = self.client.post('/admin-communication/api/acknowledge', json={'id': 1001})
            self.assertEqual(ack_res.status_code, 200)

            # 11. POST /admin-communication/api/task-status
            ts_res = self.client.post('/admin-communication/api/task-status', json={'id': 3001, 'status': 'Completed'})
            self.assertEqual(ts_res.status_code, 200)

            # 12. Security Check: Non-teacher role returns 403 Forbidden / PermissionError
            student_user = User.query.filter_by(username='test_student_user_p10').first()
            if not student_user:
                student_user = User(username='test_student_user_p10', name='Test Student P10', role='student', password_hash='dummy_hash')
                db.session.add(student_user)
                db.session.commit()

            from services.admin_teacher_communication_service import get_dashboard_statistics
            with self.assertRaises(PermissionError):
                get_dashboard_statistics(student_user.id)
            print("Out-of-Scope Security Check Passed: PermissionError 403 Verified")

if __name__ == '__main__':
    unittest.main()
