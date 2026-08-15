import sys

sys.path.insert(0, r'c:\Users\Lenovo\OneDrive\Desktop\school-system\school-system\school-system')
from app import create_app
from models import db, Student, Classes, Sections, Attendance, Marks, HomeworkMarks, Message
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("==================================================")
    print("DB-01 Investigation for Student SID = 7")
    print("==================================================")

    # 1. Student Record
    st = Student.query.get(7)
    if st:
        print(f"Student Data: SID={st.SID}, Name='{st.SName}', CID={st.CID}, SectionID={st.SectionID}")
    else:
        print("Student SID=7 not found directly via model query.")

    with db.engine.connect() as conn:
        # Raw SQL query on student table
        raw_st = conn.execute(text("SELECT * FROM student WHERE SID=7")).mappings().first()
        print(f"Raw Student Row: {raw_st}")

        # 2. Check Attendance records for SID=7
        att_rows = conn.execute(text("SELECT * FROM attendance WHERE SID=7")).mappings().fetchall()
        print(f"Attendance Records Count for SID=7: {len(att_rows)}")
        for a in att_rows:
            print(f"  Attendance: Date={a.get('AttDate')}, Status='{a.get('Status')}', CID={a.get('CID')}, LessonID={a.get('LessonID')}")

        # 3. Check Marks records for SID=7
        marks_rows = conn.execute(text("SELECT * FROM marks WHERE SID=7")).mappings().fetchall()
        print(f"Marks Records Count for SID=7: {len(marks_rows)}")
        for m in marks_rows:
            print(f"  Mark: SubID={m.get('SubID')}, Score={m.get('Score')}, TypeExamID={m.get('TypeExamID')}")

        # 4. Check HomeworkMarks records for SID=7
        hw_marks_rows = conn.execute(text("SELECT * FROM homeworkmarks WHERE SID=7")).mappings().fetchall()
        print(f"HomeworkMarks Records Count for SID=7: {len(hw_marks_rows)}")
        for hwm in hw_marks_rows:
            print(f"  HomeworkMark: HomeworkID={hwm.get('HomeworkID')}, Score={hwm.get('Score')}")

        # 5. Check if SectionID points to a valid section in classessections or sections
        if raw_st and raw_st.get('SectionID'):
            sec_id = raw_st.get('SectionID')
            cs_row = conn.execute(text("SELECT * FROM classessections WHERE SectionID=:sec"), {'sec': sec_id}).mappings().fetchall()
            print(f"ClassSections Mapping for SectionID={sec_id}: {cs_row}")
