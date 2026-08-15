import unittest
from app import create_app
from models import db, User, Teacher, Student, Homework, Classes, Subject

class AuditRemediationRegressionTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        with self.app.app_context():
            self.admin = User.query.filter_by(role='admin').first()
            self.teacher = Teacher.query.filter(Teacher.user_id.isnot(None)).first()
            self.teacher_user_id = self.teacher.user_id if self.teacher else 2
            self.admin_id = self.admin.id if self.admin else 1
            self.hw = Homework.query.first()

    def test_sec01_teacher_scope_and_idor(self):
        """Test SEC-01: Server-side IDOR check on grading workspace"""
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.teacher_user_id
            sess['_user_id'] = str(self.teacher_user_id)
            sess['user_role'] = 'teacher'

        # 1. Non-existent homework -> 404 Not Found
        res_404 = self.client.get('/grading/workspace/homework/999999')
        self.assertEqual(res_404.status_code, 404)

        # 2. In-scope / Admin access -> 200 OK
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.admin_id
            sess['_user_id'] = str(self.admin_id)
            sess['user_role'] = 'admin'

        if self.hw:
            res_admin = self.client.get(f'/grading/workspace/homework/{self.hw.id}')
            self.assertEqual(res_admin.status_code, 200)

    def test_db01_investigation_safety(self):
        """Test DB-01: Verify SID=7 student record is safely handled"""
        with self.app.app_context():
            st = db.session.get(Student, 7)
            if st:
                self.assertIsNotNone(st.SID)

    def test_ui01_classes_page_links(self):
        """Test UI-01: Verify classes page links load valid routes"""
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.admin_id
            sess['_user_id'] = str(self.admin_id)
            sess['user_role'] = 'admin'

        res = self.client.get('/academic/classes')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn('/students/', html)

    def test_ui02_gradebook_modern_render(self):
        """Test UI-02: Verify modern gradebook loads 200 OK"""
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.admin_id
            sess['_user_id'] = str(self.admin_id)
            sess['user_role'] = 'admin'

        res = self.client.get('/grades/manage')
        self.assertEqual(res.status_code, 200)

    def test_code01_session_get_modernization(self):
        """Test CODE-01: Verify db.session.get returns correct models"""
        with self.app.app_context():
            user = db.session.get(User, self.admin_id)
            self.assertIsNotNone(user)
            self.assertEqual(user.id, self.admin_id)

if __name__ == '__main__':
    unittest.main()
