import sys
import os
import re
from html.parser import HTMLParser

sys.path.insert(0, r'c:\Users\Lenovo\OneDrive\Desktop\school-system\school-system\school-system')
from app import create_app
from models import db, User, Student, Teacher, Classes, Sections, Subject, Homework, ExamSchedule, Attendance, Marks, Notification, Message, School
from sqlalchemy import inspect, text

app = create_app()
app.config['TESTING'] = True

reconciled_issues = []

def add_issue(issue_id, category, severity, page, component, problem, cause, evidence, impact):
    reconciled_issues.append({
        'id': issue_id,
        'category': category,
        'severity': severity,
        'page': page,
        'component': component,
        'problem': problem,
        'cause': cause,
        'evidence': evidence,
        'impact': impact
    })

class DomInspector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.buttons = []
        self.forms = []
        self.links = []
        self.inputs = []
        self.tables = []
        self.legacy_elements = []

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        if tag == 'button':
            self.buttons.append(attr_dict)
        elif tag == 'form':
            self.forms.append(attr_dict)
        elif tag == 'a':
            self.links.append(attr_dict)
        elif tag == 'input' or tag == 'select':
            self.inputs.append(attr_dict)
        elif tag == 'table':
            self.tables.append(attr_dict)

        # Check for legacy UI classes
        cls = attr_dict.get('class', '')
        id_attr = attr_dict.get('id', '')
        if 'legacy' in cls.lower() or 'legacy' in id_attr.lower() or 'old-' in id_attr.lower():
            self.legacy_elements.append((tag, attr_dict))

