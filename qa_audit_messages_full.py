"""
==========================================================================
MESSAGES MODULE COMPREHENSIVE QA & AUTOMATED INTEGRATION AUDIT
==========================================================================
Tests all routes, services, APIs, and rendering in Messages Module.
"""

import sys
import unittest
from app import create_app
from models import db, User, Message, Student, Classes, Sections, Subject

class TestMessagesModuleComprehensive(unittest.TestCase):
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

    def test_01_messages_index_route(self):
        """Test GET /messages route renders Enterprise SaaS Dashboard cleanly"""
        self._login()
        with self.app.app_context():
            res = self.client.get('/messages/', follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            html = res.get_data(as_text=True)
            self.assertIn('مركز الرسائل والتواصل الأكاديمي', html)
            self.assertIn('إجمالي الرسائل', html)
            self.assertIn('donutMessagesChart', html)
            print("[PASSED] GET /messages rendered cleanly with all required components.")

    def test_02_conversations_api(self):
        """Test GET /messages/api/conversations"""
        self._login()
        with self.app.app_context():
            res = self.client.get('/messages/api/conversations')
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertTrue(data.get('success'))
            self.assertIn('conversations', data)
            print(f"[PASSED] GET /messages/api/conversations returned {len(data['conversations'])} active conversations.")

    def test_03_send_message_api(self):
        """Test POST /messages/api/send"""
        self._login()
        with self.app.app_context():
            user = User.query.first()
            other_user = User.query.filter(User.id != user.id).first()
            if not other_user:
                other_user = User(name="Test Recipient", email="testrecip@school.edu", role="teacher")
                db.session.add(other_user)
                db.session.commit()

            res = self.client.post('/messages/api/send', json={
                'recipient_id': other_user.id,
                'content': 'رسالة تجريبية للاختبار والتأكد من العمل في القسم'
            })
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertTrue(data.get('success'))
            print("[PASSED] POST /messages/api/send created message record successfully.")

    def test_04_thread_api(self):
        """Test GET /messages/api/thread/<user_id>"""
        self._login()
        with self.app.app_context():
            user = User.query.first()
            other_user = User.query.filter(User.id != user.id).first()
            if other_user:
                res = self.client.get(f'/messages/api/thread/{other_user.id}')
                self.assertEqual(res.status_code, 200)
                data = res.get_json()
                self.assertTrue(data.get('success'))
                self.assertIn('messages', data)
                print(f"[PASSED] GET /messages/api/thread/{other_user.id} returned {len(data['messages'])} messages.")

if __name__ == '__main__':
    unittest.main()
