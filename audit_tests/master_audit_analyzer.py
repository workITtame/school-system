import sys
import os
import glob
import re

sys.path.insert(0, r'c:\Users\Lenovo\OneDrive\Desktop\school-system\school-system\school-system')
from app import create_app
from models import db, User, Student, Teacher, Classes, Sections, Subject, Homework, ExamSchedule, Attendance, Marks, Notification, Message
from sqlalchemy import inspect, text

app = create_app()
app.config['TESTING'] = True

findings = []

def audit_routes_and_rbac():
    with app.app_context():
        # Get all users for testing
        admin_user = User.query.filter_by(role='admin').first()
        admin_id = admin_user.id if admin_user else 1

        teachers = Teacher.query.filter(Teacher.user_id.isnot(None)).all()
        t1_user_id = teachers[0].user_id if len(teachers) > 0 else 2
        t2_user_id = teachers[1].user_id if len(teachers) > 1 else t1_user_id

        print(f"--> Testing Role-Based Access Control & Scope Isolation...")
        print(f"    Admin ID: {admin_id}, Teacher 1 ID: {t1_user_id}, Teacher 2 ID: {t2_user_id}")

        # IDOR Test 1: Teacher 1 accessing Teacher 2's specific homework workspace or gradebook
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['_user_id'] = str(t1_user_id)
                sess['user_id'] = t1_user_id
                sess['user_role'] = 'teacher'

            # Test IDOR on /grading/workspace/homework/9999 or teacher 2 homework
            res = client.get('/grading/workspace/homework/9999')
            if res.status_code == 200:
                findings.append({
                    'id': 'SEC-01',
                    'category': 'Authorization / IDOR',
                    'severity': 'HIGH',
                    'page': 'Unified Grading Workspace',
                    'route': '/grading/workspace/<type>/<id>',
                    'file': 'routes/grading_routes.py',
                    'line': 27,
                    'problem': 'Non-existent or unauthorized homework ID returns HTTP 200 without strict scope check',
                    'cause': 'Route fetches homework without validating whether homework ID belongs to current teacher or exists',
                    'expected': 'HTTP 404 or 403 Forbidden',
                    'actual': f'HTTP {res.status_code}',
                    'db_impact': 'Read attempt on unauthorized records',
                    'sec_impact': 'IDOR vulnerability allowing teachers to inspect non-scoped homework data',
                    'recommendation': 'Add teacher scope validation check (teacher_id == current_teacher.id)',
                    'repro': 'GET /grading/workspace/homework/9999 under Teacher session',
                    'priority': 'P1'
                })

def audit_templates_and_hardcoded_content():
    template_files = glob.glob(r'c:\Users\Lenovo\OneDrive\Desktop\school-system\school-system\school-system\templates/**/*.html', recursive=True)
    print(f"--> Auditing {len(template_files)} Jinja2 templates for static data, legacy markup, and hardcoded values...")

    hardcoded_patterns = [
        (r'href="#"', 'Empty anchor tag href="#" found in template'),
        (r'onclick="alert\(', 'Raw JS alert() placeholder in onclick attribute'),
        (r'data: \[(\d+,\s*)+', 'Hardcoded numerical array in Chart.js dataset'),
    ]

    for tpath in template_files:
        rel_path = os.path.relpath(tpath, r'c:\Users\Lenovo\OneDrive\Desktop\school-system\school-system\school-system')
        with open(tpath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        for pattern, label in hardcoded_patterns:
            matches = re.finditer(pattern, content)
            for m in matches:
                line_no = content[:m.start()].count('\n') + 1
                findings.append({
                    'id': f'TMPL-{len(findings)+1:02d}',
                    'category': 'Template / Hardcoded Value',
                    'severity': 'LOW' if 'href="#"' in label else 'MEDIUM',
                    'page': rel_path,
                    'route': 'Various',
                    'file': rel_path,
                    'line': line_no,
                    'problem': label,
                    'cause': 'Static placeholder code remaining in HTML/JS snippet',
                    'expected': 'Dynamic database URL or Chart.js JSON dataset',
                    'actual': m.group(0)[:40],
                    'db_impact': 'None',
                    'sec_impact': 'None',
                    'recommendation': 'Replace static placeholder with dynamic Jinja2 url_for or database metric',
                    'repro': f'Inspect line {line_no} of {rel_path}',
                    'priority': 'P3'
                })

if __name__ == '__main__':
    audit_routes_and_rbac()
    audit_templates_and_hardcoded_content()
    print(f"\nAudit completed. Total Findings Logged: {len(findings)}")
