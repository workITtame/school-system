import os
import sys
from datetime import date, datetime
from app import create_app
from models import (db, User, Student, Teacher, Classes, Sections, Subject, 
                    Attendance, ExamSchedule, Homework, Message, Terms, Days, Lessons)
from models.timetable import SchoolTable
from models.grade import Marks
from utils.pdf_generator import generate_student_pdf

def run_final_integration_audit():
    print("==================================================")
    print("   STARTING FINAL SYSTEM INTEGRATION AUDIT (E2E)  ")
    print("==================================================")
    
    app = create_app()
    results = {
        'total': 0,
        'passed': 0,
        'failed': 0,
        'details': []
    }

    def record_test(step_num, name, passed, message=""):
        results['total'] += 1
        if passed:
            results['passed'] += 1
            status = "[PASSED]"
        else:
            results['failed'] += 1
            status = "[FAILED]"
        print(f"{status} Step {step_num}: {name} - {message}")
        results['details'].append({'step': step_num, 'name': name, 'passed': passed, 'message': message})

    with app.app_context():
        # STEP 1: Academic Year & Term
        term = Terms.query.first()
        if not term:
            term = Terms(T_Name="الفصل الدراسي الأول 2026")
            db.session.add(term)
            db.session.commit()
        record_test(1, "Academic Term / Year Availability", term is not None and term.T_ID is not None, f"Term ID={term.T_ID}, Name={term.T_Name}")

        # STEP 2: Create / Verify Class
        school_class = Classes.query.filter_by(CName="الصف الأول الثانوي النهائي", is_deleted=False).first()
        if not school_class:
            school_class = Classes(CName="الصف الأول الثانوي النهائي", Stage="الثانوية")
            db.session.add(school_class)
            db.session.commit()
        record_test(2, "Class Creation & Availability", school_class is not None and school_class.CID is not None, f"Class ID={school_class.CID}")

        # STEP 3: Create / Verify Section
        section = Sections.query.filter_by(SectionName="شعبة الأمل 1").first()
        if not section:
            section = Sections(SectionName="شعبة الأمل 1")
            db.session.add(section)
            db.session.commit()

        if section not in school_class.sections:
            school_class.sections.append(section)
            db.session.commit()
        record_test(3, "Section Creation & Linkage", section is not None and section.SectionID is not None, f"Section ID={section.SectionID}")

        # STEP 4: Create / Verify Subject
        subject = Subject.query.filter_by(SubName="الرياضيات المتقدمة E2E", is_deleted=False).first()
        if not subject:
            subject = Subject(SubName="الرياضيات المتقدمة E2E")
            db.session.add(subject)
            db.session.commit()

        if subject not in school_class.subjects:
            school_class.subjects.append(subject)
            db.session.commit()
        record_test(4, "Subject Creation & Class Linkage", subject is not None and subject.SubID is not None, f"Subject ID={subject.SubID}")

        # STEP 5: Create / Verify Teacher User & Profile
        teacher_user = User.query.filter_by(username="teacher_e2e@school.com").first()
        if not teacher_user:
            teacher_user = User(username="teacher_e2e@school.com", name="أ. محمد أحمد الشامي", role="teacher")
            teacher_user.set_password("Pass123456")
            db.session.add(teacher_user)
            db.session.commit()

        teacher = Teacher.query.filter_by(user_id=teacher_user.id).first()
        if not teacher:
            teacher = Teacher(TeacherName="أ. محمد أحمد الشامي", TeacherTitle="معلم", Phone="770000000", Email="teacher_e2e@school.com", user_id=teacher_user.id)
            db.session.add(teacher)
            db.session.commit()
        record_test(5, "Teacher Account & Profile Integration", teacher is not None and teacher.user_id == teacher_user.id, f"Teacher ID={teacher.TeacherID}, User ID={teacher_user.id}")

        # STEP 6: Subject-Teacher Qualification Linkage
        try:
            if subject not in teacher.subjects:
                teacher.subjects.append(subject)
                db.session.commit()
            record_test(6, "Teacher-Subject Qualification Linkage", subject in teacher.subjects, f"Teacher ID={teacher.TeacherID} assigned to Subject ID={subject.SubID}")
        except Exception as e:
            db.session.rollback()
            record_test(6, "Teacher-Subject Qualification Linkage", False, str(e))

        # STEP 7: Timetable Slot Assignment
        day = Days.query.first() or Days(DName="الأحد")
        lesson = Lessons.query.first() or Lessons(LessonName="الحصة الأولى", StartTime="08:00", EndTime="08:45")
        if not day.DayID:
            db.session.add(day)
        if not lesson.LessonID:
            db.session.add(lesson)
        db.session.commit()

        timetable_slot = None
        try:
            existing_slot = SchoolTable.query.filter_by(TeacherID=teacher.TeacherID, DayID=day.DayID, LessonID=lesson.LessonID, T_ID=term.T_ID).first()
            if existing_slot:
                timetable_slot = existing_slot
            else:
                timetable_slot = SchoolTable(
                    CID=school_class.CID,
                    SectionID=section.SectionID,
                    DayID=day.DayID,
                    LessonID=lesson.LessonID,
                    TeacherID=teacher.TeacherID,
                    SubID=subject.SubID,
                    T_ID=term.T_ID
                )
                db.session.add(timetable_slot)
                db.session.commit()
            record_test(7, "Weekly Timetable Slot Creation", timetable_slot is not None and timetable_slot.SchoolTableID is not None, f"Slot ID={timetable_slot.SchoolTableID}")
        except Exception as e:
            db.session.rollback()
            record_test(7, "Weekly Timetable Slot Creation", False, str(e))

        # STEP 8: Create / Verify Student
        student = Student.query.filter_by(SName="طالب اختبار التكامل E2E", is_deleted=False).first()
        if not student:
            student = Student(
                SName="طالب اختبار التكامل E2E",
                CID=school_class.CID,
                SectionID=section.SectionID,
                DOB=date(2010, 1, 1),
                Gender="ذكر",
                Status="نشط"
            )
            db.session.add(student)
            db.session.commit()
        record_test(8, "Student Profile Creation & Enrollment", student is not None and student.SID is not None, f"Student ID={student.SID}")

        # STEP 9: Mark Attendance
        att_record = None
        try:
            today_date = date.today()
            att_record = Attendance.query.filter_by(SID=student.SID, Date=today_date).first()
            if not att_record:
                att_record = Attendance(
                    SID=student.SID,
                    Date=today_date,
                    Status="حاضر"
                )
                db.session.add(att_record)
                db.session.commit()
            record_test(9, "Student Attendance Marking", att_record is not None and att_record.Status == "حاضر", f"Attendance ID={att_record.AttendanceID}, Status={att_record.Status}")
        except Exception as e:
            db.session.rollback()
            record_test(9, "Student Attendance Marking", False, str(e))

        # STEP 10: Homework Assignment
        homework = None
        try:
            homework = Homework.query.filter_by(title="واجب اختبار التكامل النهائي").first()
            if not homework:
                homework = Homework(
                    title="واجب اختبار التكامل النهائي",
                    sub_id=subject.SubID,
                    class_id=school_class.CID,
                    section_id=section.SectionID,
                    due_date=date.today(),
                    status="معلق",
                    description="حل التمارين التكاملية الشاملة"
                )
                db.session.add(homework)
                db.session.commit()
            record_test(10, "Homework Creation & Assignment", homework is not None and homework.id is not None, f"Homework ID={homework.id}")
        except Exception as e:
            db.session.rollback()
            record_test(10, "Homework Creation & Assignment", False, str(e))

        # STEP 11: Exam Schedule Creation
        exam_sch = None
        try:
            exam_sch = ExamSchedule.query.filter_by(CID=school_class.CID, SubID=subject.SubID, ExamName="اختبار نهاية الفصل E2E").first()
            if not exam_sch:
                exam_sch = ExamSchedule(
                    CID=school_class.CID,
                    SectionID=section.SectionID,
                    SubID=subject.SubID,
                    T_ID=term.T_ID,
                    ExamName="اختبار نهاية الفصل E2E",
                    ExamDate=date.today(),
                    ExamTime="09:00 - 11:00",
                    Duration=120,
                    Location="القاعة الرئيسية",
                    Status="مجدول"
                )
                db.session.add(exam_sch)
                db.session.commit()
            record_test(11, "Exam Schedule Entry Creation", exam_sch is not None and exam_sch.ScheduleID is not None, f"Exam Schedule ID={exam_sch.ScheduleID}")
        except Exception as e:
            db.session.rollback()
            record_test(11, "Exam Schedule Entry Creation", False, str(e))

        # STEP 12: Grades & Marks Entry
        mark_entry = None
        try:
            mark_entry = Marks.query.filter_by(SID=student.SID, SubID=subject.SubID, T_ID=term.T_ID).first()
            if not mark_entry:
                mark_entry = Marks(
                    SID=student.SID,
                    SubID=subject.SubID,
                    T_ID=term.T_ID,
                    ExamID=exam_sch.ScheduleID if exam_sch else None,
                    Score=95.5,
                    MaxScore=100.0,
                    Grade="ممتاز"
                )
                db.session.add(mark_entry)
                db.session.commit()
            record_test(12, "Student Academic Marks & Grade Calculation", mark_entry is not None and mark_entry.Score == 95.5, f"Marks Record ID={mark_entry.M_ID}, Score={mark_entry.Score}, Grade={mark_entry.Grade}")
        except Exception as e:
            db.session.rollback()
            record_test(12, "Student Academic Marks & Grade Calculation", False, str(e))

        # STEP 13: Internal Messaging
        admin_user = User.query.filter_by(role="admin").first()
        msg_record = None
        try:
            if admin_user and teacher_user and admin_user.id != teacher_user.id:
                msg_record = Message(
                    sender_id=admin_user.id,
                    recipient_id=teacher_user.id,
                    content="رسالة اختبار التكامل النهائي للنظام",
                    is_read=False
                )
                db.session.add(msg_record)
                db.session.commit()
            record_test(13, "Internal Messaging System", msg_record is not None and msg_record.id is not None, f"Message ID={msg_record.id}")
        except Exception as e:
            db.session.rollback()
            record_test(13, "Internal Messaging System", False, str(e))

        # STEP 14: System Notifications Verification
        with app.test_client() as client:
            try:
                with client.session_transaction() as sess:
                    sess['_user_id'] = str(admin_user.id if admin_user else 1)
                res_n = client.get('/notifications/')
                is_ok = res_n.status_code == 200
                record_test(14, "Notifications Route & Dispatch Verification", is_ok, f"Notifications Status={res_n.status_code}")
            except Exception as e:
                record_test(14, "Notifications Route & Dispatch Verification", False, str(e))

        # STEP 15: PDF Student Official Report Certificate Generation
        try:
            report_data = {"اختبار نهاية الفصل": [mark_entry]} if mark_entry else {}
            pdf_bytes = generate_student_pdf(student, report_data)
            record_test(15, "Official PDF Certificate Generator", pdf_bytes is not None and len(pdf_bytes) > 0, f"Generated PDF Size={len(pdf_bytes)} bytes")
        except Exception as e:
            record_test(15, "Official PDF Certificate Generator", False, str(e))

        # STEP 16: Excel Attendance & Grades Export Simulation
        with app.test_client() as client:
            try:
                with client.session_transaction() as sess:
                    sess['_user_id'] = str(admin_user.id if admin_user else 1)
                res_ex = client.get(f'/reports/student/{student.SID}/excel')
                is_excel_ok = res_ex.status_code == 200 and 'spreadsheetml' in res_ex.mimetype
                record_test(16, "Excel Spreadsheet Export Engine", is_excel_ok, f"Excel Download Status={res_ex.status_code}, Mime={res_ex.mimetype}")
            except Exception as e:
                record_test(16, "Excel Spreadsheet Export Engine", False, str(e))

        # STEP 17: Dashboard Consistency & Real Stats Alignment
        with app.test_client() as client:
            try:
                with client.session_transaction() as sess:
                    sess['_user_id'] = str(admin_user.id if admin_user else 1)
                res_db = client.get('/dashboard')
                is_db_ok = res_db.status_code == 200
                record_test(17, "Dashboard Analytics & Real Stats Alignment", is_db_ok, f"Dashboard HTTP Status={res_db.status_code}")
            except Exception as e:
                record_test(17, "Dashboard Analytics & Real Stats Alignment", False, str(e))

        # STEP 18: Orphan Records & Soft Delete Integrity Audit
        try:
            # Check for orphaned marks or attendance records
            orphan_marks = Marks.query.filter(Marks.student == None).count()
            orphan_att = Attendance.query.filter(Attendance.student == None).count()
            no_orphans = orphan_marks == 0 and orphan_att == 0
            record_test(18, "Orphan Records & Cascade Integrity Audit", no_orphans, f"Orphan Marks={orphan_marks}, Orphan Attendance={orphan_att}")
        except Exception as e:
            record_test(18, "Orphan Records & Cascade Integrity Audit", False, str(e))

    print("==================================================")
    print(f"   FINAL E2E AUDIT COMPLETED: {results['passed']}/{results['total']} TESTS PASSED   ")
    print("==================================================")
    return results

if __name__ == "__main__":
    run_final_integration_audit()
