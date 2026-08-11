import unittest
import sys, os
from datetime import date

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import db, User, Teacher, Student, Classes, Sections, Subject, ExamSchedule, Homework, SchoolTable

class Phase2TeacherPermissionsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_teacher_scope_validation_and_permission_enforcement(self):
        with self.app.app_context():
            # 1. Admin Manager access check
            admin_user = User.query.filter_by(role='admin').first()
            self.assertIsNotNone(admin_user, "Admin user must exist")

            with self.client.session_transaction() as sess:
                sess['_user_id'] = str(admin_user.id)
                sess['user_id'] = admin_user.id
                sess['user_role'] = 'admin'

            # Admin can access reports, students, exams, homework
            res_admin_rep = self.client.get('/reports/student')
            self.assertEqual(res_admin_rep.status_code, 200, "Admin can access student reports")

            # 2. Teacher User with Scope check
            teacher = Teacher.query.filter(Teacher.user_id.isnot(None)).first()
            if not teacher:
                teacher = Teacher.query.first()
            self.assertIsNotNone(teacher, "Teacher profile must exist")
            teacher_user = User.query.get(teacher.user_id) if teacher.user_id else User.query.filter_by(role='teacher').first()

            # Find a student in teacher's scope vs out-of-scope student
            slots = SchoolTable.query.filter_by(TeacherID=teacher.TeacherID, is_deleted=False).all()
            teacher_class_ids = {s.CID for s in slots if s.CID}

            in_scope_student = Student.query.filter(Student.is_deleted == False, Student.CID.in_(list(teacher_class_ids))).first() if teacher_class_ids else None
            out_scope_student = Student.query.filter(Student.is_deleted == False, ~Student.CID.in_(list(teacher_class_ids))).first() if teacher_class_ids else None

            # Switch session to Teacher
            with self.client.session_transaction() as sess:
                sess['_user_id'] = str(teacher_user.id)
                sess['user_id'] = teacher_user.id
                sess['user_role'] = 'teacher'

            # 3. Manual student_id change check
            if out_scope_student:
                res_out = self.client.get(f'/students/view/{out_scope_student.SID}')
                self.assertEqual(res_out.status_code, 403, "Access to out-of-scope student profile must be 403 Forbidden")

                res_drawer_out = self.client.get(f'/students/api/drawer/{out_scope_student.SID}')
                self.assertEqual(res_drawer_out.status_code, 403, "Drawer API for out-of-scope student must be 403 Forbidden")

                res_rep_out = self.client.get(f'/reports/student?student_id={out_scope_student.SID}')
                self.assertEqual(res_rep_out.status_code, 403, "Report for out-of-scope student must be 403 Forbidden")

            if in_scope_student:
                res_in = self.client.get(f'/students/view/{in_scope_student.SID}')
                self.assertEqual(res_in.status_code, 200, "Access to in-scope student profile must be 200 OK")

            # 4. Manual exam_id change check
            all_classes = Classes.query.filter_by(is_deleted=False).all()
            out_class = next((c for c in all_classes if c.CID not in teacher_class_ids), None)
            
            if out_class:
                # Attempt to create exam out of scope
                res_add_exam = self.client.post('/exams/add', data={
                    'exam_type': 'اختبار غير مصرح',
                    'sub_id': 1,
                    'class_id': out_class.CID,
                    'exam_date': date.today().strftime('%Y-%m-%d')
                })
                self.assertEqual(res_add_exam.status_code, 403, "Creating exam out of scope must be 403 Forbidden")

                # Find out of scope exam
                out_exam = ExamSchedule.query.filter(ExamSchedule.CID == out_class.CID).first()
                if out_exam:
                    res_edit_exam = self.client.post(f'/exams/edit/{out_exam.ScheduleID}', data={'title': 'تعديل حاقد'})
                    self.assertEqual(res_edit_exam.status_code, 403, "Editing out-of-scope exam must be 403 Forbidden")

                    res_del_exam = self.client.post(f'/exams/delete/{out_exam.ScheduleID}')
                    self.assertEqual(res_del_exam.status_code, 403, "Deleting out-of-scope exam must be 403 Forbidden")

            # 5. Manual homework_id change check
            if out_class:
                res_add_hw = self.client.post('/homework/add', data={
                    'title': 'واجب غير مصرح',
                    'sub_id': 1,
                    'class_id': out_class.CID,
                    'due_date': date.today().strftime('%Y-%m-%d')
                })
                self.assertEqual(res_add_hw.status_code, 403, "Creating homework out of scope must be 403 Forbidden")

                out_hw = Homework.query.filter(Homework.class_id == out_class.CID).first()
                if out_hw:
                    res_edit_hw = self.client.post(f'/homework/edit/{out_hw.id}', data={'title': 'تعديل واجب'})
                    self.assertEqual(res_edit_hw.status_code, 403, "Editing out-of-scope homework must be 403 Forbidden")

                    res_del_hw = self.client.post(f'/homework/delete/{out_hw.id}')
                    self.assertEqual(res_del_hw.status_code, 403, "Deleting out-of-scope homework must be 403 Forbidden")

            # 6. Check No-Timetable Teacher does NOT get full access
            dummy_teacher_user = User.query.filter_by(role='teacher', username='uyeyry@gmai.com').first()
            if dummy_teacher_user:
                with self.client.session_transaction() as sess:
                    sess['_user_id'] = str(dummy_teacher_user.id)
                    sess['user_id'] = dummy_teacher_user.id
                    sess['user_role'] = 'teacher'

                res_rep_dummy = self.client.get('/reports/student')
                self.assertEqual(res_rep_dummy.status_code, 200)
                # Check that students dropdown is empty in template context or response
                res_data_str = res_rep_dummy.data.decode('utf-8')
                self.assertNotIn('محمد أحمد عبد الله العريقي', res_data_str, "No-timetable teacher must NOT see all students")

if __name__ == '__main__':
    unittest.main()
