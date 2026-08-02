import os
import sys
from app import create_app
from models import db, User
from models.school import School
from flask_login import login_user

def run_settings_finance_qa_audit():
    print("==================================================")
    print("   STARTING SETTINGS & FINANCE QA AUDIT         ")
    print("==================================================")
    
    app = create_app()
    app.config['LOGIN_DISABLED'] = False
    results = {
        'total': 0,
        'passed': 0,
        'failed': 0,
        'details': []
    }

    def record_test(name, passed, message=""):
        results['total'] += 1
        if passed:
            results['passed'] += 1
            status = "[PASSED]"
        else:
            results['failed'] += 1
            status = "[FAILED]"
        print(f"{status} {name}: {message}")
        results['details'].append({'name': name, 'passed': passed, 'message': message})

    with app.app_context():
        # TEST 1: School Model Schema Integrity
        try:
            sch_cols = [c.name for c in School.__table__.columns]
            has_cols = 'SchoolID' in sch_cols and 'SchoolName' in sch_cols and 'Phone' in sch_cols and 'Email' in sch_cols
            record_test("School Model Schema Integrity", has_cols, f"Found columns={sch_cols}")
        except Exception as e:
            record_test("School Model Schema Integrity", False, str(e))

        # TEST 2: Admin Access to Settings (/settings)
        admin_user = User.query.filter_by(role='admin').first()
        with app.test_client() as client:
            try:
                with client.session_transaction() as sess:
                    sess['_user_id'] = str(admin_user.id)
                    sess['_fresh'] = True
                res = client.get('/settings')
                is_ok = res.status_code == 200
                record_test("Admin Access to Settings Route (/settings)", is_ok, f"Status={res.status_code}")
            except Exception as e:
                record_test("Admin Access to Settings Route (/settings)", False, str(e))

        # TEST 3: Teacher Access Blocked from Settings (/settings)
        teacher_user = User.query.filter(User.id != 1).first()
        t_app = create_app()
        with t_app.test_client() as t_client:
            try:
                with t_client.session_transaction() as sess:
                    sess['_user_id'] = str(teacher_user.id)
                res = t_client.get('/settings', follow_redirects=False)
                is_blocked = res.status_code == 302 and '/dashboard' in res.location
                record_test("Teacher Access Blocked from Settings Route", is_blocked, f"Status={res.status_code}, Redirect={res.location if hasattr(res, 'location') else 'None'}")
            except Exception as e:
                record_test("Teacher Access Blocked from Settings Route", False, str(e))

        # TEST 4: Admin Access to Finance Dashboard (/finance)
        admin_user = User.query.filter_by(id=1).first()
        with app.test_client() as a_client:
            try:
                with a_client.session_transaction() as sess:
                    sess['_user_id'] = str(admin_user.id)
                res = a_client.get('/finance', follow_redirects=False)
                is_ok = res.status_code == 200
                record_test("Admin Access to Finance Route (/finance)", is_ok, f"Status={res.status_code}")
            except Exception as e:
                record_test("Admin Access to Finance Route (/finance)", False, str(e))

        # TEST 5: Teacher Access Blocked from Finance (/finance)
        t_app2 = create_app()
        with t_app2.test_client() as t_client2:
            try:
                with t_client2.session_transaction() as sess:
                    sess['_user_id'] = str(teacher_user.id)
                res = t_client2.get('/finance', follow_redirects=False)
                is_blocked = res.status_code == 302 and '/dashboard' in res.location
                record_test("Teacher Access Blocked from Finance Route", is_blocked, f"Status={res.status_code}, Redirect={res.location if hasattr(res, 'location') else 'None'}")
            except Exception as e:
                record_test("Teacher Access Blocked from Finance Route", False, str(e))

        # TEST 6: Settings Form POST Update Action
        with app.test_client() as client:
            try:
                with client.session_transaction() as sess:
                    sess['_user_id'] = str(admin_user.id)
                    sess['_fresh'] = True
                res_post = client.post('/settings', data={'school_name': 'مدرسة الأجيال المبدعة'})
                is_ok = res_post.status_code in [200, 302]
                record_test("Settings Form Save Action", is_ok, f"Status={res_post.status_code}")
            except Exception as e:
                record_test("Settings Form Save Action", False, str(e))

    print("==================================================")
    print(f"   AUDIT COMPLETED: {results['passed']}/{results['total']} TESTS PASSED   ")
    print("==================================================")
    return results

if __name__ == "__main__":
    run_settings_finance_qa_audit()
