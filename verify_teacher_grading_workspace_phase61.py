import unittest
from datetime import date
from app import create_app
from models import db, User, Teacher, Homework, ExamSchedule, Classes, Subject, Student

class TestTeacherGradingWorkspacePhase61(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_unified_grading_workspace_homework_and_exam_lifecycle(self):
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

            cls = Classes.query.filter_by(is_deleted=False).first()
            sub = Subject.query.filter_by(is_deleted=False).first()

            # Create Test Homework
            test_hw = Homework(
                title='واجب موحد تقييمي 6.1',
                sub_id=sub.SubID if sub else 1,
                class_id=cls.CID if cls else 1,
                due_date=date.today(),
                status='بانتظار التصحيح'
            )
            db.session.add(test_hw)

            # Create Test Exam
            test_exam = ExamSchedule(
                ExamName='اختبار موحد تقييمي 6.1',
                SubID=sub.SubID if sub else 1,
                CID=cls.CID if cls else 1,
                ExamDate=date.today(),
                Status='منشور'
            )
            db.session.add(test_exam)
            db.session.commit()

            hw_id = test_hw.id
            exam_id = test_exam.ScheduleID

            # 2. GET Homework Workspace Metadata (/grading/workspace/homework/<hw_id>)
            hw_ws = self.client.get(f'/grading/workspace/homework/{hw_id}')
            print(f"GET /grading/workspace/homework/{hw_id} status code: {hw_ws.status_code}")
            self.assertEqual(hw_ws.status_code, 200)
            self.assertEqual(hw_ws.get_json().get('source_type'), 'homework')

            # 3. GET Exam Workspace Metadata (/grading/workspace/exam/<exam_id>)
            ex_ws = self.client.get(f'/grading/workspace/exam/{exam_id}')
            print(f"GET /grading/workspace/exam/{exam_id} status code: {ex_ws.status_code}")
            self.assertEqual(ex_ws.status_code, 200)
            self.assertEqual(ex_ws.get_json().get('source_type'), 'exam')

            # 4. GET Students List API (/grading/api/students?source_type=homework&source_id=<hw_id>)
            st_res = self.client.get(f'/grading/api/students?source_type=homework&source_id={hw_id}')
            print(f"GET /grading/api/students status code: {st_res.status_code}")
            self.assertEqual(st_res.status_code, 200)
            students = st_res.get_json()

            if students and len(students) > 0:
                student_id = students[0]['student_id']

                # 5. GET Submission API (/grading/api/submission)
                sub_res = self.client.get(f'/grading/api/submission?source_type=homework&source_id={hw_id}&student_id={student_id}')
                print(f"GET /grading/api/submission status code: {sub_res.status_code}")
                self.assertEqual(sub_res.status_code, 200)

                # 6. POST Save Grade & Feedback (/grading/api/save)
                save_res = self.client.post('/grading/api/save', json={
                    'source_type': 'homework',
                    'source_id': hw_id,
                    'student_id': student_id,
                    'grade': 9.5,
                    'feedback': 'عمل ممتازي وإجابة دقيقة متكاملة'
                })
                print(f"POST /grading/api/save status code: {save_res.status_code}")
                self.assertEqual(save_res.status_code, 200)

                # 7. POST Auto Save Grade (/grading/api/autosave)
                auto_res = self.client.post('/grading/api/autosave', json={
                    'source_type': 'homework',
                    'source_id': hw_id,
                    'student_id': student_id,
                    'grade': 10.0,
                    'feedback': 'حفظ فوري تلقائي'
                })
                print(f"POST /grading/api/autosave status code: {auto_res.status_code}")
                self.assertEqual(auto_res.status_code, 200)

                # 8. POST Reopen Submission (/grading/api/reopen)
                reopen_res = self.client.post('/grading/api/reopen', json={
                    'source_type': 'homework',
                    'source_id': hw_id,
                    'student_id': student_id
                })
                print(f"POST /grading/api/reopen status code: {reopen_res.status_code}")
                self.assertEqual(reopen_res.status_code, 200)

            # 9. POST Bulk Publish (/grading/api/bulk)
            bulk_res = self.client.post('/grading/api/bulk', json={
                'source_type': 'homework',
                'source_id': hw_id,
                'action': 'publish'
            })
            print(f"POST /grading/api/bulk status code: {bulk_res.status_code}")
            self.assertEqual(bulk_res.status_code, 200)

            # 10. POST Export Results (/grading/api/export)
            exp_res = self.client.post('/grading/api/export', json={
                'source_type': 'homework',
                'source_id': hw_id
            })
            print(f"POST /grading/api/export status code: {exp_res.status_code}")
            self.assertEqual(exp_res.status_code, 200)

            # 11. POST Notify Students (/grading/api/notify)
            notif_res = self.client.post('/grading/api/notify', json={
                'source_type': 'homework',
                'source_id': hw_id
            })
            print(f"POST /grading/api/notify status code: {notif_res.status_code}")
            self.assertEqual(notif_res.status_code, 200)

            # 12. GET Statistics API (/grading/api/statistics)
            stat_res = self.client.get(f'/grading/api/statistics?source_type=homework&source_id={hw_id}')
            print(f"GET /grading/api/statistics status code: {stat_res.status_code}")
            self.assertEqual(stat_res.status_code, 200)

            # 13. Out-of-Scope Security Check: Create homework for out-of-scope class
            out_hw = Homework(
                title='واجب خارج نطاق المعلم تصحيح 6.1',
                sub_id=99,
                class_id=9999,
                due_date=date.today(),
                status='منشور'
            )
            db.session.add(out_hw)
            db.session.commit()

            out_res = self.client.get(f'/grading/workspace/homework/{out_hw.id}')
            print(f"GET Out-of-Scope Grading Workspace status code: {out_res.status_code}")
            self.assertEqual(out_res.status_code, 403)

            # Cleanup
            db.session.delete(test_hw)
            db.session.delete(test_exam)
            db.session.delete(out_hw)
            db.session.commit()

if __name__ == '__main__':
    unittest.main()
