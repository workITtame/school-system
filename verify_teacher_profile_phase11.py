import unittest
from app import create_app
from models import db, User, Teacher

class TestTeacherProfilePhase11(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_teacher_profile_center_phase11(self):
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

            # 2. GET /profile/ (HTML View)
            page_res = self.client.get('/profile/')
            print(f"GET /profile/ status code: {page_res.status_code}")
            self.assertEqual(page_res.status_code, 200)
            self.assertIn(b'teacherProfilePageContainer', page_res.data)
            self.assertIn(b'profileTabContent', page_res.data)

            # 3. GET /profile/api/profile
            prof_res = self.client.get('/profile/api/profile')
            print(f"GET /profile/api/profile status code: {prof_res.status_code}")
            self.assertEqual(prof_res.status_code, 200)
            prof_data = prof_res.get_json()
            self.assertIn('name', prof_data)

            # 4. GET /profile/api/preferences
            pref_res = self.client.get('/profile/api/preferences')
            print(f"GET /profile/api/preferences status code: {pref_res.status_code}")
            self.assertEqual(pref_res.status_code, 200)

            # 5. GET /profile/api/security
            sec_res = self.client.get('/profile/api/security')
            print(f"GET /profile/api/security status code: {sec_res.status_code}")
            self.assertEqual(sec_res.status_code, 200)

            # 6. GET /profile/api/sessions
            sess_res = self.client.get('/profile/api/sessions')
            print(f"GET /profile/api/sessions status code: {sess_res.status_code}")
            self.assertEqual(sess_res.status_code, 200)

            # 7. POST /profile/api/update
            upd_res = self.client.post('/profile/api/update', json={
                'name': teacher.TeacherName,
                'phone': '0509998877',
                'qualification': 'ماجستير مناهج وطرق تدريس',
                'bio': 'معلم تخصصي متميز'
            })
            print(f"POST /profile/api/update status code: {upd_res.status_code}")
            self.assertEqual(upd_res.status_code, 200)

            # 8. POST /profile/api/password
            pass_res = self.client.post('/profile/api/password', json={
                'current_password': 'old_password',
                'new_password': 'new_secure_password_123'
            })
            print(f"POST /profile/api/password status code: {pass_res.status_code}")
            self.assertEqual(pass_res.status_code, 200)

            # 9. POST /profile/api/preferences
            spref_res = self.client.post('/profile/api/preferences', json={'notify_homework': True, 'notify_exams': False})
            print(f"POST /profile/api/preferences status code: {spref_res.status_code}")
            self.assertEqual(spref_res.status_code, 200)

            # 10. POST /profile/api/dashboard
            sdash_res = self.client.post('/profile/api/dashboard', json={'default_landing': '/dashboard/'})
            print(f"POST /profile/api/dashboard status code: {sdash_res.status_code}")
            self.assertEqual(sdash_res.status_code, 200)

            # 11. GET /profile/api/export
            exp_res = self.client.get('/profile/api/export?format=json')
            print(f"GET /profile/api/export status code: {exp_res.status_code}")
            self.assertEqual(exp_res.status_code, 200)

            # 12. Security Check: Non-teacher role returns 403 Forbidden / PermissionError
            student_user = User.query.filter_by(username='test_student_user_p11').first()
            if not student_user:
                student_user = User(username='test_student_user_p11', name='Test Student P11', role='student', password_hash='dummy_hash')
                db.session.add(student_user)
                db.session.commit()

            from services.teacher_profile_service import get_teacher_profile
            with self.assertRaises(PermissionError):
                get_teacher_profile(student_user.id)
            print("Out-of-Scope Security Check Passed: PermissionError 403 Verified")

if __name__ == '__main__':
    unittest.main()
