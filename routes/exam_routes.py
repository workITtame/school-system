from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, ExamSchedule, Subject, Classes, Sections, TypeExams
from datetime import datetime
from utils.decorators import admin_required

exams_bp = Blueprint('exams', __name__, url_prefix='/exams')

@exams_bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    schedules = ExamSchedule.query.order_by(ExamSchedule.ExamDate.desc()).all()
    subjects = Subject.query.filter_by(is_deleted=False).all()
    classes = Classes.query.filter_by(is_deleted=False).all()
    exam_types = TypeExams.query.all()
    
    total_exams = len(schedules)
    active_exams = sum(1 for s in schedules if s.Status == 'مفعل')
    upcoming_exams = sum(1 for s in schedules if s.Status == 'مجدول')
    finished_exams = sum(1 for s in schedules if s.Status == 'منتهي')
    
    return render_template('exams/index.html',
                           schedules=schedules,
                           subjects=subjects,
                           classes=classes,
                           exam_types=exam_types,
                           total_exams=total_exams,
                           active_exams=active_exams,
                           upcoming_exams=upcoming_exams,
                           finished_exams=finished_exams)

@exams_bp.route('/add', methods=['POST'])
@admin_required
def add_exam():
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    
    sub_id = request.form.get('sub_id')
    class_id = request.form.get('class_id')
    exam_date = request.form.get('exam_date')
    exam_time = request.form.get('exam_time')
    exam_type = request.form.get('exam_type')
    status = request.form.get('status', 'مجدول')
    
    if sub_id and class_id and exam_date and exam_time:
        try:
            date_obj = datetime.strptime(exam_date, '%Y-%m-%d').date()
            new_exam = ExamSchedule(
                SubID=sub_id,
                CID=class_id,
                ExamDate=date_obj,
                ExamTime=exam_time,
                ExamName=exam_type,
                Status=status
            )
            db.session.add(new_exam)
            db.session.commit()
            flash('تمت إضافة الاختبار بنجاح', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ: {str(e)}', 'danger')
    else:
        flash('جميع الحقول مطلوبة', 'warning')
        
    return redirect(url_for('exams.index'))

@exams_bp.route('/delete/<int:id>', methods=['POST'])
@admin_required
def delete_exam(id):
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    exam = ExamSchedule.query.get_or_404(id)
    try:
        db.session.delete(exam)
        db.session.commit()
        flash('تم حذف الاختبار بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء الحذف: {str(e)}', 'danger')
    return redirect(url_for('exams.index'))
