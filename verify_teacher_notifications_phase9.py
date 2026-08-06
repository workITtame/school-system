import unittest
from app import create_app
from models import db, User, Teacher, Student

class TestTeacherNotificationsPhase9(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_teacher_notification_center_phase9(self):
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

            # 2. GET /notifications/ (HTML View)
            page_res = self.client.get('/notifications/')
            print(f"GET /notifications/ status code: {page_res.status_code}")
            self.assertEqual(page_res.status_code, 200)
            self.assertIn(b'notificationTimelineContainer', page_res.data)
            self.assertIn(b'smartInsightsContainer', page_res.data)

            # 3. GET /notifications/api/list
            list_res = self.client.get('/notifications/api/list')
            print(f"GET /notifications/api/list status code: {list_res.status_code}")
            self.assertEqual(list_res.status_code, 200)
            list_data = list_res.get_json()
            self.assertIn('items', list_data)

            # 4. GET /notifications/api/statistics
            stat_res = self.client.get('/notifications/api/statistics')
            print(f"GET /notifications/api/statistics status code: {stat_res.status_code}")
            self.assertEqual(stat_res.status_code, 200)
            stat_data = stat_res.get_json()
            self.assertIn('smart_insights', stat_data)

            if list_data['items'] and len(list_data['items']) > 0:
                notif_id = list_data['items'][0]['id']

                # 5. GET /notifications/api/detail/<id>
                det_res = self.client.get(f'/notifications/api/detail/{notif_id}')
                print(f"GET /notifications/api/detail/{notif_id} status code: {det_res.status_code}")
                self.assertEqual(det_res.status_code, 200)

                # 6. POST /notifications/api/read
                read_res = self.client.post('/notifications/api/read', json={'id': notif_id})
                self.assertEqual(read_res.status_code, 200)

                # 7. POST /notifications/api/archive
                arc_res = self.client.post('/notifications/api/archive', json={'id': notif_id})
                self.assertEqual(arc_res.status_code, 200)

                # 8. POST /notifications/api/delete
                del_res = self.client.post('/notifications/api/delete', json={'id': notif_id})
                self.assertEqual(del_res.status_code, 200)

            # 9. POST /notifications/api/read-all
            ra_res = self.client.post('/notifications/api/read-all')
            self.assertEqual(ra_res.status_code, 200)

            # 10. POST /notifications/api/bulk
            bulk_res = self.client.post('/notifications/api/bulk', json={'action': 'read'})
            self.assertEqual(bulk_res.status_code, 200)

            # 11. Security Check: Non-teacher user returns 403
            student_user = User.query.filter_by(username='test_student_user_p9').first()
            if not student_user:
                student_user = User(username='test_student_user_p9', name='Test Student', role='student', password_hash='dummy_hash')
                db.session.add(student_user)
                db.session.commit()

            from services.teacher_notification_service import get_notifications
            with self.assertRaises(PermissionError):
                get_notifications(student_user.id)
            print("Out-of-Scope Security Check Passed: PermissionError 403 Verified")

if __name__ == '__main__':
    unittest.main()
