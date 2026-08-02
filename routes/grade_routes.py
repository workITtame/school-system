from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, Student, Subject, Classes, Sections, Terms, TypeExams, DetailMarks, Marks, Teacher

grades_bp = Blueprint('grades', __name__, url_prefix='/grades')

@grades_bp.route('/manage', methods=['GET'])
def manage_grades():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return render_template('grades/manage.html')

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
