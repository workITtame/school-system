import unittest
from datetime import date
from app import create_app
from models import db, User, Teacher, Student, Homework, Subject, Classes

class TestProductionPhase12(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_production_hardening_and_all_modules_phase12(self):
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

            # MODULE 1: Dashboard
            dash_res = self.client.get('/dashboard')
            print(f"1. Dashboard HTTP Status: {dash_res.status_code}")
            self.assertIn(dash_res.status_code, [200, 302])

            # MODULE 2: Students Workspace
            st_res = self.client.get('/students/')
            print(f"2. Students Workspace HTTP Status: {st_res.status_code}")
            self.assertEqual(st_res.status_code, 200)

            # MODULE 3: Timetable
            tt_res = self.client.get('/timetable/')
            print(f"3. Timetable HTTP Status: {tt_res.status_code}")
            self.assertEqual(tt_res.status_code, 200)

            # MODULE 4: Attendance Center
            att_res = self.client.get('/attendance/')
            print(f"4. Attendance Center HTTP Status: {att_res.status_code}")
            self.assertEqual(att_res.status_code, 200)

            # MODULE 5: Homework Workspace
            hw_res = self.client.get('/homework/')
            print(f"5. Homework Workspace HTTP Status: {hw_res.status_code}")
            self.assertEqual(hw_res.status_code, 200)

            # MODULE 6: Unified Grading Workspace
            sub = teacher.subjects[0] if (teacher.subjects and len(teacher.subjects) > 0) else Subject.query.filter_by(is_deleted=False).first()
            cls = Classes.query.filter_by(is_deleted=False).first()
            test_hw = Homework(
                title='واجب إنتاجي تجريبي 12',
                sub_id=sub.SubID if sub else 1,
                class_id=cls.CID if cls else 1,
                due_date=date.today(),
                status='بانتظار التصحيح'
            )
            db.session.add(test_hw)
            db.session.commit()

            grd_res = self.client.get(f'/grading/workspace/homework/{test_hw.id}')
            print(f"6. Unified Grading Workspace HTTP Status: {grd_res.status_code}")
            self.assertEqual(grd_res.status_code, 200)

            # Cleanup test hw
            db.session.delete(test_hw)
            db.session.commit()

            # MODULE 7: Exams Center
            ex_res = self.client.get('/exams/')
            print(f"7. Exams Center HTTP Status: {ex_res.status_code}")
            self.assertEqual(ex_res.status_code, 200)

            # MODULE 8: Gradebook Center
            gb_res = self.client.get('/grades/')
            print(f"8. Gradebook Center HTTP Status: {gb_res.status_code}")
            self.assertEqual(gb_res.status_code, 200)

            # MODULE 9: Messages Workspace
            msg_res = self.client.get('/messages/')
            print(f"9. Messages Workspace HTTP Status: {msg_res.status_code}")
            self.assertEqual(msg_res.status_code, 200)

            # MODULE 10: Notifications Center
            notif_res = self.client.get('/notifications/')
            print(f"10. Notifications Center HTTP Status: {notif_res.status_code}")
            self.assertEqual(notif_res.status_code, 200)

            # MODULE 11: Administrative Communication Center
            ac_res = self.client.get('/admin-communication/')
            print(f"11. Admin Communication HTTP Status: {ac_res.status_code}")
            self.assertEqual(ac_res.status_code, 200)

            # MODULE 12: Profile & Settings Center
            prof_res = self.client.get('/profile/')
            print(f"12. Profile & Settings Center HTTP Status: {prof_res.status_code}")
            self.assertEqual(prof_res.status_code, 200)

            # SECURITY CHECK: Non-Teacher Scope Access -> HTTP 403 / PermissionError
            student_user = User.query.filter_by(username='test_student_user_prod_p12').first()
            if not student_user:
                student_user = User(username='test_student_user_prod_p12', name='Student Prod P12', role='student', password_hash='dummy_hash')
                db.session.add(student_user)
                db.session.commit()

            from services.teacher_profile_service import get_teacher_profile
            with self.assertRaises(PermissionError):
                get_teacher_profile(student_user.id)
            print("Security Scope Test Passed: Non-teacher access blocked with PermissionError (403)")

if __name__ == '__main__':
    unittest.main()
