from app import create_app
from models import db, User, Teacher, Classes, Sections, Subject, Student, SchoolTable
from services.teacher_dashboard_service import get_teacher_by_user_id, get_teacher_subject_and_class_ids

app = create_app()
with app.app_context():
    teachers = Teacher.query.filter_by(is_deleted=False).all()
    print(f"Total Teachers in DB: {len(teachers)}")
    for t in teachers:
        user = User.query.get(t.user_id) if t.user_id else None
        user_name = user.name if user else 'No User'
        print(f"\n--- Teacher ID: {t.TeacherID}, Name: {t.TeacherName}, Linked User ID: {t.user_id} ({user_name}), Email: {t.Email} ---")
        
        # Check subjects
        sub_ids = [s.SubID for s in t.subjects]
        sub_names = [s.SubName for s in t.subjects]
        print(f"  Subjects ({len(sub_ids)}): {sub_names}")
        
        # Check SchoolTable slots
        slots = SchoolTable.query.filter_by(TeacherID=t.TeacherID, is_deleted=False).all()
        slot_cids = list(set([s.CID for s in slots if s.CID]))
        slot_secids = list(set([s.SectionID for s in slots if s.SectionID]))
        print(f"  SchoolTable Slots ({len(slots)}): ClassIDs: {slot_cids}, SectionIDs: {slot_secids}")
        
        # Check get_teacher_subject_and_class_ids logic
        all_sub_ids, teacher_cids, teacher_secids = get_teacher_subject_and_class_ids(t)
        print(f"  Combined ClassIDs: {teacher_cids}, Combined SectionIDs: {teacher_secids}")
        
        # Check students in these classes
        if teacher_cids:
            st_query = Student.query.filter(Student.is_deleted == False, Student.CID.in_(teacher_cids))
            if teacher_secids:
                st_query = st_query.filter(Student.SectionID.in_(teacher_secids))
            st_count = st_query.count()
            print(f"  --> Student count for this teacher: {st_count}")
        else:
            # Fallback: Check if teacher has subjects, what classes have those subjects, OR all active students!
            all_students = Student.query.filter(Student.is_deleted == False).count()
            print(f"  --> No ClassIDs assigned in SchoolTable! Total DB active students: {all_students}")
