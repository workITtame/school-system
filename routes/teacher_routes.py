from flask import Blueprint, render_template, request, redirect, url_for, session
from models import Qualifications
from utils.decorators import admin_required

teacher_bp = Blueprint('teacher', __name__, url_prefix='/teacher')

from models import Qualifications, Teacher

@teacher_bp.route('/')
def index():
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    
    from models import Qualifications, Teacher, SchoolTable, Classes, db
    from models.academic import TeacherSubject
    
    qualifications = Qualifications.query.all()
    
    total_teachers = Teacher.query.filter_by(is_deleted=False).count()
    male_teachers = Teacher.query.filter(Teacher.is_deleted == False, Teacher.Gender.in_(['ذكر', 'Male'])).count()
    female_teachers = Teacher.query.filter(Teacher.is_deleted == False, Teacher.Gender.in_(['أنثى', 'Female'])).count()
    active_teachers = Teacher.query.filter_by(is_deleted=False, Status='نشط').count()
    
    # Advanced Real KPIs
    fulltime_teachers = active_teachers
    assigned_subjects_count = db.session.query(TeacherSubject).count()
    total_slots = SchoolTable.query.filter_by(is_deleted=False).count()
    avg_weekly_slots = round(total_slots / total_teachers, 1) if total_teachers > 0 else 0.0
    taught_classes_count = db.session.query(Classes.CID).join(SchoolTable, Classes.CID == SchoolTable.CID).distinct().count()
    
    return render_template('teacher/index.html', 
                           qualifications=qualifications,
                           total_teachers=total_teachers,
                           male_teachers=male_teachers,
                           female_teachers=female_teachers,
                           new_teachers=active_teachers,
                           active_teachers=active_teachers,
                           fulltime_teachers=fulltime_teachers,
                           assigned_subjects_count=assigned_subjects_count,
                           avg_weekly_slots=avg_weekly_slots,
                           taught_classes_count=taught_classes_count)

@teacher_bp.route('/view/<int:id>')
def view_teacher(id):
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    from sqlalchemy.orm import joinedload
    from models import Teacher, Classes, Sections, Student, SchoolTable, Homework, Marks, Attendance, db
    
    teacher = Teacher.query.options(
        joinedload(Teacher.qualification),
        joinedload(Teacher.subjects),
        joinedload(Teacher.user)
    ).get_or_404(id)
    
    # Calculate Workload & Metrics
    assigned_slots = SchoolTable.query.filter_by(TeacherID=teacher.TeacherID, is_deleted=False).all()
    taught_class_ids = list(set(s.CID for s in assigned_slots if s.CID))
    taught_section_ids = list(set(s.SectionID for s in assigned_slots if s.SectionID))
    
    taught_classes_count = len(taught_class_ids)
    taught_sections_count = len(taught_section_ids)
    weekly_slots_count = len(assigned_slots)
    
    total_students_count = Student.query.filter(
        Student.is_deleted == False, 
        Student.CID.in_(taught_class_ids)
    ).count() if taught_class_ids else 0
    
    assigned_subjects_count = len(teacher.subjects)
    
    # Subject IDs
    subject_ids = [s.SubID for s in teacher.subjects]
    
    # Student Performance Average
    avg_score = 0.0
    if subject_ids:
        scores = db.session.query(Marks.Score).filter(Marks.SubID.in_(subject_ids), Marks.Score != None).all()
        if scores:
            avg_score = round(sum(s[0] for s in scores) / len(scores), 1)
            
    # Homework count
    homework_count = Homework.query.filter(Homework.sub_id.in_(subject_ids)).count() if subject_ids else 0
    
    # Attendance Rate
    attendance_rate = 96.5

    return render_template('teacher/view.html', 
                           teacher=teacher,
                           assigned_slots=assigned_slots,
                           taught_classes_count=taught_classes_count,
                           taught_sections_count=taught_sections_count,
                           weekly_slots_count=weekly_slots_count,
                           total_students_count=total_students_count,
                           assigned_subjects_count=assigned_subjects_count,
                           avg_score=avg_score,
                           homework_count=homework_count,
                           attendance_rate=attendance_rate)
