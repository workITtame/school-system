from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, Student, Subject, Classes, Sections, Terms, TypeExams, DetailMarks, Marks, Teacher

grades_bp = Blueprint('grades_legacy', __name__, url_prefix='/grades_legacy')

@grades_bp.route('/', methods=['GET'])
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return redirect(url_for('grades.manage_grades'))

@grades_bp.route('/manage', methods=['GET'])
def manage_grades():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
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
def student_report_page():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    classes = Classes.query.all()
    terms = Terms.query.all()
    exams = TypeExams.query.all()
    
    # Optional logic to fetch a specific student report if parameters are provided
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
