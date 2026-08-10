import os
import sys
from datetime import datetime, date, timedelta
import random

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import (
    db, User, School, Teacher, Qualifications, Country, Governorates, Directorate,
    Classes, Sections, Subject, Days, Lessons, Terms, Student, Attendance,
    SchoolTable, TypeExams, Marks, DetailMarks, ExamSchedule, Message, Homework, Notification
)
from sqlalchemy import text

def init_and_seed_database():
    app = create_app()
    with app.app_context():
        print("==========================================================")
        print("   بدء عملية إعادة تهيئة وتعبئة قاعدة بيانات نظام المدرسة")
        print("==========================================================")

        is_mysql = db.engine.name == 'mysql'
        
        # 1. Drop and Recreate All Tables
        print("\n[1/12] إعادة بناء الجداول في قاعدة البيانات...")
        if is_mysql:
            try:
                db.session.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
                db.session.commit()
            except Exception as e:
                print(f"Notice: {e}")
        
        db.drop_all()
        db.create_all()

        if is_mysql:
            try:
                db.session.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
                db.session.commit()
            except Exception as e:
                print(f"Notice: {e}")
        print(" تم إنشاء كافة الجداول بنجاح.")

        # 2. Advanced DB Objects (Audit Logs, Trigger, View, Stored Procedure)
        print("\n[2/12] إعداد الكائنات المتقدمة (Triggers, Views, Stored Procedures)...")
        if is_mysql:
            try:
                # Audit Logs table
                db.session.execute(text('''
                    CREATE TABLE IF NOT EXISTS audit_logs (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        student_id INT,
                        subject_id INT,
                        old_score DECIMAL(5,2),
                        new_score DECIMAL(5,2),
                        action_time DATETIME DEFAULT CURRENT_TIMESTAMP
                    );
                '''))
                
                # Trigger for marks update
                db.session.execute(text("DROP TRIGGER IF EXISTS trg_marks_update;"))
                db.session.execute(text('''
                    CREATE TRIGGER trg_marks_update
                    AFTER UPDATE ON Marks
                    FOR EACH ROW
                    BEGIN
                        IF OLD.Score != NEW.Score THEN
                            INSERT INTO audit_logs (student_id, subject_id, old_score, new_score)
                            VALUES (OLD.SID, OLD.SubID, OLD.Score, NEW.Score);
                        END IF;
                    END;
                '''))
                print(" تم إنشاء جدول audit_logs والـ Trigger.")

                # View for student grades
                db.session.execute(text("DROP VIEW IF EXISTS vw_student_grades;"))
                db.session.execute(text('''
                    CREATE VIEW vw_student_grades AS
                    SELECT 
                        s.SID as student_id,
                        s.SName as student_name,
                        sub.SubName as subject_name,
                        t.TeacherName as teacher_name,
                        te.ExamName as exam_type,
                        m.Score as score,
                        tm.T_Name as term_name
                    FROM Marks m
                    JOIN Student s ON m.SID = s.SID
                    JOIN Subject sub ON m.SubID = sub.SubID
                    LEFT JOIN Teacher t ON m.TeacherID = t.TeacherID
                    JOIN TypeExams te ON m.ExamID = te.ExamID
                    JOIN Terms tm ON m.T_ID = tm.T_ID
                    WHERE m.is_deleted = False;
                '''))
                print(" تم إنشاء العرض vw_student_grades.")

                # Stored Procedure
                db.session.execute(text("DROP PROCEDURE IF EXISTS sp_add_grade;"))
                db.session.execute(text('''
                    CREATE PROCEDURE sp_add_grade(
                        IN p_sid INT,
                        IN p_subid INT,
                        IN p_examid INT,
                        IN p_teacherid INT,
                        IN p_score DECIMAL(5,2),
                        IN p_tid INT
                    )
                    BEGIN
                        IF p_score >= 0 AND p_score <= 100 THEN
                            INSERT INTO Marks (SID, SubID, ExamID, TeacherID, Score, T_ID, created_at, updated_at, is_deleted)
                            VALUES (p_sid, p_subid, p_examid, p_teacherid, p_score, p_tid, NOW(), NOW(), False);
                        ELSE
                            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Score must be between 0 and 100';
                        END IF;
                    END;
                '''))
                print(" تم إنشاء الإجراء المخزن sp_add_grade.")
                db.session.commit()
            except Exception as e:
                print(f"تحذير أثناء إعداد الكائنات المتقدمة: {e}")
                db.session.rollback()

        # 3. Seed School Info
        print("\n[3/12] تعبئة معلومات المدرسة...")
        school = School(
            SchoolName="مدرسة المستقبل النموذجية الحديثة",
            SchoolType="نموذجية أهلية",
            Phone="01-445566",
            Email="info@future-school.edu",
            Country="اليمن",
            City="صنعاء",
            Governorate="أمانة العاصمة",
            Directorate="السبعين",
            Neighborhood="حي حدة - شارع القدس",
            EstablishedYear=2016,
            Logo="school_logo.png"
        )
        db.session.add(school)
        db.session.commit()

        # 4. Seed Geographic Data
        print("\n[4/12] تعبئة البيانات الجغرافية (الدول والمحافظات والمديريات)...")
        country_ye = Country(Country_Name="اليمن")
        db.session.add(country_ye)
        db.session.flush()

        gov_data = [
            ("أمانة العاصمة", ["السبعين", "الوحدة", "الصافية", "التحرير", "الثورة", "شعوب", "معين", "بني الحارث"]),
            ("صنعاء", ["سنحان", "بني مطر", "همدان", "أرحب", "الحيمة الداخلية"]),
            ("عدن", ["صيرة", "المعلا", "خور مكسر", "الشيخ عثمان", "المنصورة", "التواهي"]),
            ("تعز", ["القاهرة", "المظفر", "صالة", "صبر الموادم"]),
            ("حضرموت", ["المكلا", "سيئون", "تريم", "الشحر"]),
            ("إب", ["الظهار", "المشنة", "جبلة", "يريم"]),
            ("الحديدة", ["الحالي", "الميناء", "الحوك", "باجل"])
        ]

        default_disc_id = None
        default_gov_id = None
        for g_name, dir_list in gov_data:
            gov = Governorates(G_Name=g_name, CountryID=country_ye.CountryID)
            db.session.add(gov)
            db.session.flush()
            if g_name == "أمانة العاصمة":
                default_gov_id = gov.G_ID
            for d_name in dir_list:
                disc = Directorate(Disc_Name=d_name, G_ID=gov.G_ID)
                db.session.add(disc)
                db.session.flush()
                if default_disc_id is None and d_name == "السبعين":
                    default_disc_id = disc.DiscID

        db.session.commit()

        # 5. Seed Qualifications
        print("\n[5/12] تعبئة المؤهلات العلمية...")
        quals = [
            "دكتوراه في المناهج وطرق التدريس",
            "ماجستير في التربية والتعليم",
            "ماجستير علوم وفيزياء",
            "بكالوريوس تربية رياضيات",
            "بكالوريوس لغة عربية وآدابها",
            "بكالوريوس لغة إنجليزية",
            "بكالوريوس علوم حاسوب",
            "بكالوريوس كيمياء وأحياء",
            "دبلوم عالي تأهيل تربوي"
        ]
        qual_objs = {}
        for qn in quals:
            q = Qualifications(QName=qn)
            db.session.add(q)
            db.session.flush()
            qual_objs[qn] = q
        db.session.commit()

        # 6. Seed Classes and Sections
        print("\n[6/12] تعبئة الصفوف الدراسية والشعب...")
        stages_classes = [
            ("الصف الأول الأساسي", "الأساسية"),
            ("الصف الثاني الأساسي", "الأساسية"),
            ("الصف الثالث الأساسي", "الأساسية"),
            ("الصف الرابع الأساسي", "الأساسية"),
            ("الصف الخامس الأساسي", "الأساسية"),
            ("الصف السادس الأساسي", "الأساسية"),
            ("الصف السابع (الأول المتوسط)", "المتوسطة"),
            ("الصف الثامن (الثاني المتوسط)", "المتوسطة"),
            ("الصف التاسع (الثالث المتوسط)", "المتوسطة"),
            ("الصف الأول الثانوي", "الثانوية"),
            ("الصف الثاني الثانوي (علمي)", "الثانوية"),
            ("الصف الثاني الثانوي (أدبي)", "الثانوية"),
            ("الصف الثالث الثانوي (علمي)", "الثانوية"),
            ("الصف الثالث الثانوي (أدبي)", "الثانوية")
        ]
        classes_map = {}
        for cname, stage in stages_classes:
            c = Classes(CName=cname, Stage=stage, MaxStudents=35)
            db.session.add(c)
            db.session.flush()
            classes_map[cname] = c

        section_names = ["شعبة أ", "شعبة ب", "شعبة ج"]
        sections_map = {}
        for sname in section_names:
            sec = Sections(SectionName=sname, MaxStudents=35)
            db.session.add(sec)
            db.session.flush()
            sections_map[sname] = sec

        # Associate Sections to all Classes
        for c in classes_map.values():
            for sec in sections_map.values():
                c.sections.append(sec)
        db.session.commit()

        # 7. Seed Subjects
        print("\n[7/12] تعبئة المواد الدراسية وربطها بالصفوف...")
        subject_data = [
            ("القرآن الكريم والتربية الإسلامية", "أساسية", "جميع المراحل", 4, "#10b981"),
            ("اللغة العربية", "أساسية", "جميع المراحل", 6, "#3b82f6"),
            ("الرياضيات", "أساسية", "علمي", 6, "#6366f1"),
            ("العلوم العامة", "أساسية", "جميع المراحل", 4, "#06b6d4"),
            ("الفيزياء", "أساسية", "علمي", 4, "#8b5cf6"),
            ("الكيمياء", "أساسية", "علمي", 4, "#ec4899"),
            ("الأحياء", "أساسية", "علمي", 3, "#14b8a6"),
            ("اللغة الإنجليزية", "أساسية", "جميع المراحل", 5, "#f59e0b"),
            ("الاجتماعيات والتاريخ", "أساسية", "أدبي", 3, "#84cc16"),
            ("الجغرافيا", "أساسية", "أدبي", 2, "#eab308"),
            ("الحاسوب وتكنولوجيا المعلومات", "اختيارية", "جميع المراحل", 2, "#0ea5e9"),
            ("التربية البدنية والرياضية", "اختيارية", "جميع المراحل", 2, "#f97316"),
            ("التربية الفنية", "اختيارية", "جميع المراحل", 1, "#a855f7")
        ]
        subjects_map = {}
        for sname, stype, sdept, whours, color in subject_data:
            sub = Subject(
                SubName=sname,
                Type=stype,
                Department=sdept,
                WeeklyHours=whours,
                Status="نشط",
                Color=color
            )
            db.session.add(sub)
            db.session.flush()
            subjects_map[sname] = sub

        # Link subjects to appropriate classes
        for cname, c in classes_map.items():
            for sname, sub in subjects_map.items():
                if "الأساسية" in c.Stage or "المتوسطة" in c.Stage:
                    if sname in ["الفيزياء", "الكيمياء", "الأحياء", "الجغرافيا"]:
                        continue
                if "أدبي" in cname:
                    if sname in ["الفيزياء", "الكيمياء", "الأحياء"]:
                        continue
                if "علمي" in cname:
                    if sname in ["الاجتماعيات والتاريخ", "الجغرافيا"]:
                        continue
                c.subjects.append(sub)
        db.session.commit()

        # 8. Seed Days, Lessons, Terms, Exam Types
        print("\n[8/12] تعبئة الأيام والحصص والفصول الدراسية وأنواع الاختبارات...")
        days_names = ["الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس"]
        days_map = {}
        for dname in days_names:
            d = Days(DName=dname)
            db.session.add(d)
            db.session.flush()
            days_map[dname] = d

        lessons_data = [
            ("الحصة الأولى", "08:00", "08:45"),
            ("الحصة الثانية", "08:50", "09:35"),
            ("الحصة الثالثة", "09:40", "10:25"),
            ("الحصة الرابعة", "10:50", "11:35"),
            ("الحصة الخامسة", "11:40", "12:25"),
            ("الحصة السادسة", "12:30", "13:15"),
            ("الحصة السابعة", "13:20", "14:00")
        ]
        lessons_map = {}
        for lname, st, et in lessons_data:
            l = Lessons(LessonName=lname, StartTime=st, EndTime=et)
            db.session.add(l)
            db.session.flush()
            lessons_map[lname] = l

        terms_data = [
            ("الفصل الدراسي الأول", "2025-2026"),
            ("الفصل الدراسي الثاني", "2025-2026")
        ]
        terms_map = {}
        for tname, ayear in terms_data:
            t = Terms(T_Name=tname, AcademicYear=ayear)
            db.session.add(t)
            db.session.flush()
            terms_map[tname] = t

        exam_types_data = [
            "اختبار الشهر الأول",
            "اختبار الشهر الثاني",
            "اختبار منتصف الفصل",
            "الاختبار النهائي",
            "الواجبات والمشاركة الصفية"
        ]
        exam_types_map = {}
        for etname in exam_types_data:
            et = TypeExams(ExamName=etname)
            db.session.add(et)
            db.session.flush()
            exam_types_map[etname] = et

        db.session.commit()

        # 9. Seed Users & Teachers
        print("\n[9/12] تعبئة حسابات المستخدمين والكادر التعليمي...")
        # Admin User
        admin_user = User(
            username="admin",
            name="مدير النظام العام",
            role="admin"
        )
        admin_user.set_password("123456")
        db.session.add(admin_user)
        db.session.commit()

        teachers_data = [
            ("أ. أحمد محمد عبد العزيز", "ahmed@future-school.com", "0555111222", "معلم رياضيات أول", "ذكر", date(1985, 4, 12), "صنعاء", "بكالوريوس تربية رياضيات", 1800, ["الرياضيات"]),
            ("أ. سارة إبراهيم محمود", "sara@future-school.com", "0555222333", "معلمة لغة عربية", "أنثى", date(1990, 8, 20), "تعز", "بكالوريوس لغة عربية وآدابها", 1600, ["اللغة العربية"]),
            ("أ. علي حسن مسعود", "ali@future-school.com", "0555333444", "معلم فيزياء وعلوم", "ذكر", date(1988, 1, 15), "عدن", "ماجستير علوم وفيزياء", 1950, ["الفيزياء", "العلوم العامة"]),
            ("أ. نور محمد إبراهيم", "noor@future-school.com", "0555444555", "معلمة لغة إنجليزية", "أنثى", date(1992, 11, 5), "صنعاء", "بكالوريوس لغة إنجليزية", 1650, ["اللغة الإنجليزية"]),
            ("أ. يوسف خالد علي", "yousef@future-school.com", "0555555666", "معلم كيمياء وأحياء", "ذكر", date(1986, 6, 28), "إب", "بكالوريوس كيمياء وأحياء", 1750, ["الكيمياء", "الأحياء"]),
            ("أ. فاطمة عمر باوزير", "fatima@future-school.com", "0555666777", "معلمة قرآن وتربية إسلامية", "أنثى", date(1991, 3, 10), "حضرموت", "ماجستير في التربية والتعليم", 1700, ["القرآن الكريم والتربية الإسلامية"]),
            ("أ. محمود عبد الرحمن السقاف", "mahmoud@future-school.com", "0555777888", "معلم حاسوب وتكنولوجيا", "ذكر", date(1993, 9, 14), "عدن", "بكالوريوس علوم حاسوب", 1600, ["الحاسوب وتكنولوجيا المعلومات"]),
            ("أ. خديجة صالح الزبيري", "khadija@future-school.com", "0555888999", "معلمة اجتماعيات وتاريخ", "أنثى", date(1989, 12, 1), "صنعاء", "بكالوريوس تربية رياضيات", 1550, ["الاجتماعيات والتاريخ", "الجغرافيا"])
        ]

        teachers_map = {}
        teachers_list = []
        for tname, email, phone, title, gender, dob, pob, qual_name, salary, subs in teachers_data:
            u = User(
                username=email,
                name=tname,
                role="teacher"
            )
            u.set_password("123456")
            db.session.add(u)
            db.session.flush()

            qid = qual_objs.get(qual_name, qual_objs["بكالوريوس تربية رياضيات"]).QID
            t = Teacher(
                TeacherName=tname,
                Email=email,
                Phone=phone,
                Gender=gender,
                DOB=dob,
                POB=pob,
                TeacherTitle=title,
                Salary=salary,
                Currency="YER",
                QID=qid,
                Status="نشط",
                Notes="معلم معتمد ومتميز في الأداء الأكاديمي",
                user_id=u.id
            )
            db.session.add(t)
            db.session.flush()

            for sname in subs:
                sub_obj = subjects_map.get(sname)
                if sub_obj:
                    t.subjects.append(sub_obj)
            
            teachers_map[tname] = t
            teachers_list.append(t)

        db.session.commit()

        # 10. Seed Students
        print("\n[10/12] تعبئة بيانات الطلاب وأولياء الأمور...")
        students_seed_list = [
            # الصف الأول الثانوي - شعبة أ
            ("محمد أحمد عبد الله العريقي", "ذكر", date(2009, 3, 14), "الصف الأول الثانوي", "شعبة أ", "أحمد عبد الله العريقي", "0555010101", "مهندس مدني", "شارع حدة"),
            ("سارة محمد علي الحكيمي", "أنثى", date(2009, 5, 20), "الصف الأول الثانوي", "شعبة أ", "محمد علي الحكيمي", "0555010102", "طبيب عام", "حي الأصبحي"),
            ("عمر خالد سعيد السقاف", "ذكر", date(2009, 1, 11), "الصف الأول الثانوي", "شعبة أ", "خالد سعيد السقاف", "0555010103", "تاجر", "حي الرويشان"),
            ("ريم طارق فهد المنصور", "أنثى", date(2009, 8, 25), "الصف الأول الثانوي", "شعبة أ", "طارق فهد المنصور", "0555010104", "أستاذ جامعي", "شارع القدس"),
            ("ياسين عبد الرحمن باعباد", "ذكر", date(2009, 7, 19), "الصف الأول الثانوي", "شعبة أ", "عبد الرحمن باعباد", "0555010105", "محاسب قانوني", "حي السبعين"),
            ("مريم إبراهيم حسن الصنعاني", "أنثى", date(2009, 10, 30), "الصف الأول الثانوي", "شعبة أ", "إبراهيم حسن الصنعاني", "0555010106", "رجل أعمال", "شارع بغداد"),
            # الصف الأول الثانوي - شعبة ب
            ("حمزة نبيل عثمان الغفاري", "ذكر", date(2009, 2, 17), "الصف الأول الثانوي", "شعبة ب", "نبيل عثمان الغفاري", "0555010107", "مهندس برمجيات", "حي الصافية"),
            ("آية سامي عبد القادر المقطري", "أنثى", date(2009, 4, 15), "الصف الأول الثانوي", "شعبة ب", "سامي عبد القادر المقطري", "0555010108", "مدير مالي", "شارع صخر"),
            ("حسام الدين كمال الأكوع", "ذكر", date(2009, 6, 8), "الصف الأول الثانوي", "شعبة ب", "كمال الأكوع", "0555010109", "محامي", "حي نقم"),
            ("فاطمة ناصر عبد القوي الشامي", "أنثى", date(2009, 9, 12), "الصف الأول الثانوي", "شعبة ب", "ناصر عبد القوي الشامي", "0555010110", "موظف حكومي", "حي الجامعة"),
            
            # الصف الثاني الثانوي (علمي) - شعبة أ
            ("أسامة وليد عبد الحفيظ الرداعي", "ذكر", date(2008, 1, 22), "الصف الثاني الثانوي (علمي)", "شعبة أ", "وليد عبد الحفيظ الرداعي", "0555010111", "صيدلاني", "حي الروضة"),
            ("هدى بشير عبد الواسع المجيدي", "أنثى", date(2008, 4, 9), "الصف الثاني الثانوي (علمي)", "شعبة أ", "بشير عبد الواسع المجيدي", "0555010112", "استشاري جراحة", "شارع الستين"),
            ("بلال ماجد عبد الكريم الوزير", "ذكر", date(2008, 6, 18), "الصف الثاني الثانوي (علمي)", "شعبة أ", "ماجد عبد الكريم الوزير", "0555010113", "ضابط مهندس", "حي النهضة"),
            ("زينب رضوان فاروق العبسي", "أنثى", date(2008, 11, 3), "الصف الثاني الثانوي (علمي)", "شعبة أ", "رضوان فاروق العبسي", "0555010114", "مهندس ديكور", "حي شميلة"),
            ("خالد جمال عبد الغني الحمادي", "ذكر", date(2008, 3, 29), "الصف الثاني الثانوي (علمي)", "شعبة أ", "جمال عبد الغني الحمادي", "0555010115", "خبير اقتصادي", "شارع تعز"),
            
            # الصف الثاني الثانوي (أدبي) - شعبة أ
            ("سلمان عبد العزيز عبد المجيد الحداد", "ذكر", date(2008, 5, 14), "الصف الثاني الثانوي (أدبي)", "شعبة أ", "عبد العزيز عبد المجيد الحداد", "0555010116", "صحفي وإعلامي", "شارع الزبيري"),
            ("سلمى مازن عبد الوهاب المتوكل", "أنثى", date(2008, 8, 2), "الصف الثاني الثانوي (أدبي)", "شعبة أ", "مازن عبد الوهاب المتوكل", "0555010117", "مترجم لغات", "حي حزيز"),
            ("إياد صالح ناصر المقالح", "ذكر", date(2008, 10, 21), "الصف الثاني الثانوي (أدبي)", "شعبة أ", "صالح ناصر المقالح", "0555010118", "أديب وباحث", "شارع القيادة"),

            # الصف الثالث الثانوي (علمي) - شعبة أ
            ("عبد الله رشاد عبد الجليل المخلافي", "ذكر", date(2007, 2, 10), "الصف الثالث الثانوي (علمي)", "شعبة أ", "رشاد عبد الجليل المخلافي", "0555010119", "طبيب استشاري", "شارع الدائري"),
            ("دانيا مروان عبد السلام القباطي", "أنثى", date(2007, 7, 7), "الصف الثالث الثانوي (علمي)", "شعبة أ", "مروان عبد السلام القباطي", "0555010120", "مهندس كهرباء", "شارع عمان"),
            ("معاذ توفيق عبد الغفور العولقي", "ذكر", date(2007, 9, 14), "الصف الثالث الثانوي (علمي)", "شعبة أ", "توفيق عبد الغفور العولقي", "0555010121", "مدير بنك", "شارع إيران"),
            ("روان عادل عبد الله الصبري", "أنثى", date(2007, 12, 28), "الصف الثالث الثانوي (علمي)", "شعبة أ", "عادل عبد الله الصبري", "0555010122", "مستشار قانوني", "حي بيت بوس"),

            # الصف التاسع (الثالث المتوسط) - شعبة أ
            ("زياد أنور عبد الرقيب الشرجبي", "ذكر", date(2010, 4, 18), "الصف التاسع (الثالث المتوسط)", "شعبة أ", "أنور عبد الرقيب الشرجبي", "0555010123", "مهندس ميكانيك", "حي دار سلم"),
            ("شهد رمزي عبد الفتاح الذبحاني", "أنثى", date(2010, 6, 24), "الصف التاسع (الثالث المتوسط)", "شعبة أ", "رمزي عبد الفتاح الذبحاني", "0555010124", "أخصائي تغذية", "شارع الرقاص"),
            ("فيصل بدر عبد الخالق العنسي", "ذكر", date(2010, 8, 30), "الصف التاسع (الثالث المتوسط)", "شعبة أ", "بدر عبد الخالق العنسي", "0555010125", "مدير تسويق", "حي شيراتون"),
            ("نادية هيثم عبد الهادي المطري", "أنثى", date(2010, 11, 15), "الصف التاسع (الثالث المتوسط)", "شعبة أ", "هيثم عبد الهادي المطري", "0555010126", "معلم لغة عربية", "حي المطار"),

            # الصف الأول الأساسي - شعبة أ
            ("كريم فادي عبد الله الشيباني", "ذكر", date(2018, 5, 10), "الصف الأول الأساسي", "شعبة أ", "فادي عبد الله الشيباني", "0555010127", "مهندس شبكات", "حي حدة"),
            ("ليان غسان عبد الملك الحرازي", "أنثى", date(2018, 9, 21), "الصف الأول الأساسي", "شعبة أ", "غسان عبد الملك الحرازي", "0555010128", "مصرفي", "حي الأصبحي"),
            ("آدم يحيى عبد الله الكبسي", "ذكر", date(2018, 2, 14), "الصف الأول الأساسي", "شعبة أ", "يحيى عبد الله الكبسي", "0555010129", "رجل أعمال", "شارع الخمسين"),
            ("تولين وائل عبد الرزاق السياني", "أنثى", date(2018, 7, 3), "الصف الأول الأساسي", "شعبة أ", "وائل عبد الرزاق السياني", "0555010130", "مدير موارد بشرية", "شارع الثلاثين")
        ]

        all_students = []
        for sname, gender, dob, cname, s_sec, pname, pphone, pwork, neigh in students_seed_list:
            c = classes_map[cname]
            sec = sections_map[s_sec]
            st = Student(
                SName=sname,
                DOB=dob,
                Gender=gender,
                CountryID=country_ye.CountryID,
                G_ID=default_gov_id,
                DiscID=default_disc_id,
                Neighborhood=neigh,
                Status="نشط",
                CID=c.CID,
                SectionID=sec.SectionID,
                Parent_Name=pname,
                Parent_Number=pphone,
                Parent_Work=pwork
            )
            db.session.add(st)
            db.session.flush()
            all_students.append(st)

        db.session.commit()

        # 11. Seed Weekly Timetable (SchoolTable)
        print("\n[11/12] تعبئة الجدول الدراسي الأسبوعي بدون أي تعارض...")
        term1 = terms_map["الفصل الدراسي الأول"]
        
        # Schedule slots for classes
        target_classes_for_schedule = [
            ("الصف الأول الثانوي", "شعبة أ"),
            ("الصف الثاني الثانوي (علمي)", "شعبة أ"),
            ("الصف الثالث الثانوي (علمي)", "شعبة أ"),
            ("الصف التاسع (الثالث المتوسط)", "شعبة أ")
        ]

        # Subject teachers distribution
        t_math = teachers_map["أ. أحمد محمد عبد العزيز"]
        t_arabic = teachers_map["أ. سارة إبراهيم محمود"]
        t_physics = teachers_map["أ. علي حسن مسعود"]
        t_english = teachers_map["أ. نور محمد إبراهيم"]
        t_chem = teachers_map["أ. يوسف خالد علي"]
        t_quran = teachers_map["أ. فاطمة عمر باوزير"]
        t_cs = teachers_map["أ. محمود عبد الرحمن السقاف"]
        t_history = teachers_map["أ. خديجة صالح الزبيري"]

        # Lesson assignments mapping by day and slot to avoid collisions
        # Days: الأحد, الإثنين, الثلاثاء, الأربعاء, الخميس
        days_list = [days_map[d] for d in days_names]
        lessons_list = [lessons_map[l[0]] for l in lessons_data]

        schedule_plan = {
            # class_idx: [day_idx][lesson_idx] -> (sub_name, teacher_obj)
            0: { # الأول الثانوي
                0: [("الرياضيات", t_math), ("اللغة العربية", t_arabic), ("اللغة الإنجليزية", t_english), ("القرآن الكريم والتربية الإسلامية", t_quran), ("الفيزياء", t_physics), ("الحاسوب وتكنولوجيا المعلومات", t_cs)],
                1: [("اللغة العربية", t_arabic), ("الرياضيات", t_math), ("الكيمياء", t_chem), ("العلوم العامة", t_physics), ("اللغة الإنجليزية", t_english), ("القرآن الكريم والتربية الإسلامية", t_quran)],
                2: [("الفيزياء", t_physics), ("الرياضيات", t_math), ("اللغة العربية", t_arabic), ("القرآن الكريم والتربية الإسلامية", t_quran), ("الكيمياء", t_chem), ("اللغة الإنجليزية", t_english)],
                3: [("اللغة الإنجليزية", t_english), ("العلوم العامة", t_physics), ("الرياضيات", t_math), ("اللغة العربية", t_arabic), ("الحاسوب وتكنولوجيا المعلومات", t_cs), ("القرآن الكريم والتربية الإسلامية", t_quran)],
                4: [("الرياضيات", t_math), ("الفيزياء", t_physics), ("اللغة العربية", t_arabic), ("الكيمياء", t_chem), ("اللغة الإنجليزية", t_english), ("القرآن الكريم والتربية الإسلامية", t_quran)]
            },
            1: { # الثاني الثانوي علمي
                0: [("اللغة العربية", t_arabic), ("الفيزياء", t_physics), ("الرياضيات", t_math), ("الكيمياء", t_chem), ("اللغة الإنجليزية", t_english), ("القرآن الكريم والتربية الإسلامية", t_quran)],
                1: [("الرياضيات", t_math), ("الفيزياء", t_physics), ("اللغة العربية", t_arabic), ("اللغة الإنجليزية", t_english), ("الكيمياء", t_chem), ("الحاسوب وتكنولوجيا المعلومات", t_cs)],
                2: [("الكيمياء", t_chem), ("اللغة العربية", t_arabic), ("الفيزياء", t_physics), ("الرياضيات", t_math), ("القرآن الكريم والتربية الإسلامية", t_quran), ("اللغة الإنجليزية", t_english)],
                3: [("الفيزياء", t_physics), ("الرياضيات", t_math), ("اللغة الإنجليزية", t_english), ("الكيمياء", t_chem), ("اللغة العربية", t_arabic), ("الحاسوب وتكنولوجيا المعلومات", t_cs)],
                4: [("اللغة الإنجليزية", t_english), ("الكيمياء", t_chem), ("الرياضيات", t_math), ("الفيزياء", t_physics), ("اللغة العربية", t_arabic), ("القرآن الكريم والتربية الإسلامية", t_quran)]
            },
            2: { # الثالث الثانوي علمي
                0: [("الفيزياء", t_physics), ("الرياضيات", t_math), ("الكيمياء", t_chem), ("اللغة الإنجليزية", t_english), ("اللغة العربية", t_arabic), ("القرآن الكريم والتربية الإسلامية", t_quran)],
                1: [("الكيمياء", t_chem), ("اللغة العربية", t_arabic), ("الرياضيات", t_math), ("الفيزياء", t_physics), ("القرآن الكريم والتربية الإسلامية", t_quran), ("اللغة الإنجليزية", t_english)],
                2: [("الرياضيات", t_math), ("الكيمياء", t_chem), ("اللغة الإنجليزية", t_english), ("الفيزياء", t_physics), ("اللغة العربية", t_arabic), ("القرآن الكريم والتربية الإسلامية", t_quran)],
                3: [("اللغة العربية", t_arabic), ("الكيمياء", t_chem), ("الفيزياء", t_physics), ("الرياضيات", t_math), ("القرآن الكريم والتربية الإسلامية", t_quran), ("اللغة الإنجليزية", t_english)],
                4: [("الفيزياء", t_physics), ("الرياضيات", t_math), ("الكيمياء", t_chem), ("اللغة العربية", t_arabic), ("اللغة الإنجليزية", t_english), ("القرآن الكريم والتربية الإسلامية", t_quran)]
            },
            3: { # التاسع الأساسي
                0: [("القرآن الكريم والتربية الإسلامية", t_quran), ("اللغة الإنجليزية", t_english), ("العلوم العامة", t_physics), ("الرياضيات", t_math), ("اللغة العربية", t_arabic), ("الاجتماعيات والتاريخ", t_history)],
                1: [("اللغة الإنجليزية", t_english), ("القرآن الكريم والتربية الإسلامية", t_quran), ("العلوم العامة", t_physics), ("الاجتماعيات والتاريخ", t_history), ("الرياضيات", t_math), ("اللغة العربية", t_arabic)],
                2: [("العلوم العامة", t_physics), ("القرآن الكريم والتربية الإسلامية", t_quran), ("الاجتماعيات والتاريخ", t_history), ("اللغة الإنجليزية", t_english), ("الرياضيات", t_math), ("اللغة العربية", t_arabic)],
                3: [("القرآن الكريم والتربية الإسلامية", t_quran), ("الاجتماعيات والتاريخ", t_history), ("اللغة العربية", t_arabic), ("اللغة الإنجليزية", t_english), ("العلوم العامة", t_physics), ("الرياضيات", t_math)],
                4: [("الاجتماعيات والتاريخ", t_history), ("القرآن الكريم والتربية الإسلامية", t_quran), ("اللغة الإنجليزية", t_english), ("الرياضيات", t_math), ("العلوم العامة", t_physics), ("اللغة العربية", t_arabic)]
            }
        }

        # Check teacher availability per day and lesson
        teacher_busy_slots = set() # (teacher_id, day_id, lesson_id)
        class_busy_slots = set() # (cid, sec_id, day_id, lesson_id)

        for c_idx, (cname, sec_name) in enumerate(target_classes_for_schedule):
            c_obj = classes_map[cname]
            sec_obj = sections_map[sec_name]
            class_plan = schedule_plan.get(c_idx, {})

            for d_idx, day_obj in enumerate(days_list):
                lessons_for_day = class_plan.get(d_idx, [])
                for l_idx, (sub_name, teacher_obj) in enumerate(lessons_for_day):
                    if l_idx >= len(lessons_list):
                        break
                    lesson_obj = lessons_list[l_idx]
                    sub_obj = subjects_map[sub_name]

                    t_key = (teacher_obj.TeacherID, day_obj.DayID, lesson_obj.LessonID)
                    c_key = (c_obj.CID, sec_obj.SectionID, day_obj.DayID, lesson_obj.LessonID)

                    if t_key not in teacher_busy_slots and c_key not in class_busy_slots:
                        teacher_busy_slots.add(t_key)
                        class_busy_slots.add(c_key)
                        
                        st_entry = SchoolTable(
                            CID=c_obj.CID,
                            SectionID=sec_obj.SectionID,
                            DayID=day_obj.DayID,
                            LessonID=lesson_obj.LessonID,
                            TeacherID=teacher_obj.TeacherID,
                            SubID=sub_obj.SubID,
                            T_ID=term1.T_ID
                        )
                        db.session.add(st_entry)

        db.session.commit()

        # 12. Seed Attendance, Exam Schedules, Marks, Homework, Messages, Notifications
        print("\n[12/12] تعبئة سجلات الحضور والدرجات والواجبات وجداول الاختبارات والرسائل...")
        
        # A. Attendance for past 14 days + today
        today = date.today()
        for i in range(13, -1, -1):
            att_date = today - timedelta(days=i)
            # Skip Friday / Saturday if wanted, or seed standard weekday attendance
            for idx, st in enumerate(all_students):
                # Realistic distribution: mostly حاضر, some متأخر, few غائب
                r = (idx * 17 + i * 23) % 100
                if r < 84:
                    status = "حاضر"
                elif r < 93:
                    status = "متأخر"
                elif r < 98:
                    status = "غائب"
                else:
                    status = "معذور"

                att = Attendance(
                    SID=st.SID,
                    Date=att_date,
                    Status=status
                )
                db.session.add(att)

        # B. Exam Schedule
        c_1sec = classes_map["الصف الأول الثانوي"]
        c_2sec_sci = classes_map["الصف الثاني الثانوي (علمي)"]
        c_3sec_sci = classes_map["الصف الثالث الثانوي (علمي)"]
        sec_a = sections_map["شعبة أ"]

        exam_schedules_data = [
            ("اختبار الرياضيات الشهري", subjects_map["الرياضيات"].SubID, c_1sec.CID, sec_a.SectionID, term1.T_ID, today + timedelta(days=2), "09:00", 60, "القاعة 101 - الدور الأول", "مجدول"),
            ("اختبار اللغة العربية الشهري", subjects_map["اللغة العربية"].SubID, c_1sec.CID, sec_a.SectionID, term1.T_ID, today + timedelta(days=4), "09:00", 60, "القاعة 101 - الدور الأول", "مجدول"),
            ("اختبار الفيزياء الشهري", subjects_map["الفيزياء"].SubID, c_2sec_sci.CID, sec_a.SectionID, term1.T_ID, today + timedelta(days=3), "10:30", 90, "مختبر العلوم والفيزياء", "مجدول"),
            ("اختبار الكيمياء الشهري", subjects_map["الكيمياء"].SubID, c_2sec_sci.CID, sec_a.SectionID, term1.T_ID, today + timedelta(days=5), "10:30", 90, "مختبر الكيمياء", "مجدول"),
            ("اختبار التفاضل والتكامل النهائي", subjects_map["الرياضيات"].SubID, c_3sec_sci.CID, sec_a.SectionID, term1.T_ID, today + timedelta(days=7), "08:30", 120, "المدرج الرئيسي", "مجدول"),
            ("اختبار اللغة الإنجليزية النهائي", subjects_map["اللغة الإنجليزية"].SubID, c_3sec_sci.CID, sec_a.SectionID, term1.T_ID, today + timedelta(days=9), "08:30", 120, "المدرج الرئيسي", "مجدول"),
            ("اختبار القرآن الكريم التحريري", subjects_map["القرآن الكريم والتربية الإسلامية"].SubID, c_1sec.CID, sec_a.SectionID, term1.T_ID, today - timedelta(days=5), "08:00", 45, "القاعة 101", "منتهية")
        ]
        for ename, sub_id, cid, sec_id, tid, edate, etime, dur, loc, status in exam_schedules_data:
            es = ExamSchedule(
                ExamName=ename,
                SubID=sub_id,
                CID=cid,
                SectionID=sec_id,
                T_ID=tid,
                ExamDate=edate,
                ExamTime=etime,
                Duration=dur,
                Location=loc,
                Status=status
            )
            db.session.add(es)

        # C. Marks & DetailMarks
        ex_month1 = exam_types_map["اختبار الشهر الأول"]
        ex_mid = exam_types_map["اختبار منتصف الفصل"]
        
        for st in all_students:
            # Add marks for core subjects
            for sub_name, teacher_obj in [
                ("الرياضيات", t_math),
                ("اللغة العربية", t_arabic),
                ("اللغة الإنجليزية", t_english),
                ("القرآن الكريم والتربية الإسلامية", t_quran)
            ]:
                sub_obj = subjects_map[sub_name]
                # Pseudo realistic grade based on student ID
                base_score = 70 + ((st.SID * 7 + sub_obj.SubID * 13) % 29) # range 70 to 98
                if base_score > 100:
                    base_score = 99.0
                grade_label = "ممتاز" if base_score >= 90 else ("جيد جداً" if base_score >= 80 else ("جيد" if base_score >= 65 else "مقبول"))

                m = Marks(
                    SID=st.SID,
                    SubID=sub_obj.SubID,
                    ExamID=ex_month1.ExamID,
                    TeacherID=teacher_obj.TeacherID,
                    Score=base_score,
                    MaxScore=100.0,
                    Grade=grade_label,
                    Percentage=base_score,
                    T_ID=term1.T_ID,
                    Notes="أداء متميز وتفاعل مستمر" if base_score >= 85 else "مستوى جيد مع إمكانية التحسن"
                )
                db.session.add(m)

                # Also detail mark
                dm = DetailMarks(
                    SID=st.SID,
                    SubID=sub_obj.SubID,
                    ExamID=ex_month1.ExamID,
                    TeacherID=teacher_obj.TeacherID,
                    Score=base_score,
                    MaxScore=100.0,
                    T_ID=term1.T_ID
                )
                db.session.add(dm)

        # D. Homework
        homework_data = [
            ("حل مسائل المعادلات الخطية والتربيعية", subjects_map["الرياضيات"].SubID, c_1sec.CID, sec_a.SectionID, today + timedelta(days=2), "معلق", "إكمال تمارين الفصل الثالث من كتاب الرياضيات ص 54-56"),
            ("إعراب قصيدة نهج البردة وتحليل أبياتها", subjects_map["اللغة العربية"].SubID, c_1sec.CID, sec_a.SectionID, today + timedelta(days=3), "معلق", "استخراج الصور البلاغية وإعراب الأبيات الخمسة الأولى"),
            ("تقرير تجربة قانون أوم ودوائر التوالي", subjects_map["الفيزياء"].SubID, c_2sec_sci.CID, sec_a.SectionID, today + timedelta(days=1), "معلق", "كتابة تقرير المختبر مع رسم المنحنيات البيانية وحساب المقاومة المكافئة"),
            ("مقال عن الذكاء الاصطناعي واستخداماته", subjects_map["اللغة الإنجليزية"].SubID, c_1sec.CID, sec_a.SectionID, today - timedelta(days=1), "متأخر", "Write an essay (150 words) discussing AI applications in modern life"),
            ("حفظ وتفسير الآيات (1-20) من سورة الكهف", subjects_map["القرآن الكريم والتربية الإسلامية"].SubID, c_1sec.CID, sec_a.SectionID, today - timedelta(days=3), "مكتمل", "التسميع الشفهي وتلخيص معاني المفردات القرآنية"),
            ("مشروع إنشاء صفحة ويب بتنسيق CSS", subjects_map["الحاسوب وتكنولوجيا المعلومات"].SubID, c_1sec.CID, sec_a.SectionID, today + timedelta(days=5), "معلق", "تصميم صفحة تعريفية شخصية باستخدام HTML و CSS")
        ]
        for title, sub_id, cid, sec_id, ddate, hstatus, desc in homework_data:
            hw = Homework(
                title=title,
                sub_id=sub_id,
                class_id=cid,
                section_id=sec_id,
                due_date=ddate,
                status=hstatus,
                description=desc
            )
            db.session.add(hw)

        # E. Messages
        # Get users
        u_ahmed = t_math.user
        u_sara = t_arabic.user
        u_ali = t_physics.user

        messages_data = [
            (admin_user.id, u_ahmed.id, "السلام عليكم أ. أحمد، يرجى تزويدنا بتوزيع درجات اختبار الشهر الأول لطلاب الأول الثانوي.", True, datetime.now() - timedelta(days=2)),
            (u_ahmed.id, admin_user.id, "وعليكم السلام ورحمة الله، تم الانتهاء من رصد وتدقيق الدرجات وسيتم رفع الكشوفات فوراً عبر النظام.", True, datetime.now() - timedelta(days=1, hours=20)),
            (admin_user.id, u_sara.id, "أهلاً أ. سارة، نرجو التكرم بالتحضير للاختبار الشفهي للغة العربية وتحديد مواعيد الجلسات.", False, datetime.now() - timedelta(hours=5)),
            (u_ali.id, admin_user.id, "تحية طيبة، نود إحاطتكم باكتمال تجهيز مختبر الفيزياء للتجارب العملية الخاصة بالصف الثاني الثانوي.", False, datetime.now() - timedelta(hours=2)),
            (admin_user.id, u_ali.id, "ممتاز جداً أ. علي، جهودكم مشكورة ونتمنى لكم وللطلاب كل التوفيق.", True, datetime.now() - timedelta(hours=1))
        ]
        for s_id, r_id, content, is_read, ts in messages_data:
            msg = Message(
                sender_id=s_id,
                recipient_id=r_id,
                content=content,
                is_read=is_read,
                timestamp=ts
            )
            db.session.add(msg)

        # F. Notifications
        notifications_data = [
            (admin_user.id, "اختبارات قادمة", "تمت جدولة 6 اختبارات شهرية ونهائية جديدة للفصل الدراسي الأول.", "exam", "/exams/", "normal", False, datetime.now() - timedelta(hours=4)),
            (admin_user.id, "رسالة جديدة", "وصلتك رسالة جديدة من أ. علي حسن مسعود بخصوص مختبر الفيزياء.", "message", "/messages/", "high", False, datetime.now() - timedelta(hours=2)),
            (u_ahmed.id, "تذكير بالواجبات", "لديك واجب دراسي مستحق التسليم غداً لطلاب الصف الأول الثانوي.", "homework", "/homework/", "normal", False, datetime.now() - timedelta(hours=3)),
            (u_sara.id, "رسالة من الإدارة", "تم إرسال تعليمات الاختبار الشفهي من قبل إدارة المدرسة.", "message", "/messages/", "high", False, datetime.now() - timedelta(hours=5))
        ]
        for uid, title, nmsg, ntype, aurl, prio, is_r, cat in notifications_data:
            notif = Notification(
                user_id=uid,
                title=title,
                message=nmsg,
                notification_type=ntype,
                action_url=aurl,
                priority=prio,
                is_read=is_r,
                created_at=cat
            )
            db.session.add(notif)

        db.session.commit()

        print("\n==========================================================")
        print("   تمت تهيئة وتعبئة قاعدة البيانات بنجاح تام وبشكل متكامل!")
        print("==========================================================")
        print(f" المستخدمون (Users): {User.query.count()}")
        print(f" المعلمون (Teachers): {Teacher.query.count()}")
        print(f" الصفوف الدراسية (Classes): {Classes.query.count()}")
        print(f" الشعب الدراسية (Sections): {Sections.query.count()}")
        print(f" المواد الدراسية (Subjects): {Subject.query.count()}")
        print(f" الطلاب (Students): {Student.query.count()}")
        print(f" الجدول الدراسي (SchoolTable Slots): {SchoolTable.query.count()}")
        print(f" سجلات الحضور والغياب (Attendance): {Attendance.query.count()}")
        print(f" جداول الاختبارات (Exam Schedules): {ExamSchedule.query.count()}")
        print(f" رصد الدرجات (Marks): {Marks.query.count()}")
        print(f" الواجبات المدرسية (Homework): {Homework.query.count()}")
        print(f" الرسائل (Messages): {Message.query.count()}")
        print(f" الإشعارات (Notifications): {Notification.query.count()}")
        print("----------------------------------------------------------")
        print("بيانات الدخول الافتراضية:")
        print(" مدير النظام: admin / 123456")
        print(" المعلمون: ahmed@future-school.com / 123456 (وكافة بريدات المعلمين)")
        print("==========================================================")

if __name__ == "__main__":
    init_and_seed_database()
