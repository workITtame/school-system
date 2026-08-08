from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from models import db, Student, Subject, Classes, Sections, Terms, TypeExams, DetailMarks, Marks, Teacher

grades_bp = Blueprint('grades', __name__, url_prefix='/grades')
grades_legacy_bp = Blueprint('grades_legacy', __name__, url_prefix='/grades_legacy')

@grades_bp.route('/', methods=['GET'])
@grades_legacy_bp.route('/', methods=['GET'])
def index():
    if not current_user.is_authenticated and 'user_id' not in session:
        return redirect(url_for('auth.login'))
    user_role = getattr(current_user, 'role', '').strip("'") if current_user and hasattr(current_user, 'role') else None
    if user_role == 'teacher':
        return redirect(url_for('gradebook.index'))
    return redirect(url_for('grades.manage_grades'))

@grades_bp.route('/manage', methods=['GET'])
@grades_legacy_bp.route('/manage', methods=['GET'])
def manage_grades():
    if not current_user.is_authenticated and 'user_id' not in session:
        return redirect(url_for('auth.login'))
    user_role = getattr(current_user, 'role', '').strip("'") if current_user and hasattr(current_user, 'role') else None
    if user_role == 'teacher':
        return redirect(url_for('gradebook.index'))
        
    total_students = Student.query.filter_by(is_deleted=False).count()
    total_exams = TypeExams.query.filter_by(is_deleted=False).count()
    total_subjects = Subject.query.filter_by(is_deleted=False).count()
    total_classes = Classes.query.filter_by(is_deleted=False).count()
    
    all_marks = Marks.query.all()
    total_marks_count = len(all_marks)
    
    scores = [float(m.Score) for m in all_marks if m.Score is not None]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0
    max_score = max(scores) if scores else 0.0
    min_score = min(scores) if scores else 0.0
    
    pass_count = sum(1 for s in scores if s >= 60)
    fail_count = sum(1 for s in scores if s < 60)
    pass_rate = round((pass_count / len(scores)) * 100, 1) if scores else 0.0
    fail_rate = round((fail_count / len(scores)) * 100, 1) if scores else 0.0
    
    rating_label = 'ممتاز جداً' if avg_score >= 90 else ('جيد جداً' if avg_score >= 80 else ('جيد' if avg_score >= 70 else ('مقبول' if avg_score >= 60 else 'ضعيف')))
    
    terms = Terms.query.filter_by(is_deleted=False).all()
    classes = Classes.query.filter_by(is_deleted=False).all()
    exams = TypeExams.query.filter_by(is_deleted=False).all()
    subjects = Subject.query.filter_by(is_deleted=False).all()
    
    stats = {
        "total_students": total_students,
        "total_exams": total_exams,
        "total_subjects": total_subjects,
        "total_classes": total_classes,
        "total_marks_count": total_marks_count,
        "avg_score": avg_score,
        "max_score": max_score,
        "min_score": min_score,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "pass_rate": pass_rate,
        "fail_rate": fail_rate,
        "rating_label": rating_label
    }

    all_students = Student.query.filter_by(is_deleted=False).order_by(Student.SName).all()

    return render_template('grades/manage.html', 
                           stats=stats, 
                           terms=terms, 
                           classes=classes, 
                           exams=exams, 
                           subjects=subjects,
                           all_students=all_students)

@grades_bp.route('/report', methods=['GET'])
@grades_legacy_bp.route('/report', methods=['GET'])
def student_report_page():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    classes = Classes.query.all()
    terms = Terms.query.all()
    exams = TypeExams.query.all()
    
    student_id = request.args.get('student_id')
    term_id = request.args.get('term_id')
    exam_id = request.args.get('exam_id')
    
    report_data = None
    if student_id and term_id and exam_id:
        student = Student.query.get(student_id)
        if student:
            marks = Marks.query.filter_by(SID=student_id, T_ID=term_id, ExamID=exam_id).all()
            report_data = {
                "student": student,
                "marks": marks
            }
            
    return render_template('grades/student_report.html', 
                           classes=classes, 
                           terms=terms, 
                           exams=exams, 
                           report_data=report_data)

@grades_bp.route('/add_exam', methods=['POST'])
@grades_legacy_bp.route('/add_exam', methods=['POST'])
def add_exam():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    exam_name = request.form.get('exam_name') or request.form.get('ExamName')
    if exam_name:
        try:
            new_type = TypeExams(ExamName=exam_name)
            db.session.add(new_type)
            db.session.commit()
            flash('تم إضافة نوع الاختبار بنجاح', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'خطأ عند الإضافة: {e}', 'danger')
    return redirect(url_for('grades.manage_grades'))

