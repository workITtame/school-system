import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, User

app = create_app()
with app.app_context():
    # Force table creation if not exists
    from sqlalchemy import text
    try:
        db.session.execute(text("DROP DATABASE school_system_db;"))
    except:
        pass
    db.session.execute(text("CREATE DATABASE school_system_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"))
    db.session.execute(text("USE school_system_db;"))
    db.create_all()
    
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', name='مدير النظام', role='admin')
        db.session.add(admin)
        print("Created new admin user.")
    
    admin.set_password('123456')
    
    # Seed Geographic Data
    from models import Country, Governorates, Directorate
    if not Country.query.first():
        c = Country(Country_Name='اليمن')
        db.session.add(c)
        db.session.flush() # get id
        
        g = Governorates(G_Name='صنعاء', CountryID=c.CountryID)
        db.session.add(g)
        db.session.flush()
        
        d = Directorate(Disc_Name='السبعين', G_ID=g.G_ID)
        db.session.add(d)

    # Seed Days
    from models import Days, Lessons, Terms, TypeExams
    if not Days.query.first():
        days = ['الأحد', 'الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس']
        for d in days:
            db.session.add(Days(DName=d))
            
    # Seed Lessons
    if not Lessons.query.first():
        lessons = ['الحصة الأولى', 'الحصة الثانية', 'الحصة الثالثة', 'الحصة الرابعة', 'الحصة الخامسة', 'الحصة السادسة', 'الحصة السابعة']
        for l in lessons:
            db.session.add(Lessons(LessonName=l))
            
    # Seed Terms
    if not Terms.query.first():
        terms = ['الترم الأول', 'الترم الثاني']
        for t in terms:
            db.session.add(Terms(T_Name=t))

    # Seed Exam Types
    if not TypeExams.query.first():
        exams = ['نصف الترم', 'نهاية الترم', 'اختبار شهري', 'مشاركة']
        for e in exams:
            db.session.add(TypeExams(ExamName=e))

    # Create Audit Logs table and Triggers
    try:
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
        print("Created audit_logs table and trg_marks_update Trigger.")
    except Exception as e:
        print("Failed to create audit trigger:", e)

    db.session.commit()
    
    # Create Database View for Student Grades
    try:
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
            JOIN Teacher t ON m.TeacherID = t.TeacherID
            JOIN TypeExams te ON m.ExamID = te.ExamID
            JOIN Terms tm ON m.T_ID = tm.T_ID
            WHERE m.is_deleted = False;
        '''))
        print("Created vw_student_grades View.")
    except Exception as e:
        print("Failed to create view:", e)

    # Create Stored Procedure for Adding Grade securely
    try:
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
        print("Created sp_add_grade Stored Procedure.")
    except Exception as e:
        print("Failed to create procedure:", e)

    db.session.commit()
    print("Database seeded and Admin password has been reset to '123456' successfully!")
    print("Test check_password('123456'):", admin.check_password('123456'))
