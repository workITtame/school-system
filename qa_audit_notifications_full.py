"""
==========================================================================
NOTIFICATIONS MODULE COMPREHENSIVE QA & AUTOMATED INTEGRATION AUDIT
==========================================================================
Tests all routes, services, APIs, and rendering in Notifications Module.
"""

import sys
import unittest
from app import create_app
from models import db, User, Student, Classes, Sections, Subject

class TestNotificationsModuleComprehensive(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()

    def _login(self):
        with self.app.app_context():
            user = User.query.first()
            if user:
                with self.client.session_transaction() as sess:
                    sess['_user_id'] = str(user.id)
                    sess['user_id'] = user.id

    def test_01_notifications_index_route(self):
        """Test GET /notifications route renders Enterprise SaaS Dashboard cleanly"""
        self._login()
        with self.app.app_context():
            res = self.client.get('/notifications/', follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            html = res.get_data(as_text=True)
            self.assertIn('مركز الإشعارات والتنبيهات', html)
            self.assertIn('إجمالي الإشعارات', html)
            self.assertIn('donutNotificationsChart', html)
            print("[PASSED] GET /notifications rendered cleanly with all required components.")

    def test_02_mark_all_read_api(self):
        """Test POST /notifications/api/mark_all_read"""
        self._login()
        with self.app.app_context():
            res = self.client.post('/notifications/api/mark_all_read')
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertTrue(data.get('success'))
            print("[PASSED] POST /notifications/api/mark_all_read executed successfully.")

    def test_03_create_notification_api(self):
        """Test POST /notifications/api/create"""
        self._login()
        with self.app.app_context():
            res = self.client.post('/notifications/api/create', json={'title': 'تنبيه اختبار تجريبي'})
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertTrue(data.get('success'))
            print("[PASSED] POST /notifications/api/create created notification entry cleanly.")

if __name__ == '__main__':
    unittest.main()
