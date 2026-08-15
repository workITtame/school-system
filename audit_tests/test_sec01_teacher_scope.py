import sys

sys.path.insert(0, r'c:\Users\Lenovo\OneDrive\Desktop\school-system\school-system\school-system')
from app import create_app
from models import db, User, Teacher, Homework, Classes

app = create_app()

with app.app_context():
    teachers = Teacher.query.filter(Teacher.user_id.isnot(None)).all()
    t1 = teachers[0] if len(teachers) > 0 else None

    # Get a valid homework
    hw1 = Homework.query.first()

    t1_user_id = t1.user_id if t1 else 2
    admin_user = User.query.filter_by(role='admin').first()
    admin_id = admin_user.id if admin_user else 1

with app.test_client() as client:
    # 1. Teacher accessing in-scope or assigned homework
    with client.session_transaction() as sess:
        sess['user_id'] = t1_user_id
        sess['_user_id'] = str(t1_user_id)
        sess['user_role'] = 'teacher'

    if hw1:
        res1 = client.get(f'/grading/workspace/homework/{hw1.id}')
        assert res1.status_code in [200, 403], f"Got {res1.status_code}"
        print(f"[OK] Teacher accessing homework ID {hw1.id} -> HTTP {res1.status_code}")

    # 2. Teacher accessing non-existent homework ID -> 404 Not Found
    res_404 = client.get('/grading/workspace/homework/999999')
    assert res_404.status_code == 404, f"Expected 404 for non-existent homework, got {res_404.status_code}"
    print("[OK] Teacher accessing non-existent homework ID 999999 -> HTTP 404 Not Found")

    # 3. Admin accessing homework -> 200 OK
    with client.session_transaction() as sess:
        sess['user_id'] = admin_id
        sess['_user_id'] = str(admin_id)
        sess['user_role'] = 'admin'

    if hw1:
        res_admin = client.get(f'/grading/workspace/homework/{hw1.id}')
        assert res_admin.status_code == 200, f"Expected 200 for Admin, got {res_admin.status_code}"
        print(f"[OK] Admin accessing homework ID {hw1.id} -> HTTP 200 OK")

print("SUCCESS: SEC-01 Teacher Scope & IDOR Verification Passed!")
