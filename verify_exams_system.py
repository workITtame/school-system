import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app import create_app

app = create_app()

def verify():
    print("=== Verifying Exams & Grading System Tasks ===\n")

    # 1. Check Database Constraints
    print("1. Checking Database Constraints (Unique Marks & 0-100 Validation)")
    grade_model_path = os.path.join(app.root_path, 'models', 'grade.py')
    with open(grade_model_path, 'r', encoding='utf-8') as f:
        content = f.read()
        if "uix_student_exam_mark" in content and "CheckConstraint('Score >= 0 AND Score <= 100'" in content:
            print("[OK] Database constraints found: duplicate prevention and 0-100 boundaries.")
        else:
            print("[FAILED] Database constraints missing.")

    # 2. Check Backend API
    print("\n2. Checking Backend (Professional API) in api_routes.py")
    api_path = os.path.join(app.root_path, 'routes', 'api_routes.py')
    with open(api_path, 'r', encoding='utf-8') as f:
        api_content = f.read()
        if "@api_bp.route(\"/grades/bulk\", methods=['POST'])" in api_content and "if score < 0 or score > 100:" in api_content:
            print("[OK] Backend API found for Bulk Grades with backend 0-100 validation.")
        else:
            print("[FAILED] Bulk grades API missing.")

    # 3. Check Grade UI (Bulk Input, JS Grade Letter, Chart)
    print("\n3. Checking Frontend UI (manage.html)")
    manage_html = os.path.join(app.root_path, 'templates', 'grades', 'manage.html')
    with open(manage_html, 'r', encoding='utf-8') as f:
        manage_content = f.read()
        if "id=\"btnSaveBulk\"" in manage_content:
            print("[OK] Bulk input UI found (إدخال جماعي).")
        if "function calculateLetter(score)" in manage_content:
            print("[OK] JavaScript live Grade calculation found (حساب تقدير).")
        if "new Chart(ctx" in manage_content:
            print("[OK] Chart.js analytics found (رسم بياني للأداء).")

    # 4. Check PDF Report
    print("\n4. Checking PDF Report UI (student_report.html)")
    report_html = os.path.join(app.root_path, 'templates', 'grades', 'student_report.html')
    if os.path.exists(report_html):
        with open(report_html, 'r', encoding='utf-8') as f:
            if "@media print" in f.read():
                print("[OK] Print-ready PDF report template found (تقرير pdf للطالب).")
            else:
                print("[FAILED] Report template lacks print CSS.")
    else:
        print("[FAILED] student_report.html missing.")

    # 5. Check Dashboard Button
    print("\n5. Checking Dashboard Button")
    dash_html = os.path.join(app.root_path, 'templates', 'dashboard', 'index.html')
    with open(dash_html, 'r', encoding='utf-8') as f:
        content = f.read()
        if "نظام الامتحانات والدرجات" in content and "grades.manage_grades" in content:
            print("[OK] Exams & Grades quick-access button found in Dashboard.")
        else:
            print("[FAILED] Dashboard button missing.")

    print("\n=== Verification Completed ===")

if __name__ == "__main__":
    verify()
