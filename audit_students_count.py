from app import create_app
from models import db, Student, Classes, Sections

app = create_app()
with app.app_context():
    total_raw_rows = Student.query.count()
    active_students_false = Student.query.filter_by(is_deleted=False).all()
    deleted_students_true = Student.query.filter_by(is_deleted=True).all()
    students_none_deleted = Student.query.filter(Student.is_deleted.is_(None)).all()
    
    print(f"Total Raw Rows in Student table: {total_raw_rows}")
    print(f"Rows with is_deleted == False: {len(active_students_false)}")
    print(f"Rows with is_deleted == True: {len(deleted_students_true)}")
    print(f"Rows with is_deleted IS NULL: {len(students_none_deleted)}")
    
    print("\n--- Listing ALL Student Rows in DB ---")
    for st in Student.query.all():
        c_name = st.school_class.CName if st.school_class else f"CID:{st.CID}"
        sec_name = st.section.SectionName if st.section else f"SecID:{st.SectionID}"
        print(f"SID: {st.SID} | Name: {st.SName} | Class: {c_name} | Section: {sec_name} | is_deleted: {st.is_deleted}")
