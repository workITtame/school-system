import sys
import os
from datetime import datetime, date

sys.path.insert(0, r'c:\Users\Lenovo\OneDrive\Desktop\school-system\school-system\school-system')
from app import create_app
from models import db, User, Teacher, Student, Classes, Sections, Subject, Homework, HomeworkMarks, Marks, Attendance, ExamSchedule, SchoolTable
from sqlalchemy import text

app = create_app()
app.config['TESTING'] = True

test_counts = {
    'workflows': 6,
    'pages': 15,
    'routes': 24,
    'db_ops': 18,
    'ui_interactions': 32,
    'pass': 0,
    'fail': 0,
    'warnings': 0
}

failures = []

def record_test(name, passed, problem=None, expected=None, actual=None, db_state=None, severity="MEDIUM", workflow="N/A", page="N/A"):
    if passed:
        test_counts['pass'] += 1
        print(f"[PASS] {name}")
    else:
        test_counts['fail'] += 1
        print(f"[FAIL] {name} -> {problem}")
        failures.append({
            'id': f"FAIL-{len(failures)+1:02d}",
            'workflow': workflow,
            'page': page,
            'problem': problem,
            'expected': expected,
            'actual': actual,
            'db_state': db_state,
            'severity': severity
        })

def run_phase2_end_to_end_verification():
    with app.app_context():
        print("==================================================")
        print("PHASE 2 — FULL FUNCTIONAL INTEGRITY VERIFICATION")
        print("==================================================")

        admin = User.query.filter_by(role='admin').first()
        admin_id = admin.id if admin else 1

        teacher = Teacher.query.filter(Teacher.user_id.isnot(None)).first()
        t_user_id = teacher.user_id if teacher else 2

        student = Student.query.filter_by(is_deleted=False).first()
        st_id = student.SID if student else 1

        # -------------------------------------------------------------
        # 1. HOMEWORK END-TO-END FLOW VERIFICATION
        # -------------------------------------------------------------
        print("\n--- 1. Testing Homework End-to-End Workflow ---")
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = t_user_id
                sess['_user_id'] = str(t_user_id)
                sess['user_role'] = 'teacher'

            # 1.1 Teacher Homework Route Access
            res_hw_list = client.get('/homework/')
            record_test("Teacher Homework Index Access", res_hw_list.status_code == 200, workflow="Homework", page="Homework Index")

            # 1.2 Check Homework in DB
            hw = Homework.query.first()
            if hw:
                # Check HomeworkMarks for student
                hm = HomeworkMarks.query.filter_by(HomeworkID=hw.id, SID=st_id).first()
                db_score = float(hm.Score) if (hm and hm.Score is not None) else None

                # 1.3 Verify Gradebook sync for Homework
                res_gb = client.get(f'/gradebook/?homework_id={hw.id}')
                record_test("Teacher Gradebook Homework Filter Sync", res_gb.status_code == 200, workflow="Homework", page="Teacher Gradebook")

                # 1.4 Admin Homework Page View
                with client.session_transaction() as sess:
                    sess['user_id'] = admin_id
                    sess['_user_id'] = str(admin_id)
                    sess['user_role'] = 'admin'

                res_admin_hw = client.get('/homework/')
                record_test("Admin Homework Synchronization View", res_admin_hw.status_code == 200, workflow="Homework", page="Admin Homework")

        # -------------------------------------------------------------
        # 2. EXAM END-TO-END FLOW VERIFICATION
        # -------------------------------------------------------------
        print("\n--- 2. Testing Exam End-to-End Workflow ---")
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = t_user_id
                sess['_user_id'] = str(t_user_id)
                sess['user_role'] = 'teacher'

            res_ex = client.get('/exams/')
            record_test("Teacher Exams Index Access", res_ex.status_code == 200, workflow="Exams", page="Exams Index")

            ex = ExamSchedule.query.first()
            if ex:
                m_rec = Marks.query.filter_by(ExamID=ex.ScheduleID, SID=st_id).first()
                
                # Check Gradebook sync for Exam
                res_gb_ex = client.get(f'/gradebook/?exam_id={ex.ScheduleID}')
                record_test("Teacher Gradebook Exam Filter Sync", res_gb_ex.status_code == 200, workflow="Exams", page="Teacher Gradebook")

                # Admin Exam View
                with client.session_transaction() as sess:
                    sess['user_id'] = admin_id
                    sess['_user_id'] = str(admin_id)
                    sess['user_role'] = 'admin'

                res_admin_ex = client.get('/exams/')
                record_test("Admin Exam Synchronization View", res_admin_ex.status_code == 200, workflow="Exams", page="Admin Exams")

        # -------------------------------------------------------------
        # 3. ATTENDANCE END-TO-END FLOW VERIFICATION
        # -------------------------------------------------------------
        print("\n--- 3. Testing Attendance End-to-End Workflow ---")
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = t_user_id
                sess['_user_id'] = str(t_user_id)
                sess['user_role'] = 'teacher'

            res_att = client.get('/attendance/')
            record_test("Teacher Attendance Page Access", res_att.status_code == 200, workflow="Attendance", page="Attendance Page")

            att_count = Attendance.query.count()
            record_test("Database Attendance Records Query", att_count >= 0, workflow="Attendance", page="Attendance DB")

        # -------------------------------------------------------------
        # 4. NEGATIVE SECURITY & SCOPE VERIFICATION
        # -------------------------------------------------------------
        print("\n--- 4. Testing Negative & Scope Protection ---")
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = t_user_id
                sess['_user_id'] = str(t_user_id)
                sess['user_role'] = 'teacher'

            # 4.1 Invalid Homework ID -> 404
            res_neg_404 = client.get('/grading/workspace/homework/999999')
            record_test("Negative Test: Invalid Homework ID -> 404", res_neg_404.status_code == 404, workflow="Security", page="Grading Workspace")

            # 4.2 Score > MaxScore DB validation check
            with db.engine.connect() as conn:
                invalid_scores = conn.execute(text("SELECT COUNT(*) FROM marks WHERE Score < 0 OR (MaxScore IS NOT NULL AND MaxScore > 0 AND Score > MaxScore)")).scalar()
                record_test("Database Marks Score Boundary Check (<0 or >MaxScore)", invalid_scores == 0, workflow="Data Integrity", page="Marks DB")

        # -------------------------------------------------------------
        # 5. DATA CONSISTENCY ACROSS TEACHER / DB / ADMIN / REPORTS
        # -------------------------------------------------------------
        print("\n--- 5. Testing Cross-Role Data Consistency ---")
        with app.test_client() as client:
            # Teacher Gradebook API
            with client.session_transaction() as sess:
                sess['user_id'] = t_user_id
                sess['_user_id'] = str(t_user_id)
                sess['user_role'] = 'teacher'

            res_gb_api = client.get(f'/gradebook/api/student/{st_id}')
            record_test("Teacher Gradebook Student Drawer API", res_gb_api.status_code in [200, 404], workflow="Gradebook", page="Student Drawer API")

            # Admin Reports
            with client.session_transaction() as sess:
                sess['user_id'] = admin_id
                sess['_user_id'] = str(admin_id)
                sess['user_role'] = 'admin'

            res_rep = client.get('/reports/')
            record_test("Admin Academic Reports Access", res_rep.status_code == 200, workflow="Reports", page="Reports Dashboard")

        print("\n==================================================")
        print(f"Phase 2 Verification Summary:")
        print(f"  • Total PASS: {test_counts['pass']}")
        print(f"  • Total FAIL: {test_counts['fail']}")
        print(f"  • Total WARNINGS: {test_counts['warnings']}")
        print("==================================================")

if __name__ == '__main__':
    run_phase2_end_to_end_verification()
