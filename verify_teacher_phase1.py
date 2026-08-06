import sys
import unittest
from app import create_app
from models import db, User, Teacher

class TestTeacherDashboardPhase1(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_admin_route_protection_403(self):
        """Verify that teacher user receives 403 Forbidden on admin routes."""
        # Find or create a teacher user
        teacher_user = User.query.filter_by(role='teacher').first()
        if not teacher_user:
            teacher_user = User(username='test_teacher', name='معلم اختباري', role='teacher')
            teacher_user.set_password('123456')
            db.session.add(teacher_user)
            db.session.commit()

        with self.client.session_transaction() as sess:
            sess['user_id'] = teacher_user.id
            sess['user_role'] = 'teacher'
            sess['_user_id'] = str(teacher_user.id)

        # Attempt to access admin routes like /teacher/ (admin teacher management list)
        response = self.client.get('/teacher/')
        print("GET /teacher/ response status code for teacher:", response.status_code)
        self.assertEqual(response.status_code, 403)

    def test_teacher_dashboard_route(self):
        """Verify /teacher/dashboard loads correctly for teacher."""
        teacher_user = User.query.filter_by(role='teacher').first()
        if not teacher_user:
            teacher_user = User(username='test_teacher', name='معلم اختباري', role='teacher')
            teacher_user.set_password('123456')
            db.session.add(teacher_user)
            db.session.commit()

        with self.client.session_transaction() as sess:
            sess['user_id'] = teacher_user.id
            sess['user_role'] = 'teacher'
            sess['_user_id'] = str(teacher_user.id)

        response = self.client.get('/teacher/dashboard')
        print("GET /teacher/dashboard status code:", response.status_code)
        self.assertEqual(response.status_code, 200)
        self.assertIn('لوحة المعلم'.encode('utf-8'), response.data)

    def test_dashboard_redirect_for_teacher(self):
        """Verify /dashboard redirects teacher to /teacher/dashboard."""
        teacher_user = User.query.filter_by(role='teacher').first()
        if not teacher_user:
            teacher_user = User(username='test_teacher', name='معلم اختباري', role='teacher')
            teacher_user.set_password('123456')
            db.session.add(teacher_user)
            db.session.commit()

        with self.client.session_transaction() as sess:
            sess['user_id'] = teacher_user.id
            sess['user_role'] = 'teacher'
            sess['_user_id'] = str(teacher_user.id)

        response = self.client.get('/dashboard')
        print("GET /dashboard redirect status code:", response.status_code, "Location:", response.location)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/teacher/dashboard', response.location)

if __name__ == '__main__':
    unittest.main()
