from app import create_app
from models import db, Student, Classes, Sections

app = create_app()
with app.app_context():
    valid_class_students = Student.query.filter(Student.is_deleted == False, Student.CID.isnot(None)).all()
    print(f"Students with valid assigned Class (CID is NOT NULL): {len(valid_class_students)}")
    for st in valid_class_students:
        c_name = st.school_class.CName if st.school_class else f"CID:{st.CID}"
        sec_name = st.section.SectionName if st.section else f"SecID:{st.SectionID}"
        print(f"   - SID: {st.SID} | Name: {st.SName} | Class: {c_name} | Section: {sec_name}")

    print("\nStudents WITHOUT Class (CID IS NULL - API Test Rows):")
    null_class_students = Student.query.filter(Student.is_deleted == False, Student.CID.is_(None)).all()
    print(f"Total API Test / Null Class Rows: {len(null_class_students)}")
