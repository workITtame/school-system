from app import create_app
from models import db, Teacher, User, Subject, Classes, Sections, Student, SchoolTable

app = create_app()
with app.app_context():
    teachers = Teacher.query.filter_by(is_deleted=False).all()
    
    for t in teachers:
        if 'smir' in (t.Email or '').lower() or 'سمير' in t.TeacherName or 'سمور' in t.TeacherName:
            print("="*60)
            print(f"Teacher ID: {t.TeacherID}")
            print(f"Teacher Name: {t.TeacherName}")
            print(f"Email: {t.Email}")
            print(f"User ID: {t.user_id}")
            
            user = db.session.get(User, t.user_id) if t.user_id else None
            if user:
                print(f"Linked User Name: {getattr(user, 'name', 'N/A')}, User Role: {getattr(user, 'role', 'N/A')}")
                
            # Subjects
            subs = [s.SubName for s in t.subjects] if t.subjects else []
            print(f"Assigned Subjects ({len(subs)}): {', '.join(subs) if subs else 'None'}")
            
            # SchoolTable slots
            slots = SchoolTable.query.filter_by(TeacherID=t.TeacherID, is_deleted=False).all()
            slot_cids = list(set([s.CID for s in slots if s.CID]))
            slot_secids = list(set([s.SectionID for s in slots if s.SectionID]))
            print(f"SchoolTable Timetable Slots Count: {len(slots)}")
            print(f"Timetable Class IDs: {slot_cids}")
            print(f"Timetable Section IDs: {slot_secids}")
            
            classes = Classes.query.filter(Classes.CID.in_(slot_cids)).all() if slot_cids else []
            class_names = [c.CName for c in classes]
            print(f"Classes Taught ({len(class_names)}): {', '.join(class_names) if class_names else 'لا يوجد فصول مجدولة بالجدول الأسبوعي'}")
            
            sections = Sections.query.filter(Sections.SectionID.in_(slot_secids)).all() if slot_secids else []
            section_names = [s.SectionName for s in sections]
            print(f"Sections Taught ({len(section_names)}): {', '.join(section_names) if section_names else 'لا يوجد شعب مجدولة بالجدول الأسبوعي'}")
            
            # All Classes & Sections in school DB for context
            all_classes = Classes.query.filter_by(is_deleted=False).all()
            all_sections = Sections.query.filter_by(is_deleted=False).all()
            print(f"\nTotal Classes in School DB ({len(all_classes)}): {[c.CName for c in all_classes]}")
            print(f"Total Sections in School DB ({len(all_sections)}): {[s.SectionName for s in all_sections]}")
            
            # Students in timetable classes if any, or total in DB
            if slot_cids:
                st_query = Student.query.filter(Student.is_deleted == False, Student.CID.in_(slot_cids))
                if slot_secids:
                    st_query = st_query.filter(Student.SectionID.in_(slot_secids))
                st_list = st_query.all()
                print(f"\nStudents in Timetable Classes ({len(st_list)}):")
                for st in st_list[:5]:
                    print(f"   - {st.SName} (Class: {st.school_class.CName if st.school_class else 'N/A'})")
            else:
                all_st = Student.query.filter_by(is_deleted=False).all()
                print(f"\nTotal Active Students in DB: {len(all_st)}")
                class_breakdown = {}
                for st in all_st:
                    c_name = st.school_class.CName if st.school_class else 'غير محدد'
                    class_breakdown[c_name] = class_breakdown.get(c_name, 0) + 1
                print(f"Breakdown of Students by Class in DB: {class_breakdown}")
