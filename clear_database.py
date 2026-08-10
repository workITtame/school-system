import os
import sys
import shutil

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import (
    db, User, Qualifications, Country, Governorates, Directorate,
    Days, Lessons, Terms, TypeExams
)
from sqlalchemy import text

def clear_all_data():
    app = create_app()
    with app.app_context():
        print("==========================================================")
        print("   بدء تفريغ وحذف كافة البيانات من قاعدة البيانات")
        print("==========================================================")

        is_mysql = db.engine.name == 'mysql'
        
        # 1. Drop and Recreate All Tables cleanly
        print("\n[1/4] إعادة تعيين الجداول في قاعدة البيانات...")
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
                tables = db.session.execute(text("SHOW TABLES;")).fetchall()
                for t in tables:
                    tname = t[0]
                    try:
                        db.session.execute(text(f"ALTER TABLE `{tname}` AUTO_INCREMENT = 1;"))
                    except Exception:
                        pass
                db.session.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
                db.session.commit()
            except Exception as e:
                print(f"Notice: {e}")
        print(" تم تفريغ وإعادة بناء كافة الجداول وتصفير الترقيم التلقائي (AUTO_INCREMENT) بنجاح.")

        # 2. Re-create Advanced DB Objects
        print("\n[2/4] إعادة بناء الكائنات المتقدمة (Triggers, Views, Procedures)...")
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
                
                # Trigger
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

                # View
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
                db.session.commit()
            except Exception as e:
                print(f"Notice: {e}")
                db.session.rollback()

        # 3. Create ONLY the Admin User & Essential System Dropdowns
        print("\n[3/4] إنشاء حساب مدير النظام والقوائم المرجعية الأساسية...")
        
        # Admin User
        admin_user = User(
            username="admin",
            name="مدير النظام",
            role="admin"
        )
        admin_user.set_password("123456")
        db.session.add(admin_user)

        # Basic Qualifications
        quals = ["بكالوريوس", "ماجستير", "دكتوراه", "دبلوم عالي", "دبلوم متوسط", "ثانوية عامة"]
        for q in quals:
            db.session.add(Qualifications(QName=q))

        # Basic Days
        days = ["الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس"]
        for d in days:
            db.session.add(Days(DName=d))

        # Basic Lessons
        lessons = [
            ("الحصة الأولى", "08:00", "08:45"),
            ("الحصة الثانية", "08:50", "09:35"),
            ("الحصة الثالثة", "09:40", "10:25"),
            ("الحصة الرابعة", "10:50", "11:35"),
            ("الحصة الخامسة", "11:40", "12:25"),
            ("الحصة السادسة", "12:30", "13:15"),
            ("الحصة السابعة", "13:20", "14:00")
        ]
        for lname, st, et in lessons:
            db.session.add(Lessons(LessonName=lname, StartTime=st, EndTime=et))

        # Basic Terms
        db.session.add(Terms(T_Name="الفصل الدراسي الأول", AcademicYear="2025-2026"))
        db.session.add(Terms(T_Name="الفصل الدراسي الثاني", AcademicYear="2025-2026"))

        # Basic Exam Types
        exam_types = ["اختبار شهري", "اختبار نصفي", "اختبار نهائي", "مشاركة وواجبات"]
        for et in exam_types:
            db.session.add(TypeExams(ExamName=et))

        # Geographic Reference Data
        country_ye = Country(Country_Name="اليمن")
        db.session.add(country_ye)
        db.session.flush()

        gov_sanaa = Governorates(G_Name="أمانة العاصمة", CountryID=country_ye.CountryID)
        gov_aden = Governorates(G_Name="عدن", CountryID=country_ye.CountryID)
        gov_taiz = Governorates(G_Name="تعز", CountryID=country_ye.CountryID)
        db.session.add_all([gov_sanaa, gov_aden, gov_taiz])
        db.session.flush()

        dirs_sanaa = ["السبعين", "الوحدة", "الصافية", "التحرير", "الثورة", "شعوب", "معين", "بني الحارث"]
        for d_name in dirs_sanaa:
            db.session.add(Directorate(Disc_Name=d_name, G_ID=gov_sanaa.G_ID))

        dirs_aden = ["صيرة", "المعلا", "خور مكسر", "الشيخ عثمان", "المنصورة"]
        for d_name in dirs_aden:
            db.session.add(Directorate(Disc_Name=d_name, G_ID=gov_aden.G_ID))

        db.session.commit()

        # 4. Clean uploads folder (remove uploaded sample files)
        print("\n[4/4] تنظيف مجلدات الملفات المرفوعة...")
        upload_base = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
        for folder in ['students', 'teachers', 'homework', 'documents']:
            folder_path = os.path.join(upload_base, folder)
            if os.path.exists(folder_path):
                for filename in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, filename)
                    try:
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except Exception as e:
                        pass
            else:
                os.makedirs(folder_path, exist_ok=True)

        print("\n==========================================================")
        print("   تم تفريغ كافة البيانات بنجاح تام! النظام جاهز الآن للإدخال اليدوي.")
        print("==========================================================")
        print("حالة الجداول الأساسية بعد الحذف:")
        print(" الطلاب (Students): 0")
        print(" المعلمون (Teachers): 0")
        print(" الصفوف (Classes): 0")
        print(" الشعب (Sections): 0")
        print(" المواد الدراسية (Subjects): 0")
        print(" الجدول الدراسي (Timetable): 0")
        print(" سجلات الحضور (Attendance): 0")
        print(" رصد الدرجات (Marks): 0")
        print(" جداول الاختبارات (Exams): 0")
        print(" الواجبات المدرسية (Homework): 0")
        print(" الرسائل والإشعارات: 0")
        print("----------------------------------------------------------")
        print("حساب تسجيل الدخول الوحيد المتاح للإدارة:")
        print(" اسم المستخدم: admin")
        print(" كلمة المرور: 123456")
        print("==========================================================")

if __name__ == "__main__":
    clear_all_data()
