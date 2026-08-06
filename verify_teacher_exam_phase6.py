import unittest
from datetime import date
from app import create_app
from models import db, User, Teacher, ExamSchedule, Classes, Subject, Sections

class TestTeacherExamsPhase6(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_teacher_exams_workspace_complete_lifecycle_and_security(self):
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

            # 2. GET /exams/ (HTML Workspace View)
            page_res = self.client.get('/exams/')
            print(f"GET /exams/ status code: {page_res.status_code}")
            self.assertEqual(page_res.status_code, 200)

            # 3. GET /exams/api/list (JSON Exam List API)
            list_res = self.client.get('/exams/api/list')
            print(f"GET /exams/api/list status code: {list_res.status_code}")
            self.assertEqual(list_res.status_code, 200)
            list_data = list_res.get_json()
            self.assertIn('items', list_data)

            # 4. POST /exams/api/create (Create Exam)
            cls = Classes.query.filter_by(is_deleted=False).first()
            sub = Subject.query.filter_by(is_deleted=False).first()
            sec = Sections.query.filter_by(is_deleted=False).first()

            create_payload = {
                'title': 'اختبار الرياضيات التجريبي مرحلة 6',
                'subject_id': sub.SubID if sub else 1,
                'class_id': cls.CID if cls else 1,
                'section_id': sec.SectionID if sec else 1,
                'exam_date': date.today().strftime('%Y-%m-%d'),
                'exam_time': '09:00 ص',
                'duration': 60,
                'status': 'مسودة'
            }
            create_res = self.client.post('/exams/api/create', json=create_payload)
            print(f"POST /exams/api/create status code: {create_res.status_code}")
            self.assertEqual(create_res.status_code, 200)
            create_data = create_res.get_json()
            self.assertTrue(create_data.get('success'))
            exam_id = create_data.get('id')

            # 5. GET /exams/api/details/<id>
            det_res = self.client.get(f'/exams/api/details/{exam_id}')
            print(f"GET /exams/api/details/{exam_id} status code: {det_res.status_code}")
            self.assertEqual(det_res.status_code, 200)
            det_data = det_res.get_json()
            self.assertEqual(det_data.get('id'), exam_id)

            # 6. POST /exams/api/update/<id>
            update_res = self.client.post(f'/exams/api/update/{exam_id}', json={'title': 'اختبار الرياضيات المعدل'})
            print(f"POST /exams/api/update/{exam_id} status code: {update_res.status_code}")
            self.assertEqual(update_res.status_code, 200)

            # 7. POST /exams/api/publish/<id>
            pub_res = self.client.post(f'/exams/api/publish/{exam_id}')
            print(f"POST /exams/api/publish/{exam_id} status code: {pub_res.status_code}")
            self.assertEqual(pub_res.status_code, 200)

            # 8. POST /exams/api/close/<id>
            close_res = self.client.post(f'/exams/api/close/{exam_id}')
            print(f"POST /exams/api/close/{exam_id} status code: {close_res.status_code}")
            self.assertEqual(close_res.status_code, 200)

            # 9. POST /exams/api/duplicate/<id>
            dup_res = self.client.post(f'/exams/api/duplicate/{exam_id}')
            print(f"POST /exams/api/duplicate/{exam_id} status code: {dup_res.status_code}")
            self.assertEqual(dup_res.status_code, 200)
            dup_id = dup_res.get_json().get('id')

            # 10. GET /exams/api/students/<id>
            st_res = self.client.get(f'/exams/api/students/{exam_id}')
            print(f"GET /exams/api/students/{exam_id} status code: {st_res.status_code}")
            self.assertEqual(st_res.status_code, 200)

            # 11. GET /exams/api/results/<id>
            res_res = self.client.get(f'/exams/api/results/{exam_id}')
            print(f"GET /exams/api/results/{exam_id} status code: {res_res.status_code}")
            self.assertEqual(res_res.status_code, 200)

            # 12. POST /exams/api/restore/<id>
            restore_res = self.client.post(f'/exams/api/restore/{exam_id}')
            print(f"POST /exams/api/restore/{exam_id} status code: {restore_res.status_code}")
            self.assertEqual(restore_res.status_code, 200)

            # 13. DELETE /exams/api/delete/<id>
            del_res = self.client.delete(f'/exams/api/delete/{exam_id}')
            print(f"DELETE /exams/api/delete/{exam_id} status code: {del_res.status_code}")
            self.assertEqual(del_res.status_code, 200)

            # Cleanup duplicate if created
            if dup_id:
                self.client.delete(f'/exams/api/delete/{dup_id}')

            # 14. Out-of-Scope Security Check: Create exam for out-of-scope class
            out_exam = ExamSchedule(
                ExamName='اختبار خارج نطاق المعلم',
                SubID=99,
                CID=9999,
                SectionID=99,
                ExamDate=date.today(),
                Status='منشور'
            )
            db.session.add(out_exam)
            db.session.commit()

            out_res = self.client.get(f'/exams/api/details/{out_exam.id if hasattr(out_exam, "id") else out_exam.ScheduleID}')
            print(f"GET Out-of-Scope Exam Details status code: {out_res.status_code}")
            self.assertEqual(out_res.status_code, 403)

            # Cleanup
            db.session.delete(out_exam)
            db.session.commit()

if __name__ == '__main__':
    unittest.main()
