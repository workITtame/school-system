import sys
from app import create_app
from models import db, Teacher, User, Subject, Classes, Sections, Student, SchoolTable

app = create_app()
with app.app_context():
    teacher = Teacher.query.filter_by(TeacherID=1).first()
    print(f"اسم المعلم (TeacherID=1): {teacher.TeacherName}")
    print(f"البريد الإلكتروني: {teacher.Email}")
    print(f"اسم حساب المستخدم: {teacher.user.name if teacher.user else 'غير مرتبط'}")
    print(f"دور المستخدم: {teacher.user.role if teacher.user else 'غير مرتبط'}")
    
    subjects = [s.SubName for s in teacher.subjects]
    print(f"المواد المسندة للمعلم: {subjects}")
    
    slots = SchoolTable.query.filter_by(TeacherID=teacher.TeacherID, is_deleted=False).all()
    print(f"عدد الحصص في الجدول الأسبوعي (SchoolTable): {len(slots)}")
    
    # All Active Students in DB
    students = Student.query.filter_by(is_deleted=False).all()
    print(f"\nإجمالي عدد الطلاب النشطين في المدرسة: {len(students)} طالب")
    
    # Breakdown of classes in DB
    classes = Classes.query.filter_by(is_deleted=False).all()
    sections = Sections.query.filter_by(is_deleted=False).all()
    print(f"إجمالي عدد الفصول/الصفوف في قاعدة البيانات: {len(classes)} فصول")
    for c in classes:
        st_in_c = Student.query.filter_by(CID=c.CID, is_deleted=False).count()
        print(f"   - {c.CName} (CID={c.CID}): {st_in_c} طلاب")
        
    print(f"\nإجمالي عدد الشعب المسجلة في قاعدة البيانات: {len(sections)} شعبة")
    section_names = list(set([s.SectionName for s in sections if s.SectionName]))
    print(f"أسماء الشعب في المدرسة: {section_names[:10]}")