def run_deep_production_audit():
    with app.app_context():
        # Get users for testing
        admin = User.query.filter_by(role='admin').first()
        admin_id = admin.id if admin else 1

        teacher = Teacher.query.filter(Teacher.user_id.isnot(None)).first()
        teacher_user = User.query.get(teacher.user_id) if (teacher and teacher.user_id) else User.query.filter_by(role='teacher').first()
        teacher_id = teacher_user.id if teacher_user else 2

        student = Student.query.filter_by(is_deleted=False).first()
        st_id = student.SID if student else 1

        hw = Homework.query.first()
        hw_id = hw.id if hw else 1

        # -------------------------------------------------------------
        # 1. DATABASE SCHEMA & ORPHAN RECORDS AUDIT
        # -------------------------------------------------------------
        inspector = inspect(db.engine)
        table_names = inspector.get_table_names()

        with db.engine.connect() as conn:
            # Check student CID orphan
            orphan_st = conn.execute(text("SELECT SID, SName, CID FROM student WHERE CID IS NOT NULL AND CID NOT IN (SELECT CID FROM classes)")).fetchall()
            if orphan_st:
                for st in orphan_st:
                    add_issue(
                        issue_id=f"MEDIUM-01",
                        category="Database Integrity",
                        severity="MEDIUM",
                        page="Students Database",
                        component="student table",
                        problem=f"Student ID {st[0]} ('{st[1]}') has foreign key CID={st[2]} pointing to non-existent class",
                        cause="Legacy data insertion or hard-deleted class without cascade update on student table",
                        evidence=f"SELECT * FROM student WHERE SID={st[0]} -> CID={st[2]} (not in classes table)",
                        impact="Potential NULL pointer or missing class name when joining student with school_class in UI"
                    )

            # Check marks with score > maxscore
            invalid_marks = conn.execute(text("SELECT * FROM marks WHERE Score < 0 OR (MaxScore IS NOT NULL AND MaxScore > 0 AND Score > MaxScore)")).fetchall()
            if invalid_marks:
                for m in invalid_marks:
                    add_issue(
                        issue_id=f"HIGH-01",
                        category="Database Integrity",
                        severity="HIGH",
                        page="Gradebook Database",
                        component="marks table",
                        problem=f"Mark Record #{m[0]} has Score={m[2]} exceeding MaxScore={m[3]}",
                        cause="Missing backend validation constraint on raw mark insertion route",
                        evidence=f"SELECT * FROM marks WHERE MarkID={m[0]} -> Score={m[2]}, MaxScore={m[3]}",
                        impact="Incorrect percentage calculation (>100%) in gradebook and student report cards"
                    )

        # -------------------------------------------------------------
        # 2. RBAC & IDOR PARAMETER TAMPERING AUDIT
        # -------------------------------------------------------------
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['_user_id'] = str(teacher_id)
                sess['user_id'] = teacher_id
                sess['user_role'] = 'teacher'

            # IDOR Check 1: Teacher accessing non-existent / unauthorized homework workspace
            res_idor_hw = client.get('/grading/workspace/homework/99999')
            if res_idor_hw.status_code == 200:
                add_issue(
                    issue_id="HIGH-02",
                    category="Authorization / IDOR",
                    severity="HIGH",
                    page="Unified Grading Workspace",
                    component="grading.grading_workspace route",
                    problem="Teacher session can access homework workspace route /grading/workspace/homework/99999 without checking teacher ownership",
                    cause="Missing ownership validation check (homework.TeacherID == current_teacher.TeacherID) in route handler",
                    evidence="GET /grading/workspace/homework/99999 under Teacher session returns HTTP 200 OK instead of 403/404",
                    impact="Teacher A can view and inspect homework workspace of Teacher B by manipulating homework ID in URL"
                )

        # -------------------------------------------------------------
        # 3. DOM & HTML RENDERED Audit Across Pages
        # -------------------------------------------------------------
        pages_to_audit = [
            ('/dashboard', 'Admin Dashboard'),
            ('/students/', 'Students Page'),
            ('/academic/classes', 'Classes Page'),
            ('/academic/subjects', 'Subjects Page'),
            ('/timetable/builder', 'Timetable Builder'),
            ('/attendance/', 'Attendance Page'),
            ('/exams/', 'Exams Page'),
            ('/grades/manage', 'Grades Management'),
            ('/gradebook/', 'Gradebook Page'),
            ('/homework/', 'Homework Page'),
            ('/finance', 'Finance Page'),
            ('/reports/', 'Reports Page'),
            ('/messages/', 'Messages Page'),
            ('/notifications/', 'Notifications Page'),
            ('/profile/', 'Profile Page')
        ]

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = admin_id
                sess['user_role'] = 'admin'
                sess['_user_id'] = str(admin_id)
                sess['_fresh'] = True

            # Use app request context to log in admin
            with app.test_request_context():
                from flask_login import login_user
                login_user(admin)

            for path, page_name in pages_to_audit:
                # Login for test client request
                with client.session_transaction() as sess:
                    sess['_user_id'] = str(admin_id)
                    sess['user_id'] = admin_id
                    sess['user_role'] = 'admin'

                res = client.get(path, follow_redirects=True)
                if res.status_code != 200:
                    add_issue(
                        issue_id=f"HIGH-{len(reconciled_issues)+1:02d}",
                        category="Routing / HTTP Status",
                        severity="HIGH",
                        page=page_name,
                        component=path,
                        problem=f"Route {path} returned HTTP {res.status_code} for Admin session",
                        cause="Server-side route exception or missing endpoint",
                        evidence=f"GET {path} -> HTTP {res.status_code}",
                        impact="Page fails to render for logged-in Administrator"
                    )
                    continue

                html_content = res.get_data(as_text=True)
                parser = DomInspector()
                parser.feed(html_content)

                # Check for legacy UI markup in Gradebook
                if path == '/gradebook/' and len(parser.legacy_elements) > 0:
                    add_issue(
                        issue_id="LOW-01",
                        category="Legacy Code / UI",
                        severity="LOW",
                        page="Gradebook Page",
                        component="gradebook/index.html",
                        problem="Gradebook template renders residual legacy UI elements in DOM alongside modern workspace",
                        cause="Legacy HTML markup retained inside comment/hidden container",
                        evidence=f"Found {len(parser.legacy_elements)} legacy elements in DOM parser",
                        impact="Unnecessary DOM overhead and potential CSS rule collision"
                    )

                # Check for empty buttons or dead href="#"
                for link in parser.links:
                    href = link.get('href', '')
                    if href == '#':
                        add_issue(
                            issue_id=f"LOW-{len(reconciled_issues)+1:02d}",
                            category="Template / Navigation",
                            severity="LOW",
                            page=page_name,
                            component="Anchor Tag",
                            problem=f"Anchor tag on {page_name} uses empty placeholder href='#'",
                            cause="Static markup snippet without dynamic url_for binding",
                            evidence=f"Link text: '{link.get('title', 'link')}', href='#'",
                            impact="Clicking link scrolls to top of page without performing action"
                        )

        print("\n==================================================")
        print(f"Deep Production Audit Completed!")
        print(f"Total Reconciled Unique Issues: {len(reconciled_issues)}")
        print("==================================================")

        for iss in reconciled_issues:
            print(f"[{iss['id']}] ({iss['severity']}) {iss['page']} -> {iss['problem']}")

if __name__ == '__main__':
    run_deep_production_audit()
