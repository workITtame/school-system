import os
import sys
from datetime import datetime, date, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app import create_app
from models import (
    db, User, Classes, Sections, Subject, Teacher, Qualifications,
    Student, Attendance, Terms, TypeExams, ExamSchedule, Marks, Homework, Message
)

app = create_app()

def seed_demo_data():
    with app.app_context():
        print("--- Seeding Comprehensive Demo Data into MySQL ---")

        # 1. Qualifications
        q_bachelor = Qualifications.query.filter_by(QName='بكالوريوس').first()
        if not q_bachelor:
            q_bachelor = Qualifications(QName='بكالوريوس')
            db.session.add(q_bachelor)
        
        q_master = Qualifications.query.filter_by(QName='ماجستير').first()
        if not q_master:
            q_master = Qualifications(QName='ماجستير')
            db.session.add(q_master)
        db.session.commit()

        # 2. Classes & Sections
        class_names = [
            ('الأول الثانوي', 'الثانوية'),
            ('الثاني الثانوي', 'الثانوية'),
            ('الثالث الثانوي', 'الثانوية'),
            ('الأول المتوسط', 'المتوسطة'),
            ('الثاني المتوسط', 'المتوسطة'),
            ('الابتدائي الأول', 'الأساسية')
        ]
        classes_dict = {}
        for cname, stage in class_names:
            c = Classes.query.filter_by(CName=cname, is_deleted=False).first()
            if not c:
                c = Classes(CName=cname, Stage=stage)
                db.session.add(c)
                db.session.commit()
            classes_dict[cname] = c

        section_names = ['شعبة أ', 'شعبة ب', 'شعبة ج']
        sections_dict = {}
        for sname in section_names:
            sec = Sections.query.filter_by(SectionName=sname, is_deleted=False).first()
            if not sec:
                sec = Sections(SectionName=sname)
                db.session.add(sec)
                db.session.commit()
            sections_dict[sname] = sec

        # Link classes and sections
        for c in classes_dict.values():
            for sec in sections_dict.values():
                if sec not in c.sections:
                    c.sections.append(sec)
        db.session.commit()

        # 3. Subjects
        sub_list = [
            ('الرياضيات', 'أساسية', 'علمي', 'نشط'),
            ('اللغة العربية', 'أساسية', 'جميع المراحل', 'نشط'),
            ('الفيزياء', 'أساسية', 'علمي', 'نشط'),
            ('الكيمياء', 'أساسية', 'علمي', 'نشط'),
            ('اللغة الإنجليزية', 'أساسية', 'جميع المراحل', 'نشط'),
            ('العلوم', 'أساسية', 'جميع المراحل', 'نشط'),
            ('التربية الإسلامية', 'أساسية', 'جميع المراحل', 'نشط')
        ]
        subjects_dict = {}
        for sname, stype, sdept, status in sub_list:
            sub = Subject.query.filter_by(SubName=sname, is_deleted=False).first()
            if not sub:
                sub = Subject(SubName=sname, Type=stype, Department=sdept, Status=status)
                db.session.add(sub)
                db.session.commit()
            subjects_dict[sname] = sub

        # 4. Teachers
        teachers_info = [
            ('أ. أحمد محمد عبد العزيز', 'ahmed@future-school.com', '0555123456', 'معلم رياضيات', q_bachelor.QID, ['الرياضيات']),
            ('أ. سارة إبراهيم محمود', 'sara@future-school.com', '0555234567', 'معلمة لغة عربية', q_bachelor.QID, ['اللغة العربية']),
            ('أ. علي حسن مسعود', 'ali@future-school.com', '0555345678', 'معلم علوم وفيزياء', q_master.QID, ['الفيزياء', 'العلوم']),
            ('أ. نور محمد إبراهيم', 'noor@future-school.com', '0555456789', 'معلمة لغة إنجليزية', q_bachelor.QID, ['اللغة الإنجليزية']),
            ('أ. يوسف خالد علي', 'yousef@future-school.com', '0555567890', 'معلم كيمياء', q_bachelor.QID, ['الكيمياء'])
        ]

        for tname, email, phone, title, qid, subs in teachers_info:
            t = Teacher.query.filter_by(TeacherName=tname, is_deleted=False).first()
            if not t:
                # Create user for teacher
                u_name = email.split('@')[0]
                u = User.query.filter_by(username=email).first()
                if not u:
                    u = User(username=email, name=tname, role='teacher')
                    u.set_password('123456')
                    db.session.add(u)
                    db.session.commit()

                t = Teacher(
                    TeacherName=tname,
                    Email=email,
                    Phone=phone,
                    TeacherTitle=title,
                    QID=qid,
                    Gender='ذكر' if 'أحمد' in tname or 'علي' in tname or 'يوسف' in tname else 'أنثى',
                    Salary=1500,
                    Status='نشط',
                    user_id=u.id
                )
                db.session.add(t)
                db.session.commit()

            # Assign subjects
            for sub_name in subs:
                sub_obj = subjects_dict.get(sub_name)
                if sub_obj and sub_obj not in t.subjects:
                    t.subjects.append(sub_obj)
        db.session.commit()

        # 5. Students
        c_1sec = classes_dict['الأول الثانوي']
        c_2sec = classes_dict['الثاني الثانوي']
        sec_a = sections_dict['شعبة أ']
        sec_b = sections_dict['شعبة ب']

        students_info = [
            ('محمد أحمد علي', 'ذكر', date(2008, 5, 12), c_1sec.CID, sec_a.SectionID, 'أحمد علي', '0555123456'),
            ('سارة محمد عبدالله', 'أنثى', date(2008, 3, 22), c_1sec.CID, sec_a.SectionID, 'محمد عبدالله', '0555234567'),
            ('علي حسن محمود', 'ذكر', date(2007, 11, 30), c_1sec.CID, sec_b.SectionID, 'حسن محمود', '0555345678'),
            ('نور محمد إبراهيم', 'أنثى', date(2008, 7, 15), c_2sec.CID, sec_a.SectionID, 'محمد إبراهيم', '0555456789'),
            ('يوسف خالد علي', 'ذكر', date(2007, 9, 10), c_2sec.CID, sec_b.SectionID, 'خالد علي', '0555567890'),
            ('عمر فهد السعيد', 'ذكر', date(2008, 1, 14), c_1sec.CID, sec_a.SectionID, 'فهد السعيد', '0555678901'),
            ('ريم طارق المنصور', 'أنثى', date(2008, 4, 18), c_1sec.CID, sec_b.SectionID, 'طارق المنصور', '0555789012')
        ]

        seeded_students = []
        for sname, gender, dob, cid, sec_id, pname, pnum in students_info:
            s = Student.query.filter_by(SName=sname, is_deleted=False).first()
            if not s:
                s = Student(
                    SName=sname,
                    Gender=gender,
                    DOB=dob,
                    CID=cid,
                    SectionID=sec_id,
                    Parent_Name=pname,
                    Parent_Number=pnum,
                    Status='نشط'
                )
                db.session.add(s)
                db.session.commit()
            seeded_students.append(s)

        # 6. Attendance Records
        today = date.today()
        for i in range(5):
            att_date = today - timedelta(days=i)
            for idx, st in enumerate(seeded_students):
                att = Attendance.query.filter_by(SID=st.SID, Date=att_date).first()
                if not att:
                    status = 'حاضر'
                    if (idx + i) % 7 == 0:
                        status = 'غائب'
                    elif (idx + i) % 5 == 0:
                        status = 'متأخر'
                    
                    att = Attendance(
                        SID=st.SID,
                        Date=att_date,
                        Status=status
                    )
                    db.session.add(att)
        db.session.commit()

        # 7. Terms & TypeExams
        term1 = Terms.query.filter_by(T_Name='الفصل الدراسي الأول', is_deleted=False).first()
        if not term1:
            term1 = Terms(T_Name='الفصل الدراسي الأول', AcademicYear='2024-2025')
            db.session.add(term1)
            db.session.commit()

        exam_type1 = TypeExams.query.filter_by(ExamName='اختبار الشهر الأول', is_deleted=False).first()
        if not exam_type1:
            exam_type1 = TypeExams(ExamName='اختبار الشهر الأول')
            db.session.add(exam_type1)
            db.session.commit()

        # 8. Marks
        math_sub = subjects_dict['الرياضيات']
        arabic_sub = subjects_dict['اللغة العربية']
        for st in seeded_students:
            for sub in [math_sub, arabic_sub]:
                mk = Marks.query.filter_by(SID=st.SID, SubID=sub.SubID, T_ID=term1.T_ID, ExamID=exam_type1.ExamID).first()
                if not mk:
                    score = 85.0 if st.SID % 2 == 0 else 92.0
                    grade = 'ممتاز' if score >= 90 else 'جيد جداً'
                    mk = Marks(
                        SID=st.SID,
                        SubID=sub.SubID,
                        T_ID=term1.T_ID,
                        ExamID=exam_type1.ExamID,
                        Score=score,
                        Grade=grade,
                        Percentage=score
                    )
                    db.session.add(mk)
        db.session.commit()

        # 9. Homework / Assignments
        hw1 = Homework.query.filter_by(title='حل تمارين درس المعادلة التربيعية').first()
        if not hw1:
            hw1 = Homework(
                title='حل تمارين درس المعادلة التربيعية',
                sub_id=math_sub.SubID,
                class_id=c_1sec.CID,
                section_id=sec_a.SectionID,
                due_date=today + timedelta(days=3),
                status='معلق',
                description='حل التمارين من الصفحة 45 إلى 48 كراسة الرياضيات'
            )
            db.session.add(hw1)

        hw2 = Homework.query.filter_by(title='مراجعة درس المتباينات والقيم المطلقة').first()
        if not hw2:
            hw2 = Homework(
                title='مراجعة درس المتباينات والقيم المطلقة',
                sub_id=math_sub.SubID,
                class_id=c_2sec.CID,
                section_id=sec_a.SectionID,
                due_date=today + timedelta(days=5),
                status='مكتمل',
                description='إجابة أسئلة المراجعة العامة'
            )
            db.session.add(hw2)
        db.session.commit()

        # 10. Messages
        admin_user = User.query.filter_by(role='admin').first()
        teacher_user = User.query.filter_by(role='teacher').first()
        if admin_user and teacher_user:
            m1 = Message.query.filter_by(content='السلام عليكم ورحمة الله، يرجى تزويدنا بتوزيع منهج الرياضيات للأسبوع القادم.').first()
            if not m1:
                m1 = Message(
                    sender_id=admin_user.id,
                    recipient_id=teacher_user.id,
                    content='السلام عليكم ورحمة الله، يرجى تزويدنا بتوزيع منهج الرياضيات للأسبوع القادم.',
                    is_read=True
                )
                db.session.add(m1)
                
                m2 = Message(
                    sender_id=teacher_user.id,
                    recipient_id=admin_user.id,
                    content='وعليكم السلام ورحمة الله، تم تجهيز خطة المنهج وسيتم رفعها اليوم على النظام.',
                    is_read=True
                )
                db.session.add(m2)
                db.session.commit()

        print("--- Demo Data Seeded Successfully into MySQL ---")

if __name__ == '__main__':
    seed_demo_data()
